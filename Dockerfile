# Stage 1: Build liboqs and Pybind11 extension
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    ninja-build \
    git \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy project files needed for building
COPY liboqs_src ./liboqs_src
COPY aegis_engine.cpp .
COPY CMakeLists.txt .
COPY pyproject.toml .
COPY requirements.txt .

# Build liboqs
RUN cd liboqs_src && \
    mkdir build && cd build && \
    cmake -GNinja -DOQS_USE_OPENSSL=OFF -DBUILD_SHARED_LIBS=ON .. && \
    ninja && \
    ninja install

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install pybind11

# Build Pybind11 extension
# We use cmake directly or we can let pip install -e . do it if we had a setup.py
# Since we just have CMakeLists.txt, let's build the shared library manually 
RUN mkdir build_pybind && cd build_pybind && \
    cmake -DPython3_EXECUTABLE=/opt/venv/bin/python .. && \
    make && \
    cp aegis_engine*.so /build/

# Stage 2: Runtime
FROM python:3.11-slim

# Install runtime dependencies for liboqs (if any, e.g. libssl if we used it, but we disabled OpenSSL)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy virtual environment
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy liboqs shared libraries from builder (installed in /usr/local)
COPY --from=builder /usr/local/lib/liboqs* /usr/local/lib/
# Update ldconfig so the shared library is found
RUN ldconfig

# Copy compiled python extension
COPY --from=builder /build/aegis_engine*.so /app/

# Copy the rest of the application
COPY . /app/

# Install the Python package in editable mode so aegis_ml is available
RUN pip install -e .

EXPOSE 8000

# Healthcheck for FastAPI
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

# Run the FastAPI server via Uvicorn
CMD ["uvicorn", "module4_dashboard:app", "--host", "0.0.0.0", "--port", "8000"]

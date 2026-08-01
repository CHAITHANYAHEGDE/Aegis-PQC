FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Install build dependencies for C++ extensions
RUN apt-get update && apt-get install -y cmake build-essential python3-dev && rm -rf /var/lib/apt/lists/*

CMD ["python3", "phase11_5_pipeline.py"]

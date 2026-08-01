# Installation Guide

## Prerequisites
- **Operating System:** Linux, macOS, or Windows (via WSL2).
- **Compiler:** GCC/Clang with C++17 support.
- **CMake:** Version 3.20 or newer.
- **Python:** Version 3.11+.
- **Docker** (Optional, for containerized deployments).

## 1. Clone the Repository
```bash
git clone https://github.com/example/aegis-pqc.git
cd aegis-pqc
```

## 2. Initialize Submodules (liboqs)
```bash
git submodule update --init --recursive
```

## 3. Python Virtual Environment
We recommend using a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Build the C++ Engine (aegis_engine)
The build process uses CMake to compile `liboqs` and our pybind11 extension (`aegis_engine`).
```bash
mkdir -p build && cd build
cmake ..
make -j$(nproc)
cd ..
```

## 5. Verify Installation
Run a quick smoke test to verify the pybind11 module:
```bash
python3 -c "import aegis_engine; print(aegis_engine.get_supported_algorithms())"
```
If you see a list of algorithms like `['ML-KEM-512', 'ML-KEM-768']`, the setup is successful!

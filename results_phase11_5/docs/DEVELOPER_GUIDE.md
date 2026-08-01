# Developer Guide

## Environment Setup
1. **C++17 Compiler**: GCC 9+ or Clang 10+.
2. **CMake**: Version 3.14 or higher.
3. **ONNX Runtime**: `onnxruntime` libraries must be available in your system path or linked statically.
4. **Python**: Python 3.11+ with `pybind11` installed (`pip install pybind11`).

## Compiling the Native Engine
```bash
mkdir build && cd build
cmake -DCMAKE_CXX_STANDARD=17 ..
make -j4
```
This generates `aegis_engine.cpython-311-*.so` which can be imported directly in Python.

## Training New Models
1. Ensure your hardware supports Performance Monitoring Units (PMU).
2. Run `export_models.py` to gather telemetry and export a new `.onnx` file.
3. Replace the `rf_model.onnx` in the root directory with your newly trained model.
4. The C++ engine automatically loads `rf_model.onnx` upon instantiation.

## Testing and Validation
Run the full suite of statistical tests to ensure your new model doesn't regress on F1, ROC-AUC, or Latency:
```bash
python3.11 phase11_5_pipeline.py
python3.11 scalability_benchmark.py
```

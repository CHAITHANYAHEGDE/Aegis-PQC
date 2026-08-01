# Architecture Guide

Aegis-PQC employs a **Synchronous Inline Mitigation Architecture**. Unlike traditional Intrusion Detection Systems (IDS) that evaluate logs asynchronously, Aegis-PQC embeds the AI evaluation directly into the cryptographic request lifecycle.

## 1. Request Flow
1. **Application Call**: The host application invokes `run_crypto("ML-KEM-512")`.
2. **Pre-Execution Hook**: Telemetry snapshot (Hardware PMU & Software usage) is taken.
3. **PQC Execution**: The underlying C/C++ crypto library (e.g., `liboqs`) performs Key Encapsulation or Signature.
4. **Post-Execution Hook**: Second telemetry snapshot is taken.
5. **Feature Fusion**: The delta between snapshots is parsed into an ONNX-compatible tensor.
6. **ONNX Inference**: The pre-trained AI model evaluates the tensor (e.g., Random Forest `rf_model.onnx`).
7. **Policy Engine**: If the probability of anomaly exceeds a calibrated threshold, the mitigation strategy (Throttling, Random Delay, Key Rotation) is triggered.
8. **Return**: The functional return is provided to the host application.

## 2. Telemetry Subsystem
- **Software Metrics**: `execution_time_us`, `max_rss_kb`, `context_switches`, `cpu_usage`.
- **Hardware Counters**: Requires Ring-0 access to read `hw_cpu_cycles`, `hw_cache_misses`, `hw_branch_misses`, etc., via Linux `perf_event_open`.

## 3. C++ / Python Boundary
The core is written in C++17 to leverage `onnxruntime_cxx_api.h` and raw system calls, avoiding the Python Global Interpreter Lock (GIL). The Python API (`aegis_engine.so`) uses `pybind11` purely as a thin wrapper for training, benchmarking, and FastAPI orchestration.

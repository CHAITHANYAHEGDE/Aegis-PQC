# Phase 11 Repository Review & Audit

## 1. Existing Architecture Overview
Aegis PQC integrates the `liboqs` cryptographic library with a Python-based anomaly detection backend.
- **`aegis_engine.cpp`**: C++ PyBind11 wrapper. Executes crypto and harvests both software telemetry (RSS, execution time) and true hardware counters (Linux perf_event).
- **`aegis_ml/hardware/`**: Provides the telemetry abstraction (Hardware/Software modes).
- **`aegis_ml/models/`**: Implements Anomaly Detection models (Autoencoder, Isolation Forest, Random Forest, Temporal LSTMs).
- **`aegis_ml/countermeasures/`**: Implements the Response Policy engine in Python, triggering delays/logging based on Python anomaly scores.
- **`module4_dashboard.py`**: FastAPI UI for real-time visualization of telemetry and mitigations.

## 2. Missing Components for Production Runtime
1. **Native C++ ML Inference**: The C++ engine currently hands off telemetry to Python. To be a production runtime, the C++ layer must execute ML inference inline using an engine like ONNX Runtime.
2. **Native Telemetry Fusion**: The fusion of software and hardware metrics currently happens in Python (`aegis_ml/fusion.py`). This must be ported to C++ to avoid context switching.
3. **Native Policy Engine**: The `ResponsePolicy` logic inside `aegis_ml/countermeasures/` is purely Python-based. The C++ runtime must independently evaluate thresholds, attack persistence, and cooldowns.

## 3. Code Smells & Technical Debt
- **Context-Switching Overhead**: The primary debt is the reliance on Python for security-critical decisions. `aegis_engine.run_crypto()` returns data, Python evaluates it, and then Python injects countermeasures on *subsequent* requests. This asynchronous loop leaves a critical window where attacks might succeed before mitigation activates.
- **Feature Pipeline Duplication**: Feature scaling and PCA transformation in Python will need to be exactly replicated or exported to C++ to ensure deterministic inference.
- **Hardcoded Thresholds**: Certain EWMA thresholds in `aegis_ml/models/adaptive_threshold.py` are coupled to the dataset rather than dynamically calibrated in C++.

## 4. Reuse Opportunities
- **ONNX Exportable Models**: The `Autoencoder` (PyTorch) and `RandomForest` (scikit-learn via `skl2onnx`) can be exported effortlessly without rewriting model architectures in C++.
- **`aegis_engine.cpp` Telemetry Loops**: The `PerfGroup` hardware telemetry system built in Phase 10 is perfectly positioned for native inline inference; we only need to pass the struct to the ONNX graph instead of returning it to Python.
- **Python Research Pipeline**: The existing `benchmark_phase*.py` and `aegis_ml` infrastructure can be entirely preserved as an offline training and analysis platform. We will only change the "inference" step in production.

## 5. Files to be Modified during Phase 11
- `aegis_engine.cpp`: Add ONNX runtime integration, C++ fusion, and synchronous countermeasure execution.
- `CMakeLists.txt`: Link `onnxruntime`.
- `aegis_ml/models/`: Add `export_onnx()` methods.
- `benchmark_phase11.py` (NEW): Compare native latency vs Python latency.
- `tests/test_native_runtime.py` (NEW): Validate C++ inference matches Python.
- `module4_dashboard.py` / `index.html`: Expose runtime backend status (Native vs Python).
- `PATENT_NOTES.md` (NEW): Document architectural contributions.
- `README.md` & `docs/ARCHITECTURE.md`: Update to reflect the native edge architecture.

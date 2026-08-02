# Aegis-PQC: Post-Quantum Cryptography AI Shield

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![C++17](https://img.shields.io/badge/C++-17-blue.svg)](https://en.cppreference.com/w/cpp/17)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![Status: Research Prototype](https://img.shields.io/badge/Status-Research_Prototype-orange.svg)]()

> **Note:** Aegis-PQC is a v1.0.1 research prototype. Current performance metrics are based on **synthetic telemetry simulation** and have not been validated against physical PMU side-channel data.

---

## 📖 Introduction

Aegis-PQC is a highly optimized, cross-language anomaly detection engine designed to protect Post-Quantum Cryptographic (PQC) algorithms from timing and cache-based side-channel attacks. By tightly coupling `liboqs` cryptographic operations with synchronous native C++ Machine Learning inference (via ONNX Runtime), Aegis-PQC evaluates telemetry *during* execution and proactively throttles or obfuscates compromised keys before they are returned to the caller.

### ❓ Why This Project Exists
As the world transitions to Post-Quantum Cryptography (e.g., ML-KEM, ML-DSA), early software implementations are often vulnerable to microarchitectural side-channel attacks. Traditional defenses (like constant-time programming) are difficult to maintain and verify perfectly. Aegis-PQC explores a heuristic defense layer: using high-speed machine learning models to detect anomalies and inject real-time noise into the execution path.

---

## 🏗 Architecture Overview

Aegis-PQC operates on a strict Native-Edge Architecture to minimize context-switching overhead:

1. **Telemetry Capture:** C++ Native engine hooks into cryptographic routines (e.g., `OQS_KEM_encaps`).
2. **Native Inference:** The captured telemetry is passed directly to an in-memory ONNX Runtime session evaluating a Random Forest model.
3. **Synchronous Mitigation:** If an anomaly is detected, a C++ Policy Engine applies jitter (delay injection) before the function returns.
4. **Python Backend:** A decoupled Python stack handles offline model training, dataset generation, and Dashboard UI updates.

### ✨ Key Innovations
- **Synchronous Mitigation:** Microsecond-scale blocking inference inline with cryptographic execution.
- **Thread-Safe Cryptography:** Robust memory cleanup and thread-safe Meyer's singletons for ML singletons.
- **Cross-Language Decoupling:** Model training in PyTorch/Scikit-Learn, serialized to ONNX for C++ execution.

---

<details>
<summary><h2>🛠 Installation & Build Instructions</h2></summary>

### Requirements
- **OS:** macOS or Linux
- **Compiler:** Clang/GCC supporting C++17
- **Python:** >= 3.11
- **Dependencies:** `liboqs`, `onnxruntime`, `pybind11`, `psutil`, `fastapi`, `uvicorn`

### Build the Native Extension
```bash
git clone https://github.com/your-org/aegis-pqc.git
cd aegis-pqc

# Set up Python environment
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Build the C++ extension
mkdir build && cd build
cmake -DCMAKE_CXX_STANDARD=17 ..
make
```
</details>

---

<details>
<summary><h2>🚀 Running the Suite</h2></summary>

### Running the Dashboard
The FastAPI dashboard visualizes real-time mitigation data.
```bash
python module4_dashboard.py
# Navigate to http://localhost:8000
```

### Running Validation
Execute the complete end-to-end dataset generation, training, and cross-validation pipeline:
```bash
python phase11_5_pipeline.py
```

### Running Benchmarks
Measure the native latency and throughput of the inline ML engine:
```bash
python benchmark_phase11.py
```
</details>

---

## 📊 Performance Summary

The framework has been benchmarked for latency overhead strictly inside the C++ runtime.

### Benchmark Tables
*Hardware: Apple M3, macOS 26.5.2, Apple Clang 21.0.0 (Sequential 1 Thread)*

| Metric | Measurement | Notes |
|--------|-------------|-------|
| **1 TPS Latency (p99)** | 444µs | Includes observed C-state sleep overheads. |
| **5000 TPS Latency (p99)** | 46µs | Peak throughput overhead per operation. |
| **Max Throughput** | 5000+ TPS / core | Scales efficiently with ML-KEM-512 operations. |

---

## 🛡 Threat Model & Security Considerations

### Threat Model
The adversary is assumed to have unprivileged code execution on the same physical machine as the victim (e.g., cloud multi-tenancy) and is attempting to extract PQC secrets via shared L3 cache monitoring (Flush+Reload) or precise timing interrupts.

### Limitations
- **Synthetic Telemetry:** Hardware telemetry is currently generated via synthetic mathematical proxies. Physical PMU validation is required.
- **Perfect Separability Bias:** The 1.000 F1 scores achieved during validation represent perfect separability of the *synthetic* data generation script, not physical attack data. 
- **Thermal Throttling FPs:** The system is susceptible to False Positives induced by high CPU contention or thermal throttling, which masquerades as timing attacks.

---

## 🔬 Research & Future Work

### Research Contributions
1. **Coupled Execution:** First-pass architecture for tight telemetry-crypto coupling.
2. **In-Band Mitigation:** Proof-of-concept for real-time delay injection based on ML outputs.

### Future Work
- Integration with Linux `perf_event_open` for true L3 cache miss harvesting.
- Porting to ARM CoreSight for PMU validation on Apple Silicon.
- Deep Learning models (LSTM) for sequence-based anomaly tracking in C++.

---

## 🤝 Contributing
We welcome contributions from security researchers and engineers! 
1. Open an issue describing your proposed changes.
2. Submit a Pull Request.
3. Ensure all tests and benchmarks pass locally before requesting review.

---

## 📝 License
This project is licensed under the [MIT License](LICENSE).

## 📚 Citation
If you use Aegis-PQC in your research, please cite:
```bibtex
@software{aegis_pqc_2026,
  author = {Your Name},
  title = {Aegis-PQC: Post-Quantum Cryptography AI Shield},
  year = {2026},
  url = {https://github.com/your-org/aegis-pqc}
}
```

## 🙏 Acknowledgements
Special thanks to the open-source contributors of `liboqs`, `onnxruntime`, and `scikit-learn` for enabling this architecture.

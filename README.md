# 🛡️ Real-Time Execution-Introspection Guard for Post-Quantum Cryptographic Systems

> **Patent Pending (Provisional Application in Progress)**

An advanced, low-latency zero-allocation C++20 Post-Quantum Cryptography engine (NIST Kyber-768) integrated with an AI-driven Execution Introspection Guard in Python to mitigate Side-Channel Timing Attacks in real time.

## 🚀 Key Features
- **Modern C++20 Kyber Engine:** Implements polynomial ring arithmetic over $R_q = \mathbb{Z}_q[X]/(X^{256} + 1)$ with $q = 3329$ and zero dynamic memory allocation.
- **AI Execution Introspection Guard:** Analyzes microsecond execution timing traces using statistical Z-score anomaly detection to identify and mask side-channel timing attacks.
- **Dynamic Noise Mitigation:** Automatically injects non-deterministic micro-timing perturbations when an anomaly is detected.

## ⚡ How to Run
```bash
chmod +x run_all.sh
./run_all.sh


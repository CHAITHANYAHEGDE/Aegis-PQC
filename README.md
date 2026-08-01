# 🛡️ Aegis-PQC: Post-Quantum Cryptographic Core & Autonomous AI Threat Guard

![Language](https://img.shields.io/badge/Language-C%2B%2B17%20|%20Python%203.11-blue)
![Security](https://img.shields.io/badge/Security-NIST_PQC_Standard-blue)
![Status](https://img.shields.io/badge/Status-Research_In_Progress-yellow)
![License](https://img.shields.io/badge/License-MIT-green)

> **Hybrid Post-Quantum Cryptographic Engine with Real-Time Neural Side-Channel Attack Detection**

---

## 📋 Overview

Aegis-PQC is a publication-quality cybersecurity architecture combining:

1. **Post-Quantum Cryptography** — Real integration with the `liboqs` (Open Quantum Safe) project, providing native C++ execution of NIST-standardized algorithms (e.g., ML-KEM-512, ML-KEM-768).
2. **AI-Powered Side-Channel Defense** — A modular Machine Learning pipeline featuring PyTorch Autoencoders, Isolation Forests, One-Class SVMs, and Local Outlier Factors for real-time threat detection.
3. **Active Runtime Countermeasure Engine** — A modular plugin system providing response policies like randomized execution delays, request throttling, and forensic logging triggered by model confidence.

The system is designed to be highly extensible, allowing security researchers to seamlessly swap algorithms, inject anomaly profiles, and evaluate ML defense models.

---

## 📚 Documentation

Detailed documentation is available in the `docs/` directory:

- [Installation Guide](docs/INSTALLATION.md)
- [Developer Guide](docs/DEVELOPER_GUIDE.md)
- [Reproducibility Guide](docs/REPRODUCIBILITY.md)
- [Docker Deployment](docs/DOCKER_GUIDE.md)
- [API Reference](docs/API.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [Benchmark Framework](docs/BENCHMARK.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Known Limitations](docs/KNOWN_LIMITATIONS.md)

---

## 🚀 Quick Start

Ensure you have Docker and Docker Compose installed.

> **Note:** Docker configuration has been prepared but has not yet been validated in a local Docker environment. Users should verify the container build after installing Docker.

```bash
git clone https://github.com/CHAITHANYAHEGDE/Aegis-PQC.git
cd Aegis-PQC
git submodule update --init --recursive
docker compose up --build
```

### Running the AI Benchmark

To run the benchmarking suite (training & evaluating anomaly detectors against PQC executions):
```bash
python run_benchmark.py --algo ML-KEM-512 --runs 1000
```
*(Requires local Python environment setup as detailed in the [Installation Guide](docs/INSTALLATION.md))*

---

## 📁 Project Structure

```
Aegis-PQC/
|-- aegis_engine.cpp       # Native C++ pybind11 integration to liboqs
|-- aegis_ml/              # Modular Machine Learning pipeline
|   |-- models/            # Implementations of anomaly detection models
|   |-- countermeasures/   # Active defense response policies and plugins
|   |-- dataset.py         # Telemetry data generation
|   |-- features.py        # Feature engineering and normalization
|   |-- experiment.py      # Experiment metadata tracking
|-- liboqs_src/            # Upstream Open Quantum Safe library
|-- docs/                  # Project documentation suite
|-- run_benchmark.py       # Main ML benchmarking script
|-- benchmark_phase9.py    # Countermeasure overhead benchmarks
|-- module4_dashboard.py   # FastAPI interactive dashboard with defense UI
+-- README.md              # This file
```

---

## 🔬 Research Status

This project is **research in progress**.
Target Venues:
- IEEE Symposium on Security and Privacy (S&P)
- ACM CCS Workshop on Artificial Intelligence and Security (AISec)

## 📄 License

This project is licensed under the MIT License.

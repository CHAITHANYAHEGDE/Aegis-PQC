# Aegis-PQC: Post-Quantum Cryptography AI Shield

Aegis-PQC is a research-grade, real-time side-channel anomaly detection framework designed to protect Post-Quantum Cryptographic (PQC) algorithms. It provides a native C++ runtime that synchronously fuses software-level telemetry and hardware performance counters, feeding them into a highly optimized ONNX ML model to actively throttle or mitigate attacks mid-execution.

## Features
- **Native C++ Performance**: ~20µs latency per cryptographic execution with full AI inference.
- **Synchronous Mitigation**: Rejects or obfuscates keys proactively upon side-channel detection.
- **Hardware-Software Fusion**: Fuses kernel `perf_event` hardware counters with process-level telemetry.
- **Patent-Ready Architecture**: Designed with stringent security boundaries and reproducible validations.
- **Extensive Validation**: Cross-validated with Random Forest and XGBoost across Stratified 5-folds, evaluated with Brier scores, Reliability diagrams, and SHAP explainability.

## Quick Start
```bash
# Clone the repository
git clone https://github.com/your-org/aegis-pqc.git
cd aegis-pqc

# Build Native Extension
mkdir build && cd build
cmake -DCMAKE_CXX_STANDARD=17 ..
make

# Run the Validation Pipeline
cd ..
python3.11 phase11_5_pipeline.py
```

## Documentation
- [Architecture Guide](results_phase11_5/docs/ARCHITECTURE_GUIDE.md): Deep dive into the Native C++ Pipeline.
- [Security Review](results_phase11_5/docs/SECURITY_REVIEW.md): STRIDE Threat Model and Adversarial ML limits.
- [Patent Support](results_phase11_5/docs/PATENT_SUPPORT.md): Candidate novelties.
- [Reproducibility](results_phase11_5/docs/REPRODUCIBILITY.md): Docker configurations and dataset hashes.
- [Failure Analysis](results_phase11_5/docs/failure_analysis.md): Breakdown of False Positives & Negatives.

## CI/CD
Continuous Integration is configured via GitHub Actions in `.github/workflows/validation.yml`, ensuring that all statistical tests, metrics, and latency constraints hold true across builds.

## License
MIT License

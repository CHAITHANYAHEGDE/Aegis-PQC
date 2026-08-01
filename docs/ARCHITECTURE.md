# Architecture Guide

Aegis PQC bridges quantum-safe cryptography with machine learning anomaly detection.

## Stack Overview
- **Core Cryptography (C):** `liboqs` provides reference implementations of NIST-approved algorithms (ML-KEM, ML-DSA).
- **Engine Extension (C++ / pybind11):** `aegis_engine.cpp` acts as the native bridge between Python and C. It executes cryptographic operations and collects real-time execution telemetry (latency, memory usage).
- **ML Pipeline (Python):** `aegis_ml/` processes the telemetry and trains anomaly detection models (Autoencoder, Isolation Forest, OCSVM, LOF).
- **API & UI (Python/HTML):** FastAPI exposes endpoints for real-time inference and a dashboard for visualization.

## Modules
1. `aegis_engine.cpp`: Native wrapper.
2. `aegis_ml/dataset.py`: Extracts features and builds Pandas dataframes from the engine.
3. `aegis_ml/features.py`: Normalization and feature engineering.
4. `aegis_ml/models/`: Implementation of anomaly detectors inheriting `BaseModel`.
5. `aegis_ml/countermeasures/`: Modular plugins for runtime mitigations (Random Delay, Throttling, etc.) managed by `ResponsePolicy`.
6. `run_benchmark.py`: Main entry point for generating data, training models, and generating visual reports.
7. `module4_dashboard.py`: FastAPI server for real-time inference and active defense management.

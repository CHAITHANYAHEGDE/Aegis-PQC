# Developer Guide

Welcome to the Aegis PQC development team! This guide covers coding standards, workflows, and testing.

## Code Style & Linting
We enforce code quality using `ruff` and `black`.

1. **Format Code:**
   ```bash
   black .
   ```
2. **Lint Code:**
   ```bash
   ruff check .
   ```
   *Note:* The `liboqs_src/` directory is excluded from linting.

## Directory Structure
- `aegis_engine.cpp`: Native C++ implementation of the PQC engine (pybind11).
- `aegis_ml/`: Modular ML pipeline for anomaly detection.
- `liboqs_src/`: Upstream quantum-safe cryptographic algorithms.
- `docs/`: Project documentation.
- `tests/`: Pytest test suite.

## Adding a New Model
To add a new anomaly detection model to `aegis_ml`:
1. Create a new file in `aegis_ml/models/` (e.g., `my_model.py`).
2. Inherit from `BaseModel` (found in `aegis_ml/models/base.py`).
3. Implement `fit()`, `predict()`, `score()`, `save()`, and `load()`.
4. Register the model in `aegis_ml/models/registry.py`.

## Running Tests
Run the unit test suite:
```bash
pytest tests/
```

# Reproducibility Guide

A core tenet of Aegis PQC is strict scientific reproducibility. We ensure that benchmarks run on a given machine can be reproduced exactly.

## Environment Logging
When a benchmark is run using `run_benchmark.py`, the `aegis_ml/experiment.py` module captures full system metadata:
- Python, CMake, and Compiler versions.
- OS and CPU architecture.
- `liboqs` and `pybind11` versions.
- Git commit hash (if available).
- Random seeds.

This metadata is saved to `experiments/YYYYMMDD_HHMMSS/metadata.json`.

## Pinning Dependencies
We strictly pin Python dependencies in `requirements.txt` to prevent silent drift in model behavior due to updated libraries.

## Reproducing an Experiment
1. Ensure your hardware matches the metadata specification (optional, but required for timing equivalence).
2. Install the exact dependencies using `pip install -r requirements.txt`.
3. Re-run the benchmark using the same command and algorithms specified in the experiment logs.

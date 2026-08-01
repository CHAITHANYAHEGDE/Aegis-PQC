# Benchmark Guide

The benchmarking framework evaluates how well different AI models detect side-channel anomalies during Post-Quantum Cryptography (PQC) execution.

## Running a Benchmark
```bash
python run_benchmark.py --algo ML-KEM-512 --runs 1000 --outdir custom_experiments
```

### Arguments:
- `--algo`: The PQC algorithm to profile (e.g., `ML-KEM-512`, `ML-KEM-768`).
- `--runs`: Total number of execution traces to gather (50% normal, 50% anomalies).
- `--outdir`: Directory to store metadata, logs, charts, and results.

## Artifacts Generated
Upon completion, the benchmark produces:
- `metrics.json`: Detailed F1, Precision, Recall, and ROC AUC metrics for all models.
- `metadata.json`: System and environment reproducibility info.
- `benchmark.log`: Structured execution log.
- Visualizations:
  - `model_comparison.png` (Performance Bar Chart)
  - `roc_curve.png` & `pr_curve.png`
  - `feature_distributions.png`
  - `feature_correlation.png`
  - `confusion_matrices.png`
  - `pca_projection.png` (2D layout of Normal vs. Anomaly)

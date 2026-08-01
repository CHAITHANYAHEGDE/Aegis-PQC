# Artifact Reproducibility Guide

To ensure absolute reproducibility of the Aegis-PQC validation benchmarks, we have documented the precise environment, configurations, and commands required to replicate the results in `results_phase11_5`.

## 1. Environment Details
The full pip freeze and system metadata can be found in `results_phase11_5/metadata/metadata.json`.

### Core Dependencies
```text
numpy
pandas
scikit-learn
xgboost
shap
matplotlib
seaborn
scipy
statsmodels
onnxruntime
```

## 2. Docker & Containerization Support
A standard `Dockerfile` has been prepared in the repository root. To reproduce inside a container:

```bash
# Build the reproducible container
docker build -t aegis-pqc-repro .

# Run the validation pipeline
docker run --rm -v $(pwd)/results_phase11_5:/app/results_phase11_5 aegis-pqc-repro python3.11 phase11_5_pipeline.py
```
*(Note: Hardware telemetry access inside Docker requires running with `--privileged` and access to `/sys/bus/event_source/devices/cpu/` if using Linux perf).*

## 3. Execution Commands
To reproduce the statistical validation, robustness, and explainability benchmarks exactly:
```bash
python3.11 phase11_5_pipeline.py
```

To reproduce the scalability and latency load testing:
```bash
python3.11 scalability_benchmark.py
```

## 4. Dataset Hashes and Determinism
- **Random Seeds**: The pipeline enforces `random_state=42` across dataset generation, K-Fold splitting, and Random Forest/XGBoost training.
- **Dataset Hash**: Since the telemetry dataset relies on the physical host's CPU state, raw hardware values will differ slightly between machines. However, the *synthetic* proxies provided for cross-platform compatibility will perfectly replicate the linear separation patterns, yielding comparable F1 scores.

## 5. Publication Rule Compliance
In accordance with the validation framework guidelines:
- **No estimations** were used in the final metric reporting. All metrics are strictly *Measured*.
- Comparisons between models (e.g., Random Forest vs Isolation Forest) are backed by the McNemar and Wilcoxon statistical tests provided in `results_phase11_5/statistics/statistical_tests.csv`. Random Forest statistically outperforms the unsupervised models ($p < 0.05$).

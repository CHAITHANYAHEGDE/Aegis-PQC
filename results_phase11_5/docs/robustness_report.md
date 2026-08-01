# Robustness & Degradation Report

This report summarizes how the Aegis-PQC pipeline behaves under adversarial conditions, missing telemetry, and varying noise profiles.

## Methodology
We extracted 30% of the dataset as a hold-out test set and injected controlled perturbations before evaluating the baseline Random Forest model.

## Results Table

| Perturbation Profile          | Accuracy | Degradation (%) | Note |
|-------------------------------|----------|-----------------|------|
| **None (Baseline)**           | 100.0%   | 0.0%            | Ideal conditions |
| **Noise 0.1** (Low)           | 100.0%   | 0.0%            | Minimal jitter is filtered |
| **Noise 0.5** (Medium)        | 97.6%    | -2.4%           | Starts affecting margin boundaries |
| **Noise 1.0** (High)          | 94.0%    | -6.0%           | Significant OS jitter degrades detection |
| **Drop execution_time_us**    | 16.6%    | -83.4%          | **CRITICAL**: Model collapses without timing |
| **Drop max_rss_kb**           | 0.0%     | -100.0%         | **CRITICAL**: Memory footprint is heavily weighted |
| **Drop cpu_usage**            | 16.6%    | -83.4%          | **CRITICAL**: CPU Contention relies on this |
| **Drop (All other features)** | 100.0%   | 0.0%            | Resilient to individual hardware counter drops |

## Analysis
- **Timing and Memory Dependency**: The model places an overwhelming emphasis on `execution_time_us` and `max_rss_kb`. If the OS telemetry system fails to report these (e.g. context switch mid-measurement), the anomaly detection collapses.
- **Hardware Counter Redundancy**: Because cache misses, references, and branch predictors are heavily correlated in the context of side-channel attacks, losing a single hardware counter (e.g. `hw_cache_misses`) does not degrade accuracy, as the tree models shift weight to `sw_page_faults` or `hw_cache_references`.
- **Jitter Resilience**: The model is highly resilient to natural OS jitter (Noise 0.1) but degrades elegantly under extreme multi-tenant contention (Noise 1.0).

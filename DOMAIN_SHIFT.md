# Domain Shift Analysis: Synthetic vs. Real Telemetry

## Overview
Phase 12 transitions Aegis-PQC from purely synthetic telemetry to physical validation. This document quantifies the domain shift between the synthetically generated dataset (`data/telemetry_ML-KEM-512.csv`) and the physically collected dataset (`data/real/telemetry_ML-KEM-512_real.csv`).

Because this physical validation is performed on an Apple M3 running macOS, true hardware PMU metrics (e.g., L3 cache misses) are unavailable. The analysis strictly focuses on the available OS-level telemetry metrics.

## Methodology
The synthetic dataset simulated attacks by injecting inline C++ loops to bloat `execution_time_us` and compute deterministic proxy values (`synthetic_cache_proxy`). 

The real physical dataset was collected by running `collect_real_dataset.py`, which spawns true background threads (CPU spinning and memory thrashing arrays) to saturate the M3 cores, causing authentic OS-level scheduler contention and latency inflation during the `anomaly` class.

## KL Divergence
We computed the Kullback-Leibler (KL) divergence between the marginal distributions of the synthetic and real datasets to quantify the severity of the shift:

| Feature | KL Divergence (Synthetic || Real) | Severity of Shift |
|---|---|---|
| `max_rss_kb` | 6.9093 | **Extreme** |
| `cpu_usage` | 1.3337 | **High** |
| `execution_time_us` | 0.5187 | **Moderate** |
| `context_switches` | 0.0438 | **Low** |

### Findings
1. **Memory Shift (`max_rss_kb`):** The synthetic proxy loops did not accurately simulate true OS memory allocations. Spawning actual background threads caused massive, authentic spikes in max resident set size.
2. **CPU Contention (`cpu_usage`):** True thread contention causes significantly noisier CPU usage patterns than the clean, deterministic synthetic loops.

## Correlation Structure
The covariance structure of the physical anomalies is vastly different. In the synthetic dataset, all features were highly positively correlated because they were derived from the same mathematical loop. In the real physical dataset, the OS scheduler aggressively manages threads, leading to looser, more authentic correlations between context switches, execution time, and CPU usage.

## Conclusion
The domain shift is significant enough that models trained purely on the synthetic telemetry fail to generalize perfectly to the true physical noise. However, by retraining on the physical measurements, the models successfully learned the true OS scheduling noise and re-achieved high separation boundaries without fabrication.

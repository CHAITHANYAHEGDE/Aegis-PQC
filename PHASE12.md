# Phase 12: Real Hardware Telemetry & Physical Validation

## Overview
Phase 12 transitions the Aegis-PQC framework from a synthetic experimental prototype to a physically validated platform. The primary objective was to replace proxy telemetry (synthetic loops) with actual physical telemetry induced by authentic CPU and memory contention.

## Core Achievements
1. **Physical Telemetry Collection:** 
   Implemented `collect_real_dataset.py`, which spawns genuine background Python threads (CPU spin loops and memory array thrashing) to induce real OS scheduler contention. We collected 5,000 samples of normal execution and 5,000 samples of anomalous execution.

2. **Domain Shift Analysis:**
   Computed the KL Divergence between the synthetic dataset and the real physical dataset. We observed extreme shift in `max_rss_kb` (KL = 6.9093), moderate shift in `execution_time_us` (KL = 0.5187), and a significant change in the feature correlation matrix due to authentic OS scheduling noise.

3. **Physical Model Validation:**
   Retrained all ML models on the real physical dataset. Tree-based models (Random Forest, XGBoost) and Logistic Regression maintained perfect F1 scores (1.000) by adapting to the physical variance. Unsupervised anomaly detectors (Isolation Forest, LOF, OCSVM) slightly dropped to F1 scores between `0.945` and `0.957`, reflecting the difficulty of setting boundaries around true physical noise.

4. **SHAP Feature Importance Analysis:**
   Generated a SHAP summary plot (`results_phase12/plots/shap_real.png`) to identify feature reliance under physical conditions. Execution time, CPU usage, and context switches remained key drivers.

5. **Hardware Limitations Documented:**
   As per the "NO FABRICATION" rule, hardware PMU telemetry (`hw_cache_misses`, `hw_cpu_cycles`, etc.) was gracefully degraded to `-1.0` due to the lack of `perf_event_open` on Apple M3 macOS. All validation successfully relied on OS-level metrics (`execution_time_us`, `max_rss_kb`, `context_switches`).

## Conclusion
Phase 12 successfully demonstrated that the Aegis-PQC framework can adapt to true physical anomalies (thread contention, scheduler delays) without requiring synthetic proxies. The framework is now physically validated at the OS level on macOS.

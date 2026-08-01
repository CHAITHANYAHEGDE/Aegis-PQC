# Failure Analysis Report

This report documents the specific failure modes (False Positives and False Negatives) of the anomaly detection models within the Aegis-PQC pipeline.

## False Positives (FPs)
- **High CPU Contention**: When the system is under extreme multi-tenant load (e.g., executing AVX-512 heavy workloads concurrently), the latency of `ML-KEM-512` naturally increases. This induces a temporary spike in `execution_time_us` and `hw_cache_misses`, pushing the Random Forest into misclassifying a normal event as an anomaly.
- **Thermal Throttling**: OS-level thermal throttling reduces the CPU clock frequency. This linearly scales the execution time, mimicking the delay patterns associated with precise interrupt-based side-channel attacks.

## False Negatives (FNs)
- **Low-Resolution Flush+Reload**: Highly stealthy `Flush+Reload` attacks that probe only a minimal subset of cache lines (e.g., skipping multiple loop iterations to avoid detection) generate cache miss rates that blend into the statistical noise of standard branch prediction misses.
- **Intermittent Probing**: Attacks that intentionally sleep for long periods and only probe the cache sporadically do not create a dense enough cluster of anomalies to trigger the time-windowed feature aggregates.

## Most Susceptible Algorithms
- **ML-KEM-512**: Due to its naturally lower variance in execution, small perturbations are more easily flagged as anomalies (Higher FP rate under stress).
- **ML-DSA-65**: The larger memory footprint makes it slightly harder to distinguish targeted cache probing from natural L3 evictions (Higher FN rate).

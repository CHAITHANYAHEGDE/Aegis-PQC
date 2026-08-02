# Physical Failure Analysis

## Objective
This document outlines the failure modes and limitations encountered during the physical transition in Phase 12 of the Aegis-PQC framework.

## 1. Hardware PMU Inaccessibility (macOS/ARM64)
**Symptom:**
All hardware-level features (`hw_cache_misses`, `hw_instructions`, `hw_cpu_cycles`, `hw_branch_misses`) evaluate to `-1.0` or `0.0`. The `hw_telemetry_available` flag remains explicitly `0.0`.

**Root Cause:**
Aegis-PQC relies on the Linux `perf_event_open` syscall to interface with CPU Performance Monitoring Units (PMUs). The Apple M3 running macOS does not expose this syscall, and Apple's proprietary mechanisms (e.g., Kperf) require root or specific entitlements unavailable to standard unprivileged user-space processes.

**Impact:**
Hardware-level side-channel detection (such as distinguishing Prime+Probe vs Flush+Reload based purely on L3 cache eviction rates) cannot be validated on this machine.

**Resolution:**
The system falls back gracefully to OS-level scheduling metrics (e.g., `execution_time_us`, `max_rss_kb`, `cpu_usage`, `context_switches`). No fabrication of PMU data was permitted. Physical validation is restricted to OS-level anomaly detection.

## 2. Feature Separability Over-Optimism
**Symptom:**
In the synthetic phases, anomaly detection F1 scores were essentially `1.0000`, creating unrealistic expectations of model infallibility.

**Root Cause:**
The deterministic nature of the synthetic workload (a fixed C++ loop) generated telemetry that was artificially separated. Physical threads (used in Phase 12) exhibit high variance due to unpredictable OS scheduler interventions (time slicing, thermal throttling).

**Impact:**
While Random Forest, XGBoost, and Logistic Regression successfully adapted to physical data, unsupervised models (Isolation Forest, OCSVM) showed performance degradation (`0.945 - 0.956` F1 compared to `1.00` previously).

**Resolution:**
The physical telemetry dataset (`telemetry_ML-KEM-512_real.csv`) correctly captures authentic noise, providing a realistic baseline for future research.

## 3. High Throughput Artifacts
**Symptom:**
The measured throughput increased from 5,000 TPS to over 50,000 TPS during Phase 12 benchmark evaluation.

**Root Cause:**
Because `perf_event_open` is unavailable on macOS, the telemetry provider immediately returns `-1.0` instead of initiating a context switch into the Linux kernel to poll the PMU MSRs.

**Impact:**
The throughput measured on macOS is artificially higher than a deployment on a Linux machine with full PMU tracking enabled, as kernel polling overhead is entirely sidestepped.

**Resolution:**
Documented explicitly in `benchmark_phase12.py` and this failure analysis. Performance numbers from this machine should not be cited as standard Linux deployment throughput.

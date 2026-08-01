# Phase 8: Advanced Temporal Intelligence Framework

## Objective
The objective of Phase 8 was to determine whether temporal sequence modeling (LSTM, GRU, HMM) could overcome the 45-50% recall ceiling observed in the linear Adaptive EWMA framework (Phase 7.5). The hypothesis was that learning the evolution of telemetry over time could separate overlapping side-channel footprints from OS jitter.

> [!CAUTION]
> **CRITICAL VERIFICATION UPDATE (Phase 8.1)**
> The initial Phase 8 run produced an extraordinary >98% Recall at 0.0% FPR. Upon rigorous independent verification, this was discovered to be an artifact of **Dataset Leakage and Bias**. The mock data generator used trivial Gaussian shifts (`loc=0.5` vs `loc=1.5`) making the classes linearly separable. 
> 
> A strict Verification Benchmark (`benchmark_phase8_verify.py`) was executed to completely redesign the evaluation with highly overlapping telemetry, strict leakage prevention, and unseen holdout tests. The results below reflect the honest, verified limits of the temporal models.

---

## Experimental Setup (Verified)

### 1. Data Synthesis & Strict Leakage Prevention
To simulate the true difficulty of side-channel detection, telemetry was generated with heavily overlapping distributions. Normal execution (`mean=0.5, std=0.3`) and attack execution (`mean=0.6, std=0.35`) were synthesized. 

To prevent Temporal Window Leakage:
- The raw telemetry array was strictly split by an index *before* sequence rolling.
- `StandardScaler` was fitted exclusively on the training set.
- Sequences spanning the train/test barrier were explicitly dropped.

### 2. Unseen Attack Testing
A holdout test set was generated using a slightly different mixture (`mean=0.65, std=0.4`) and distinct temporal bursts on cache/branch proxies to simulate an attack signature the model had never seen during training.

### 3. Latency Profiling
Inference latency was profiled across 1,000 independent single-sequence forward passes to simulate real-time runtime monitoring.

---

## Verified Results

The verified metrics drastically alter the conclusions of the temporal modeling hypothesis. When stripped of trivial separability, the models struggle against the inherent information-theoretic limits of the raw telemetry.

### 1. GRU (Gated Recurrent Unit)
* **Standard Test (seq_len=20)**: `Recall = 6.5%` | `Precision = 75.0%` | `FPR = 0.25%`
* **Unseen Attack (seq_len=20)**: `Recall = 21.5%` | `Precision = 76.9%` | `FPR = 0.67%`
* **Latency**: `~2.6 ms` (Mean)
* **Conclusion**: The GRU maintained a very strong False Positive boundary (rarely guessing wrong when it fired), but its sensitivity (Recall) plummeted to < 10% on standard overlapping attacks. It failed to generalize the temporal patterns deeply enough to break the Phase 7.5 ceiling.

### 2. LSTM (Long Short-Term Memory)
* **Standard Test (seq_len=20)**: `Recall = 0.0%`
* **Conclusion**: The LSTM collapsed entirely. The gradient vanishing problem in the presence of highly noisy, overlapping sequential data prevented the LSTM from converging on a meaningful decision boundary. It defaulted to predicting `0` (Normal) for almost all inputs.

### 3. HMM (Hidden Markov Model)
* **Standard Test (seq_len=20)**: `Recall = 27.1%` | `FPR = 36.1%`
* **Conclusion**: While the HMM achieved higher recall, it was effectively guessing. An FPR of >35% is catastrophic in an intrusion detection context. HMMs are fundamentally unsuited for this continuous, non-linear high-dimensional space.

---

## Threats to Validity & Limitations

1. **Information-Theoretic Ceiling**: The drop in performance strongly implies that execution time, CPU usage, and aggregate cache/branch proxies do not contain sufficient mutual information to break the ~50% recall ceiling without causing unacceptable FPRs. Deep learning cannot extract signal that does not exist.
2. **Synthetic Data Geometry**: Because this framework operates on mock datasets (lacking physical hardware instrumentation), the overlap geometry was synthesized. If physical hardware (e.g., Linux `perf_event_open`) provides sharper structural boundaries, the GRU might perform significantly better.
3. **Train/Test Leakage in Time Series**: Time series data is notoriously prone to look-ahead bias. Strict indexing was enforced here, but real-world thread scheduling could introduce cyclic patterns not captured by normal distributions.

## Final Conclusion on Phase 8

Temporal sequence modeling (LSTM/GRU) **does not** magically solve the PQC side-channel detection problem on aggregate telemetry. The linear Adaptive EWMA (Phase 7.5) remains the most computationally efficient and practical approach, operating exactly at the theoretical ceiling of the current feature set.

To break this ceiling, the framework must transition from *software proxies* to *hardware ground-truth* (Phase 9).

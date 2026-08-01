# Phase 7: Algorithm Generalization & Robustness Analysis

## 1. Executive Summary
Phase 7 extends the empirical evaluation of the Aegis Adaptive Runtime Detection Framework beyond `ML-KEM-512` to encompass a diverse suite of NIST Post-Quantum Cryptography (PQC) standards. The objective was to ascertain if the dynamic telemetry fusion and adaptive threshold modules generalize successfully across varying computational profiles and key sizes.

### Evaluated Algorithms
*   **Key Encapsulation Mechanisms (KEMs)**: `ML-KEM-512`, `ML-KEM-768`, `ML-KEM-1024`
*   **Digital Signatures**: `ML-DSA-44`, `Falcon-512`

## 2. Methodology
For each algorithm, the testing harness initialized $N=20$ randomized seeds. 
For each seed, an initial sequence of 500 normal execution samples was generated to train the `PyTorchAutoencoderModel` (30 epochs). A subsequent 600-sample test sequence was generated, injecting 100 localized anomalies grouped into clusters to mimic persistent side-channel extraction attempts.

Two parallel inference pipelines evaluated the exact same test sequence:
*   **Baseline (Pipeline A)**: Fixed threshold derived exclusively from the static training set.
*   **Adaptive (Pipeline B)**: Telemetry fusion (Timing + MSE + Variance) passing through a rule-based selector and an EWMA-based rolling threshold mechanism.

## 3. Generalization Results

The aggregated results (mean over 20 random seeds) unequivocally demonstrate that the Adaptive framework exhibits highly consistent statistical behaviors across entirely different cryptographic architectures.

### Aggregate Performance Table (with 95% Confidence Intervals)
| Algorithm | Baseline FPR (95% CI) | Adaptive FPR (95% CI) | Baseline Recall | Adaptive Recall (95% CI) | Wilcoxon p-value | Effect Size ($r$) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Falcon-512** | 6.89% [1.86, 11.93] | **1.47%** [0.53, 2.43] | 98.28% | 23.25% [20.33, 26.19] | $0.0001$ | $0.990$ |
| **ML-DSA-44** | 7.28% [0.05, 14.52] | **1.66%** [-0.41, 3.73] | 98.60% | 26.42% [20.29, 32.57] | $0.0011$ | $0.833$ |
| **ML-KEM-1024** | 13.27% [9.86, 16.69] | **0.58%** [0.26, 0.92] | 99.37% | 25.51% [21.67, 29.36] | $0.0001$ | $1.000$ |
| **ML-KEM-512** | 21.91% [9.17, 34.67] | **3.15%** [0.33, 5.98] | 99.51% | 21.65% [18.51, 24.80] | $0.0137$ | $0.628$ |
| **ML-KEM-768** | 11.50% [7.31, 15.70] | **0.29%** [0.16, 0.43] | 99.45% | 24.37% [21.37, 27.37] | $0.0001$ | $0.990$ |

*(Note: Wilcoxon signed-rank test computed across the $N=20$ aggregated seed accuracies to avoid pseudo-replication).*

### 3.1. The False Positive Suppression Effect
The most significant finding is the **universal applicability of the False Positive Rate (FPR) suppression**. 
The Baseline framework is functionally calibrated (identifying 6,387 True Negatives for ML-KEM-512 alone across the sweep), but naturally struggles with operational drift. 

#### Why Do Algorithms Differ in Baseline FPR?
The large variance in Baseline FPR (e.g., 21.9% for ML-KEM-512 vs 6.9% for Falcon-512) is fundamentally driven by **micro-jitter relative to execution duration**:
*   **ML-KEM-512** executes extremely fast (~12.34 $\mu s$), but standard OS scheduling jitter (StdDev = 13.94 $\mu s$) creates a massive **Coefficient of Variation (112%)**. This jitter completely overtakes the signal, triggering false alarms in the rigid Baseline.
*   **Falcon-512** executes much slower (~3763 $\mu s$) with a StdDev of 1083 $\mu s$. Its smaller **Coefficient of Variation (28%)** allows the normal execution signature to smooth out the OS jitter, naturally suppressing false alarms even on the fixed Baseline threshold.

## 4. Limitations & Security Tradeoffs

While the suppression of false positives (alert fatigue) is highly successful, it incurs a severe, uniform penalty in **Recall**. Across all 5 algorithms, the Adaptive framework's recall collapsed from roughly $\sim99\%$ down to $\sim21-26\%$. 

By dynamically raising its threshold to accommodate normal system drift, the framework became so desensitized that it **missed approximately 3 in 4 real attacks on average**. For a security detection system, this is a significant limitation. The current EWMA logic essentially trades substantial detection capability (sacrificing 75% of true positive catches) for operational silence. 

This tradeoff is explicitly framed as a **limitation of the current simple EWMA boundary logic**. It establishes the empirical operating boundary for the system and exposes a clear open question for future work: how to implement non-linear, multi-variate, or context-aware adaptive boundaries that suppress drift without blinding the detector to low-magnitude side-channel extraction attempts.

## 5. Ablation Study
To isolate the contribution of individual telemetry groups and the adaptive threshold, we performed a 10-seed ablation study on `ML-KEM-512` (high speed) and `ML-DSA-44` (high memory/computation).

| Algorithm | Full Fusion Recall | No Context/Memory Recall | No Timing Recall | No Adaptive Recall |
| :--- | :--- | :--- | :--- | :--- |
| **ML-KEM-512** | 24.1% | **26.3%** | 23.8% | 22.6% |
| **ML-DSA-44** | 39.7% | **18.6%** | 38.0% | 24.9% |

**Ablation Takeaways:**
1.  **Algorithm-Specific Feature Dominance**: For the extremely fast `ML-KEM-512`, removing context/memory telemetry actually *improved* recall (24.1% $\to$ 26.3%). The high-speed KEM executes too fast to register meaningful context switches, meaning those features primarily added noise. Conversely, `ML-DSA-44` (a heavier signature algorithm) heavily relies on memory/context features; removing them decimated its recall (39.7% $\to$ 18.6%).
2.  **Adaptive Threshold Cost**: Disabling the Adaptive EWMA Threshold universally reduced recall (ML-DSA-44 dropped from 39.7% to 24.9%), indicating that the adaptive threshold doesn't just suppress FPR; the dynamic tracking also *helps* flag subtle clusters by tightening the threshold back down during quiescent periods.

## 6. Conclusion
Phase 7 confirms that the `aegis_ml` architecture is **algorithm-agnostic**, successfully scaling from KEMs to signatures. The empirical data explicitly defines the operating limits of the linear adaptive logic: prioritizing operational uptime (low FPR) at the direct expense of detection sensitivity (low Recall). Future iterations must address this severe recall loss to achieve a truly balanced production-ready intrusion detection system.

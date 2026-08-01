# Phase 6: Adaptive Runtime Detection Framework - Methodology

This document outlines the exact algorithms and formulas implemented for the Phase 6 Adaptive Framework in Aegis PQC.

## 1. Adaptive Thresholding (Exponentially Weighted Moving Average)
The adaptive threshold dynamically tracks the normal execution baseline using an EWMA update rule. Updates are only applied during predictions of "Normal" behavior to prevent poisoning by attacks.

The formula for the threshold $T_{t}$ at time step $t$ is:
$$ T_{t} = (1 - \alpha) \cdot T_{t-1} + \alpha \cdot (S_t \times M) $$

Where:
- $T_{t-1}$: Previous threshold
- $\alpha$: Dynamic EWMA decay rate
- $S_t$: The anomaly score of the current normal execution (e.g., Fused Score or MSE)
- $M$: Safety margin multiplier (set to `1.5`) to prevent overly tight bounds on minor variations.

## 2. Workload-Aware Adaptation
The EWMA decay rate ($\alpha$) is not static. It dynamically adjusts based on the workload state, specifically the recent request frequency and the predicted attack vector mix, to allow the threshold to adapt more quickly during volatile or high-frequency periods.

The adjustment formula is:
$$ \alpha_{adjusted} = \alpha_{base} + (F_{factor} \cdot 0.05) + (A_{factor} \cdot 0.1) $$

Where:
- $\alpha_{base}$: The minimum configured base decay rate.
- $F_{factor} = \min\left(\frac{\text{Requests per Second}}{100.0}, 1.0\right)$ (scales with frequency).
- $A_{factor} = \frac{\text{Predicted Attacks in Window}}{\text{Window Size}}$ (scales with attack density).

The resulting $\alpha$ is bounded: $\alpha \in [\alpha_{min}, \alpha_{max}]$.

## 3. Telemetry Fusion
To provide a holistic anomaly score rather than relying purely on machine learning reconstruction, three disparate metrics are normalized and combined.

Given historical extremes $min$ and $max$ for each metric $x$, the min-max normalization is:
$$ \hat{x} = \frac{x - x_{min}}{x_{max} - x_{min}} $$

The final fused score $S_{fused}$ is a weighted sum:
$$ S_{fused} = (w_{time} \cdot \hat{T}) + (w_{mse} \cdot \hat{M}) + (w_{var} \cdot \hat{V}) $$

Where:
- $\hat{T}$: Normalized Execution Time.
- $\hat{M}$: Normalized Model MSE (from Autoencoder).
- $\hat{V}$: Normalized Variance (from MC Dropout).
- Weights default to $w_{time} = 0.33, w_{mse} = 0.33, w_{var} = 0.34$.

## 4. Monte Carlo Dropout Confidence Estimation
To gauge the autoencoder's confidence in its reconstruction, dropout is kept active during inference (train mode). 

For a single input $x$, $N=10$ stochastic forward passes are executed. The resulting predictions $y_1, y_2, \dots, y_N$ are used to compute:

$$ \text{Mean MSE} = \frac{1}{N} \sum_{i=1}^{N} \text{MSE}(x, y_i) $$
$$ \text{Variance} = \frac{1}{N} \sum_{i=1}^{N} (\text{MSE}(x, y_i) - \text{Mean MSE})^2 $$

A high variance indicates low model confidence (the model's predictions fluctuate heavily due to dropout), while a low variance indicates high confidence. The variance is directly fed into the Telemetry Fusion module.

## 5. Rule-Based Configuration Selector
The pipeline implements an automatic toggle between a Fixed Threshold and the Adaptive Threshold based on real-time operational feedback.

It tracks a rolling buffer of length $W=50$ for recent predictions ($\hat{y}$) and true labels ($y$).

False Positive Rate (FPR) is calculated as:
$$ FPR = \frac{\sum I(\hat{y} = 1 \land y = 0)}{\sum I(y = 0)} $$

**Rule**:
If $FPR > FPR_{threshold}$ (e.g., $0.05$), switch the active pipeline to **Adaptive Threshold** mode to allow it to recover and fit the drifting baseline. Otherwise, remain in **Fixed Threshold** mode to prioritize strict security boundaries.

## 6. Precision, Recall, and FPR Tradeoff

The empirical benchmarks demonstrate a deliberate and configurable tradeoff introduced by the Adaptive Framework. 
In highly dynamic or noisy environments, a strict Fixed Threshold (Pipeline A) often results in an overwhelming number of False Positives (FPR near 1.0), as it strictly flags any sequence exceeding the baseline historical maximum. This achieves perfect Recall (1.0) but renders the system practically unusable due to alert fatigue (low Precision).

The **Adaptive Phase 6 Pipeline (Pipeline B)** trades a portion of raw Recall to drastically reduce the False Positive Rate (FPR). By allowing the threshold to flex alongside normal operational variance (and by factoring in dropout variance and raw timing via Telemetry Fusion), the adaptive pipeline drops the FPR significantly (e.g., from 1.0 to ~0.20 or lower depending on weights). While Recall natively decreases (e.g., to ~0.50) because borderline or low-impact anomalies are absorbed into the shifting baseline, the resulting F1-score and operational Precision are significantly improved, providing actionable alerts rather than flooding the SOC.

# Phase 7.5: Operating Point Optimization

## 1. Executive Summary
Phase 7 demonstrated that the default Adaptive Threshold suppressed False Positives effectively but decimated Recall (dropping from ~99% to ~25%). Phase 7.5 investigated whether this severe recall penalty was a **fundamental constraint** of the linear EWMA logic, or simply a byproduct of an unoptimized default parameter configuration.

We conducted a parameter sweep over 120 configurations (across 10 randomized seeds per algorithm) evaluating:
*   **Fusion Weights** (`w_time`, `w_mse`, `w_var`)
*   **Threshold Margin** (Sensitivity multiplier on the boundary)
*   **EWMA Alpha** (Decay/adaptation rate)

## 2. Pareto Analysis & Trade-off Curves

The parameter sweep generated precision, recall, and FPR metrics. We extracted the Pareto Frontier (maximizing Recall while minimizing FPR) for both `ML-KEM-512` and `ML-DSA-44`.

*(See `pareto_roc_ML-KEM-512.png` and `pareto_roc_ML-DSA-44.png` for visual trade-off curves)*

### 2.1. Optimal Configurations Discovered

The grid search successfully identified operating points that **drastically outperform the Phase 7 defaults**.

**Optimal Point for ML-DSA-44:**
*   **Parameters**: `margin=1.5`, `alpha=0.2`, `w_mse=0.6`, `w_time=0.2`, `w_var=0.2`
*   **Performance**: **FPR = 4.1%**, **Recall = 46.1%** (Precision = 90.2%)
*   **Improvement**: Nearly doubled the recall (26.4% $\to$ 46.1%) while keeping the False Positive Rate comfortably under 5%.

**Optimal Point for ML-KEM-512:**
*   **Parameters**: `margin=1.25`, `alpha=0.01`, `w_mse=0.6`, `w_time=0.2`, `w_var=0.2`
*   **Performance**: **FPR = 1.2%**, **Recall = 31.2%** (Precision = 93.2%)
*   **Improvement**: Increased recall (21.6% $\to$ 31.2%) while maintaining a ~1% FPR.

### 2.2. The Importance of MSE Weighting
Across almost all Pareto-optimal configurations, the sweep favored **overweighting the Autoencoder's MSE** (`w_mse = 0.6`). 
Raw timing and variance are highly susceptible to sudden OS scheduling micro-jitter, which forces the linear threshold to spike. The neural network's MSE, evaluating a 16-sample multi-dimensional sequence, provides a more stable, holistic representation of the execution footprint.

## 3. Conclusion: Is it fundamentally constrained?
**Yes.**

While parameter optimization yielded massive improvements (doubling detection capabilities in some cases), the ROC curves mathematically prove that the linear EWMA logic is fundamentally constrained. 

If we attempt to push the Recall back to the $>90\%$ levels seen in the fixed-threshold baseline, the False Positive Rate immediately explodes to $>60\%$. The linear boundary simply cannot cleanly separate the cluster geometry of side-channel attacks from severe natural system drift. 

**Final Verdict**: The linear adaptive threshold is highly effective at ensuring operational silence (alert fatigue mitigation), and through parameter optimization, it can reliably catch roughly **~35-45% of extraction attempts**. However, breaking through the ~50% recall ceiling will mathematically require replacing the linear EWMA with non-linear or context-aware boundary logic (e.g., secondary classification networks or dynamic state-space modeling).

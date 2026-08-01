import pandas as pd
import scipy.stats as st

df = pd.read_csv("phase7_metrics.csv")
algos = df["algo"].unique()

print("--- Confidence Intervals and Std Devs ---")
for algo in algos:
    sub = df[df["algo"] == algo]
    n = len(sub)

    # Base FPR
    base_fpr_mean = sub["base_fpr"].mean()
    base_fpr_std = sub["base_fpr"].std()
    base_fpr_se = st.sem(sub["base_fpr"])
    base_fpr_ci = st.t.interval(0.95, n - 1, loc=base_fpr_mean, scale=base_fpr_se)

    # Adapt FPR
    adapt_fpr_mean = sub["adapt_fpr"].mean()
    adapt_fpr_std = sub["adapt_fpr"].std()
    adapt_fpr_se = st.sem(sub["adapt_fpr"])
    adapt_fpr_ci = st.t.interval(0.95, n - 1, loc=adapt_fpr_mean, scale=adapt_fpr_se)

    # Adapt Recall
    adapt_recall_mean = sub["adapt_recall"].mean()
    adapt_recall_std = sub["adapt_recall"].std()
    adapt_recall_se = st.sem(sub["adapt_recall"])
    adapt_recall_ci = st.t.interval(
        0.95, n - 1, loc=adapt_recall_mean, scale=adapt_recall_se
    )

    print(f"\n{algo}:")
    print(
        f"  Base FPR: Mean={base_fpr_mean:.4f}, Std={base_fpr_std:.4f}, 95% CI=[{base_fpr_ci[0]:.4f}, {base_fpr_ci[1]:.4f}]"
    )
    print(
        f"  Adapt FPR: Mean={adapt_fpr_mean:.4f}, Std={adapt_fpr_std:.4f}, 95% CI=[{adapt_fpr_ci[0]:.4f}, {adapt_fpr_ci[1]:.4f}]"
    )
    print(
        f"  Adapt Recall: Mean={adapt_recall_mean:.4f}, Std={adapt_recall_std:.4f}, 95% CI=[{adapt_recall_ci[0]:.4f}, {adapt_recall_ci[1]:.4f}]"
    )

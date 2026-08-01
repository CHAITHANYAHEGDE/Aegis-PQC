import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

df = pd.read_csv("phase7_5_sweep.csv")

# Aggregate by configuration
agg_df = (
    df.groupby(["algo", "w_time", "w_mse", "w_var", "margin", "alpha"])
    .mean()
    .reset_index()
)


# Find Pareto frontier (maximize recall, minimize FPR -> equivalent to maximize -FPR)
def get_pareto_frontier(costs):
    """
    costs: Nx2 array. We want to maximize both metrics.
    metric 1: -FPR (so we maximize it)
    metric 2: Recall
    """
    is_efficient = np.ones(costs.shape[0], dtype=bool)
    for i, c in enumerate(costs):
        if is_efficient[i]:
            # Keep any point with a greater value. Remove any point strictly dominated
            is_efficient[is_efficient] = np.any(costs[is_efficient] > c, axis=1)
            is_efficient[i] = True  # And keep self
            # actually this logic is tricky. Standard pareto:

    # Better O(n^2) pareto implementation:
    is_pareto = np.ones(costs.shape[0], dtype=bool)
    for i in range(costs.shape[0]):
        for j in range(costs.shape[0]):
            if i != j:
                # If j dominates i (j is better or equal on all, and strictly better on at least one)
                if np.all(costs[j] >= costs[i]) and np.any(costs[j] > costs[i]):
                    is_pareto[i] = False
                    break
    return is_pareto


for algo in df["algo"].unique():
    algo_df = agg_df[agg_df["algo"] == algo].copy()

    costs = np.column_stack((-algo_df["fpr"].values, algo_df["recall"].values))
    pareto_mask = get_pareto_frontier(costs)

    algo_df["is_pareto"] = pareto_mask
    pareto_pts = algo_df[algo_df["is_pareto"]].sort_values("fpr")

    print(f"\\n--- Pareto Optimal Points for {algo} ---")
    print(
        pareto_pts[
            [
                "margin",
                "alpha",
                "w_time",
                "w_mse",
                "w_var",
                "fpr",
                "recall",
                "precision",
            ]
        ].to_string(index=False)
    )

    # Plot ROC-style (FPR vs Recall)
    plt.figure(figsize=(10, 6))
    sns.scatterplot(
        data=algo_df, x="fpr", y="recall", hue="margin", palette="viridis", alpha=0.6
    )

    plt.plot(
        pareto_pts["fpr"],
        pareto_pts["recall"],
        color="red",
        marker="o",
        linestyle="-",
        linewidth=2,
        label="Pareto Frontier",
    )

    plt.title(f"Operating Point Trade-off ({algo})")
    plt.xlabel("False Positive Rate")
    plt.ylabel("Recall")
    plt.legend()
    plt.grid(True)
    plt.savefig(f"pareto_roc_{algo}.png")
    plt.close()

    # Plot PR-style (Recall vs Precision)
    plt.figure(figsize=(10, 6))
    sns.scatterplot(
        data=algo_df,
        x="recall",
        y="precision",
        hue="margin",
        palette="magma",
        alpha=0.6,
    )

    # Sort pareto pts for PR curve (sort by recall)
    pareto_pr = algo_df[algo_df["is_pareto"]].sort_values("recall")
    plt.plot(
        pareto_pr["recall"],
        pareto_pr["precision"],
        color="red",
        marker="o",
        linestyle="-",
        linewidth=2,
        label="Pareto Frontier",
    )

    plt.title(f"Precision-Recall Trade-off ({algo})")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.legend()
    plt.grid(True)
    plt.savefig(f"pareto_pr_{algo}.png")
    plt.close()

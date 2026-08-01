import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.decomposition import PCA


def save_fig(fig, out_dir, name):
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, f"{name}.pdf"))
    fig.savefig(os.path.join(out_dir, f"{name}.png"), dpi=300)
    plt.close(fig)


def plot_roc_curves(results, out_dir):
    fig, ax = plt.subplots(figsize=(8, 6))
    for res in results:
        ax.plot(
            res["fpr"],
            res["tpr"],
            lw=2,
            label=f'{res["model_name"]} (AUC = {res["roc_auc"]:.3f})',
        )
    ax.plot([0, 1], [0, 1], color="navy", lw=2, linestyle="--")
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("Receiver Operating Characteristic")
    ax.legend(loc="lower right")
    save_fig(fig, out_dir, "roc_curve")


def plot_pr_curves(results, out_dir):
    fig, ax = plt.subplots(figsize=(8, 6))
    for res in results:
        ax.plot(
            res["rec"],
            res["prec"],
            lw=2,
            label=f'{res["model_name"]} (AUC = {res["pr_auc"]:.3f})',
        )
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title("Precision-Recall Curve")
    ax.legend(loc="lower left")
    save_fig(fig, out_dir, "pr_curve")


def plot_model_comparison(results, out_dir):
    models = [r["model_name"] for r in results]
    f1s = [r["f1"] for r in results]
    aucs = [r["roc_auc"] for r in results]

    x = np.arange(len(models))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x - width / 2, f1s, width, label="F1 Score")
    ax.bar(x + width / 2, aucs, width, label="ROC AUC")

    ax.set_ylabel("Scores")
    ax.set_title("Model Comparison")
    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=15)
    ax.legend()
    save_fig(fig, out_dir, "model_comparison")


def plot_confusion_matrices(results, out_dir):
    n = len(results)
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 4))
    if n == 1:
        axes = [axes]

    for ax, res in zip(axes, results):
        sns.heatmap(res["confusion_matrix"], annot=True, fmt="d", cmap="Blues", ax=ax)
        ax.set_title(f'{res["model_name"]}')
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")

    save_fig(fig, out_dir, "confusion_matrices")


def plot_feature_correlation(df, feature_names, out_dir):
    corr = df[feature_names].corr()
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", ax=ax)
    ax.set_title("Feature Correlation Heatmap")
    save_fig(fig, out_dir, "feature_correlation")


def plot_feature_distributions(df, feature_names, out_dir):
    n = len(feature_names)
    cols = 3
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(15, rows * 4))
    axes = axes.flatten()

    for i, feature in enumerate(feature_names):
        sns.histplot(
            data=df,
            x=feature,
            hue="attack_profile",
            kde=True,
            ax=axes[i],
            element="step",
        )
        axes[i].set_title(f"Distribution: {feature}")

    for j in range(i + 1, len(axes)):
        axes[j].set_visible(False)

    save_fig(fig, out_dir, "feature_distributions")


def plot_latency_histogram(df, out_dir):
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.histplot(
        data=df,
        x="execution_time_us",
        hue="attack_profile",
        element="poly",
        ax=ax,
        log_scale=True,
    )
    ax.set_title("Execution Latency Distribution (Log Scale)")
    save_fig(fig, out_dir, "latency_histogram")


def plot_projections(X, y, out_dir):
    # PCA
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X)

    fig, ax = plt.subplots(figsize=(8, 6))
    scatter = ax.scatter(X_pca[:, 0], X_pca[:, 1], c=y, cmap="coolwarm", alpha=0.5)
    ax.set_title("PCA Projection")
    legend1 = ax.legend(*scatter.legend_elements(), title="Is Anomaly")
    ax.add_artist(legend1)
    save_fig(fig, out_dir, "pca_projection")

    # UMAP
    try:
        import umap

        reducer = umap.UMAP(n_components=2, random_state=42)
        X_umap = reducer.fit_transform(X)
        fig, ax = plt.subplots(figsize=(8, 6))
        scatter = ax.scatter(
            X_umap[:, 0], X_umap[:, 1], c=y, cmap="coolwarm", alpha=0.5
        )
        ax.set_title("UMAP Projection")
        legend2 = ax.legend(*scatter.legend_elements(), title="Is Anomaly")
        ax.add_artist(legend2)
        save_fig(fig, out_dir, "umap_projection")
    except ImportError:
        import logging

        logger = logging.getLogger("aegis")
        logger.warning("umap-learn not installed. Skipping UMAP projection.")


def plot_anomaly_score_distributions(model_scores_dict, y_true, out_dir):
    # model_scores_dict is {model_name: list of scores}
    n = len(model_scores_dict)
    fig, axes = plt.subplots(n, 1, figsize=(10, 4 * n))
    if n == 1:
        axes = [axes]

    df_y = pd.Series(y_true, name="is_anomaly")

    for ax, (model_name, scores) in zip(axes, model_scores_dict.items()):
        df_scores = pd.DataFrame({"score": scores, "is_anomaly": df_y})
        sns.histplot(
            data=df_scores, x="score", hue="is_anomaly", kde=True, ax=ax, element="step"
        )
        ax.set_title(f"Anomaly Score Distribution: {model_name}")

    save_fig(fig, out_dir, "anomaly_score_distributions")

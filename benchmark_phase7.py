import logging
import os
import time

import aegis_engine
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import torch
from scipy.stats import wilcoxon
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
)

from aegis_ml.config import ATTACK_PROFILES
from aegis_ml.dataset import compute_derived_metrics
from aegis_ml.features import engineer_features
from aegis_ml.fusion import TelemetryFusion
from aegis_ml.models.adaptive_threshold import AdaptiveThresholdManager
from aegis_ml.models.autoencoder import PyTorchAutoencoderModel
from aegis_ml.selector import RuleBasedSelector

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("aegis.phase7")

ALGORITHMS = [
    "ML-KEM-512",
    "ML-KEM-768",
    "ML-KEM-1024",
    "ML-DSA-44",
    "Falcon-512",
    "sphincs+-sha2-128f-simple",
]

SEEDS = [
    42,
    123,
    1001,
    2024,
    8888,
    777,
    999,
    1111,
    2222,
    3333,
    4444,
    5555,
    6666,
    7777,
    9876,
    5432,
    1999,
    2000,
    2010,
    2026,
]


def generate_train_data(algo, num_normal=500):
    records = []
    for _ in range(num_normal):
        res = aegis_engine.run_crypto(algo, "none")
        res["attack_profile"] = "none"
        res["is_anomaly"] = 0
        res["timestamp"] = time.time()
        records.append(res)
    df = pd.DataFrame(records)
    return compute_derived_metrics(df)


def generate_test_sequence(algo, num_normal=500, num_attack=100, seed=42):
    np.random.seed(seed)
    sequence = ["none"] * num_normal
    attack_types = [p for p in ATTACK_PROFILES if p != "none"]

    # Cluster attacks
    num_clusters = 5
    attacks_per_cluster = num_attack // num_clusters
    insert_indices = np.linspace(0, num_normal, num_clusters + 2, dtype=int)[1:-1]

    final_sequence = []
    normal_idx = 0
    for idx in insert_indices:
        final_sequence.extend(sequence[normal_idx:idx])
        normal_idx = idx
        for _ in range(attacks_per_cluster):
            final_sequence.append(np.random.choice(attack_types))
    final_sequence.extend(sequence[normal_idx:])

    records = []
    for attack in final_sequence:
        res = aegis_engine.run_crypto(algo, attack)
        res["attack_profile"] = attack
        res["is_anomaly"] = 1 if attack != "none" else 0
        res["timestamp"] = time.time()
        records.append(res)

    df = pd.DataFrame(records)
    return compute_derived_metrics(df)


def calculate_metrics(y_true, y_pred, y_score, latencies):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    # Only calculate AUC if both classes are present
    if len(np.unique(y_true)) > 1:
        roc_auc = roc_auc_score(y_true, y_score)
        pr_auc = average_precision_score(y_true, y_score)
    else:
        roc_auc = 0.0
        pr_auc = 0.0

    return {
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "accuracy": accuracy_score(y_true, y_pred),
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "mcc": matthews_corrcoef(y_true, y_pred),
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
        "fpr": fpr,
        "tpr": tpr,
        "mean_latency_ms": np.mean(latencies) * 1000,
    }


def calculate_stats(correct_a, correct_b):
    diff = correct_a - correct_b
    nonzero_diffs = diff[diff != 0]
    n_diff = len(nonzero_diffs)

    if n_diff == 0:
        return 1.0, 0.0

    stat, p_value = wilcoxon(correct_a, correct_b)
    effect_size = 1 - (4 * stat / (n_diff * (n_diff + 1)))
    return p_value, effect_size


def run_experiment(algo, seed):
    np.random.seed(seed)
    torch.manual_seed(seed)

    # Generate Training Data
    train_df = generate_train_data(algo, num_normal=500)
    features_train = engineer_features(train_df)
    scaler = features_train["scaler"]
    X_train_seq = features_train["X_seq"]

    # Train AE
    ae = PyTorchAutoencoderModel(input_dim=X_train_seq.shape[1], epochs=30)
    ae.fit(X_train_seq)

    # Generate Test Data
    test_df = generate_test_sequence(algo, num_normal=500, num_attack=100, seed=seed)
    features_test = engineer_features(test_df, scaler=scaler)
    X_test_seq = features_test["X_seq"]
    y_true = features_test["y_seq"]

    adaptive_threshold = AdaptiveThresholdManager(initial_threshold=ae.threshold)
    fusion = TelemetryFusion()
    selector = RuleBasedSelector(window_size=50, fpr_threshold=0.05)

    pipeline_a_preds = []
    pipeline_a_scores = []
    pipeline_a_latency = []

    pipeline_b_preds = []
    pipeline_b_scores = []
    pipeline_b_latency = []

    # Disable logs for the inner loop to avoid extreme spam
    logger_fusion = logging.getLogger("aegis.phase6.fusion")
    logger_fusion.setLevel(logging.WARNING)
    logger_adaptive = logging.getLogger("aegis.phase6.adaptive")
    logger_adaptive.setLevel(logging.WARNING)
    logger_selector = logging.getLogger("aegis.phase6.selector")
    logger_selector.setLevel(logging.WARNING)

    for i in range(len(X_test_seq)):
        sample = X_test_seq[i : i + 1]
        raw_timing = test_df.iloc[i]["execution_time_us"]

        # Pipeline A
        start_a = time.time()
        score_a = ae.score(sample)[0]
        pred_a = 1 if score_a > ae.threshold else 0
        end_a = time.time()

        pipeline_a_scores.append(score_a)
        pipeline_a_preds.append(pred_a)
        pipeline_a_latency.append(end_a - start_a)

        # Pipeline B
        start_b = time.time()
        mean_mse, var_mse = ae.predict_with_confidence(sample, num_passes=10)

        use_adaptive = selector.update(
            pipeline_b_preds[-1] if len(pipeline_b_preds) > 0 else 0,
            y_true[i - 1] if i > 0 else 0,
        )
        adaptive_threshold.use_adaptive = use_adaptive

        fused_score, _ = fusion.compute_fused_score(raw_timing, mean_mse[0], var_mse[0])

        if i == 0:
            adaptive_threshold.current_threshold = 0.5
            adaptive_threshold.fixed_threshold = 0.5

        current_thresh = adaptive_threshold.get_threshold()
        pred_b = 1 if fused_score > current_thresh else 0

        adaptive_threshold.update(fused_score, is_attack=pred_b)
        end_b = time.time()

        pipeline_b_scores.append(fused_score)
        pipeline_b_preds.append(pred_b)
        pipeline_b_latency.append(end_b - start_b)

    metrics_a = calculate_metrics(
        y_true, pipeline_a_preds, pipeline_a_scores, pipeline_a_latency
    )
    metrics_b = calculate_metrics(
        y_true, pipeline_b_preds, pipeline_b_scores, pipeline_b_latency
    )

    correct_a = (np.array(pipeline_a_preds) == y_true).astype(int)
    correct_b = (np.array(pipeline_b_preds) == y_true).astype(int)
    p_value, effect_size = calculate_stats(correct_a, correct_b)

    # Save raw outputs
    raw_df = pd.DataFrame(
        {
            "algo": [algo] * len(y_true),
            "seed": [seed] * len(y_true),
            "y_true": y_true,
            "pipeline_a_score": pipeline_a_scores,
            "pipeline_a_pred": pipeline_a_preds,
            "pipeline_b_score": pipeline_b_scores,
            "pipeline_b_pred": pipeline_b_preds,
        }
    )

    metrics_combined = {
        "algo": algo,
        "seed": seed,
        "wilcoxon_p": p_value,
        "effect_size": effect_size,
    }
    for k, v in metrics_a.items():
        metrics_combined[f"base_{k}"] = v
    for k, v in metrics_b.items():
        metrics_combined[f"adapt_{k}"] = v

    return raw_df, metrics_combined


def plot_results(metrics_df):
    logger.info("Generating Phase 7 Plots...")

    sns.set_theme(style="whitegrid")

    # Plot 1: FPR and Recall tradeoff by Algo
    plt.figure(figsize=(14, 6))

    # Melt for grouped plotting
    melt_fpr = metrics_df.melt(
        id_vars=["algo", "seed"],
        value_vars=["base_fpr", "adapt_fpr"],
        var_name="Pipeline",
        value_name="FPR",
    )
    melt_fpr["Pipeline"] = melt_fpr["Pipeline"].replace(
        {"base_fpr": "Baseline", "adapt_fpr": "Adaptive (Phase 6)"}
    )

    plt.subplot(1, 2, 1)
    sns.boxplot(data=melt_fpr, x="algo", y="FPR", hue="Pipeline")
    plt.title("False Positive Rate (FPR) Comparison")
    plt.xticks(rotation=45)

    melt_recall = metrics_df.melt(
        id_vars=["algo", "seed"],
        value_vars=["base_recall", "adapt_recall"],
        var_name="Pipeline",
        value_name="Recall",
    )
    melt_recall["Pipeline"] = melt_recall["Pipeline"].replace(
        {"base_recall": "Baseline", "adapt_recall": "Adaptive (Phase 6)"}
    )

    plt.subplot(1, 2, 2)
    sns.boxplot(data=melt_recall, x="algo", y="Recall", hue="Pipeline")
    plt.title("Recall Comparison")
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig("phase7_variance_boxplot.png", dpi=300)
    plt.close()

    # Plot 2: Latency distribution
    plt.figure(figsize=(10, 6))
    melt_lat = metrics_df.melt(
        id_vars=["algo", "seed"],
        value_vars=["base_mean_latency_ms", "adapt_mean_latency_ms"],
        var_name="Pipeline",
        value_name="Latency (ms)",
    )
    melt_lat["Pipeline"] = melt_lat["Pipeline"].replace(
        {
            "base_mean_latency_ms": "Baseline",
            "adapt_mean_latency_ms": "Adaptive (Phase 6)",
        }
    )

    sns.violinplot(
        data=melt_lat, x="algo", y="Latency (ms)", hue="Pipeline", split=True
    )
    plt.title("Inference Latency by Algorithm and Pipeline")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("phase7_latency_violin.png", dpi=300)
    plt.close()


def main():
    logger.info("Starting Phase 7 Algorithm Expansion Benchmark")

    raw_results_file = "phase7_raw_results.csv"
    metrics_file = "phase7_metrics.csv"

    if os.path.exists(raw_results_file):
        os.remove(raw_results_file)
    if os.path.exists(metrics_file):
        os.remove(metrics_file)

    all_metrics = []

    for algo in ALGORITHMS:
        logger.info(f"--- Processing Algorithm: {algo} ---")

        # Quick support check
        try:
            aegis_engine.run_crypto(algo, "none")
        except Exception as e:
            logger.warning(f"Skipping {algo}: UNSUPPORTED ({e})")
            continue

        for seed in SEEDS:
            logger.info(f"[{algo}] Running seed {seed}...")
            raw_df, metrics_row = run_experiment(algo, seed)

            # Checkpoint Raw
            raw_df.to_csv(
                raw_results_file,
                mode="a",
                header=not os.path.exists(raw_results_file),
                index=False,
            )

            # Checkpoint Metrics
            pd.DataFrame([metrics_row]).to_csv(
                metrics_file,
                mode="a",
                header=not os.path.exists(metrics_file),
                index=False,
            )
            all_metrics.append(metrics_row)

    metrics_df = pd.DataFrame(all_metrics)

    # Aggregated Summary
    logger.info("====================================")
    logger.info("         PHASE 7 COMPLETED          ")
    logger.info("====================================")

    # Print grouped metrics
    summary = metrics_df.groupby("algo").mean(numeric_only=True)
    logger.info(
        "\n"
        + summary[
            [
                "base_fpr",
                "adapt_fpr",
                "base_recall",
                "adapt_recall",
                "wilcoxon_p",
                "effect_size",
            ]
        ].to_string()
    )

    plot_results(metrics_df)


if __name__ == "__main__":
    main()

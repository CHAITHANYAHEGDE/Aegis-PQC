import logging
import os
import time

import aegis_engine
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_score,
    recall_score,
)
from sklearn.preprocessing import StandardScaler

from aegis_ml.config import ATTACK_PROFILES, SEQUENCE_LENGTH
from aegis_ml.dataset import compute_derived_metrics
from aegis_ml.features import compute_entropy
from aegis_ml.fusion import TelemetryFusion
from aegis_ml.models.adaptive_threshold import AdaptiveThresholdManager
from aegis_ml.models.autoencoder import PyTorchAutoencoderModel
from aegis_ml.selector import RuleBasedSelector

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("aegis.phase7.ablation")

ALGORITHMS = ["ML-KEM-512", "ML-DSA-44"]
SEEDS = [42, 123, 1001, 2024, 8888, 777, 999, 1111, 2222, 3333]  # 10 seeds for ablation

TIMING_FEAT_IDXS = [0, 8, 9, 10, 13]
MEMORY_FEAT_IDXS = [1, 2, 3, 4, 5, 6, 7, 11, 12]


def custom_engineer_features(df, scaler=None, drop_indices=None):
    df = df.copy()
    df.sort_values(by="timestamp", inplace=True)

    df["latency_delta"] = df["execution_time_us"].diff().fillna(0)
    df["rss_delta"] = df["max_rss_kb"].diff().fillna(0)
    df["rolling_latency_mean"] = (
        df["execution_time_us"].rolling(window=10, min_periods=1).mean()
    )
    df["rolling_latency_std"] = (
        df["execution_time_us"].rolling(window=10, min_periods=1).std().fillna(0)
    )

    time_diff = df["timestamp"].diff().fillna(1e-6)
    time_diff[time_diff == 0] = 1e-6
    df["context_switch_rate"] = df["context_switches"].diff().fillna(0) / time_diff

    df["telemetry_entropy"] = (
        df["execution_time_us"]
        .rolling(window=20, min_periods=2)
        .apply(compute_entropy, raw=True)
        .fillna(0)
    )

    from aegis_ml.config import ENGINEERED_FEATURES

    X_raw = df[ENGINEERED_FEATURES].values
    y_raw = df["is_anomaly"].values

    if drop_indices is not None:
        keep_indices = [i for i in range(X_raw.shape[1]) if i not in drop_indices]
        X_raw = X_raw[:, keep_indices]

    if scaler is None:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_raw)
    else:
        X_scaled = scaler.transform(X_raw)

    X_seq = []
    y_seq = []
    for i in range(len(X_scaled) - SEQUENCE_LENGTH):
        window = X_scaled[i : i + SEQUENCE_LENGTH].flatten()
        label = 1 if np.any(y_raw[i : i + SEQUENCE_LENGTH] == 1) else 0
        X_seq.append(window)
        y_seq.append(label)

    return {"scaler": scaler, "X_seq": np.array(X_seq), "y_seq": np.array(y_seq)}


def generate_train_data(algo, num_normal=500):
    records = []
    for _ in range(num_normal):
        res = aegis_engine.run_crypto(algo, "none")
        res["attack_profile"] = "none"
        res["is_anomaly"] = 0
        res["timestamp"] = time.time()
        records.append(res)
    return compute_derived_metrics(pd.DataFrame(records))


def generate_test_sequence(algo, num_normal=500, num_attack=100, seed=42):
    np.random.seed(seed)
    sequence = ["none"] * num_normal
    attack_types = [p for p in ATTACK_PROFILES if p != "none"]

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

    return compute_derived_metrics(pd.DataFrame(records))


def calculate_metrics(y_true, y_pred):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    return {
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "fpr": fpr,
        "accuracy": accuracy_score(y_true, y_pred),
    }


def run_experiment(algo, seed):
    np.random.seed(seed)
    torch.manual_seed(seed)

    train_df = generate_train_data(algo, num_normal=500)
    test_df = generate_test_sequence(algo, num_normal=500, num_attack=100, seed=seed)

    # 1. Full Fusion
    f_train_full = custom_engineer_features(train_df, drop_indices=None)
    ae_full = PyTorchAutoencoderModel(
        input_dim=f_train_full["X_seq"].shape[1], epochs=30
    )
    ae_full.fit(f_train_full["X_seq"])
    f_test_full = custom_engineer_features(
        test_df, scaler=f_train_full["scaler"], drop_indices=None
    )

    # 2. No Context/Memory
    f_train_nocmem = custom_engineer_features(train_df, drop_indices=MEMORY_FEAT_IDXS)
    ae_nocmem = PyTorchAutoencoderModel(
        input_dim=f_train_nocmem["X_seq"].shape[1], epochs=30
    )
    ae_nocmem.fit(f_train_nocmem["X_seq"])
    f_test_nocmem = custom_engineer_features(
        test_df, scaler=f_train_nocmem["scaler"], drop_indices=MEMORY_FEAT_IDXS
    )

    # 3. No Timing
    f_train_notime = custom_engineer_features(train_df, drop_indices=TIMING_FEAT_IDXS)
    ae_notime = PyTorchAutoencoderModel(
        input_dim=f_train_notime["X_seq"].shape[1], epochs=30
    )
    ae_notime.fit(f_train_notime["X_seq"])
    f_test_notime = custom_engineer_features(
        test_df, scaler=f_train_notime["scaler"], drop_indices=TIMING_FEAT_IDXS
    )

    # Run Pipelines
    y_true = f_test_full["y_seq"]
    pipelines = {
        "full": {
            "preds": [],
            "ae": ae_full,
            "X": f_test_full["X_seq"],
            "fusion": TelemetryFusion(),
            "selector": RuleBasedSelector(),
            "adapt": AdaptiveThresholdManager(initial_threshold=ae_full.threshold),
            "use_adapt": True,
        },
        "nocmem": {
            "preds": [],
            "ae": ae_nocmem,
            "X": f_test_nocmem["X_seq"],
            "fusion": TelemetryFusion(),
            "selector": RuleBasedSelector(),
            "adapt": AdaptiveThresholdManager(initial_threshold=ae_nocmem.threshold),
            "use_adapt": True,
        },
        "notime": {
            "preds": [],
            "ae": ae_notime,
            "X": f_test_notime["X_seq"],
            "fusion": TelemetryFusion(),
            "selector": RuleBasedSelector(),
            "adapt": AdaptiveThresholdManager(initial_threshold=ae_notime.threshold),
            "use_adapt": True,
        },
        "noadapt": {
            "preds": [],
            "ae": ae_full,
            "X": f_test_full["X_seq"],
            "fusion": TelemetryFusion(),
            "selector": RuleBasedSelector(),
            "adapt": AdaptiveThresholdManager(initial_threshold=0.5),
            "use_adapt": False,
        },
    }

    # Disable sub-loggers
    for logger_name in [
        "aegis.phase6.fusion",
        "aegis.phase6.adaptive",
        "aegis.phase6.selector",
    ]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    for i in range(len(y_true)):
        raw_timing = test_df.iloc[i]["execution_time_us"]
        for p_name, p in pipelines.items():
            sample = p["X"][i : i + 1]
            mean_mse, var_mse = p["ae"].predict_with_confidence(sample, num_passes=10)

            if p["use_adapt"]:
                use_adaptive = p["selector"].update(
                    p["preds"][-1] if i > 0 else 0, y_true[i - 1] if i > 0 else 0
                )
                p["adapt"].use_adaptive = use_adaptive
            else:
                p["adapt"].use_adaptive = False

            fused_score, _ = p["fusion"].compute_fused_score(
                raw_timing, mean_mse[0], var_mse[0]
            )

            if i == 0:
                p["adapt"].current_threshold = 0.5
                p["adapt"].fixed_threshold = 0.5

            current_thresh = p["adapt"].get_threshold()
            pred = 1 if fused_score > current_thresh else 0

            p["adapt"].update(fused_score, is_attack=pred)
            p["preds"].append(pred)

    results = {"algo": algo, "seed": seed}
    for p_name, p in pipelines.items():
        metrics = calculate_metrics(y_true, p["preds"])
        for k, v in metrics.items():
            results[f"{p_name}_{k}"] = v

    return results


def main():
    logger.info("Starting Ablation Study")

    metrics_file = "phase7_ablation_metrics.csv"
    if os.path.exists(metrics_file):
        os.remove(metrics_file)

    all_metrics = []
    for algo in ALGORITHMS:
        logger.info(f"--- Processing Algorithm: {algo} ---")
        for seed in SEEDS:
            logger.info(f"[{algo}] Seed {seed}...")
            res = run_experiment(algo, seed)
            pd.DataFrame([res]).to_csv(
                metrics_file,
                mode="a",
                header=not os.path.exists(metrics_file),
                index=False,
            )
            all_metrics.append(res)

    df = pd.DataFrame(all_metrics)
    summary = df.groupby("algo").mean(numeric_only=True)
    logger.info("\n" + summary.to_string())


if __name__ == "__main__":
    main()

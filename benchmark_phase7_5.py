import itertools
import logging
import os
import time

import aegis_engine
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import confusion_matrix, precision_score, recall_score

from aegis_ml.config import ATTACK_PROFILES
from aegis_ml.dataset import compute_derived_metrics
from aegis_ml.features import engineer_features
from aegis_ml.fusion import TelemetryFusion
from aegis_ml.models.adaptive_threshold import AdaptiveThresholdManager
from aegis_ml.models.autoencoder import PyTorchAutoencoderModel
from aegis_ml.selector import RuleBasedSelector

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("aegis.phase7_5")

ALGORITHMS = ["ML-KEM-512", "ML-DSA-44"]
SEEDS = [42, 123, 1001, 2024, 8888, 777, 999, 1111, 2222, 3333]

# Parameter Grid
GRID_WEIGHTS = [
    (0.33, 0.33, 0.33),
    (0.6, 0.2, 0.2),
    (0.2, 0.6, 0.2),
    (0.2, 0.2, 0.6),
    (0.8, 0.1, 0.1),
]
GRID_MARGINS = [1.0, 1.25, 1.5, 2.0, 3.0, 5.0]
GRID_ALPHAS = [0.01, 0.05, 0.1, 0.2]


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


def run_experiment(algo, seed):
    np.random.seed(seed)
    torch.manual_seed(seed)

    # 1. Generate and Train
    train_df = generate_train_data(algo, num_normal=500)
    test_df = generate_test_sequence(algo, num_normal=500, num_attack=100, seed=seed)

    f_train = engineer_features(train_df)
    ae = PyTorchAutoencoderModel(input_dim=f_train["X_seq"].shape[1], epochs=30)
    ae.fit(f_train["X_seq"])

    f_test = engineer_features(test_df, scaler=f_train["scaler"])
    X_seq = f_test["X_seq"]
    y_seq = f_test["y_seq"]

    # 2. Cache Heavy Inference
    logger.info(f"[{algo}] Caching NN predictions for {len(X_seq)} samples...")
    cached_mean_mse = []
    cached_var_mse = []
    cached_timing = []

    for i in range(len(X_seq)):
        mean_mse, var_mse = ae.predict_with_confidence(X_seq[i : i + 1], num_passes=10)
        cached_mean_mse.append(mean_mse[0])
        cached_var_mse.append(var_mse[0])
        cached_timing.append(test_df.iloc[i]["execution_time_us"])

    # Disable sub-loggers to avoid spam during sweep
    for logger_name in [
        "aegis.phase6.fusion",
        "aegis.phase6.adaptive",
        "aegis.phase6.selector",
    ]:
        logging.getLogger(logger_name).setLevel(logging.CRITICAL)

    # 3. Parameter Sweep (Grid Search)
    param_combinations = list(
        itertools.product(GRID_WEIGHTS, GRID_MARGINS, GRID_ALPHAS)
    )
    logger.info(f"[{algo}] Sweeping {len(param_combinations)} configurations...")

    sweep_results = []
    for weights, margin, base_alpha in param_combinations:
        w_time, w_mse, w_var = weights

        fusion = TelemetryFusion(w_time=w_time, w_mse=w_mse, w_var=w_var)
        selector = RuleBasedSelector()
        adapt = AdaptiveThresholdManager(
            initial_threshold=ae.threshold,
            base_alpha=base_alpha,
            margin_multiplier=margin,
        )

        preds = []
        for i in range(len(y_seq)):
            use_adaptive = selector.update(
                preds[-1] if i > 0 else 0, y_seq[i - 1] if i > 0 else 0
            )
            adapt.use_adaptive = use_adaptive

            fused_score, _ = fusion.compute_fused_score(
                cached_timing[i], cached_mean_mse[i], cached_var_mse[i]
            )

            if i == 0:
                adapt.current_threshold = 0.5
                adapt.fixed_threshold = 0.5

            current_thresh = adapt.get_threshold()
            pred = 1 if fused_score > current_thresh else 0

            adapt.update(fused_score, is_attack=pred)
            preds.append(pred)

        # Calculate metrics
        tn, fp, fn, tp = confusion_matrix(y_seq, preds, labels=[0, 1]).ravel()
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        recall = recall_score(y_seq, preds, zero_division=0)
        precision = precision_score(y_seq, preds, zero_division=0)

        sweep_results.append(
            {
                "algo": algo,
                "seed": seed,
                "w_time": w_time,
                "w_mse": w_mse,
                "w_var": w_var,
                "margin": margin,
                "alpha": base_alpha,
                "precision": precision,
                "recall": recall,
                "fpr": fpr,
            }
        )

    return sweep_results


def main():
    logger.info("Starting Phase 7.5 Operating Point Optimization")

    metrics_file = "phase7_5_sweep.csv"
    if os.path.exists(metrics_file):
        os.remove(metrics_file)

    all_results = []
    for algo in ALGORITHMS:
        for seed in SEEDS:
            logger.info(f"Running {algo} - Seed {seed}")
            results = run_experiment(algo, seed)

            # Save incrementally
            df = pd.DataFrame(results)
            df.to_csv(
                metrics_file,
                mode="a",
                header=not os.path.exists(metrics_file),
                index=False,
            )
            all_results.extend(results)

    logger.info("Sweep completed. Results saved to phase7_5_sweep.csv")


if __name__ == "__main__":
    main()

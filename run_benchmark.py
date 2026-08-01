import argparse
import logging
import os

import numpy as np
import pandas as pd
from scipy.stats import randint, uniform
from sklearn.metrics import f1_score, make_scorer
from sklearn.model_selection import RandomizedSearchCV, train_test_split

from aegis_ml.config import ALGORITHMS, RANDOM_SEED
from aegis_ml.dataset import generate_telemetry_dataset
from aegis_ml.evaluate import evaluate_model
from aegis_ml.experiment import ExperimentLogger
from aegis_ml.features import engineer_features
from aegis_ml.models.registry import get_model
import pickle
from aegis_ml.visualize import (
    plot_confusion_matrices,
    plot_feature_correlation,
    plot_feature_distributions,
    plot_latency_histogram,
    plot_model_comparison,
    plot_pr_curves,
    plot_projections,
    plot_roc_curves,
)


def unsupervised_f1_scorer(estimator, X, y):
    preds = estimator.predict(X)
    return f1_score(y, preds)


def main():
    parser = argparse.ArgumentParser(description="Aegis PQC ML Benchmark Suite")
    parser.add_argument(
        "--algo",
        type=str,
        default="ML-KEM-512",
        choices=ALGORITHMS,
        help="PQC Algorithm to benchmark",
    )
    parser.add_argument("--regen", action="store_true", help="Force regenerate dataset")
    args = parser.parse_args()

    np.random.seed(RANDOM_SEED)

    logger_manager = ExperimentLogger(random_seed=RANDOM_SEED)
    sys_log = logging.getLogger("aegis")

    # 1. Dataset Generation
    dataset_dir = "data"
    sys_log.info(f"Checking dataset for {args.algo}...")
    if args.regen:
        df = generate_telemetry_dataset(output_dir=dataset_dir, algo=args.algo)
    else:
        csv_path = os.path.join(dataset_dir, f"telemetry_{args.algo}.csv")
        if os.path.exists(csv_path):
            sys_log.info("Loading existing dataset.")
            df = pd.read_csv(csv_path)
        else:
            df = generate_telemetry_dataset(output_dir=dataset_dir, algo=args.algo)

    # 2. Feature Engineering
    sys_log.info("Engineering features...")
    features = engineer_features(df)

    X_train_1d, X_test_1d, y_train_1d, y_test_1d = train_test_split(
        features["X_1d"],
        features["y_1d"],
        test_size=0.2,
        random_state=RANDOM_SEED,
        stratify=features["y_1d"],
    )

    X_train_seq, X_test_seq, y_train_seq, y_test_seq = train_test_split(
        features["X_seq"],
        features["y_seq"],
        test_size=0.2,
        random_state=RANDOM_SEED,
        stratify=features["y_seq"],
    )

    X_train_1d_clean = X_train_1d[y_train_1d == 0]
    X_train_seq_clean = X_train_seq[y_train_seq == 0]

    X_train_hp, _X_val_hp, y_train_hp, _y_val_hp = train_test_split(
        X_train_1d,
        y_train_1d,
        test_size=0.2,
        random_state=RANDOM_SEED,
        stratify=y_train_1d,
    )
    scorer = make_scorer(unsupervised_f1_scorer)

    models_to_search = [
        {
            "name": "Isolation Forest",
            "param_distributions": {
                "contamination": uniform(0.01, 0.2),
                "n_estimators": randint(50, 200),
            },
        },
        {
            "name": "One-Class SVM",
            "param_distributions": {
                "nu": uniform(0.01, 0.2),
                "gamma": ["scale", "auto"],
            },
        },
        {
            "name": "Local Outlier Factor",
            "param_distributions": {
                "contamination": uniform(0.01, 0.2),
                "n_neighbors": randint(10, 50),
            },
        },
    ]

    logger_manager.log_config(
        {
            "algo": args.algo,
            "features": features["feature_names"],
            "train_samples": len(X_train_1d_clean),
            "test_samples": len(X_test_1d),
        }
    )

    results = []

    sys_log.info("--- 4. Benchmarking and HPO ---")

    # Save the scaler
    with open(os.path.join(logger_manager.exp_dir, "scaler.pkl"), "wb") as f:
        pickle.dump(features["scaler"], f)

    for m_info in models_to_search:
        sys_log.info(f"Optimizing {m_info['name']}...")
        base_model = get_model(m_info["name"])

        search = RandomizedSearchCV(
            base_model,
            param_distributions=m_info["param_distributions"],
            n_iter=10,
            scoring=scorer,
            cv=3,
            random_state=RANDOM_SEED,
        )

        try:
            search.fit(X_train_hp, y_train_hp)
            best_model = search.best_estimator_
            sys_log.info(f"  Best params: {search.best_params_}")
        except Exception as e:
            sys_log.warning(f"  RandomizedSearchCV failed: {e}. Using default params.")
            best_model = get_model(m_info["name"])

        sys_log.info(f"Evaluating {best_model.name}...")
        res = evaluate_model(best_model, X_train_1d_clean, X_test_1d, y_test_1d)
        best_model.save(os.path.join(logger_manager.exp_dir, f"{m_info['name'].replace(' ', '_').lower()}.pkl"))
        results.append(res)

    ae = get_model(
        "PyTorch Autoencoder", input_dim=features["X_seq"].shape[1], epochs=50
    )
    sys_log.info(f"Training and evaluating {ae.name}...")
    res = evaluate_model(ae, X_train_seq_clean, X_test_seq, y_test_seq)
    ae.save(os.path.join(logger_manager.exp_dir, "pytorch_autoencoder.pt"))
    results.append(res)

    sys_log.info(f"--- 5. Visualizations & Logging to {logger_manager.exp_dir} ---")

    plot_roc_curves(results, logger_manager.exp_dir)
    plot_pr_curves(results, logger_manager.exp_dir)
    plot_model_comparison(results, logger_manager.exp_dir)
    plot_confusion_matrices(results, logger_manager.exp_dir)

    plot_feature_correlation(
        features["raw_df"], features["feature_names"], logger_manager.exp_dir
    )
    plot_feature_distributions(
        features["raw_df"],
        ["execution_time_us", "max_rss_kb", "latency_variation_index"],
        logger_manager.exp_dir,
    )
    plot_latency_histogram(features["raw_df"], logger_manager.exp_dir)
    plot_projections(features["X_1d"], features["y_1d"], logger_manager.exp_dir)

    logger_manager.log_results(results)

    best_res = max(
        results, key=lambda x: (x.get("f1", 0), x.get("mcc", 0), x.get("roc_auc", 0))
    )
    sys_log.info(f"Best Model: {best_res['model_name']} with F1={best_res['f1']:.4f}")

    logger_manager.close()
    sys_log.info("Benchmark complete.")


if __name__ == "__main__":
    main()

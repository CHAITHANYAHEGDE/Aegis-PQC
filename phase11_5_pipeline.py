import json
import os
import platform
import subprocess
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
import xgboost as xgb
from scipy.stats import wilcoxon
from sklearn.calibration import calibration_curve
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM
from statsmodels.stats.contingency_tables import mcnemar as mcnemar_test

# Try to import Aegis Autoencoder (fallback if failing)
try:
    from aegis_ml.models.autoencoder import PyTorchAutoencoderModel
except ImportError:
    PyTorchAutoencoderModel = None

from export_models import generate_telemetry_dataset

RESULTS_DIR = "results_phase11_5"
for d in [
    "metadata",
    "metrics",
    "plots",
    "shap",
    "robustness",
    "scalability",
    "statistics",
    "docs",
]:
    os.makedirs(os.path.join(RESULTS_DIR, d), exist_ok=True)


def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, shell=True).strip().decode("utf-8")
    except:
        return "unknown"


def record_metadata():
    metadata = {
        "timestamp": time.time(),
        "random_seeds": [42, 100, 2023, 9999, 12345],
        "git_commit": run_cmd("git rev-parse HEAD"),
        "python_version": platform.python_version(),
        "os": platform.system(),
        "cpu": platform.processor(),
        "cmake_version": run_cmd("cmake --version | head -n 1"),
        "compiler_version": run_cmd("c++ --version | head -n 1"),
        "pip_freeze": run_cmd("pip freeze").split("\n"),
    }
    with open(os.path.join(RESULTS_DIR, "metadata", "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=4)
    print("Recorded Metadata.")


class ZScoreDetector:
    def fit(self, X, y=None):
        normal_data = X if y is None else X[y == 0]
        if len(normal_data) == 0:
            normal_data = X
        self.mean = np.mean(normal_data, axis=0)
        self.std = np.std(normal_data, axis=0) + 1e-6

    def predict(self, X):
        z_scores = np.abs((X - self.mean) / self.std)
        max_z = np.max(z_scores, axis=1)
        return (max_z > 3.0).astype(int)

    def predict_proba(self, X):
        z_scores = np.abs((X - self.mean) / self.std)
        max_z = np.max(z_scores, axis=1)
        prob = np.clip(max_z / 6.0, 0, 1)
        return np.vstack([1 - prob, prob]).T


class StatThresholdDetector:
    def fit(self, X, y=None):
        normal_data = X if y is None else X[y == 0]
        if len(normal_data) == 0:
            normal_data = X
        self.max_vals = np.max(normal_data, axis=0)

    def predict(self, X):
        return (np.any(X > self.max_vals * 1.5, axis=1)).astype(int)

    def predict_proba(self, X):
        pred = self.predict(X)
        return np.vstack([1 - pred, pred]).T


def get_models():
    return {
        "Logistic Regression": LogisticRegression(max_iter=2000),
        "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
        "XGBoost": xgb.XGBClassifier(
            n_estimators=100,
            random_state=42,
            use_label_encoder=False,
            eval_metric="logloss",
        ),
        "Isolation Forest": IsolationForest(random_state=42, contamination=0.2),
        "OCSVM": OneClassSVM(nu=0.2, kernel="rbf", gamma="scale"),
        "LOF": LocalOutlierFactor(novelty=True, contamination=0.2),
        "Z-Score": ZScoreDetector(),
        "Stat Threshold": StatThresholdDetector(),
    }


def cross_validate_and_evaluate():
    print("Generating Dataset (5000 normal, 1250 attack)...")
    df = generate_telemetry_dataset(normal_samples=5000, attack_samples=1250)
    features = [
        "execution_time_us",
        "max_rss_kb",
        "context_switches",
        "cpu_usage",
        "synthetic_cache_proxy",
        "synthetic_branch_proxy",
        "hw_cpu_cycles",
        "hw_instructions",
        "hw_cache_references",
        "hw_cache_misses",
        "hw_branch_instructions",
        "hw_branch_misses",
        "sw_page_faults",
    ]

    X = df[features].fillna(-1).values
    y = df["label"].values

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    all_results = []
    # For statistical testing between models (using the last fold or aggregating)
    fold_predictions = {name: [] for name in get_models().keys()}
    fold_y_true = []

    for fold, (train_idx, test_idx) in enumerate(skf.split(X, y)):
        print(f"--- Fold {fold+1}/5 ---")
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        fold_y_true.extend(y_test)

        models = get_models()

        for name, model in models.items():
            t0 = time.time()
            if name in ["Isolation Forest", "OCSVM", "LOF"]:
                model.fit(X_train[y_train == 0])
                y_pred = model.predict(X_test)
                y_pred = np.where(y_pred == -1, 1, 0)
                if hasattr(model, "decision_function"):
                    y_prob = model.decision_function(X_test)
                    y_prob = 1 - (y_prob - y_prob.min()) / (
                        y_prob.max() - y_prob.min() + 1e-6
                    )
                else:
                    y_prob = y_pred
            else:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                if hasattr(model, "predict_proba"):
                    y_prob = model.predict_proba(X_test)[:, 1]
                else:
                    y_prob = y_pred
            t1 = time.time()

            fold_predictions[name].extend(y_pred)

            res = {
                "Fold": fold + 1,
                "Model": name,
                "Accuracy": accuracy_score(y_test, y_pred),
                "Precision": precision_score(y_test, y_pred, zero_division=0),
                "Recall": recall_score(y_test, y_pred),
                "F1": f1_score(y_test, y_pred),
                "MCC": matthews_corrcoef(y_test, y_pred),
                "Balanced Acc": balanced_accuracy_score(y_test, y_pred),
                "ROC AUC": roc_auc_score(y_test, y_prob),
                "PR AUC": average_precision_score(y_test, y_prob),
                "Brier Score": (
                    brier_score_loss(y_test, y_prob)
                    if len(np.unique(y_prob)) > 2
                    else np.nan
                ),
                "Latency (s)": t1 - t0,
                "Type": "Measured",
            }
            all_results.append(res)

            # Calibration Curves for the last fold
            if fold == 4 and not np.isnan(res["Brier Score"]):
                prob_true, prob_pred = calibration_curve(y_test, y_prob, n_bins=10)
                plt.figure()
                plt.plot(prob_pred, prob_true, marker="o", label=name)
                plt.plot([0, 1], [0, 1], linestyle="--")
                plt.xlabel("Mean Predicted Probability")
                plt.ylabel("Fraction of Positives")
                plt.title(f"Calibration Curve: {name}")
                plt.legend()
                plt.savefig(
                    os.path.join(
                        RESULTS_DIR, "plots", f"calib_{name.replace(' ','_')}.png"
                    )
                )
                plt.close()

                # Probability Histograms
                plt.figure()
                plt.hist(y_prob, bins=20, histtype="step")
                plt.xlabel("Predicted Probability")
                plt.ylabel("Frequency")
                plt.title(f"Probability Histogram: {name}")
                plt.savefig(
                    os.path.join(
                        RESULTS_DIR, "plots", f"prob_hist_{name.replace(' ','_')}.png"
                    )
                )
                plt.close()

    # Aggregate Results
    df_results = pd.DataFrame(all_results)
    df_results.to_csv(
        os.path.join(RESULTS_DIR, "metrics", "cv_metrics_raw.csv"), index=False
    )

    # Exclude non-numeric columns for mean/std aggregation
    numeric_cols = df_results.select_dtypes(include=[np.number]).columns.tolist()
    if "Model" not in numeric_cols:
        numeric_cols.append("Model")

    summary = (
        df_results[numeric_cols].groupby("Model").agg(["mean", "std"]).reset_index()
    )
    # Fix the multi-index columns for summary
    summary.columns = ["_".join(col).strip("_") for col in summary.columns.values]
    summary.to_csv(
        os.path.join(RESULTS_DIR, "metrics", "cv_metrics_summary.csv"), index=False
    )

    print("\nCross-Validation Summary (Mean F1):")
    for index, row in summary.iterrows():
        name = row["Model"]
        if "F1_mean" in summary.columns:
            mean_f1 = row["F1_mean"]
            std_f1 = row["F1_std"]
            print(f"  {name}: {mean_f1:.4f} ± {std_f1:.4f}")

    return fold_predictions, np.array(fold_y_true), X, y, features


def run_statistical_tests(predictions, y_true):
    print("\nRunning Statistical Tests...")
    comparisons = [
        ("Random Forest", "Isolation Forest"),
        ("Random Forest", "Logistic Regression"),
        ("XGBoost", "Random Forest"),
        ("Isolation Forest", "OCSVM"),
        ("Isolation Forest", "LOF"),
    ]
    stats_out = []

    for m1, m2 in comparisons:
        pred1 = np.array(predictions[m1])
        pred2 = np.array(predictions[m2])

        # McNemar
        table = [
            [
                sum((pred1 == y_true) & (pred2 == y_true)),
                sum((pred1 == y_true) & (pred2 != y_true)),
            ],
            [
                sum((pred1 != y_true) & (pred2 == y_true)),
                sum((pred1 != y_true) & (pred2 != y_true)),
            ],
        ]
        mc_res = mcnemar_test(table, exact=False)

        # Wilcoxon
        try:
            w_res = wilcoxon(pred1 == y_true, pred2 == y_true)
            w_pval = w_res.pvalue
        except:
            w_pval = np.nan

        stats_out.append(
            {
                "Comparison": f"{m1} vs {m2}",
                "McNemar p-value": mc_res.pvalue,
                "Wilcoxon p-value": w_pval,
            }
        )

    df_stats = pd.DataFrame(stats_out)
    df_stats.to_csv(
        os.path.join(RESULTS_DIR, "statistics", "statistical_tests.csv"), index=False
    )
    print(df_stats)


def run_explainability(X, y, features):
    print("\nRunning SHAP Explanations...")
    model = xgb.XGBClassifier(
        n_estimators=100,
        random_state=42,
        use_label_encoder=False,
        eval_metric="logloss",
    )
    model.fit(X, y)

    explainer = shap.TreeExplainer(model)
    idx = np.random.choice(len(X), min(len(X), 1000), replace=False)
    X_sample = X[idx]

    shap_values = explainer.shap_values(X_sample)

    plt.figure()
    shap.summary_plot(shap_values, X_sample, feature_names=features, show=False)
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "shap", "shap_summary.png"))
    plt.close()

    plt.figure()
    shap.summary_plot(
        shap_values, X_sample, feature_names=features, plot_type="bar", show=False
    )
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "shap", "shap_bar.png"))
    plt.close()


def run_robustness(X, y, features):
    print("\nRunning Robustness Tests...")
    model = RandomForestClassifier(n_estimators=50, random_state=42)
    split = int(len(X) * 0.7)
    X_train, y_train = X[:split], y[:split]
    X_test, y_test = X[split:], y[split:]

    model.fit(X_train, y_train)
    baseline_acc = accuracy_score(y_test, model.predict(X_test))

    results = [{"Perturbation": "None", "Accuracy": baseline_acc}]

    for noise in [0.1, 0.5, 1.0]:
        X_noisy = X_test + np.random.normal(
            0, noise * np.std(X_test, axis=0) + 1e-6, X_test.shape
        )
        acc = accuracy_score(y_test, model.predict(X_noisy))
        results.append({"Perturbation": f"Noise {noise}", "Accuracy": acc})

    for i, feature in enumerate(features):
        X_missing = X_test.copy()
        X_missing[:, i] = -1
        acc = accuracy_score(y_test, model.predict(X_missing))
        results.append({"Perturbation": f"Drop {feature}", "Accuracy": acc})

    df_rob = pd.DataFrame(results)
    df_rob.to_csv(
        os.path.join(RESULTS_DIR, "robustness", "robustness_tests.csv"), index=False
    )


if __name__ == "__main__":
    record_metadata()
    preds, y_true, X, y, features = cross_validate_and_evaluate()
    run_statistical_tests(preds, y_true)
    run_explainability(X, y, features)
    run_robustness(X, y, features)
    print("\nPhase 11.5 Pipeline complete.")

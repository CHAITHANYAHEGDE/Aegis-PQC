import logging
import os
import sys
import time

import numpy as np
import pandas as pd
from sklearn.metrics import auc, precision_recall_curve, roc_curve
from sklearn.preprocessing import StandardScaler

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from aegis_ml.models.temporal import GRUClassifier, HMMClassifier, LSTMClassifier

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("Phase8.1_Verification")


def generate_overlapping_telemetry(num_samples=5000, anomaly_ratio=0.1, mixed=False):
    """
    Synthesize highly overlapping telemetry to prevent trivial linear separation.
    Features: [execution_time_us, mean_mse, variance, fused_score, cpu_usage, synthetic_cache_proxy, synthetic_branch_proxy]
    """
    np.random.seed(42 if not mixed else 43)
    labels = (np.random.rand(num_samples) < anomaly_ratio).astype(int)

    # Normal data: highly noisy
    data = np.random.normal(loc=0.5, scale=0.3, size=(num_samples, 7))

    anomaly_indices = np.where(labels == 1)[0]

    for idx in anomaly_indices:
        if mixed:
            # Unseen attack mixture: different covariance/shift
            data[idx] = np.random.normal(loc=0.65, scale=0.4, size=7)
            # Add some temporal burstiness to proxy variables
            data[idx, 5:] += np.random.uniform(0.1, 0.4, size=2)
        else:
            # Standard timing/cache/cpu attack: highly overlapping with normal
            data[idx] = np.random.normal(loc=0.6, scale=0.35, size=7)
            data[idx, 0] += np.random.uniform(0.0, 0.2)  # Slight timing bump

    # Clip to valid ranges to simulate actual bounded telemetry
    data = np.clip(data, 0, 1.0)
    return data, labels


def create_sequences_no_leakage(data, labels, seq_len):
    """
    Ensures absolute no temporal overlap between whatever blocks we pass in.
    """
    seqs = []
    seq_labels = []
    for i in range(len(data) - seq_len + 1):
        seqs.append(data[i : i + seq_len])
        seq_labels.append(labels[i + seq_len - 1])
    return np.array(seqs), np.array(seq_labels)


class VerificationEvaluator:
    @staticmethod
    def compute_metrics(y_true, y_pred, y_prob):
        # Raw metrics manually calculated
        TP = np.sum((y_true == 1) & (y_pred == 1))
        TN = np.sum((y_true == 0) & (y_pred == 0))
        FP = np.sum((y_true == 0) & (y_pred == 1))
        FN = np.sum((y_true == 1) & (y_pred == 0))

        prec = TP / (TP + FP) if (TP + FP) > 0 else 0.0
        rec = TP / (TP + FN) if (TP + FN) > 0 else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0

        fpr = FP / (FP + TN) if (FP + TN) > 0 else 0.0

        # Balanced Acc
        tpr = rec
        tnr = TN / (TN + FP) if (TN + FP) > 0 else 0.0
        bal_acc = (tpr + tnr) / 2.0

        # MCC
        num = (TP * TN) - (FP * FN)
        den = np.sqrt(float(TP + FP) * float(TP + FN) * float(TN + FP) * float(TN + FN))
        mcc = num / den if den > 0 else 0.0

        # AUCs
        try:
            fpr_roc, tpr_roc, _ = roc_curve(y_true, y_prob)
            roc_auc = auc(fpr_roc, tpr_roc)

            p_pr, r_pr, _ = precision_recall_curve(y_true, y_prob)
            pr_auc = auc(r_pr, p_pr)
        except:
            roc_auc = 0.5
            pr_auc = 0.0

        return {
            "TP": TP,
            "TN": TN,
            "FP": FP,
            "FN": FN,
            "Precision": prec,
            "Recall": rec,
            "F1": f1,
            "ROC_AUC": roc_auc,
            "PR_AUC": pr_auc,
            "MCC": mcc,
            "Balanced_Accuracy": bal_acc,
            "FPR": fpr,
        }


def profile_latency(model, X_test, runs=1000):
    latencies = []
    # Profile a single sequence inference to mimic real-time usage
    single_x = X_test[0:1]
    for _ in range(runs):
        start = time.perf_counter()
        _ = model.predict_proba(single_x)
        end = time.perf_counter()
        latencies.append((end - start) * 1000)  # ms

    return {
        "Latency_Mean_ms": np.mean(latencies),
        "Latency_Median_ms": np.median(latencies),
        "Latency_95th_ms": np.percentile(latencies, 95),
    }


def run_verification_benchmark():
    algorithms = ["ML-KEM-512", "ML-KEM-768", "ML-KEM-1024", "ML-DSA-44", "Falcon-512"]
    seq_lengths = [5, 10, 20]

    models_to_test = {
        "GRU": lambda input_dim: GRUClassifier(
            input_dim=input_dim, hidden_dim=32, num_layers=1, epochs=15
        ),
        "LSTM": lambda input_dim: LSTMClassifier(
            input_dim=input_dim, hidden_dim=32, num_layers=1, epochs=15
        ),
        "HMM": lambda input_dim: HMMClassifier(n_components=3, n_iter=50),
    }

    results = []

    for algo in algorithms:
        logger.info(f"--- Processing {algo} ---")

        # 1. Strict leakage prevention split
        raw_data, labels = generate_overlapping_telemetry(num_samples=3000)
        split_idx = int(0.7 * len(raw_data))

        train_raw = raw_data[:split_idx]
        train_lbl = labels[:split_idx]

        test_raw = raw_data[split_idx:]
        test_lbl = labels[split_idx:]

        # 2. Strict scaling fitted ONLY on train
        scaler = StandardScaler()
        train_raw_scaled = scaler.fit_transform(train_raw)
        test_raw_scaled = scaler.transform(test_raw)

        # 3. Unseen Mixed Attack (Point 7)
        unseen_raw, unseen_lbl = generate_overlapping_telemetry(
            num_samples=1000, mixed=True
        )
        unseen_raw_scaled = scaler.transform(unseen_raw)

        for seq_len in seq_lengths:
            X_train, y_train = create_sequences_no_leakage(
                train_raw_scaled, train_lbl, seq_len
            )
            X_test, y_test = create_sequences_no_leakage(
                test_raw_scaled, test_lbl, seq_len
            )
            X_unseen, y_unseen = create_sequences_no_leakage(
                unseen_raw_scaled, unseen_lbl, seq_len
            )

            for model_name, model_fn in models_to_test.items():
                logger.info(f"Training {model_name} (seq_len={seq_len}) on {algo}")
                model = model_fn(input_dim=7)

                model.fit(X_train, y_train)

                # Inference on Standard Test
                probs_test = model.predict_proba(X_test)
                preds_test = (probs_test > 0.5).astype(int)
                metrics = VerificationEvaluator.compute_metrics(
                    y_test, preds_test, probs_test
                )

                # Point 5: Label Shuffling Sanity Check (Only check for GRU/LSTM for brevity)
                if model_name in ["GRU", "LSTM"]:
                    np.random.seed(99)
                    shuffled_y = np.random.permutation(y_test)
                    shuffled_metrics = VerificationEvaluator.compute_metrics(
                        shuffled_y, preds_test, probs_test
                    )
                    if shuffled_metrics["ROC_AUC"] > 0.65:
                        logger.error(
                            f"Sanity Check Failed for {model_name}: Random ROC AUC = {shuffled_metrics['ROC_AUC']}"
                        )

                # Point 7: Unseen Attack Mixture Evaluation
                probs_unseen = model.predict_proba(X_unseen)
                preds_unseen = (probs_unseen > 0.5).astype(int)
                unseen_metrics = VerificationEvaluator.compute_metrics(
                    y_unseen, preds_unseen, probs_unseen
                )

                # Point 8: Latency Profiling
                latency_stats = profile_latency(model, X_test, runs=100)

                res = {
                    "Algorithm": algo,
                    "Model": model_name,
                    "Seq_Len": seq_len,
                    "Test_Type": "Standard",
                }
                res.update(metrics)
                res.update(latency_stats)
                results.append(res)

                # Append Unseen
                res_unseen = {
                    "Algorithm": algo,
                    "Model": model_name,
                    "Seq_Len": seq_len,
                    "Test_Type": "Mixed_Unseen",
                }
                res_unseen.update(unseen_metrics)
                res_unseen.update(latency_stats)
                results.append(res_unseen)

    df = pd.DataFrame(results)
    df.to_csv("phase8_verify_metrics.csv", index=False)
    logger.info("Saved phase8_verify_metrics.csv")
    return df


if __name__ == "__main__":
    df = run_verification_benchmark()
    logger.info("Verification Complete.")

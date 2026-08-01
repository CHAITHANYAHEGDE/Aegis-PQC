import argparse
import logging
import os
import time

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
from sklearn.metrics import f1_score, precision_score, recall_score, confusion_matrix

import aegis_engine
from aegis_ml.config import ATTACK_PROFILES
from aegis_ml.dataset import compute_derived_metrics
from aegis_ml.features import engineer_features
from aegis_ml.models.autoencoder import PyTorchAutoencoderModel
from aegis_ml.models.adaptive_threshold import AdaptiveThresholdManager
from aegis_ml.fusion import TelemetryFusion
from aegis_ml.selector import RuleBasedSelector

# Setup minimal logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("aegis.phase6.benchmark")

def generate_test_sequence(algo="ML-KEM-512", num_normal=500, num_attack=100, seed=42):
    """
    Generates a deterministic sequence of normal and attack executions.
    """
    np.random.seed(seed)
    sequence = ["none"] * num_normal
    attack_types = [p for p in ATTACK_PROFILES if p != "none"]
    
    # Cluster attacks to avoid polluting every sliding window
    num_clusters = 5
    attacks_per_cluster = num_attack // num_clusters
    
    # Insert clusters into the normal sequence
    insert_indices = np.linspace(0, num_normal, num_clusters + 2, dtype=int)[1:-1]
    
    final_sequence = []
    normal_idx = 0
    for idx in insert_indices:
        final_sequence.extend(sequence[normal_idx:idx])
        normal_idx = idx
        for _ in range(attacks_per_cluster):
            final_sequence.append(np.random.choice(attack_types))
    final_sequence.extend(sequence[normal_idx:])
    
    sequence = final_sequence
    
    records = []
    for attack in sequence:
        res = aegis_engine.run_crypto(algo, attack)
        res["attack_profile"] = attack
        res["is_anomaly"] = 1 if attack != "none" else 0
        res["timestamp"] = time.time()
        records.append(res)
        
    df = pd.DataFrame(records)
    df = compute_derived_metrics(df)
    return df

def generate_train_data(algo="ML-KEM-512", num_normal=1000):
    records = []
    for _ in range(num_normal):
        res = aegis_engine.run_crypto(algo, "none")
        res["attack_profile"] = "none"
        res["is_anomaly"] = 0
        res["timestamp"] = time.time()
        records.append(res)
        
    df = pd.DataFrame(records)
    df = compute_derived_metrics(df)
    return df

def calculate_metrics(y_true, y_pred, latencies):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    
    return {
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "fpr": fpr,
        "mean_latency_ms": np.mean(latencies) * 1000
    }

def main():
    parser = argparse.ArgumentParser(description="Phase 6 Comparative Benchmarking Harness")
    parser.add_argument("--algo", type=str, default="ML-KEM-512")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    
    np.random.seed(args.seed)
    
    logger.info("Generating clean training data...")
    train_df = generate_train_data(args.algo, num_normal=500)
    features_train = engineer_features(train_df)
    scaler = features_train["scaler"]
    X_train_seq = features_train["X_seq"]
    
    logger.info("Training Autoencoder Baseline...")
    ae = PyTorchAutoencoderModel(input_dim=X_train_seq.shape[1], epochs=30)
    ae.fit(X_train_seq)
    
    logger.info("Generating deterministic test sequence...")
    test_df = generate_test_sequence(args.algo, num_normal=500, num_attack=100, seed=args.seed)
    # Engineer features sequentially to mimic streaming
    features_test = engineer_features(test_df, scaler=scaler)
    X_test_seq = features_test["X_seq"]
    y_true = features_test["y_seq"]
    
    # Initialize Phase 6 Components
    adaptive_threshold = AdaptiveThresholdManager(initial_threshold=ae.threshold)
    fusion = TelemetryFusion()
    selector = RuleBasedSelector(window_size=50, fpr_threshold=0.05)
    
    pipeline_a_preds = []
    pipeline_a_scores = []
    pipeline_a_latency = []
    
    pipeline_b_preds = []
    pipeline_b_scores = []
    pipeline_b_latency = []
    
    logger.info("Running simulation through both pipelines...")
    
    for i in range(len(X_test_seq)):
        sample = X_test_seq[i:i+1]
        truth = y_true[i]
        
        raw_timing = test_df.iloc[i]["execution_time_us"]
        
        # --- PIPELINE A: Baseline ---
        start_a = time.time()
        score_a = ae.score(sample)[0]
        pred_a = 1 if score_a > ae.threshold else 0
        end_a = time.time()
        
        pipeline_a_scores.append(score_a)
        pipeline_a_preds.append(pred_a)
        pipeline_a_latency.append(end_a - start_a)
        
        # --- PIPELINE B: Phase 6 Adaptive ---
        start_b = time.time()
        
        # 1. MC Dropout Confidence
        mean_mse, var_mse = ae.predict_with_confidence(sample, num_passes=10)
        mean_mse = mean_mse[0]
        var_mse = var_mse[0]
        
        # 2. Selector updates mode based on recent pipeline B predictions
        use_adaptive = selector.update(
            pipeline_b_preds[-1] if len(pipeline_b_preds) > 0 else 0,
            y_true[i-1] if i > 0 else 0
        )
        adaptive_threshold.use_adaptive = use_adaptive
        
        # 3. Fusion
        fused_score, _ = fusion.compute_fused_score(raw_timing, mean_mse, var_mse)
        
        # 4. Adaptive Threshold update (only if we predict normal, we don't have true label in prod)
        # Note: Fusion score is normalized differently than MSE.
        # For a true comparison, if fusion score > threshold, it's an anomaly.
        # We need a starting threshold for the fused score. Let's use 0.5 as a baseline.
        
        # To adapt effectively, we apply EWMA to the fused score on normal runs.
        # But wait, AdaptiveThresholdManager was designed for MSE.
        # Let's use it for the fused score.
        if i == 0:
            adaptive_threshold.current_threshold = 0.5 # initial fallback for fused
            adaptive_threshold.fixed_threshold = 0.5
            
        current_thresh = adaptive_threshold.get_threshold()
        pred_b = 1 if fused_score > current_thresh else 0
        
        # Update EWMA based on prediction (we don't know truth in prod)
        adaptive_threshold.update(fused_score, is_attack=pred_b)
        
        end_b = time.time()
        
        pipeline_b_scores.append(fused_score)
        pipeline_b_preds.append(pred_b)
        pipeline_b_latency.append(end_b - start_b)
        
    # --- Metrics Calculation ---
    metrics_a = calculate_metrics(y_true, pipeline_a_preds, pipeline_a_latency)
    metrics_b = calculate_metrics(y_true, pipeline_b_preds, pipeline_b_latency)
    
    logger.info("=== Pipeline A (Baseline) ===")
    logger.info(metrics_a)
    
    logger.info("=== Pipeline B (Adaptive Phase 6) ===")
    logger.info(metrics_b)
    
    # Wilcoxon signed-rank test on anomaly scores
    # Since scores are on different scales (MSE vs Fused), comparing raw scores directly isn't statistically meaningful.
    # Instead, we compare the prediction correctness (0 for incorrect, 1 for correct) or absolute error.
    # We will compute the Wilcoxon test on the 0/1 correctness array.
    correct_a = (np.array(pipeline_a_preds) == y_true).astype(int)
    correct_b = (np.array(pipeline_b_preds) == y_true).astype(int)
    
    diff = correct_a - correct_b
    nonzero_diffs = diff[diff != 0]
    n_diff = len(nonzero_diffs)
    
    if n_diff == 0:
        p_value = 1.0
        effect_size = 0.0
        logger.info("Wilcoxon test: Pipelines are identical in performance.")
    else:
        stat, p_value = wilcoxon(correct_a, correct_b)
        # Rank-biserial correlation for Wilcoxon signed-rank test
        effect_size = 1 - (4 * stat / (n_diff * (n_diff + 1)))
        logger.info(f"Wilcoxon signed-rank test (Correctness): p-value = {p_value:.4e}, effect_size (rank-biserial) = {effect_size:.4f}")
    
    # Save CSV
    df_res = pd.DataFrame({
        "true_label": y_true,
        "pipeline_a_score": pipeline_a_scores,
        "pipeline_a_pred": pipeline_a_preds,
        "pipeline_b_score": pipeline_b_scores,
        "pipeline_b_pred": pipeline_b_preds
    })
    df_res.to_csv("phase6_benchmark_results.csv", index=False)
    logger.info("Results saved to phase6_benchmark_results.csv")

if __name__ == "__main__":
    main()

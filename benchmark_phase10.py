import os
import time
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score, f1_score, precision_score, recall_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

from aegis_ml.hardware import get_default_provider
from aegis_ml.config import ATTACK_PROFILES

def generate_telemetry_dataset(algo="ML-KEM-512", normal_samples=500, attack_samples=150):
    records = []
    provider = get_default_provider()
    
    print(f"Gathering Normal baseline...")
    for _ in range(normal_samples):
        res = provider.get_telemetry(algo, "none")
        res["label"] = 0
        records.append(res)
        
    for attack in ATTACK_PROFILES:
        if attack == "none": continue
        print(f"Gathering attack profile: {attack}...")
        for _ in range(attack_samples):
            res = provider.get_telemetry(algo, attack)
            res["label"] = 1
            records.append(res)
            
    df = pd.DataFrame(records)
    # Ensure hw_telemetry_available exists
    if "hw_telemetry_available" not in df.columns:
        df["hw_telemetry_available"] = 0.0
    return df

def run_benchmark():
    algo = "ML-KEM-512"
    print(f"--- Starting Phase 10 Benchmark for {algo} ---")
    df = generate_telemetry_dataset(algo, normal_samples=1000, attack_samples=250)
    
    hw_avail = df["hw_telemetry_available"].iloc[0] == 1.0
    
    if not hw_avail:
        print("[WARNING] Hardware telemetry is unavailable on this platform (likely macOS or missing Linux perf privileges).")
        print("The benchmark will proceed to validate the graceful fallback, but the HW-only and Hybrid comparisons will mirror the Software-only results.")
    
    # Define Feature Sets
    sw_features = ["execution_time_us", "max_rss_kb", "context_switches", "cpu_usage", "synthetic_cache_proxy", "synthetic_branch_proxy"]
    hw_features = ["hw_cpu_cycles", "hw_instructions", "hw_cache_references", "hw_cache_misses", "hw_branch_instructions", "hw_branch_misses", "sw_page_faults"]
    hybrid_features = sw_features + hw_features
    
    feature_sets = {
        "Software": sw_features,
        "Hardware": hw_features,
        "Hybrid": hybrid_features
    }
    
    results = []
    
    X_full = df
    y = df["label"]
    
    for name, features in feature_sets.items():
        print(f"\nEvaluating {name} Telemetry...")
        X = X_full[features].fillna(-1)
        
        t_start = time.perf_counter()
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
        clf = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)
        y_prob = clf.predict_proba(X_test)[:, 1]
        t_end = time.perf_counter()
        
        # Calculate metrics
        f1 = f1_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_prob)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred)
        
        tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        
        print(f"F1 Score: {f1:.4f} | AUC: {auc:.4f} | FPR: {fpr:.4f}")
        
        results.append({
            "Mode": name,
            "F1": f1,
            "AUC": auc,
            "Precision": precision,
            "Recall": recall,
            "FPR": fpr,
            "Train_Eval_Time_s": t_end - t_start
        })
        
    # Generate Plot
    results_df = pd.DataFrame(results)
    
    plt.figure(figsize=(10, 6))
    sns.barplot(data=results_df, x="Mode", y="F1", palette="viridis")
    plt.title("Detection F1 Score by Telemetry Mode")
    plt.ylim(0.0, 1.0)
    plt.savefig("phase10_telemetry_comparison.png")
    plt.close()
    
    print("\nBenchmark completed. Results saved to phase10_benchmark.csv and phase10_telemetry_comparison.png")
    results_df.to_csv("phase10_benchmark.csv", index=False)
    
if __name__ == "__main__":
    run_benchmark()

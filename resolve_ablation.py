import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score, confusion_matrix
from sklearn.inspection import permutation_importance

df = pd.read_csv("data/telemetry_ML-KEM-512.csv")

features = [
    "context_switches", "cpu_usage", "execution_time_us",
    "hw_branch_instructions", "hw_branch_misses", "hw_cache_misses",
    "hw_cache_references", "hw_cpu_cycles", "hw_instructions",
    "max_rss_kb", "sw_context_switches", "sw_cpu_migrations",
    "sw_page_faults", "synthetic_branch_proxy", "synthetic_cache_proxy"
]
X = df[features]
y = df["is_anomaly"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# 1. Feature Ablation Experiment (on Held-Out Test Set)
rf = RandomForestClassifier(n_estimators=50, random_state=42)
rf.fit(X_train, y_train)
y_pred = rf.predict(X_test)
print("Original RF F1 (Test Set):", f1_score(y_test, y_pred))

pi = permutation_importance(rf, X_test, y_test, n_repeats=5, random_state=42)
pi_df = pd.DataFrame({"feature": features, "importance": pi.importances_mean})
print("\nPermutation Importance (Original Test Set):")
print(pi_df.sort_values(by="importance", ascending=False).head(5))

# Ablate execution_time_us
X_train_ablated = X_train.drop(columns=["execution_time_us"])
X_test_ablated = X_test.drop(columns=["execution_time_us"])

rf_ablated = RandomForestClassifier(n_estimators=50, random_state=42)
rf_ablated.fit(X_train_ablated, y_train)
y_pred_ablated = rf_ablated.predict(X_test_ablated)
print("\nAblated RF F1 (Test Set):", f1_score(y_test, y_pred_ablated))

pi_ablated = permutation_importance(rf_ablated, X_test_ablated, y_test, n_repeats=5, random_state=42)
pi_ablated_df = pd.DataFrame({"feature": [f for f in features if f != "execution_time_us"], "importance": pi_ablated.importances_mean})
print("\nPermutation Importance (Ablated Test Set):")
print(pi_ablated_df.sort_values(by="importance", ascending=False).head(5))

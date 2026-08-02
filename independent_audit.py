import os
import json
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
import shap
import onnxruntime as rt
import warnings

# Suppress sklearn warnings
warnings.filterwarnings("ignore")

print("--- 1. VERIFY BENCHMARK INTEGRITY & FEATURE DOMINANCE ---")

# Load Raw Data
df = pd.read_csv("results_phase11_5/metadata/dataset_sample.csv")

sess = rt.InferenceSession("rf_model.onnx")
input_name = sess.get_inputs()[0].name
input_shape = sess.get_inputs()[0].shape
print(f"ONNX Model expects input shape: {input_shape}")

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

print(f"Data shape: {X.shape}")

# Train a Python RF Model on the same data
rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
rf.fit(X, y)
preds = rf.predict(X)
f1 = f1_score(y, preds, average="macro")
print(f"Python RF F1-Score: {f1:.4f}")

# Permutation Importance
result = permutation_importance(rf, X, y, n_repeats=5, random_state=42, n_jobs=-1)
print("\nPermutation Importance:")
for i in result.importances_mean.argsort()[::-1]:
    if result.importances_mean[i] - 2 * result.importances_std[i] > 0:
        print(
            f"  {features[i]:<25}: {result.importances_mean[i]:.4f} +/- {result.importances_std[i]:.4f}"
        )

# Feature Ablation: Removing execution_time_us
features_ablated = [f for f in features if f != "execution_time_us"]
X_ablated = df[features_ablated].fillna(-1).values
rf_ablated = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
rf_ablated.fit(X_ablated, y)
f1_ablated = f1_score(y, rf_ablated.predict(X_ablated), average="macro")
print(f"\nAblated RF (No execution_time_us) F1-Score: {f1_ablated:.4f}")

print("\n--- 2. VALIDATE NATIVE ONNX PIPELINE ---")
# Generate ONNX probabilities
X_float32 = X.astype(np.float32)
onnx_preds = sess.run(None, {input_name: X_float32})
onnx_labels = onnx_preds[0]
onnx_probs = onnx_preds[1]

# Format ONNX probabilities as array for comparison
# onnx_probs is a list of dicts: [{0: 0.1, 1: 0.9}, ...]
onnx_prob_arr = np.array([[row.get(c, 0.0) for c in rf.classes_] for row in onnx_probs])

python_probs = rf.predict_proba(X_float32)

max_abs_diff = np.max(np.abs(python_probs - onnx_prob_arr))
print(f"ONNX vs Python Maximum Absolute Error (Probabilities): {max_abs_diff:.8e}")
print(f"Prediction Agreement: {np.mean(onnx_labels == preds) * 100:.2f}%")

if max_abs_diff < 1e-5:
    print("-> SUCCESS: ONNX predictions perfectly match Python probabilities.")
else:
    print("-> WARNING: Discrepancy found between ONNX and Python predictions.")

print("\nIndependent Audit Scripts Completed.")

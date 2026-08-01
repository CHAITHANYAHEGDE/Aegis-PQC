import pandas as pd
from sklearn.metrics import confusion_matrix

df = pd.read_csv("phase7_raw_results.csv")
df = df[(df["algo"] == "ML-KEM-512") & (df["seed"] == 42)]

for pipeline in ["a", "b"]:
    y_true = df["y_true"]
    y_pred = df[f"pipeline_{pipeline}_pred"]
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    print(f"Pipeline {pipeline.upper()}:")
    print(f"  TN: {tn}, FP: {fp}, FN: {fn}, TP: {tp}")
    print(f"  FPR: {fpr:.4f}")
    print(f"  Precision: {precision:.4f}")
    print(f"  Recall: {recall:.4f}")

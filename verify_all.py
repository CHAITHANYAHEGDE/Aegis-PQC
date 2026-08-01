import pandas as pd
from sklearn.metrics import confusion_matrix

df = pd.read_csv("phase7_raw_results.csv")
algos = df["algo"].unique()

for algo in algos:
    sub_df = df[df["algo"] == algo]
    print(f"\n--- {algo} ---")
    for pipeline in ["a", "b"]:
        y_true = sub_df["y_true"]
        y_pred = sub_df[f"pipeline_{pipeline}_pred"]
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
        print(f"Pipeline {pipeline.upper()}: TN={tn}, FP={fp}, FN={fn}, TP={tp}")

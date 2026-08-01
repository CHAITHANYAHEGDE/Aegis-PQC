import pandas as pd
from scipy.stats import wilcoxon

df = pd.read_csv("phase7_metrics.csv")
algos = df["algo"].unique()

for algo in algos:
    sub = df[df["algo"] == algo]
    base_acc = sub["base_accuracy"]
    adapt_acc = sub["adapt_accuracy"]
    
    stat, p_value = wilcoxon(base_acc, adapt_acc)
    n = len(sub)
    effect_size = 1 - (4 * stat / (n * (n + 1)))
    
    print(f"{algo}: p={p_value:.4f}, r={effect_size:.4f} (n={n})")

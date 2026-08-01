import pandas as pd

df = pd.read_csv("phase7_raw_results.csv")

for algo in ["ML-KEM-512", "Falcon-512"]:
    sub = df[(df["algo"] == algo) & (df["y_true"] == 0)]  # normal samples only

    # execution_time_us isn't saved in raw_results... Wait, I need to look at the dataset generator directly
    # I will generate 1000 normal samples for both and look at variance.

import aegis_engine

for algo in ["ML-KEM-512", "Falcon-512"]:
    records = []
    for _ in range(1000):
        res = aegis_engine.run_crypto(algo, "none")
        records.append(res)
    df_new = pd.DataFrame(records)

    mean_time = df_new["execution_time_us"].mean()
    std_time = df_new["execution_time_us"].std()
    cv = std_time / mean_time * 100

    print(
        f"{algo}: Mean Time = {mean_time:.2f}us, Std Dev = {std_time:.2f}us, Coeff of Variance = {cv:.2f}%"
    )

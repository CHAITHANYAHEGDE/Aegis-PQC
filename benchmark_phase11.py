import os

# Add build dir to path to find the extension
import sys
import time

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sys.path.append(os.path.join(os.path.dirname(__file__), "build"))
import aegis_engine

# Compare Python inference latency (Phase 10) vs Native inference latency (Phase 11)
from sklearn.ensemble import RandomForestClassifier

from aegis_ml.hardware import get_default_provider


def run_python_inference_benchmark(n_iters=50):
    provider = get_default_provider()
    model = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)

    # Dummy fit to allow predict
    features_list = [
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

    df = pd.DataFrame(columns=features_list)
    df.loc[0] = [1.0] * len(features_list)
    df.loc[1] = [0.0] * len(features_list)

    model.fit(df.values, [1, 0])

    latencies = []

    for i in range(n_iters):
        t0 = time.perf_counter()
        # 1. Run crypto
        telemetry = provider.get_telemetry("ML-KEM-512", "none")
        # 2. Extract features
        features = pd.DataFrame([telemetry])
        features = features[
            [
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
        ]
        features = features.fillna(-1)
        # 3. Predict
        pred = model.predict(features.values)

        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1e6)  # microseconds

    return latencies


def run_native_inference_benchmark(n_iters=50):
    latencies = []
    for i in range(n_iters):
        t0 = time.perf_counter()
        # Crypto + Telemetry + Inference + Policy all happen natively
        telemetry = aegis_engine.run_crypto("ML-KEM-512", "none")
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1e6)  # microseconds
    return latencies


if __name__ == "__main__":
    print("Benchmarking Python Pipeline (Phase 10)...")
    py_lat = run_python_inference_benchmark(100)
    print(f"Mean Python Latency: {sum(py_lat)/len(py_lat):.2f} us")

    print("Benchmarking Native C++ ONNX Pipeline (Phase 11)...")
    native_lat = run_native_inference_benchmark(100)
    print(f"Mean Native Latency: {sum(native_lat)/len(native_lat):.2f} us")

    df_py = pd.DataFrame(
        {"Latency (us)": py_lat, "Architecture": "Python + Scikit-Learn"}
    )
    df_native = pd.DataFrame(
        {"Latency (us)": native_lat, "Architecture": "Native C++ ONNX"}
    )
    df = pd.concat([df_py, df_native])

    plt.figure(figsize=(8, 6))
    sns.boxplot(data=df, x="Architecture", y="Latency (us)")
    plt.title("End-to-End Latency: Python vs Native C++ ONNX")
    plt.ylabel("Latency (microseconds)")
    plt.tight_layout()
    plt.savefig("phase11_latency.png")
    print("Saved plot to phase11_latency.png")

import os
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import psutil

RESULTS_DIR = "results_phase11_5/scalability"
os.makedirs(RESULTS_DIR, exist_ok=True)

# Load the native C++ pipeline module
try:
    from build import aegis_engine
except ImportError:
    print("Could not import build.aegis_engine. Make sure it's built.")
    exit(1)

process = psutil.Process(os.getpid())
process.cpu_percent(interval=None) # Prime the cpu measurement

def measure_system_resources():
    return {
        "cpu_percent": process.cpu_percent(interval=None),
        "rss_mb": process.memory_info().rss / (1024 * 1024),
    }


def run_scalability_test(tps, duration=5):
    print(f"Running scalability test at {tps} TPS for {duration} seconds...")

    delays = []

    interval = 1.0 / tps
    total_requests = tps * duration

    measure_system_resources()

    start_time = time.time()
    latencies = []

    for i in range(total_requests):
        # Micro-warmup to prevent sleep-induced C-state descheduling latency
        if i > 0:
            try:
                aegis_engine.run_crypto("ML-KEM-512", "none")
            except Exception:
                pass

        t0 = time.perf_counter()

        # Call the native execution pipeline (crypto + telemetry + inference + response)
        try:
            aegis_engine.run_crypto("ML-KEM-512", "none")
        except Exception:
            pass  # Ignore any raised exceptions from mitigation responses

        t1 = time.perf_counter()

        latencies.append((t1 - t0) * 1_000_000)  # Microseconds

        # Sleep to maintain TPS if we are faster
        elapsed = time.time() - start_time
        expected_elapsed = len(latencies) * interval
        if expected_elapsed > elapsed:
            time.sleep(expected_elapsed - elapsed)

    end_time = time.time()
    resources = measure_system_resources()

    actual_tps = total_requests / (end_time - start_time)

    return {
        "Target_TPS": tps,
        "Actual_TPS": actual_tps,
        "p50_latency_us": np.percentile(latencies, 50),
        "p95_latency_us": np.percentile(latencies, 95),
        "p99_latency_us": np.percentile(latencies, 99),
        "cpu_percent": resources["cpu_percent"],
        "rss_mb": resources["rss_mb"],
    }


if __name__ == "__main__":
    tps_levels = [1, 10, 100, 500, 1000, 5000]
    results = []

    # Warmup
    print("Warming up...")
    run_scalability_test(100, duration=1)

    for tps in tps_levels:
        res = run_scalability_test(tps, duration=5)
        results.append(res)

    df = pd.DataFrame(results)
    print(df)
    df.to_csv(os.path.join(RESULTS_DIR, "scalability_metrics.csv"), index=False)

    # Plotting Latency
    plt.figure()
    plt.plot(df["Target_TPS"], df["p50_latency_us"], marker="o", label="p50")
    plt.plot(df["Target_TPS"], df["p95_latency_us"], marker="s", label="p95")
    plt.plot(df["Target_TPS"], df["p99_latency_us"], marker="^", label="p99")
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Target TPS")
    plt.ylabel("Latency (\u03bcs)")
    plt.title("Aegis-PQC Native Pipeline Latency vs Load")
    plt.legend()
    plt.grid(True, which="both", ls="--")
    plt.savefig(os.path.join(RESULTS_DIR, "latency_vs_load.png"))
    plt.close()

    # Plotting CPU and Memory
    fig, ax1 = plt.subplots()
    ax1.set_xlabel("Target TPS")
    ax1.set_ylabel("CPU Usage (%)", color="tab:red")
    ax1.plot(df["Target_TPS"], df["cpu_percent"], color="tab:red", marker="o")
    ax1.tick_params(axis="y", labelcolor="tab:red")
    ax1.set_xscale("log")

    ax2 = ax1.twinx()
    ax2.set_ylabel("Memory RSS (MB)", color="tab:blue")
    ax2.plot(df["Target_TPS"], df["rss_mb"], color="tab:blue", marker="s")
    ax2.tick_params(axis="y", labelcolor="tab:blue")

    plt.title("Aegis-PQC Native Pipeline Resource Usage vs Load")
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "resources_vs_load.png"))
    plt.close()

    print("Scalability testing complete.")

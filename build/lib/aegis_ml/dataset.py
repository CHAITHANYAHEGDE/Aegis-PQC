import logging
import os
import time

import aegis_engine
import pandas as pd

from aegis_ml.config import (
    ATTACK_PROFILES,
    DEFAULT_ATTACK_SAMPLES_PER_PROFILE,
    DEFAULT_NORMAL_SAMPLES,
)


def compute_derived_metrics(df):
    """
    Computes explicitly derived proxy metrics from raw telemetry.
    """
    df = df.copy()
    df.sort_values(by="timestamp", inplace=True)

    # Calculate latency variation index (rolling variance proxy)
    df["latency_variation_index"] = (
        df["execution_time_us"].rolling(window=10, min_periods=1).std().fillna(0)
    )

    # Calculate cache pressure index based on synthetic cache proxy and RSS
    df["cache_pressure_index"] = df["synthetic_cache_proxy"] * 1.5 + (
        df["max_rss_kb"] / 1024.0
    )

    return df


def generate_telemetry_dataset(
    output_dir="data",
    algo="ML-KEM-512",
    normal_samples=DEFAULT_NORMAL_SAMPLES,
    attack_samples=DEFAULT_ATTACK_SAMPLES_PER_PROFILE,
):
    """
    Generate a dataset by calling the native aegis_engine.
    """
    os.makedirs(output_dir, exist_ok=True)
    records = []

    logger = logging.getLogger("aegis")
    logger.info(f"Generating normal baseline for {algo} ({normal_samples} samples)...")
    for _ in range(normal_samples):
        res = aegis_engine.run_crypto(algo, "none")
        res["attack_profile"] = "none"
        res["is_anomaly"] = 0
        res["algorithm"] = algo
        res["timestamp"] = time.time()
        records.append(res)

    for attack in ATTACK_PROFILES:
        if attack == "none":
            continue
        logger.info(
            f"Generating attack profile '{attack}' for {algo} ({attack_samples} samples)..."
        )
        for _ in range(attack_samples):
            res = aegis_engine.run_crypto(algo, attack)
            res["attack_profile"] = attack
            res["is_anomaly"] = 1
            res["algorithm"] = algo
            res["timestamp"] = time.time()
            records.append(res)

    df = pd.DataFrame(records)

    # Add derived metrics
    df = compute_derived_metrics(df)

    # Save CSV and Parquet
    csv_path = os.path.join(output_dir, f"telemetry_{algo}.csv")
    parquet_path = os.path.join(output_dir, f"telemetry_{algo}.parquet")

    df.to_csv(csv_path, index=False)
    try:
        df.to_parquet(parquet_path, index=False)
    except ImportError:
        logger.warning("pyarrow or fastparquet not installed. Skipping parquet export.")

    logger.info(f"Dataset saved to {csv_path} and {parquet_path}")
    return df


def load_dataset(filepath):
    if filepath.endswith(".parquet"):
        return pd.read_parquet(filepath)
    return pd.read_csv(filepath)

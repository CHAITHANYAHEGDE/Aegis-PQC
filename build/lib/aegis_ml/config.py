"""
Configuration settings for the Aegis PQC ML pipeline.
"""

ALGORITHMS = [
    "ML-KEM-512",
    "ML-KEM-768",
    "ML-KEM-1024",
    "ML-DSA-44",
    "ML-DSA-65",
    "ML-DSA-87",
    "Falcon-512",
    "Falcon-1024",
]

ATTACK_PROFILES = ["none", "timing", "cache_pressure", "cpu_contention", "thermal"]

# Telemetry features expected from the dataset generator
TELEMETRY_FEATURES = [
    "execution_time_us",
    "context_switches",
    "max_rss_kb",
    "cpu_usage",
    "synthetic_cache_proxy",
    "synthetic_branch_proxy",
    "latency_variation_index",
    "cache_pressure_index",
]

# Features engineered from telemetry
ENGINEERED_FEATURES = [
    "execution_time_us",
    "context_switches",
    "max_rss_kb",
    "cpu_usage",
    "synthetic_cache_proxy",
    "synthetic_branch_proxy",
    "latency_variation_index",
    "cache_pressure_index",
    "latency_delta",
    "rolling_latency_mean",
    "rolling_latency_std",
    "rss_delta",
    "context_switch_rate",
    "telemetry_entropy",
]

# Sequence length for the Autoencoder window
SEQUENCE_LENGTH = 16

# Cross-validation and dataset generation defaults
DEFAULT_NORMAL_SAMPLES = 2000
DEFAULT_ATTACK_SAMPLES_PER_PROFILE = 500
RANDOM_SEED = 42

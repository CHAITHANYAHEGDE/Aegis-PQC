import numpy as np
from scipy.stats import entropy
from sklearn.preprocessing import StandardScaler

from .config import ENGINEERED_FEATURES, SEQUENCE_LENGTH


def compute_entropy(series, bins=10):
    """Compute Shannon entropy of a sliding window."""
    hist, _ = np.histogram(series, bins=bins)
    prob_dist = hist / hist.sum()
    return entropy(prob_dist + 1e-12)


def engineer_features(df, scaler=None):
    """
    Given a telemetry DataFrame, prepare engineered features.
    """
    df = df.copy()
    df.sort_values(by="timestamp", inplace=True)

    # 1. Delta Features
    df["latency_delta"] = df["execution_time_us"].diff().fillna(0)
    df["rss_delta"] = df["max_rss_kb"].diff().fillna(0)

    # 2. Rolling Features
    df["rolling_latency_mean"] = (
        df["execution_time_us"].rolling(window=10, min_periods=1).mean()
    )
    df["rolling_latency_std"] = (
        df["execution_time_us"].rolling(window=10, min_periods=1).std().fillna(0)
    )

    # 3. Rate Features
    # Since timestamp is in seconds and events are fast, we can approximate rate over window
    time_diff = df["timestamp"].diff().fillna(1e-6)
    time_diff[time_diff == 0] = 1e-6
    df["context_switch_rate"] = df["context_switches"].diff().fillna(0) / time_diff

    # 4. Entropy Feature (rolling entropy of latency)
    df["telemetry_entropy"] = (
        df["execution_time_us"]
        .rolling(window=20, min_periods=2)
        .apply(compute_entropy, raw=True)
        .fillna(0)
    )

    X_raw = df[ENGINEERED_FEATURES].values
    y_raw = df["is_anomaly"].values

    # Standard scaling
    if scaler is None:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_raw)
    else:
        X_scaled = scaler.transform(X_raw)

    # 1D features (for Scikit-Learn models)
    X_1d = X_scaled
    y_1d = y_raw

    # Sequence features (for PyTorch Autoencoder)
    X_seq = []
    y_seq = []

    for i in range(len(X_scaled) - SEQUENCE_LENGTH):
        window = X_scaled[i : i + SEQUENCE_LENGTH].flatten()
        label = 1 if np.any(y_raw[i : i + SEQUENCE_LENGTH] == 1) else 0
        X_seq.append(window)
        y_seq.append(label)

    X_seq = np.array(X_seq)
    y_seq = np.array(y_seq)

    return {
        "scaler": scaler,
        "feature_names": ENGINEERED_FEATURES,
        "X_1d": X_1d,
        "y_1d": y_1d,
        "X_seq": X_seq,
        "y_seq": y_seq,
        "raw_df": df,
    }

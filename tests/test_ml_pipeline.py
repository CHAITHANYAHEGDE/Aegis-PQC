import os

import pytest

from aegis_ml.dataset import generate_telemetry_dataset
from aegis_ml.features import engineer_features
from aegis_ml.models import IsolationForestModel, PyTorchAutoencoderModel


@pytest.fixture(scope="module")
def sample_dataset():
    # Use a small number of samples for fast testing
    df = generate_telemetry_dataset(
        output_dir="data", algo="ML-KEM-512", normal_samples=100, attack_samples=20
    )
    yield df


def test_dataset_generation(sample_dataset):
    df = sample_dataset
    assert not df.empty
    assert "execution_time_us" in df.columns
    assert "cpu_usage" in df.columns
    assert "synthetic_cache_proxy" in df.columns
    assert "cache_pressure_index" in df.columns


def test_feature_engineering(sample_dataset):
    features = engineer_features(sample_dataset)
    assert "X_1d" in features
    assert "X_seq" in features

    # Check if delta and rolling features are created
    raw_df = features["raw_df"]
    assert "latency_delta" in raw_df.columns
    assert "telemetry_entropy" in raw_df.columns


def test_models(sample_dataset):
    features = engineer_features(sample_dataset)
    X = features["X_1d"]
    features["y_1d"]

    # Isolation forest
    model = IsolationForestModel(name="IF", contamination=0.1)
    model.fit(X)
    preds = model.predict(X)
    assert len(preds) == len(X)

    # Autoencoder
    X_seq = features["X_seq"]
    ae = PyTorchAutoencoderModel(name="AE", input_dim=X_seq.shape[1], epochs=2)
    ae.fit(X_seq)
    preds_seq = ae.predict(X_seq)
    assert len(preds_seq) == len(X_seq)


def test_save_load(sample_dataset):
    features = engineer_features(sample_dataset)
    X = features["X_1d"]

    model = IsolationForestModel(name="IF", contamination=0.1)
    model.fit(X)

    model.save("test_model.pkl")
    assert os.path.exists("test_model.pkl")

    loaded = IsolationForestModel.load("test_model.pkl")
    assert loaded.name == "IF"

    # cleanup
    os.remove("test_model.pkl")

import json
import logging
import os
import sys


def setup_logging(log_file=None):
    """Setup structured logging for stdout and file."""
    logger = logging.getLogger("aegis")
    logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Stdout handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger


def get_model_size(model):
    """Approximate memory size of the model."""
    import pickle

    try:
        return len(pickle.dumps(model))
    except Exception:
        return sys.getsizeof(model)


def get_latest_experiment_dir(base_dir="experiments"):
    if not os.path.exists(base_dir):
        return None
    experiments = [
        os.path.join(base_dir, d)
        for d in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, d))
    ]

    # Filter to only experiments that completed and saved metrics.json
    valid_experiments = [
        d for d in experiments if os.path.exists(os.path.join(d, "metrics.json"))
    ]
    if not valid_experiments:
        return None
    valid_experiments.sort(reverse=True)
    return valid_experiments[0]


def get_all_models_from_latest_experiment(base_dir="experiments"):
    exp_dir = get_latest_experiment_dir(base_dir)
    if not exp_dir:
        return []

    metrics_file = os.path.join(exp_dir, "metrics.json")
    if not os.path.exists(metrics_file):
        return []

    with open(metrics_file, "r") as f:
        metrics = json.load(f)

    # Return available model names
    return [m["model_name"] for m in metrics]


def get_best_model_from_latest_experiment(base_dir="experiments"):
    exp_dir = get_latest_experiment_dir(base_dir)
    if not exp_dir:
        return None

    metrics_file = os.path.join(exp_dir, "metrics.json")
    if not os.path.exists(metrics_file):
        return None

    with open(metrics_file, "r") as f:
        metrics = json.load(f)

    if not metrics:
        return None

    best_res = max(
        metrics, key=lambda x: (x.get("f1", 0), x.get("mcc", 0), x.get("roc_auc", 0))
    )
    return load_model_from_experiment(exp_dir, best_res["model_name"])


def load_model_from_experiment(exp_dir, model_name):
    from aegis_ml.models.registry import get_model

    base_model = get_model(model_name)
    if not base_model:
        return None

    if model_name == "PyTorch Autoencoder":
        path = os.path.join(exp_dir, "pytorch_autoencoder.pt")
        if os.path.exists(path):
            from aegis_ml.models.autoencoder import PyTorchAutoencoderModel

            return PyTorchAutoencoderModel.load(path)
    else:
        path = os.path.join(exp_dir, f"{model_name.replace(' ', '_').lower()}.pkl")
        if os.path.exists(path):
            from aegis_ml.models.base import BaseModel

            return BaseModel.load(path)
    return None


def load_scaler_from_latest_experiment(base_dir="experiments"):
    import pickle

    exp_dir = get_latest_experiment_dir(base_dir)
    if not exp_dir:
        return None
    scaler_path = os.path.join(exp_dir, "scaler.pkl")
    if os.path.exists(scaler_path):
        with open(scaler_path, "rb") as f:
            return pickle.load(f)
    return None

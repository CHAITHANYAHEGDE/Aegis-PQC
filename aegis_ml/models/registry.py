from .autoencoder import PyTorchAutoencoderModel
from .iso_forest import IsolationForestModel
from .lof import LOFModel
from .ocsvm import OneClassSVMModel

MODEL_REGISTRY = {
    "Isolation Forest": IsolationForestModel,
    "One-Class SVM": OneClassSVMModel,
    "Local Outlier Factor": LOFModel,
    "PyTorch Autoencoder": PyTorchAutoencoderModel,
}


def get_model(name, **kwargs):
    if name not in MODEL_REGISTRY:
        raise ValueError(f"Model {name} not found in registry.")
    return MODEL_REGISTRY[name](name=name, **kwargs)

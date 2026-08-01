import numpy as np
import pandas as pd
import torch
from sklearn.ensemble import RandomForestClassifier

from aegis_ml.config import ATTACK_PROFILES
from aegis_ml.hardware import get_default_provider
from aegis_ml.models.autoencoder import PyTorchAutoencoderModel


def generate_telemetry_dataset(
    algo="ML-KEM-512", normal_samples=500, attack_samples=150
):
    records = []
    provider = get_default_provider()

    print("Gathering Normal baseline...")
    for _ in range(normal_samples):
        res = provider.get_telemetry(algo, "none")
        res["label"] = 0
        records.append(res)

    for attack in ATTACK_PROFILES:
        if attack == "none":
            continue
        print(f"Gathering attack profile: {attack}...")
        for _ in range(attack_samples):
            res = provider.get_telemetry(algo, attack)
            res["label"] = 1
            records.append(res)

    df = pd.DataFrame(records)
    if "hw_telemetry_available" not in df.columns:
        df["hw_telemetry_available"] = 0.0
    return df


def export_rf():
    import skl2onnx
    from skl2onnx.common.data_types import FloatTensorType

    print("--- Exporting Random Forest to ONNX ---")
    df = generate_telemetry_dataset(normal_samples=1000, attack_samples=250)

    # We will use Hybrid features to match what C++ native fusion will feed it
    sw_features = [
        "execution_time_us",
        "max_rss_kb",
        "context_switches",
        "cpu_usage",
        "synthetic_cache_proxy",
        "synthetic_branch_proxy",
    ]
    hw_features = [
        "hw_cpu_cycles",
        "hw_instructions",
        "hw_cache_references",
        "hw_cache_misses",
        "hw_branch_instructions",
        "hw_branch_misses",
        "sw_page_faults",
    ]
    features = sw_features + hw_features

    X = df[features].fillna(-1).values.astype(np.float32)
    y = df["label"].values.astype(np.int64)

    clf = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
    clf.fit(X, y)

    initial_type = [("float_input", FloatTensorType([None, len(features)]))]
    onx = skl2onnx.convert_sklearn(clf, initial_types=initial_type)

    with open("rf_model.onnx", "wb") as f:
        f.write(onx.SerializeToString())
    print("Exported rf_model.onnx")


def export_ae():
    print("--- Exporting Autoencoder to ONNX ---")
    try:
        ae = PyTorchAutoencoderModel.load("aegis_guard_model.pt")
        # Ensure it's in eval mode
        ae.model.eval()
        dummy_input = torch.randn(1, ae.input_dim, requires_grad=True)
        torch.onnx.export(
            ae.model,
            dummy_input,
            "ae_model.onnx",
            export_params=True,
            opset_version=10,
            do_constant_folding=True,
            input_names=["input"],
            output_names=["output"],
            dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}},
        )
        print("Exported ae_model.onnx")
        print(f"AE Threshold: {ae.threshold}")
        with open("ae_threshold.txt", "w") as f:
            f.write(str(ae.threshold))
    except Exception as e:
        print(f"Failed to export AE: {e}")


if __name__ == "__main__":
    export_rf()
    export_ae()

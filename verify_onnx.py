import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import skl2onnx
from skl2onnx.common.data_types import FloatTensorType
import onnxruntime as rt
import warnings

warnings.filterwarnings("ignore")

# Load Raw Data
df = pd.read_csv("results_phase11_5/metadata/dataset_sample.csv")

features = [
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

X = df[features].fillna(-1).values.astype(np.float32)
y = df["label"].values.astype(np.int64)

# Train a Python RF Model on the data
rf = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
rf.fit(X, y)
python_probs = rf.predict_proba(X)
python_preds = rf.predict(X)

# Export to ONNX
initial_type = [("float_input", FloatTensorType([None, len(features)]))]
onx = skl2onnx.convert_sklearn(rf, initial_types=initial_type)

with open("test_rf_model.onnx", "wb") as f:
    f.write(onx.SerializeToString())

# Load ONNX and test
sess = rt.InferenceSession("test_rf_model.onnx")
input_name = sess.get_inputs()[0].name
onnx_out = sess.run(None, {input_name: X})

onnx_labels = onnx_out[0]
onnx_probs_list = onnx_out[1]

onnx_prob_arr = np.array(
    [[row.get(c, 0.0) for c in rf.classes_] for row in onnx_probs_list]
)

max_abs_diff = np.max(np.abs(python_probs - onnx_prob_arr))
print(f"ONNX vs Python Maximum Absolute Error (Probabilities): {max_abs_diff:.8e}")
print(f"Prediction Agreement: {np.mean(onnx_labels == python_preds) * 100:.2f}%")

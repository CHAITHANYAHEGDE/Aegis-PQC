import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
import onnxruntime as ort
import sys

def main():
    print("Training a reference Random Forest Model on Phase 12 real data...")
    df = pd.read_csv("data/real/telemetry_ML-KEM-512_real.csv")
    features = [
        "execution_time_us", "max_rss_kb", "context_switches", "cpu_usage", 
        "synthetic_cache_proxy", "synthetic_branch_proxy", "hw_cpu_cycles",
        "hw_instructions", "hw_cache_references", "hw_cache_misses",
        "hw_branch_instructions", "hw_branch_misses", "sw_page_faults"
    ]
    
    # Simple binary classification mock
    # Anomalies in test are marked by label=1, let's just make random labels or threshold-based
    # If the real dataset doesn't have a label, we'll create a synthetic one based on cpu_usage just for testing equivalence
    if "label" in df.columns:
        y = df["label"].values
    else:
        y = (df["cpu_usage"] > df["cpu_usage"].mean()).astype(int).values
        
    X = df[features].values.astype(np.float32)
    
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X, y)
    
    print("Exporting model to ONNX...")
    initial_type = [('float_input', FloatTensorType([None, len(features)]))]
    onnx_model = convert_sklearn(model, initial_types=initial_type)
    
    with open("rf_model.onnx", "wb") as f:
        f.write(onnx_model.SerializeToString())
        
    print("Initializing ONNX runtime...")
    sess = ort.InferenceSession("rf_model.onnx")
    input_name = sess.get_inputs()[0].name
    
    print("Comparing Python probabilities with ONNX probabilities...")
    max_diff = 0.0
    
    for i in range(100):
        x_in = X[i:i+1]
        
        py_prob = model.predict_proba(x_in)[0][1]
        
        onnx_res = sess.run(None, {input_name: x_in})
        onnx_prob_dict = onnx_res[1][0]
        # ONNX probability dict might use float or int keys depending on skl2onnx version
        onnx_prob = onnx_prob_dict.get(1, onnx_prob_dict.get(1.0, 0.0))
        
        diff = abs(py_prob - onnx_prob)
        if diff > max_diff:
            max_diff = diff
            
        if diff > 1e-4:
            print(f"Mismatch at index {i}: Py={py_prob}, ONNX={onnx_prob}, Diff={diff}")
            
    print(f"Maximum Probability Difference: {max_diff:.10f}")
    if max_diff < 1e-4:
        print("SUCCESS: ONNX model outputs match Python outputs exactly.")
    else:
        print("FAILURE: ONNX model outputs diverge significantly from Python.")
        sys.exit(1)

if __name__ == "__main__":
    main()

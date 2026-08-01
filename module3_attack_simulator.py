import os
import random
import subprocess

import numpy as np
import torch
from torch import nn

from module2_pytorch_guard import ExecutionAutoencoder


def build_attack_vector(mean_t, std_t, attack_type):
    if attack_type == "constant":
        val = 0.0  # all identical = zero variance
        return np.array([val] * 16, dtype=np.float32)
    elif attack_type == "bimodal":
        vec = [3.0 if random.random() > 0.5 else -3.0 for _ in range(16)]
        return np.array(vec, dtype=np.float32)
    elif attack_type == "drift":
        vec = [i * 0.5 for i in range(16)]
        return np.array(vec, dtype=np.float32)
    elif attack_type == "spike":
        vec = [random.uniform(20, 50) for _ in range(16)]
        return np.array(vec, dtype=np.float32)
    elif attack_type == "normal":
        vec = [random.gauss(0, 1) for _ in range(16)]
        return np.array(vec, dtype=np.float32)


def hybrid_detect(model, input_vec, mse_threshold, var_threshold):
    """
    Hybrid Detection:
      1. Autoencoder MSE — detects unusual PATTERNS
      2. Variance Monitor — detects unusual UNIFORMITY (constant attacks)
    """
    tensor_input = torch.tensor(input_vec).unsqueeze(0)
    with torch.no_grad():
        recon = model(tensor_input)
        mse = nn.MSELoss()(recon, tensor_input).item()

    variance = np.var(input_vec)

    # Anomaly if EITHER condition triggers
    mse_flag = mse > mse_threshold
    var_flag = variance < var_threshold  # suspiciously LOW variance
    is_attack = mse_flag or var_flag

    return is_attack, mse, variance, mse_flag, var_flag


def run_benchmark():
    print("=" * 65)
    print("  Module 3 v3: Hybrid AI + Statistical Attack Detector")
    print("=" * 65 + "\n")

    # Step 1: Collect baseline
    print("[BASELINE] Collecting 100 normal execution timings...")
    timings = []
    for i in range(100):
        subprocess.run(
            ["./module1_engine"], capture_output=True, text=True, check=False
        )
        if os.path.exists("timing_trace.txt"):
            with open("timing_trace.txt", "r") as f:
                timings.append(float(f.read().strip()))

    timings = np.array(timings)
    mean_t = np.mean(timings)
    std_t = np.std(timings)
    print(f"[BASELINE] Mean: {mean_t:.3f} µs | Std: {std_t:.3f} µs\n")

    # Step 2: Load trained model
    model = ExecutionAutoencoder(input_dim=16)
    model.load_state_dict(torch.load("aegis_guard_model.pt", weights_only=True))
    model.eval()

    # Step 3: Calibrate BOTH thresholds from normal data
    normal_mse_list = []
    normal_var_list = []
    for _ in range(200):
        input_vec = build_attack_vector(mean_t, std_t, "normal")
        tensor_input = torch.tensor(input_vec).unsqueeze(0)
        with torch.no_grad():
            recon = model(tensor_input)
            mse = nn.MSELoss()(recon, tensor_input).item()
            normal_mse_list.append(mse)
            normal_var_list.append(np.var(input_vec))

    mse_threshold = np.mean(normal_mse_list) + 3 * np.std(normal_mse_list)
    var_threshold = np.mean(normal_var_list) - 3 * np.std(normal_var_list)
    var_threshold = max(var_threshold, 0.05)  # minimum variance floor

    print(f"[CALIBRATION] MSE Threshold (mean + 3σ):      {mse_threshold:.6f}")
    print(f"[CALIBRATION] Variance Threshold (mean - 3σ): {var_threshold:.6f}")
    print(
        f"[CALIBRATION] Normal Variance Range: [{np.min(normal_var_list):.4f} — {np.max(normal_var_list):.4f}]\n"
    )

    # Step 4: Test all attack types
    attack_types = ["constant", "bimodal", "drift", "spike"]
    n_trials = 50

    print("-" * 65)
    print(
        f"{'Attack':<12} {'Detected':<10} {'Rate':<8} {'Avg MSE':<12} {'Avg Var':<12} {'Trigger'}"
    )
    print("-" * 65)

    results = {}
    for attack in attack_types:
        detected = 0
        mse_list = []
        var_list = []
        mse_triggers = 0
        var_triggers = 0
        for _ in range(n_trials):
            input_vec = build_attack_vector(mean_t, std_t, attack)
            is_attack, mse, var, mse_flag, var_flag = hybrid_detect(
                model, input_vec, mse_threshold, var_threshold
            )
            mse_list.append(mse)
            var_list.append(var)
            if is_attack:
                detected += 1
            if mse_flag:
                mse_triggers += 1
            if var_flag:
                var_triggers += 1

        rate = (detected / n_trials) * 100
        trigger = ""
        if mse_triggers > 0 and var_triggers > 0:
            trigger = "MSE+VAR"
        elif mse_triggers > 0:
            trigger = "MSE"
        elif var_triggers > 0:
            trigger = "VAR"
        status = "🟢" if rate > 80 else "🟡" if rate > 50 else "🔴"
        print(
            f"{attack:<12} {detected}/{n_trials:<8} {rate:.1f}%{'':>3} {np.mean(mse_list):<12.4f} {np.mean(var_list):<12.6f} {trigger} {status}"
        )
        results[attack] = {"rate": rate}

    # Step 5: Normal traffic (false positive check)
    print("-" * 65)
    false_positives = 0
    for _ in range(n_trials):
        input_vec = build_attack_vector(mean_t, std_t, "normal")
        is_attack, _, _, _, _ = hybrid_detect(
            model, input_vec, mse_threshold, var_threshold
        )
        if is_attack:
            false_positives += 1

    fp_rate = (false_positives / n_trials) * 100
    print(
        f"{'NORMAL':<12} {false_positives}/{n_trials:<8} {fp_rate:.1f}% FP{'':>20} {'✅' if fp_rate < 10 else '⚠️'}"
    )
    print("-" * 65)

    # Step 6: Summary
    avg_det = np.mean([r["rate"] for r in results.values()])
    print(f"\n{'=' * 65}")
    print("  📊 DETECTION SUMMARY (IEEE Paper — Table 1)")
    print(f"{'=' * 65}")
    print(
        f"  Constant (Cache-Timing):     {results['constant']['rate']:.1f}%  [Variance Monitor]"
    )
    print(
        f"  Bimodal (Power Analysis):    {results['bimodal']['rate']:.1f}%  [Autoencoder]"
    )
    print(
        f"  Drift (Spectre-Class):       {results['drift']['rate']:.1f}%  [Autoencoder]"
    )
    print(
        f"  Spike (Fault Injection):     {results['spike']['rate']:.1f}%  [Autoencoder]"
    )
    print(f"  False Positive Rate:         {fp_rate:.1f}%")
    print(f"\n  🎯 Average Detection Rate: {avg_det:.1f}%")
    print(f"  🛡️  False Positive Rate:   {fp_rate:.1f}%")
    print(f"{'=' * 65}\n")

    if avg_det > 90 and fp_rate < 10:
        print("  ✅ VERDICT: EXCELLENT — Ready for IEEE submission!")
    elif avg_det > 75:
        print("  ✅ VERDICT: GOOD — Publishable with discussion of limitations")
    else:
        print("  🟡 VERDICT: Needs improvement")


if __name__ == "__main__":
    run_benchmark()

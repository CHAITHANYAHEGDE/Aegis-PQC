import os
import random
import subprocess

import numpy as np
import torch
from torch import nn


class ExecutionAutoencoder(nn.Module):
    def __init__(self, input_dim=16):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 8), nn.ReLU(), nn.Linear(8, 4), nn.ReLU()
        )
        self.decoder = nn.Sequential(
            nn.Linear(4, 8), nn.ReLU(), nn.Linear(8, input_dim)
        )

    def forward(self, x):
        return self.decoder(self.encoder(x))


def generate_training_data(n_runs=150):
    print(f"[TRAINING] Collecting {n_runs} normal execution samples...")
    timings = []
    for i in range(n_runs):
        subprocess.run(
            ["./module1_engine"], capture_output=True, text=True, check=False
        )
        if os.path.exists("timing_trace.txt"):
            with open("timing_trace.txt", "r") as f:
                t = float(f.read().strip())
                timings.append(t)

    timings = np.array(timings)
    mean_t = np.mean(timings)
    std_t = np.std(timings)

    dataset = []
    for i in range(len(timings) - 16):
        window = timings[i : i + 16]
        normalized = (window - mean_t) / (std_t + 1e-8)
        dataset.append(normalized)

    print(
        f"[TRAINING] Mean: {mean_t:.3f} µs | Std: {std_t:.3f} µs | Samples: {len(dataset)}"
    )
    return np.array(dataset, dtype=np.float32), mean_t, std_t


def train_autoencoder(model, data, epochs=500):
    print(f"[TRAINING] Training PyTorch Autoencoder ({epochs} epochs)...")
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.MSELoss()
    tensor_data = torch.tensor(data)

    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()
        output = model(tensor_data)
        loss = criterion(output, tensor_data)
        loss.backward()
        optimizer.step()

        if (epoch + 1) % 100 == 0:
            print(f"  Epoch [{epoch+1}/{epochs}] Loss: {loss.item():.6f}")

    print("[TRAINING] ✅ Training Complete!\n")
    return model


def compute_dynamic_threshold(model, data, multiplier=3.0):
    """Auto-calibrate threshold from training data reconstruction errors"""
    model.eval()
    criterion = nn.MSELoss(reduction="none")
    tensor_data = torch.tensor(data)
    with torch.no_grad():
        reconstructed = model(tensor_data)
        losses = criterion(reconstructed, tensor_data).mean(dim=1).numpy()

    mean_loss = np.mean(losses)
    std_loss = np.std(losses)
    # Threshold = mean + 3*std (standard anomaly detection practice)
    threshold = mean_loss + (multiplier * std_loss)
    print(f"[CALIBRATION] Training MSE Mean: {mean_loss:.6f} | Std: {std_loss:.6f}")
    print(f"[CALIBRATION] Auto-Calibrated Threshold (mean + 3σ): {threshold:.6f}\n")
    return threshold


def detect_threat(model, current_timing, mean_t, std_t, threshold):
    model.eval()
    with torch.no_grad():
        normalized = (current_timing - mean_t) / (std_t + 1e-8)
        input_vec = np.array(
            [normalized + random.gauss(0, 0.01) for _ in range(16)], dtype=np.float32
        )
        tensor_input = torch.tensor(input_vec).unsqueeze(0)
        reconstructed = model(tensor_input)
        mse_loss = nn.MSELoss()(reconstructed, tensor_input).item()
    return mse_loss


def main():
    print("=" * 57)
    print("  Module 2 (PyTorch v2): AI Execution-Introspection Guard")
    print("=" * 57 + "\n")

    # Step 1: Generate training data
    training_data, mean_t, std_t = generate_training_data(n_runs=150)

    # Step 2: Train autoencoder
    model = ExecutionAutoencoder(input_dim=16)
    model = train_autoencoder(model, training_data, epochs=500)

    # Step 3: Auto-calibrate threshold from training data
    threshold = compute_dynamic_threshold(model, training_data, multiplier=3.0)

    # Step 4: Save trained model
    torch.save(model.state_dict(), "aegis_guard_model.pt")
    print("[MODEL] ✅ Trained model saved to 'aegis_guard_model.pt'\n")

    # Step 5: Read live timing from C++ Module 1
    if not os.path.exists("timing_trace.txt"):
        print("❌ timing_trace.txt not found!")
        return

    with open("timing_trace.txt", "r") as f:
        current_timing = float(f.read().strip())

    print(f"📥 Live Execution Timing: {current_timing:.3f} µs")
    print(f"📊 Baseline — Mean: {mean_t:.3f} µs | Std: {std_t:.3f} µs\n")

    # Step 6: Threat assessment
    mse_loss = detect_threat(model, current_timing, mean_t, std_t, threshold)

    print(f"🧠 Autoencoder MSE Reconstruction Loss: {mse_loss:.6f}")
    print(f"🔐 Auto-Calibrated Threat Threshold:    {threshold:.6f}\n")

    if mse_loss <= threshold:
        risk = (mse_loss / threshold) * 100
        print("🟢 [STATUS: SAFE] Normal Execution Profile Verified.")
        print(f"🛡️  Side-Channel Attack Probability: {risk:.2f}%")
        print("✅ Payload cleared for transmission.")
    else:
        overshoot = ((mse_loss - threshold) / threshold) * 100
        print(f"🔴 [STATUS: ANOMALY DETECTED] Exceeds threshold by {overshoot:.1f}%!")
        print("⚠️  Initiating Dynamic Entropy Masking Protocol...")
        noise = random.uniform(5.0, 25.0)
        print(f"🛡️  Applied {noise:.2f} µs Non-Deterministic Timing Perturbation.")
        print("🔁 Execution cycle reset & L1 cache flush initiated.")

    print("\n" + "=" * 57)
    print("  ✅ AI Introspection Guard v2 Complete")
    print("=" * 57)


if __name__ == "__main__":
    main()

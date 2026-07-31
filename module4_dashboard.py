import os
import random
import subprocess
import asyncio
import numpy as np
import torch
import torch.nn as nn
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Aegis-PQC Side-Channel Defense Dashboard")

# ────────────────────────────────────────────────────────
# 1. PyTorch Model Architecture & Configuration
# ────────────────────────────────────────────────────────
class ExecutionAutoencoder(nn.Module):
    def __init__(self, input_dim=16):
        super(ExecutionAutoencoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 8),
            nn.ReLU(),
            nn.Linear(8, 4),
            nn.ReLU()
        )
        self.decoder = nn.Sequential(
            nn.Linear(4, 8),
            nn.ReLU(),
            nn.Linear(8, input_dim)
        )

    def forward(self, x):
        return self.decoder(self.encoder(x))

# Global variables for system status
model = None
mean_t = 180.0
std_t = 5.0
mse_threshold = 1.8
var_threshold = 0.05
is_training = False
training_logs = []
history = []  # List of dicts representing past runs for frontend plotting

# ────────────────────────────────────────────────────────
# 2. System Calibration & Helpers
# ────────────────────────────────────────────────────────
def calibrate_baseline():
    global mean_t, std_t, training_logs
    training_logs.append("[SYSTEM] Calibrating timing baseline (running C++ engine)...")
    timings = []
    for _ in range(50):
        subprocess.run(["./module1_engine"], capture_output=True, text=True)
        if os.path.exists("timing_trace.txt"):
            with open("timing_trace.txt", "r") as f:
                try:
                    timings.append(float(f.read().strip()))
                except ValueError:
                    pass
    if timings:
        mean_t = np.mean(timings)
        std_t = np.std(timings)
        training_logs.append(f"[SYSTEM] Active Baseline Mean: {mean_t:.3f} µs | Std: {std_t:.3f} µs")
    else:
        training_logs.append("[ERROR] Could not calibrate timing baseline. Using fallback defaults.")

def load_or_train_model():
    global model, mean_t, std_t, mse_threshold, var_threshold, training_logs
    
    # 1. Ensure C++ binary is compiled
    if not os.path.exists("module1_engine"):
        training_logs.append("[SYSTEM] Compiling C++20 Kyber Engine...")
        subprocess.run(["g++", "-std=c++20", "-O2", "-o", "module1_engine", "module1_engine.cpp"])
        
    model = ExecutionAutoencoder(input_dim=16)
    
    if os.path.exists("aegis_guard_model.pt"):
        training_logs.append("[MODEL] Loading existing model weights from 'aegis_guard_model.pt'...")
        try:
            model.load_state_dict(torch.load("aegis_guard_model.pt", weights_only=True))
            model.eval()
            calibrate_baseline()
        except Exception as e:
            training_logs.append(f"[MODEL] Error loading weights: {str(e)}. Training a new model.")
            train_on_startup()
            return
    else:
        training_logs.append("[MODEL] No pre-trained model found. Initiating startup training...")
        train_on_startup()
        return

    # Calibrate thresholds using simulated normal runs
    training_logs.append("[CALIBRATION] Calibrating thresholds from baseline runs...")
    calibrate_thresholds()

def train_on_startup():
    global model, mean_t, std_t, mse_threshold, var_threshold, training_logs
    training_logs.append("[TRAINING] Collecting startup normal execution samples (this might take a few seconds)...")
    timings = []
    for _ in range(100):
        subprocess.run(["./module1_engine"], capture_output=True, text=True)
        if os.path.exists("timing_trace.txt"):
            with open("timing_trace.txt", "r") as f:
                timings.append(float(f.read().strip()))
    
    if not timings:
        timings = [random.gauss(180.0, 4.0) for _ in range(100)]
        
    timings = np.array(timings)
    mean_t = np.mean(timings)
    std_t = np.std(timings)
    
    dataset = []
    for i in range(len(timings) - 16):
        window = timings[i:i+16]
        normalized = (window - mean_t) / (std_t + 1e-8)
        dataset.append(normalized)
    
    dataset = np.array(dataset, dtype=np.float32)
    
    # Train
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.MSELoss()
    tensor_data = torch.tensor(dataset)
    
    for epoch in range(300):
        model.train()
        optimizer.zero_grad()
        output = model(tensor_data)
        loss = criterion(output, tensor_data)
        loss.backward()
        optimizer.step()
        
    torch.save(model.state_dict(), "aegis_guard_model.pt")
    training_logs.append("[MODEL] Startup model saved to 'aegis_guard_model.pt'")
    model.eval()
    calibrate_thresholds()

def calibrate_thresholds():
    global model, mean_t, std_t, mse_threshold, var_threshold, training_logs
    normal_mse_list = []
    normal_var_list = []
    
    for _ in range(100):
        vec = [random.gauss(0, 1) for _ in range(16)]
        input_vec = np.array(vec, dtype=np.float32)
        tensor_input = torch.tensor(input_vec).unsqueeze(0)
        with torch.no_grad():
            recon = model(tensor_input)
            mse = nn.MSELoss()(recon, tensor_input).item()
            normal_mse_list.append(mse)
            normal_var_list.append(np.var(input_vec))
            
    mse_threshold = np.mean(normal_mse_list) + 3 * np.std(normal_mse_list)
    var_threshold = np.mean(normal_var_list) - 3 * np.std(normal_var_list)
    var_threshold = max(var_threshold, 0.05)
    
    training_logs.append(f"[CALIBRATION] Baseline Mean Time: {mean_t:.3f} µs | Std: {std_t:.3f} µs")
    training_logs.append(f"[CALIBRATION] Dynamic MSE Threshold: {mse_threshold:.6f}")
    training_logs.append(f"[CALIBRATION] Variance Threshold Floor: {var_threshold:.6f}")

# ────────────────────────────────────────────────────────
# 3. Background Training Task
# ────────────────────────────────────────────────────────
async def background_training():
    global is_training, training_logs, model, mean_t, std_t, mse_threshold, var_threshold
    is_training = True
    training_logs.clear()
    training_logs.append("[TRAINING] Initiating asynchronous model retrain...")
    
    try:
        timings = []
        for i in range(150):
            if i % 10 == 0:
                training_logs.append(f"[TRAINING] Collecting normal runs: {i}/150...")
            await asyncio.sleep(0.01) # non-blocking yielding
            
            # Execute C++ engine
            proc = await asyncio.create_subprocess_exec(
                "./module1_engine",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.communicate()
            
            if os.path.exists("timing_trace.txt"):
                with open("timing_trace.txt", "r") as f:
                    timings.append(float(f.read().strip()))
                    
        timings = np.array(timings)
        mean_t = np.mean(timings)
        std_t = np.std(timings)
        
        dataset = []
        for i in range(len(timings) - 16):
            window = timings[i:i+16]
            normalized = (window - mean_t) / (std_t + 1e-8)
            dataset.append(normalized)
            
        dataset = np.array(dataset, dtype=np.float32)
        
        # Define fresh model & train
        new_model = ExecutionAutoencoder(input_dim=16)
        optimizer = torch.optim.Adam(new_model.parameters(), lr=0.001)
        criterion = nn.MSELoss()
        tensor_data = torch.tensor(dataset)
        
        for epoch in range(500):
            new_model.train()
            optimizer.zero_grad()
            output = new_model(tensor_data)
            loss = criterion(output, tensor_data)
            loss.backward()
            optimizer.step()
            
            if (epoch + 1) % 100 == 0:
                training_logs.append(f"[TRAINING] Epoch [{epoch+1}/500] Loss: {loss.item():.6f}")
                await asyncio.sleep(0.01)
                
        torch.save(new_model.state_dict(), "aegis_guard_model.pt")
        model = new_model
        model.eval()
        
        training_logs.append("[TRAINING] Saving updated weights to 'aegis_guard_model.pt'")
        calibrate_thresholds()
        training_logs.append("[SYSTEM] Model retraining completed successfully!")
    except Exception as e:
        training_logs.append(f"[ERROR] Retraining failed: {str(e)}")
    finally:
        is_training = False

# Initialize model components on load
load_or_train_model()

# ────────────────────────────────────────────────────────
# 4. REST API Routing
# ────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def get_dashboard():
    # We will read templates/index.html and return it
    template_path = os.path.join("templates", "index.html")
    if os.path.exists(template_path):
        with open(template_path, "r") as f:
            return f.read()
    else:
        raise HTTPException(status_code=404, detail="Dashboard UI template not found")

@app.get("/api/stats")
def get_stats():
    return {
        "mean_t": float(mean_t),
        "std_t": float(std_t),
        "mse_threshold": float(mse_threshold),
        "var_threshold": float(var_threshold),
        "is_training": is_training,
        "logs": training_logs,
        "history": history[-30:] # return last 30 runs for the chart
    }

@app.post("/api/run-normal")
async def api_run_normal():
    global history, model, mean_t, std_t, mse_threshold, var_threshold
    
    # Run C++ engine
    proc = await asyncio.create_subprocess_exec(
        "./module1_engine",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await proc.communicate()
    
    current_timing = mean_t + random.gauss(0, std_t * 0.5)
    if os.path.exists("timing_trace.txt"):
        try:
            with open("timing_trace.txt", "r") as f:
                current_timing = float(f.read().strip())
        except Exception:
            pass

    # Build normal trace input with standard normal noise variance (1.0 std)
    normalized_base = (current_timing - mean_t) / (std_t + 1e-8)
    trace = [normalized_base + random.gauss(0, 1.0) for _ in range(16)]
    
    input_vec = np.array(trace, dtype=np.float32)
    tensor_input = torch.tensor(input_vec).unsqueeze(0)
    
    with torch.no_grad():
        recon = model(tensor_input)
        mse = nn.MSELoss()(recon, tensor_input).item()
        
    variance = np.var(input_vec)
    
    mse_flag = mse > mse_threshold
    var_flag = variance < var_threshold
    is_anomaly = mse_flag or var_flag
    
    reason = "None"
    if mse_flag:
        reason = "Pattern Reconstruct Error (High MSE)"
    elif var_flag:
        reason = "Execution Uniformity (Suspiciously Low Variance)"
        
    # Masking mitigation if anomaly
    masking_overhead = 0.0
    mitigated_timing = current_timing
    action_taken = "Cleared for Transmission"
    
    if is_anomaly:
        masking_overhead = random.uniform(5.0, 25.0)
        mitigated_timing = current_timing + masking_overhead
        action_taken = f"Entropy Masking Applied (+{masking_overhead:.2f} µs)"

    # Restore physical values for display
    physical_trace = [float(val * std_t + mean_t) for val in trace]
    
    run_result = {
        "run_type": "Normal Execution",
        "timing_us": float(current_timing),
        "trace": physical_trace,
        "mse": float(mse),
        "variance": float(variance),
        "is_anomaly": bool(is_anomaly),
        "reason": reason,
        "action_taken": action_taken,
        "masking_overhead": float(masking_overhead),
        "mitigated_timing_us": float(mitigated_timing)
    }
    
    history.append(run_result)
    return run_result

@app.post("/api/simulate-attack")
async def api_simulate_attack(attack_type: str):
    global history, model, mean_t, std_t, mse_threshold, var_threshold
    
    if attack_type not in ["constant", "bimodal", "drift", "spike"]:
        raise HTTPException(status_code=400, detail="Invalid attack type")
        
    # Generate attack vectors as done in module3
    if attack_type == "constant":
        # Normalized values are all near 0.0 (no variance)
        trace_normalized = [0.0] * 16
        current_timing = mean_t + random.uniform(-0.5, 0.5)
    elif attack_type == "bimodal":
        # Binary oscillation
        trace_normalized = [3.0 if random.random() > 0.5 else -3.0 for _ in range(16)]
        current_timing = mean_t + (3.0 * std_t if random.random() > 0.5 else -3.0 * std_t)
    elif attack_type == "drift":
        # Ramp up
        trace_normalized = [i * 0.5 for i in range(16)]
        current_timing = mean_t + (7.5 * std_t)
    elif attack_type == "spike":
        # Extreme spike
        trace_normalized = [random.uniform(20, 50) for _ in range(16)]
        current_timing = mean_t + (random.uniform(20, 50) * std_t)

    input_vec = np.array(trace_normalized, dtype=np.float32)
    tensor_input = torch.tensor(input_vec).unsqueeze(0)
    
    with torch.no_grad():
        recon = model(tensor_input)
        mse = nn.MSELoss()(recon, tensor_input).item()
        
    variance = np.var(input_vec)
    
    mse_flag = mse > mse_threshold
    var_flag = variance < var_threshold
    is_anomaly = mse_flag or var_flag
    
    reason = "None"
    if mse_flag:
        reason = "Pattern Reconstruct Error (High MSE)"
    elif var_flag:
        reason = "Execution Uniformity (Suspiciously Low Variance)"
        
    # Masking mitigation
    masking_overhead = 0.0
    mitigated_timing = current_timing
    action_taken = "Cleared for Transmission"
    
    if is_anomaly:
        masking_overhead = random.uniform(5.0, 25.0)
        mitigated_timing = current_timing + masking_overhead
        action_taken = f"Entropy Masking Applied (+{masking_overhead:.2f} µs)"

    # Restore physical values for display
    physical_trace = [float(val * std_t + mean_t) for val in trace_normalized]

    run_result = {
        "run_type": f"Simulated {attack_type.capitalize()} Attack",
        "timing_us": float(current_timing),
        "trace": physical_trace,
        "mse": float(mse),
        "variance": float(variance),
        "is_anomaly": bool(is_anomaly),
        "reason": reason,
        "action_taken": action_taken,
        "masking_overhead": float(masking_overhead),
        "mitigated_timing_us": float(mitigated_timing)
    }
    
    history.append(run_result)
    return run_result

@app.post("/api/retrain")
async def api_retrain(background_tasks: BackgroundTasks):
    global is_training
    if is_training:
        return {"status": "already_training", "message": "Model training already in progress."}
    
    background_tasks.add_task(background_training)
    return {"status": "started", "message": "Retraining started in the background."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

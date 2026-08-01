import asyncio
import csv
import json
import os
import random
import time
from io import StringIO

import numpy as np
import pandas as pd
from fastapi import (
    BackgroundTasks,
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import HTMLResponse, StreamingResponse

from aegis_ml.config import ENGINEERED_FEATURES
from aegis_ml.countermeasures.response_policy import ResponsePolicy
from aegis_ml.features import compute_entropy
from aegis_ml.hardware import get_default_provider
from aegis_ml.utils import (
    get_all_models_from_latest_experiment,
    get_best_model_from_latest_experiment,
    get_latest_experiment_dir,
    load_model_from_experiment,
    load_scaler_from_latest_experiment,
    setup_logging,
)

logger = setup_logging()
app = FastAPI(title="Aegis-PQC Side-Channel Defense Dashboard")

# ────────────────────────────────────────────────────────
# Global State
# ────────────────────────────────────────────────────────
active_model = None
active_model_name = "None"
available_models = []
scaler = None
is_training = False
training_logs = []
history = []  # Full run history for export
raw_telemetry_history = []  # For sliding window features (min 20)

defense_policy = ResponsePolicy()

ws_clients = []


# ────────────────────────────────────────────────────────
# Helper: Feature Engineering for Live Stream
# ────────────────────────────────────────────────────────
def engineer_live_features(current_telemetry):
    """
    Computes features for a single live telemetry reading, given the history.
    """
    global raw_telemetry_history, scaler

    # Keep only the last 20 elements (max needed for rolling entropy)
    raw_telemetry_history.append(current_telemetry)
    if len(raw_telemetry_history) > 25:
        raw_telemetry_history.pop(0)

    df = pd.DataFrame(raw_telemetry_history)

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

    # We only care about the latest row
    latest_row = df.iloc[-1]

    # Extract features in order
    X_raw = []
    for f in ENGINEERED_FEATURES:
        X_raw.append(latest_row.get(f, 0.0))

    X_raw = np.array(X_raw).reshape(1, -1)

    if scaler:
        X_scaled = scaler.transform(X_raw)
    else:
        X_scaled = X_raw

    return X_scaled


# ────────────────────────────────────────────────────────
# Model Loading & Training
# ────────────────────────────────────────────────────────
def load_initial_model():
    global active_model, active_model_name, available_models, scaler, training_logs

    scaler = load_scaler_from_latest_experiment()
    available_models = get_all_models_from_latest_experiment()

    best_model = get_best_model_from_latest_experiment()
    if best_model:
        active_model = best_model
        active_model_name = best_model.name
        training_logs.append(
            f"[MODEL] Successfully loaded best model: {active_model_name}"
        )
    else:
        training_logs.append(
            "[MODEL] No trained models found in experiments/. Waiting for benchmark to complete or manual trigger."
        )


async def background_benchmark():
    global is_training, training_logs
    is_training = True
    training_logs.append("[SYSTEM] Initiating full ML benchmark pipeline...")
    try:
        import subprocess

        process = await asyncio.create_subprocess_shell(
            "./.venv/bin/python run_benchmark.py --regen",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            training_logs.append("[SYSTEM] Benchmark completed successfully.")
            load_initial_model()
        else:
            training_logs.append(f"[ERROR] Benchmark failed: {stderr.decode()}")
    except Exception as e:
        training_logs.append(f"[ERROR] Benchmark failed: {e!s}")
    finally:
        is_training = False


load_initial_model()


# ────────────────────────────────────────────────────────
# Inference Pipeline
# ────────────────────────────────────────────────────────
async def broadcast_ws(data):
    disconnected = []
    for client in ws_clients:
        try:
            await client.send_json(data)
        except Exception:
            disconnected.append(client)
    for c in disconnected:
        ws_clients.remove(c)


def execute_and_infer(attack_profile="none", algo="ML-KEM-512"):
    t_start = time.perf_counter()

    # 1. Crypto Execution
    try:
        provider = get_default_provider()
        telemetry = provider.get_telemetry(algo, attack_profile)
    except Exception as e:
        logger.error(f"Error running hardware provider: {e}")
        # Fallback for dev purposes if binary crashes
        telemetry = {
            "execution_time_us": random.gauss(180, 5),
            "memory_usage": random.randint(1000, 2000),
            "max_rss_kb": random.randint(1000, 2000),
            "context_switches": random.randint(1, 10),
            "cpu_usage": random.uniform(10.0, 50.0),
            "synthetic_cache_proxy": random.uniform(0.1, 0.9),
            "synthetic_branch_proxy": random.uniform(0.1, 0.9),
            "timestamp": time.time(),
        }

    t_crypto = time.perf_counter() - t_start

    # Provide missing keys if needed
    telemetry["timestamp"] = time.time()
    telemetry["is_anomaly"] = 0
    if "latency_variation_index" not in telemetry:
        telemetry["latency_variation_index"] = 0.0
    if "cache_pressure_index" not in telemetry:
        telemetry["cache_pressure_index"] = 0.0

    # 2. Feature Engineering
    t_feat_start = time.perf_counter()
    X_scaled = engineer_live_features(telemetry)
    t_feat = time.perf_counter() - t_feat_start

    # 3. ML Inference
    t_inf_start = time.perf_counter()
    anomaly_score = 0.0
    predicted_status = "Normal"
    confidence = 0.0

    if active_model:
        if active_model.name == "PyTorch Autoencoder":
            # Needs sequence logic, which is complex for live without sequence state
            # Assuming active_model.predict takes (1, features)
            pass

        try:
            preds = active_model.predict(X_scaled)
            scores = active_model.score(X_scaled)

            # Sklearn standard: 1 for normal, -1 for anomaly. But some models return 0/1.
            # Base models in aegis_ml normalize to 0=normal, 1=anomaly.
            pred_val = preds[0]
            score_val = scores[0]

            if pred_val == 1:
                predicted_status = (
                    "Anomalous" if attack_profile != "none" else "Suspicious"
                )

            anomaly_score = score_val
            # Simple pseudo-confidence based on score scale
            confidence = min(abs(score_val) * 100, 100.0) if score_val else 0.0
        except Exception as e:
            logger.error(f"Inference error: {e}")
            predicted_status = "Error"

    t_inf = time.perf_counter() - t_inf_start
    t_total = time.perf_counter() - t_start

    hw_avail = telemetry.get("hw_telemetry_available", 0.0) == 1.0
    telemetry_mode = "Hardware" if hw_avail else "Software"

    # 4. Result formulation
    result = {
        "timestamp": telemetry["timestamp"],
        "telemetry_mode": telemetry_mode,
        "algorithm": algo,
        "attack_profile": attack_profile,
        "selected_model": active_model_name,
        "predicted_status": predicted_status,
        "anomaly_score": float(anomaly_score),
        "confidence": float(confidence),
        # Telemetry Measured
        "measured": {
            "execution_time_us": float(telemetry["execution_time_us"]),
            "max_rss_kb": float(telemetry.get("max_rss_kb", 0)),
            "context_switches": int(telemetry.get("context_switches", 0)),
            "cpu_usage": float(telemetry.get("cpu_usage", 0.0)),
            "hw_cpu_cycles": float(telemetry.get("hw_cpu_cycles", -1.0)),
            "hw_instructions": float(telemetry.get("hw_instructions", -1.0)),
            "hw_cache_misses": float(telemetry.get("hw_cache_misses", -1.0)),
            "hw_branch_misses": float(telemetry.get("hw_branch_misses", -1.0)),
        },
        # Derived
        "derived": {
            "cache_proxy": float(telemetry.get("synthetic_cache_proxy", 0.0)),
            "branch_proxy": float(telemetry.get("synthetic_branch_proxy", 0.0)),
        },
        # Performance
        "performance": {
            "crypto_latency_s": t_crypto,
            "feature_eng_latency_s": t_feat,
            "ml_inference_latency_s": t_inf,
            "total_latency_s": t_total,
        },
        "defense": {"mitigation_action": "None", "mitigation_overhead_s": 0.0},
    }

    # 3.5 Execute Countermeasures (Post-ML, Pre-Response)
    mitigation_actions, mitigation_overhead = defense_policy.evaluate_and_react(
        confidence / 100.0, telemetry
    )
    if mitigation_actions:
        result["defense"]["mitigation_action"] = ", ".join(mitigation_actions)
        result["defense"]["mitigation_overhead_s"] = mitigation_overhead
        result["performance"]["total_latency_s"] += mitigation_overhead

    history.append(result)

    # Structured log
    logger.info(
        f"INFERENCE | Model: {active_model_name} | Pred: {predicted_status} | Score: {anomaly_score:.3f} | Latency: {telemetry['execution_time_us']:.2f}us"
    )

    return result


# ────────────────────────────────────────────────────────
# REST & WebSocket API
# ────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def get_dashboard():
    template_path = os.path.join("templates", "index.html")
    if os.path.exists(template_path):
        with open(template_path, "r") as f:
            return f.read()
    else:
        raise HTTPException(status_code=404, detail="Dashboard UI template not found")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ws_clients.append(websocket)
    try:
        while True:
            # Keep alive and handle client disconnects
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_clients.remove(websocket)


@app.get("/api/stats")
def get_stats():
    return {
        "is_training": is_training,
        "active_model": active_model_name,
        "available_models": available_models,
        "logs": training_logs[-20:],
    }


@app.post("/api/run-normal")
async def api_run_normal():
    if not active_model and not is_training:
        background_benchmark()
        return {
            "status": "training",
            "message": "Benchmark started to generate initial model.",
        }

    res = execute_and_infer(attack_profile="none")
    await broadcast_ws(res)
    return res


@app.post("/api/simulate-attack")
async def api_simulate_attack(attack_type: str):
    if not active_model and not is_training:
        return {"status": "error", "message": "No active model available."}

    # We map attack_type from dashboard to the dataset generator's attack profiles
    profile_map = {
        "constant": "timing",
        "bimodal": "cache_pressure",
        "drift": "cpu_contention",
        "spike": "thermal",
    }
    profile = profile_map.get(attack_type, "none")

    res = execute_and_infer(attack_profile=profile)
    await broadcast_ws(res)
    return res


@app.post("/api/model/select")
async def api_select_model(model_name: str):
    global active_model, active_model_name

    exp_dir = get_latest_experiment_dir()
    if not exp_dir:
        raise HTTPException(status_code=404, detail="No experiments found")

    try:
        new_model = load_model_from_experiment(exp_dir, model_name)
        if new_model:
            active_model = new_model
            active_model_name = model_name
            training_logs.append(f"[SYSTEM] Switched active model to: {model_name}")
            return {"status": "success", "active_model": active_model_name}
        else:
            raise HTTPException(
                status_code=404, detail=f"Model {model_name} could not be loaded"
            )
    except Exception as e:
        logger.error(f"Error loading model {model_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to load model")


@app.post("/api/retrain")
async def api_retrain(background_tasks: BackgroundTasks):
    global is_training
    if is_training:
        return {
            "status": "already_training",
            "message": "Model training already in progress.",
        }
    background_tasks.add_task(background_benchmark)
    return {
        "status": "started",
        "message": "Benchmark and retraining started in the background.",
    }


@app.get("/api/defense/config")
def get_defense_config():
    return defense_policy.get_config()


from pydantic import BaseModel


class DefenseConfig(BaseModel):
    randomized_delay: bool = None
    throttling: bool = None
    forensic_logger: bool = None
    alerting: bool = None
    key_rotation: bool = None


@app.post("/api/defense/config")
def update_defense_config(config: DefenseConfig):
    update_dict = {k: v for k, v in config.dict().items() if v is not None}
    defense_policy.update_config(update_dict)
    return {"status": "success", "config": defense_policy.get_config()}


@app.get("/api/defense/logs")
def get_defense_logs():
    if not os.path.exists("defense_logs.jsonl"):
        return []
    logs = []
    with open("defense_logs.jsonl", "r") as f:
        for line in f:
            if line.strip():
                logs.append(json.loads(line))
    return logs[-100:]  # Return last 100 entries


@app.get("/api/export/json")
def export_json():
    return history


@app.get("/api/export/csv")
def export_csv():
    if not history:
        return HTMLResponse("No data to export")

    output = StringIO()
    writer = csv.writer(output)

    # Flatten header
    headers = [
        "timestamp",
        "algorithm",
        "attack_profile",
        "selected_model",
        "predicted_status",
        "anomaly_score",
        "confidence",
        "exec_time_us",
        "max_rss_kb",
        "context_switches",
        "cpu_usage",
        "cache_proxy",
        "branch_proxy",
        "latency_total_s",
        "latency_ml_s",
        "mitigation_action",
        "mitigation_overhead_s",
    ]
    writer.writerow(headers)

    for r in history:
        writer.writerow(
            [
                r["timestamp"],
                r["algorithm"],
                r["attack_profile"],
                r["selected_model"],
                r["predicted_status"],
                r["anomaly_score"],
                r["confidence"],
                r["measured"]["execution_time_us"],
                r["measured"]["max_rss_kb"],
                r["measured"]["context_switches"],
                r["measured"]["cpu_usage"],
                r["derived"]["cache_proxy"],
                r["derived"]["branch_proxy"],
                r["performance"]["total_latency_s"],
                r["performance"]["ml_inference_latency_s"],
                r["defense"]["mitigation_action"],
                r["defense"]["mitigation_overhead_s"],
            ]
        )

    response = StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = (
        "attachment; filename=aegis_telemetry_export.csv"
    )
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)

# Phase 9: Adaptive Runtime Countermeasure Engine

## Objective
The objective of Phase 9 was to transform Aegis PQC from a passive intrusion detection system into an active runtime defense platform. This was achieved by implementing a modular runtime response framework that activates automatically when the anomaly detection pipeline identifies a suspected side-channel attack.

## Architecture

The Countermeasure Engine operates strictly *after* the ML detection pipeline has produced an anomaly score and confidence interval. This prevents the countermeasures (which may introduce random delays or overhead) from polluting the telemetry collected during the cryptographic execution.

### Execution Flow
1. **Incoming Request**
2. **`aegis_engine.run_crypto()`**
3. **Telemetry Collection**
4. **Feature Engineering**
5. **ML Detection Pipeline** (LSTM/Autoencoder)
6. **Countermeasure Engine** (`ResponsePolicy`)
7. **Response to Client**

### Modular Plugin System
The countermeasures are implemented as a plugin-based architecture, deriving from a `BaseCountermeasure` abstract class:
- **Randomized Delay (`random_delay.py`)**: Injects non-deterministic execution delays (20-100ms) to obfuscate timing side-channels and disrupt precise attacker measurements.
- **Request Throttling (`throttling.py`)**: Uses a Token Bucket algorithm (10 tokens/sec, 1 token/sec refill) to rate-limit requests during high-confidence attacks, preventing rapid, repeated measurements.
- **Forensic Logger (`forensic_logger.py`)**: Logs high-fidelity telemetry, anomaly scores, and response actions to an append-only JSONL file (`defense_logs.jsonl`) for incident response.
- **Alert Generation (`alerting.py`)**: Emits high-priority stdout alerts to be ingested by external SIEM (Security Information and Event Management) systems.
- **Key Rotation Stub (`key_rotation.py`)**: Simulates a cryptographic key rotation event upon detecting critical threat levels.

## Risk-Based Response Policy

Instead of triggering actions on binary predictions, the `ResponsePolicy` orchestrator utilizes confidence thresholds:
- **Normal (< 30% Confidence)**: `Allow`
- **Low Threat (30% - 60% Confidence)**: `Enhanced Monitoring` (No active disruption)
- **Medium Threat (60% - 80% Confidence)**: `Randomized Delay`, `Forensic Logging`
- **High Threat (> 80% Confidence)**: `Randomized Delay`, `Forensic Logging`, `Request Throttling`, `Alert Generation`, `Key Rotation`

## Dashboard Integration
The FastAPI dashboard (`module4_dashboard.py`) was updated with a new **Active Response Policies** control panel, allowing administrators to toggle individual countermeasures in real-time. The dashboard now tracks:
- Threat Level (Low, Medium, High, Critical)
- Active Mitigation Actions
- Detection vs Mitigation Latency (overhead)
- Mitigation Counts & False Mitigation rates

## Benchmark Results

A dedicated benchmark script (`benchmark_phase9.py`) was implemented to measure the performance overhead introduced by the countermeasures:

| Scenario | Confidence | Mitigation Actions Triggered | Avg Policy Execution Time | Avg Injected Overhead |
| :--- | :--- | :--- | :--- | :--- |
| **Normal (Safe)** | 10% | Allow | ~0.0001 ms | 0.0 ms |
| **Low Threat** | 40% | Enhanced Monitoring | ~0.0001 ms | 0.0 ms |
| **Medium Threat** | 70% | Delay, Logging | ~44.1 ms | ~40.3 ms |
| **High Threat** | 95% | Delay, Logging, Throttling, Alert, Key Rotation | ~93.8 ms | ~87.1 ms |

The results show that the engine introduces zero overhead during normal execution, scaling up non-deterministic defense mechanisms only when under active attack.

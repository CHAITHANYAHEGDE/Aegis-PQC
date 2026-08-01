# API Documentation

Aegis PQC provides both a native Python API for the C++ engine, and a FastAPI REST API for deployment.

## Python API (`aegis_engine`)
- `aegis_engine.get_supported_algorithms()`: Returns a list of strings for all NIST algorithms compiled into the liboqs binary (e.g., `["ML-KEM-512", "ML-DSA-44"]`).
- `aegis_engine.run_kem_keygen(algo_name)`: Executes KEM Key Generation and returns a telemetry dict.
- `aegis_engine.run_kem_encaps(algo_name, public_key_hex)`: Executes KEM Encapsulation. Returns a telemetry dict.

*Telemetry Dict Format:*
```json
{
  "execution_time_us": 1450.5,
  "memory_usage": 1024,
  "context_switches": 2,
  "cpu_usage": 0.5,
  "synthetic_cache_proxy": 12.4,
  "synthetic_branch_proxy": 2.1
}
```

## REST API (FastAPI)
The backend service (e.g. `module4_dashboard.py`) runs on `http://localhost:8000`.

- `GET /health`: Returns system health.
- `GET /metrics`: Returns latest anomaly detection metrics and system status (used by the dashboard).
- `GET /ws`: WebSocket endpoint for real-time telemetry streaming to the frontend.

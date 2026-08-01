# API Reference

The primary interaction point for Aegis-PQC is the Native C++ extension (`aegis_engine.so`) imported into Python via pybind11.

## `aegis_engine` module

### `run_crypto(algo: str, attack_profile: str) -> dict`
Synchronously executes the given PQC algorithm while collecting hardware and software telemetry, passing it through the ONNX anomaly detection model, and applying any necessary active mitigations before returning.

**Parameters:**
- `algo` (str): The PQC algorithm to execute. Supported: `"ML-KEM-512"`, `"ML-DSA-65"`.
- `attack_profile` (str): Simulated attack to inject (for testing). Use `"none"` for normal execution, or `"timing"`, `"cache_pressure"`, `"cpu_contention"`, `"thermal"`.

**Returns:**
- `dict`: The raw telemetry readings captured during the execution (for logging/auditing purposes). The crypto output (ciphertext/key) is implicitly handled by the mitigation engine.

### `AegisEngine` class (Deprecated / Internal)
*Internal use only.* Handles the initialization of the ONNX Runtime environment and the loading of `rf_model.onnx`.

## `policy_engine.hpp` (C++)
The internal rule engine for responding to ML inferences.
- `void apply_mitigation(float anomaly_probability)`: Calculates dynamic delays or throttling based on the probability of a side-channel attack.

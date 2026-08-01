# Security Review (STRIDE & MITRE ATT&CK)

## 1. Trust Boundaries
- **Untrusted Zone**: The network layer submitting ciphertext/keys to the FastAPI endpoint.
- **Semi-Trusted Zone**: The Python FastAPI application executing the endpoints.
- **Trusted Zone**: The `aegis_engine.so` C++ shared object executing the PQC algorithms natively with isolation.
- **Hardware Zone**: PMU (Performance Monitoring Unit) and OS Telemetry counters, assumed tamper-proof by user-space.

## 2. Threat Model (STRIDE)
| Threat | Description | Mitigation |
|--------|-------------|------------|
| **Spoofing** | Attacker spoofs hardware counters to hide an attack. | Counters are retrieved via OS-level ring-0 syscalls (`perf_event_open`), inaccessible to unprivileged user-space processes. |
| **Tampering** | Attacker modifies the ONNX model to bypass detection. | The ONNX model should be digitally signed and verified by the C++ engine upon load in a production deployment (Future Work). |
| **Repudiation**| Attacker denies causing anomalies. | All anomalies are logged with cryptographic nonces and exact request timestamps. |
| **Information Disclosure** | Timing/Cache side-channels extract PQC keys. | **Aegis-PQC Core Value**: The AI shield detects this information leakage precisely by monitoring execution telemetry. |
| **Denial of Service** | Attacker spams requests to overload the AI engine. | C++ engine natively handles 5000+ TPS per core. Auto-throttling mitigations automatically kick in. |
| **Elevation of Privilege** | Attacker escapes the C++ Python binding. | C++ bindings use strict type-checking and bounded buffers for telemetry arrays. |

## 3. Adversarial Machine Learning Risks
- **Evasion Attacks**: An attacker crafts an attack (e.g., executing extraneous instructions) to manipulate the feature vector and cross the decision boundary into the "Normal" class.
  - *Mitigation*: Multi-variate detection. Hiding cache misses by adding CPU cycles will trigger a CPU Contention anomaly.
- **Data Poisoning**: Not applicable during runtime. Training data is assumed to be collected in a secure, isolated lab environment prior to deployment.

## 4. Known Limitations
- The system assumes the OS kernel is not compromised. A rootkit could intercept `perf_event_open` and spoof clean telemetry.
- The mitigation engine (PolicyEngine) relies on OS-level sleep functions which may themselves introduce micro-architectural side-channels if not implemented with constant-time delays.

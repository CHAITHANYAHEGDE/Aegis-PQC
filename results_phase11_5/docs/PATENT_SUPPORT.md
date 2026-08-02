# Patent Support Documentation

*Disclaimer: This document is for informational purposes only to assist patent attorneys in drafting claims. It does not constitute legal advice and does not automatically assert patent novelty.*

## 1. Candidate Contributions (Potential Novelty)
1. **Coupled Execution and Telemetry Capture**: The tight integration of a Post-Quantum Cryptographic algorithm with immediate, synchronous hardware telemetry capture in native C++ prior to returning to the caller application.
2. **Synchronous Runtime Anomaly Detection via ONNX**: The real-time evaluation of an ML model (via ONNX Runtime) directly within the cryptographic execution path, enabling microsecond-scale detection and mitigation before the ciphertext/plaintext is returned to a potentially malicious caller.
3. **Adaptive Cryptographic Mitigation**: An active mitigation pipeline that responds to inferred side-channel attacks by randomizing execution delays or throttling the *current* request, neutralizing the timing/cache signal before it completes.

## 2. Prior-Art Comparison Matrix

| Feature | Standard PQC Implementations (e.g., liboqs) | Existing Hardware Monitors (e.g., Intel PT) | **Aegis-PQC Framework** |
|---------|---------------------------------------------|---------------------------------------------|-------------------------|
| **PQC Support** | Yes | No | **Yes** |
| **Side-Channel Detection** | No | Asynchronous / Post-facto | **Synchronous / Real-Time** |
| **In-Band Mitigation** | Constant-time only | No | **Yes (Active Throttling/Delay)** |
| **Machine Learning** | No | Offline Analysis | **Inline C++ ONNX Inference** |

## 3. Potential Claims for Patent Attorney Review
- **Independent Claim 1**: A method for securing cryptographic execution, comprising: executing a cryptographic algorithm; simultaneously reading a plurality of hardware performance counters corresponding strictly to the duration of said execution; evaluating said counters using a machine learning model; and modifying the return state of the cryptographic algorithm based on the model's output, all within a single synchronous functional call.
- **Dependent Claim 1.1**: The method of claim 1, wherein the cryptographic algorithm is a Post-Quantum Cryptography algorithm.
- **Dependent Claim 1.2**: The method of claim 1, wherein modifying the return state includes injecting a randomized, unpredictable delay to obfuscate side-channel timing signals.

## 4. Aspects Requiring Professional Patent Search
- This feature requires professional prior-art review to ensure no existing patents cover inline ML inference specifically used for thwarting side-channel attacks during the execution of standard cryptographic libraries.
- The use of ONNX Runtime inside a security enclave or sensitive execution path for anomaly detection.

# Phase 10: Hardware Ground-Truth Validation

## Objective
The objective of Phase 10 was to validate the Aegis PQC framework against real hardware performance counters, determining how much additional detection capability can be achieved by utilizing true processor telemetry instead of software-derived synthetic proxies. A core requirement was to maintain the software telemetry pipeline as a graceful fallback and baseline.

## Implementation Details

### Hardware Abstraction Layer
A modular hardware telemetry abstraction layer was implemented to allow Aegis PQC to source telemetry from multiple underlying systems.
- **Provider Interface**: An abstract `HardwareTelemetryProvider` was added to `aegis_ml/hardware/provider.py`.
- **Implementations**: The initial implementation is `AegisEngineProvider`, which wraps the C++ extension. Future providers for Intel PCM and PAPI are stubbed out.
- **C++ `aegis_engine.cpp`**: 
  - Integrated Linux `perf_event_open` syscalls directly into the cryptographic execution loop.
  - Features captured: CPU cycles, retired instructions, cache references/misses, branch instructions/misses.
  - The C++ layer is conditionally compiled with `#ifdef __linux__`. On macOS (Darwin) or environments lacking `perf` privileges, it gracefully degrades by populating hardware metrics with `-1.0` and setting a boolean flag `hw_telemetry_available = 0.0`.

### ML Dataset Pipeline
- The Python ML pipeline was updated to consume data via the `get_default_provider()`.
- Unchanged `aegis_engine` output ensures the ML models trained in previous phases (which expect `execution_time_us`, `max_rss_kb`, and `context_switches`) continue to function without retraining on legacy datasets.

### Benchmark Script
A standalone `benchmark_phase10.py` script was created.
- The script automatically generates an ad-hoc dataset featuring *Software-Only*, *Hardware-Only*, and *Hybrid* telemetry.
- A fast Random Forest classifier evaluates the F1 Score, AUC, and FPR across all three modes to empirically validate the predictive power of hardware vs. software telemetry.

### Dashboard Integration
- The FastAPI dashboard (`module4_dashboard.py`) and UI (`index.html`) were enhanced to dynamically detect the telemetry source.
- A new indicator, **TELEMETRY SOURCE** (Software / Hardware), accurately displays the live telemetry capability of the host machine.

## Platform Support and Limitations
- **macOS / Windows**: Native hardware telemetry is unavailable due to the lack of `perf` equivalents directly exposed to user space without root. Aegis PQC falls back to high-resolution timing and software process metrics (RSS, page faults).
- **Linux**: Requires `perf_event_paranoid` to be `<= 2` (or `< 1` for some aggressive counters). If permission is denied, it gracefully defaults to the software fallback.

## Future Extensions
- **Intel PCM / PAPI**: Extend the `HardwareTelemetryProvider` to support Intel Performance Counter Monitor or PAPI (Performance Application Programming Interface) for cross-platform, architecture-independent hardware telemetry.
- **Model Retraining**: Current baseline models utilize software metrics. Future iterations of Aegis should train hybrid deep autoencoders specifically on hardware-rich feature sets for robust production deployments on Linux edge nodes.

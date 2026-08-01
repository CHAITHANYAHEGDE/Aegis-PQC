# Known Limitations

### 1. Hardware Performance Monitoring Counters (PMCs)
macOS and many standard Linux cloud environments do not expose hardware PMCs (such as true L1/L2 cache misses or CPU branch mispredictions) to user-space applications without disabling System Integrity Protection (SIP) or running with root-level privileged APIs (`perf`). 

**Workaround:** We currently use synthetic/proxy metrics for cache pressure and branch variation based on micro-timing jitter and memory allocation patterns. *The implementation does not present these synthetic or derived metrics as if they were directly measured hardware events.*

### 2. Multi-Threading
The C++ core execution engine does not natively parallelize execution of single KEM requests. Concurrency is handled at the Python backend (FastAPI/asyncio) level.

### 3. Attack Simulation
The `module3_attack_simulator.py` script mimics side-channel noise through memory and CPU exhaustion. It is *not* a true hardware differential power analysis (DPA) or electromagnetic (EM) side-channel attack simulator. It primarily demonstrates the AI's ability to detect anomalous latency and memory signatures.

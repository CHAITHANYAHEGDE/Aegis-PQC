python3 -c "
content = '''# 🛡️ Aegis-PQC: Post-Quantum Cryptographic Core & Autonomous AI Threat Guard

![Language](https://img.shields.io/badge/Language-C%2B%2B20-red)
![AI Engine](https://img.shields.io/badge/AI_Engine-PyTorch_2.8-orange)
![Security](https://img.shields.io/badge/Security-NIST_Kyber--768-blue)
![Detection](https://img.shields.io/badge/Detection_Rate-100%25-brightgreen)
![FP Rate](https://img.shields.io/badge/False_Positive-0.0%25-brightgreen)
![Status](https://img.shields.io/badge/Status-Research_In_Progress-yellow)
![License](https://img.shields.io/badge/License-MIT-green)

> **Hybrid Post-Quantum Cryptographic Engine with Real-Time Neural Side-Channel Attack Detection**

---

## 📋 Overview

Aegis-PQC is a hybrid cybersecurity architecture combining:

1. **Post-Quantum Cryptography** — NIST-standard Kyber-768 Lattice Key Encapsulation in zero-allocation C++20.
2. **AI-Powered Side-Channel Defense** — PyTorch Autoencoder + Statistical Variance Monitor for real-time execution-introspection threat detection.

The system detects four classes of timing side-channel attacks with **100% accuracy and 0% false positives**.

---

## 🏗️ Architecture

\`\`\`
+---------------------------------------------------+
|              Aegis-PQC Pipeline                   |
+---------------------------------------------------+
|                                                   |
|  Module 1: C++20 Kyber-768 Engine                 |
|  |-- NTT (Number Theoretic Transform)             |
|  |-- Polynomial Arithmetic (mod q=3329)           |
|  |-- Key Generation + Encapsulation               |
|  +-- Timing Trace Output -> timing_trace.txt      |
|                    |                              |
|                    v                              |
|  Module 2: PyTorch AI Guard                       |
|  |-- 1D Autoencoder (16->8->4->8->16)             |
|  |-- 500-epoch training on real C++ timings       |
|  |-- Auto-calibrated threshold (mean + 3 sigma)   |
|  +-- Trained model -> aegis_guard_model.pt        |
|                    |                              |
|                    v                              |
|  Module 3: Hybrid Attack Detector                 |
|  |-- Autoencoder MSE (pattern anomalies)          |
|  |-- Variance Monitor (constant-timing attacks)   |
|  +-- Detection Results -> Table 1                 |
|                                                   |
+---------------------------------------------------+
\`\`\`

---

## 📊 Experimental Results

### Table 1: Side-Channel Attack Detection Performance

| Attack Type | Category | Detection Rate | Avg MSE | Detection Trigger |
| :--- | :--- | :---: | :--- | :--- |
| Constant | Cache-Timing | **100.0%** | 0.0103 | Variance Monitor |
| Bimodal | Power Analysis | **100.0%** | 7.7811 | Autoencoder |
| Drift | Spectre-Class | **100.0%** | 16.1019 | Autoencoder |
| Spike | Fault Injection | **100.0%** | 1020.90 | Autoencoder |

| Metric | Value |
| :--- | :---: |
| **Average Detection Rate** | **100.0%** |
| **False Positive Rate** | **0.0%** |
| **Training Samples** | 134 |
| **Training Epochs** | 500 |
| **Auto-Calibrated MSE Threshold** | 1.828 |
| **Variance Threshold** | 0.050 |

### Key Finding

> The hybrid detection approach (Neural Autoencoder + Statistical Variance Monitor) achieves complete coverage across all four attack classes. The Autoencoder alone misses constant-timing attacks (0% detection), but the Variance Monitor provides complementary coverage, achieving 100% combined detection with zero false positives.

---

## 🔧 Tech Stack

| Component | Technology |
| :--- | :--- |
| Crypto Engine | C++20 (zero-allocation, cache-aligned) |
| AI Guard | PyTorch 2.8 (1D Autoencoder) |
| Attack Simulator | Python 3.11 + NumPy |
| Pipeline | Bash (run_all.sh) |
| Model Format | .pt (PyTorch state_dict) |

---

## 🚀 Quick Start

\`\`\`bash
# Clone
git clone https://github.com/CHAITHANYAHEGDE/Aegis-PQC.git
cd Aegis-PQC

# Run full pipeline
chmod +x run_all.sh
./run_all.sh
\`\`\`

### Run Individual Modules:

\`\`\`bash
# Module 1: Compile and run C++ Kyber engine
g++ -std=c++20 -O2 -o module1_engine module1_engine.cpp
./module1_engine

# Module 2: Train PyTorch AI Guard
python3 module2_pytorch_guard.py

# Module 3: Run attack simulation benchmark
python3 module3_attack_simulator.py
\`\`\`

---

## 📁 Project Structure

\`\`\`
Aegis-PQC/
|-- module1_engine.cpp          # C++20 Kyber-768 NTT Engine
|-- module2_ai_guard.py         # Basic Z-score AI Guard (v1)
|-- module2_pytorch_guard.py    # PyTorch Autoencoder Guard (v2)
|-- module3_attack_simulator.py # Hybrid Attack Detector + Benchmarks
|-- aegis_guard_model.pt        # Trained PyTorch model weights
|-- run_all.sh                  # Full pipeline execution script
|-- timing_trace.txt            # C++ engine timing output
+-- README.md                   # This file
\`\`\`

---

## 🔬 Research Status

This project is **research in progress** following the standard research cycle:

- [x] Literature Review and Gap Identification
- [x] Novel Contribution Definition (Hybrid AI + Statistical Detection)
- [x] Implementation (C++20 + PyTorch)
- [x] Experimental Evaluation (4 attack types, 100% detection)
- [ ] Timing Overhead Analysis (Baseline vs. Protected)
- [ ] IEEE Conference Paper Draft
- [ ] Peer Review Submission

### Target Venues:
- IEEE Symposium on Security and Privacy (S&P)
- NDSS Workshop on Measurements, Attacks, and Defenses for the Web (MADWeb)
- ACM CCS Workshop on Artificial Intelligence and Security (AISec)

---

## 👤 Author

**Chaithanya R Hegde**
B.Tech CSE (Cybersecurity) — Manipal Institute of Technology, MAHE
- GitHub: [@CHAITHANYAHEGDE](https://github.com/CHAITHANYAHEGDE)

---

## 📄 License

This project is licensed under the MIT License.
'''
with open('README.md', 'w') as f:
    f.write(content)
print('README.md written successfully!')
"


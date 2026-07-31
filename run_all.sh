#!/bin/bash
echo "=========================================="
echo "  Aegis-PQC: Full Pipeline Execution"
echo "=========================================="

echo ""
echo "[1/3] Compiling C++20 Kyber Engine..."
g++ -std=c++20 -O2 -o module1_engine module1_engine.cpp
echo "✅ Compiled."

echo ""
echo "[2/3] Running PyTorch AI Guard..."
python3 module2_pytorch_guard.py

echo ""
echo "[3/3] Running Attack Simulation Benchmark..."
python3 module3_attack_simulator.py

echo ""
echo "=========================================="
echo "  ✅ Aegis-PQC Pipeline Complete"
echo "=========================================="

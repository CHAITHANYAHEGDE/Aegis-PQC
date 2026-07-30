#!/bin/bash
echo "=========================================================="
echo "  LAUNCHING POST-QUANTUM AI SECURITY SHIELD ENGINE        "
echo "=========================================================="
echo ""

# 1. Compile C++ Module 1
echo "[1/3] Compiling C++20 Post-Quantum Kyber Engine..."
g++ -std=c++20 module1_engine.cpp -o module1_engine

if [ $? -ne 0 ]; then
    echo "❌ Compilation failed!"
    exit 1
fi

# 2. Run C++ Module 1
echo "[2/3] Executing Module 1 (Kyber Polynomial Multiplication)..."
./module1_engine
echo ""

# 3. Run Python AI Guard
echo "[3/3] Launching Module 2 (AI Execution Introspection Guard)..."
python3 module2_ai_guard.py

echo ""
echo "=========================================================="
echo "  ✅ SYSTEM PIPELINE EXECUTION SUCCESSFUL                 "
echo "=========================================================="


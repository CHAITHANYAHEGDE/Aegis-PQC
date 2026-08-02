import time
import psutil
import aegis_engine

def benchmark(algo="ML-KEM-512", iterations=5000):
    start_time = time.time()
    
    for _ in range(iterations):
        _ = aegis_engine.run_crypto(algo, "none")
        
    end_time = time.time()
    total_time = end_time - start_time
    tps = iterations / total_time
    latency_us = (total_time / iterations) * 1e6
    
    print(f"--- Benchmark Phase 12 (macOS Physical Validation) ---")
    print(f"Algorithm: {algo}")
    print(f"Iterations: {iterations}")
    print(f"Total Time: {total_time:.4f} seconds")
    print(f"Throughput: {tps:.2f} TPS")
    print(f"Avg Latency: {latency_us:.2f} µs per execution")
    print("Note: On macOS, hardware PMU is gracefully disabled (-1.0 returned) reducing kernel overhead.")

if __name__ == "__main__":
    print("Warming up...")
    benchmark(iterations=100)
    print("\nRunning actual benchmark...")
    benchmark(iterations=10000)

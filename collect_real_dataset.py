import sys
import time
import os
import csv
import multiprocessing
import aegis_engine

def stress_cpu():
    """Spin loop to create real CPU contention."""
    while True:
        _ = [i * i for i in range(1000)]

def stress_memory():
    """Allocate and thrash memory to create real cache contention."""
    data = []
    while True:
        data.append(bytearray(1024 * 1024))
        if len(data) > 100:
            data.clear()

def run_crypto_samples(num_samples: int, is_anomaly: int):
    """Run crypto and return telemetry dicts."""
    results = []
    for _ in range(num_samples):
        # We use "none" for attack profile so it doesn't inject synthetic loops
        telemetry = aegis_engine.run_crypto("ML-KEM-512", "none")
        telemetry["is_anomaly"] = is_anomaly
        results.append(telemetry)
        # Small sleep to let OS breathe and simulate real throughput
        time.sleep(0.001)
    return results

def main():
    os.makedirs("data/real", exist_ok=True)
    out_csv = "data/real/telemetry_ML-KEM-512_real.csv"
    
    print("Collecting normal telemetry (quiet system)...")
    normal_data = run_crypto_samples(2500, is_anomaly=0)
    
    print("Spawning background physical stress threads...")
    processes = []
    # Spawn 4 CPU stressors and 2 Memory stressors to saturate an Apple M3
    for _ in range(4):
        p = multiprocessing.Process(target=stress_cpu)
        p.start()
        processes.append(p)
    for _ in range(2):
        p = multiprocessing.Process(target=stress_memory)
        p.start()
        processes.append(p)
        
    print("Waiting for stress to stabilize...")
    time.sleep(2.0)
    
    print("Collecting anomalous telemetry (system under physical stress)...")
    anomaly_data = run_crypto_samples(2500, is_anomaly=1)
    
    print("Terminating stress threads...")
    for p in processes:
        p.terminate()
        p.join()
        
    all_data = normal_data + anomaly_data
    
    # Save to CSV
    if not all_data:
        return
        
    keys = list(all_data[0].keys())
    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(all_data)
        
    print(f"Collection complete. Saved {len(all_data)} samples to {out_csv}.")

if __name__ == "__main__":
    main()

import aegis_engine
import time

algos = [
    "ML-KEM-512", "ML-KEM-768", "ML-KEM-1024",
    "ML-DSA-44", "ML-DSA-65", "ML-DSA-87",
    "Falcon-512", "Falcon-1024",
    "sphincs+-sha2-128f-simple"
]

for algo in algos:
    start = time.time()
    res = aegis_engine.run_crypto(algo, "none")
    end = time.time()
    # if it took less than 10 microseconds, it probably didn't run
    if res['execution_time_us'] < 10:
        print(f"{algo}: UNSUPPORTED (execution_time: {res['execution_time_us']} us)")
    else:
        print(f"{algo}: SUPPORTED (execution_time: {res['execution_time_us']} us)")

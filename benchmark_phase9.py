import json
import statistics
import time

from aegis_ml.countermeasures.response_policy import ResponsePolicy


def benchmark_countermeasures():
    print("=== Phase 9: Countermeasure Overhead Benchmark ===")
    policy = ResponsePolicy()

    # Enable all defenses for benchmark
    policy.update_config(
        {
            "randomized_delay": True,
            "throttling": True,
            "forensic_logger": True,
            "alerting": True,
            "key_rotation": True,
        }
    )

    scenarios = [
        {"name": "Normal (Safe)", "confidence": 0.10, "count": 100},
        {"name": "Low Threat", "confidence": 0.40, "count": 100},
        {"name": "Medium Threat", "confidence": 0.70, "count": 100},
        {"name": "High Threat (Attack)", "confidence": 0.95, "count": 100},
    ]

    results = []

    for scenario in scenarios:
        print(f"\\nRunning scenario: {scenario['name']}")
        overhead_delays = []
        execution_times = []
        actions_list = []

        for i in range(scenario["count"]):
            # Synthetic telemetry
            telemetry = {
                "algorithm": "ML-KEM-512",
                "execution_time_us": 1200 + (i % 100),
                "anomaly_score": scenario["confidence"] * 2.0,
                "confidence": scenario["confidence"],
            }

            start = time.perf_counter()
            actions, overhead = policy.evaluate_and_react(
                scenario["confidence"], telemetry
            )
            duration = time.perf_counter() - start

            execution_times.append(duration)
            overhead_delays.append(overhead)
            if i == 0:
                actions_list = actions

        avg_exec = statistics.mean(execution_times) * 1000  # ms
        avg_overhead = statistics.mean(overhead_delays) * 1000  # ms

        print(f"  Actions taken: {', '.join(actions_list) if actions_list else 'None'}")
        print(f"  Avg Policy Engine Time: {avg_exec:.4f} ms")
        print(f"  Avg Injected Delay:     {avg_overhead:.4f} ms")

        results.append(
            {
                "scenario": scenario["name"],
                "confidence": scenario["confidence"],
                "actions": ", ".join(actions_list) if actions_list else "None",
                "avg_policy_time_ms": avg_exec,
                "avg_injected_delay_ms": avg_overhead,
            }
        )

    with open("phase9_benchmark_results.json", "w") as f:
        json.dump(results, f, indent=4)
    print("\\nResults saved to phase9_benchmark_results.json")


if __name__ == "__main__":
    benchmark_countermeasures()

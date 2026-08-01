import json
import time
import os
from .base import BaseCountermeasure
from typing import Dict, Any


class ForensicLogger(BaseCountermeasure):
    def __init__(self, log_file="defense_logs.jsonl"):
        super().__init__()
        self.log_file = log_file

    def execute(self, telemetry: Dict[str, Any], confidence: float) -> float:
        if not self.enabled:
            return 0.0

        start_time = time.perf_counter()

        log_entry = {
            "timestamp": time.time(),
            "confidence": confidence,
            "telemetry": telemetry,
        }

        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        return time.perf_counter() - start_time

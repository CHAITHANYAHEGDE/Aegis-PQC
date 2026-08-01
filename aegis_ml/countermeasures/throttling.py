import time
from .base import BaseCountermeasure
from typing import Dict, Any


class Throttling(BaseCountermeasure):
    def __init__(self, max_requests_per_sec=10):
        super().__init__()
        self.max_requests_per_sec = max_requests_per_sec
        self.tokens = max_requests_per_sec
        self.last_update = time.time()

    def execute(self, telemetry: Dict[str, Any], confidence: float) -> float:
        if not self.enabled:
            return 0.0

        # Simple token bucket
        now = time.time()
        elapsed = now - self.last_update
        self.tokens += elapsed * self.max_requests_per_sec
        if self.tokens > self.max_requests_per_sec:
            self.tokens = self.max_requests_per_sec
        self.last_update = now

        overhead = 0.0
        if self.tokens >= 1.0:
            self.tokens -= 1.0
        else:
            # Throttle by sleeping until a token is available
            wait_time = (1.0 - self.tokens) / self.max_requests_per_sec
            time.sleep(wait_time)
            self.tokens = 0.0
            self.last_update = time.time()
            overhead = wait_time

        return overhead

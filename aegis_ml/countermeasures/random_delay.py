import random
import time
from typing import Any

from .base import BaseCountermeasure


class RandomDelay(BaseCountermeasure):
    def __init__(self, min_delay_s=0.01, max_delay_s=0.05):
        super().__init__()
        self.min_delay_s = min_delay_s
        self.max_delay_s = max_delay_s

    def execute(self, telemetry: dict[str, Any], confidence: float) -> float:
        if not self.enabled:
            return 0.0

        delay = random.uniform(self.min_delay_s, self.max_delay_s)
        # Scale delay slightly with confidence
        delay = delay + (delay * confidence * 0.5)

        time.sleep(delay)
        return delay

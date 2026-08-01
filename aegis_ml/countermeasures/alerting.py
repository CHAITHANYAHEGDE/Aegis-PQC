import time
import logging
from .base import BaseCountermeasure
from typing import Dict, Any

logger = logging.getLogger("AegisAlerts")


class Alerting(BaseCountermeasure):
    def execute(self, telemetry: Dict[str, Any], confidence: float) -> float:
        if not self.enabled:
            return 0.0

        start_time = time.perf_counter()
        logger.warning(
            f"HIGH CONFIDENCE ATTACK DETECTED: {confidence:.2f} | Telemetry: {telemetry.get('execution_time_us')}us"
        )
        return time.perf_counter() - start_time

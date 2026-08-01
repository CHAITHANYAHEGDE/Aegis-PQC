from typing import Any

from .alerting import Alerting
from .forensic_logger import ForensicLogger
from .key_rotation import KeyRotation
from .random_delay import RandomDelay
from .throttling import Throttling


class ResponsePolicy:
    def __init__(self):
        # Initialize all countermeasures
        self.cm_random_delay = RandomDelay()
        self.cm_throttling = Throttling()
        self.cm_forensic_logger = ForensicLogger()
        self.cm_alerting = Alerting()
        self.cm_key_rotation = KeyRotation()

        # By default, master switch is on, but user can disable specific ones
        # We will enable them by default so the policy thresholds control them
        self.cm_random_delay.enable()
        self.cm_throttling.enable()
        self.cm_forensic_logger.enable()
        self.cm_alerting.enable()
        self.cm_key_rotation.enable()

    def evaluate_and_react(
        self, confidence: float, telemetry: dict[str, Any]
    ) -> tuple[list[str], float]:
        """
        Evaluates the threat confidence and triggers countermeasures.
        Returns a tuple of (list of triggered mitigation actions, total overhead in seconds).
        """
        actions_taken = []
        total_overhead = 0.0

        if confidence < 0.30:
            actions_taken.append("Allow")
            return actions_taken, total_overhead

        if confidence >= 0.30 and confidence < 0.60:
            actions_taken.append("Enhanced Monitoring")
            # In a full system, this might trigger higher-resolution telemetry
            return actions_taken, total_overhead

        if confidence >= 0.60:
            # 0.60 - 0.80 or > 0.80
            overhead = self.cm_random_delay.execute(telemetry, confidence)
            if overhead > 0:
                actions_taken.append("Random Delay")
                total_overhead += overhead

            overhead = self.cm_forensic_logger.execute(telemetry, confidence)
            if overhead > 0:
                actions_taken.append("Forensic Logging")
                total_overhead += overhead

        if confidence >= 0.80:
            overhead = self.cm_throttling.execute(telemetry, confidence)
            actions_taken.append("Request Throttling")
            total_overhead += overhead

            overhead = self.cm_alerting.execute(telemetry, confidence)
            if overhead > 0:
                actions_taken.append("Alert")
                total_overhead += overhead

            overhead = self.cm_key_rotation.execute(telemetry, confidence)
            if overhead > 0:
                actions_taken.append("Key Rotation")
                total_overhead += overhead

        return actions_taken, total_overhead

    def get_config(self):
        return {
            "randomized_delay": self.cm_random_delay.enabled,
            "throttling": self.cm_throttling.enabled,
            "forensic_logger": self.cm_forensic_logger.enabled,
            "alerting": self.cm_alerting.enabled,
            "key_rotation": self.cm_key_rotation.enabled,
        }

    def update_config(self, config: dict[str, bool]):
        if "randomized_delay" in config:
            self.cm_random_delay.enabled = config["randomized_delay"]
        if "throttling" in config:
            self.cm_throttling.enabled = config["throttling"]
        if "forensic_logger" in config:
            self.cm_forensic_logger.enabled = config["forensic_logger"]
        if "alerting" in config:
            self.cm_alerting.enabled = config["alerting"]
        if "key_rotation" in config:
            self.cm_key_rotation.enabled = config["key_rotation"]

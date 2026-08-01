from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseCountermeasure(ABC):
    def __init__(self):
        self.enabled = False

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    @abstractmethod
    def execute(self, telemetry: Dict[str, Any], confidence: float) -> float:
        """
        Executes the countermeasure.
        Returns the overhead latency added by this countermeasure in seconds.
        """
        pass

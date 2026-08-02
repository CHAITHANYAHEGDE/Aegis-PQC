import os

base_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "aegis_ml", "countermeasures"
)
os.makedirs(base_dir, exist_ok=True)

files = {}

files[
    "__init__.py"
] = """
from .base import BaseCountermeasure
from .random_delay import RandomDelay
from .throttling import Throttling
from .forensic_logger import ForensicLogger
from .alerting import Alerting
from .key_rotation import KeyRotation
from .response_policy import ResponsePolicy
"""

files[
    "base.py"
] = """
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
        '''
        Executes the countermeasure.
        Returns the overhead latency added by this countermeasure in seconds.
        '''
        pass
"""

files[
    "random_delay.py"
] = """
import time
import random
from .base import BaseCountermeasure
from typing import Dict, Any

class RandomDelay(BaseCountermeasure):
    def __init__(self, min_delay_s=0.01, max_delay_s=0.05):
        super().__init__()
        self.min_delay_s = min_delay_s
        self.max_delay_s = max_delay_s

    def execute(self, telemetry: Dict[str, Any], confidence: float) -> float:
        if not self.enabled:
            return 0.0
        
        delay = random.uniform(self.min_delay_s, self.max_delay_s)
        # Scale delay slightly with confidence
        delay = delay + (delay * confidence * 0.5)
        
        time.sleep(delay)
        return delay
"""

files[
    "throttling.py"
] = """
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
"""

files[
    "forensic_logger.py"
] = """
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
            "telemetry": telemetry
        }
        
        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\\n")
            
        return time.perf_counter() - start_time
"""

files[
    "alerting.py"
] = """
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
        logger.warning(f"HIGH CONFIDENCE ATTACK DETECTED: {confidence:.2f} | Telemetry: {telemetry.get('execution_time_us')}us")
        return time.perf_counter() - start_time
"""

files[
    "key_rotation.py"
] = """
import time
from .base import BaseCountermeasure
from typing import Dict, Any

class KeyRotation(BaseCountermeasure):
    def execute(self, telemetry: Dict[str, Any], confidence: float) -> float:
        if not self.enabled:
            return 0.0
            
        start_time = time.perf_counter()
        # Stub for session/key rotation
        # In a real system, this would invalidate the current ephemeral key
        time.sleep(0.005) # Simulate cost of rotating key context
        return time.perf_counter() - start_time
"""

files[
    "response_policy.py"
] = """
from typing import Dict, Any, List, Tuple
from .random_delay import RandomDelay
from .throttling import Throttling
from .forensic_logger import ForensicLogger
from .alerting import Alerting
from .key_rotation import KeyRotation

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

    def evaluate_and_react(self, confidence: float, telemetry: Dict[str, Any]) -> Tuple[List[str], float]:
        '''
        Evaluates the threat confidence and triggers countermeasures.
        Returns a tuple of (list of triggered mitigation actions, total overhead in seconds).
        '''
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
            if overhead > 0:
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
            "key_rotation": self.cm_key_rotation.enabled
        }
        
    def update_config(self, config: Dict[str, bool]):
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
"""

for fname, content in files.items():
    with open(os.path.join(base_dir, fname), "w") as f:
        f.write(content.strip() + "\\n")

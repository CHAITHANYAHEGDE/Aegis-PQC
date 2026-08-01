import logging
import time
from collections import deque

logger = logging.getLogger("aegis.phase6.adaptive")


class AdaptiveThresholdManager:
    def __init__(
        self,
        initial_threshold,
        base_alpha=0.05,
        max_alpha=0.2,
        min_alpha=0.01,
        window_size=50,
        use_adaptive=True,
        margin_multiplier=1.5,
    ):
        self.current_threshold = initial_threshold
        self.fixed_threshold = initial_threshold
        self.base_alpha = base_alpha
        self.max_alpha = max_alpha
        self.min_alpha = min_alpha
        self.use_adaptive = use_adaptive
        self.window_size = window_size
        self.margin_multiplier = margin_multiplier

        # State tracking for workload adaptation
        self.recent_timestamps = deque(maxlen=window_size)
        self.recent_labels = deque(maxlen=window_size)

    def _calculate_workload_alpha(self):
        """
        Adjusts EWMA decay rate based on run frequency and attack mix.
        """
        if len(self.recent_timestamps) < 2:
            return self.base_alpha

        time_diff = self.recent_timestamps[-1] - self.recent_timestamps[0]
        if time_diff <= 0:
            freq = 0
        else:
            freq = len(self.recent_timestamps) / time_diff

        attack_ratio = (
            sum(self.recent_labels) / len(self.recent_labels)
            if self.recent_labels
            else 0.0
        )

        # Higher frequency -> faster adaptation (up to a point)
        freq_factor = min(freq / 100.0, 1.0)  # Assuming 100 req/s is high

        # If attack ratio is high, we might want to adapt faster to a changing baseline,
        # or slower if we don't want to be poisoned. The prompt states:
        # "faster adaptation under high-frequency/mixed-attack conditions"
        attack_factor = attack_ratio

        # Scale alpha
        adjusted_alpha = self.base_alpha + (freq_factor * 0.05) + (attack_factor * 0.1)
        return max(self.min_alpha, min(self.max_alpha, adjusted_alpha))

    def update(self, mse, is_attack=0, timestamp=None):
        if timestamp is None:
            timestamp = time.time()

        self.recent_timestamps.append(timestamp)
        self.recent_labels.append(is_attack)

        if not self.use_adaptive:
            return self.fixed_threshold

        # Only update EWMA on normal executions to avoid poisoning
        if is_attack == 0:
            alpha = self._calculate_workload_alpha()
            old_threshold = self.current_threshold
            # EWMA update: New Threshold = (1 - alpha) * Old Threshold + alpha * (MSE + Margin)
            # To be safe, we track the EWMA of MSE and add standard deviations.
            # But the simplest EWMA of threshold itself:
            new_threshold = (1 - alpha) * old_threshold + alpha * (
                mse * self.margin_multiplier
            )  # simple margin

            self.current_threshold = new_threshold

            logger.info(
                f"Threshold Update: {old_threshold:.6f} -> {self.current_threshold:.6f} | alpha: {alpha:.4f}"
            )

        return self.current_threshold

    def get_threshold(self):
        return self.current_threshold if self.use_adaptive else self.fixed_threshold

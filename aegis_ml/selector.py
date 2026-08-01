import logging
from collections import deque

logger = logging.getLogger("aegis.phase6.selector")


class RuleBasedSelector:
    def __init__(self, window_size=100, fpr_threshold=0.05):
        """
        Selects between Adaptive and Fixed threshold modes based on recent False Positive Rate.
        """
        self.window_size = window_size
        self.fpr_threshold = fpr_threshold

        self.recent_predictions = deque(maxlen=window_size)
        self.recent_truths = deque(maxlen=window_size)

        self.use_adaptive = False  # Start with fixed

    def update(self, prediction, ground_truth):
        """
        Updates the rolling buffers and decides which configuration to use.
        Returns True if adaptive should be used, False otherwise.
        """
        self.recent_predictions.append(prediction)
        self.recent_truths.append(ground_truth)

        # Calculate FPR: False Positives / Total Negatives
        false_positives = 0
        total_negatives = 0

        for p, t in zip(self.recent_predictions, self.recent_truths):
            if t == 0:
                total_negatives += 1
                if p == 1:
                    false_positives += 1

        if total_negatives == 0:
            fpr = 0.0
        else:
            fpr = false_positives / total_negatives

        old_mode = self.use_adaptive

        if fpr > self.fpr_threshold:
            self.use_adaptive = True
        else:
            # Add some hysteresis / stability? For now just strict rule
            self.use_adaptive = False

        if old_mode != self.use_adaptive:
            mode_str = "Adaptive" if self.use_adaptive else "Fixed"
            logger.info(
                f"Selector Switch -> {mode_str} Mode (FPR: {fpr:.4f} crossed threshold {self.fpr_threshold})"
            )

        return self.use_adaptive

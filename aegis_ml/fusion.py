import logging

logger = logging.getLogger("aegis.phase6.fusion")

class TelemetryFusion:
    def __init__(self, w_time=0.33, w_mse=0.33, w_var=0.34):
        self.w_time = w_time
        self.w_mse = w_mse
        self.w_var = w_var
        
        # Min/max bounds for normalization
        # In a real system, these would be tracked via EWMA, but we can maintain rolling extremes.
        self.max_time = 1.0
        self.min_time = 0.0
        
        self.max_mse = 1.0
        self.min_mse = 0.0
        
        self.max_var = 1.0
        self.min_var = 0.0

    def update_bounds(self, timing, mse, variance):
        self.max_time = max(self.max_time, timing)
        self.min_time = min(self.min_time, timing)
        
        self.max_mse = max(self.max_mse, mse)
        self.min_mse = min(self.min_mse, mse)
        
        self.max_var = max(self.max_var, variance)
        self.min_var = min(self.min_var, variance)

    def normalize(self, val, min_val, max_val):
        if max_val == min_val:
            return 0.0
        return (val - min_val) / (max_val - min_val)

    def compute_fused_score(self, timing, mse, variance):
        """
        Combines timing, MSE, and variance into a single fused anomaly score.
        """
        self.update_bounds(timing, mse, variance)
        
        norm_time = self.normalize(timing, self.min_time, self.max_time)
        norm_mse = self.normalize(mse, self.min_mse, self.max_mse)
        norm_var = self.normalize(variance, self.min_var, self.max_var)
        
        contrib_time = self.w_time * norm_time
        contrib_mse = self.w_mse * norm_mse
        contrib_var = self.w_var * norm_var
        
        fused_score = contrib_time + contrib_mse + contrib_var
        
        logger.info(
            f"Fusion | Score: {fused_score:.4f} | "
            f"Timing(w={self.w_time}): {contrib_time:.4f} | "
            f"MSE(w={self.w_mse}): {contrib_mse:.4f} | "
            f"Var(w={self.w_var}): {contrib_var:.4f}"
        )
        
        return fused_score, {
            "fused_score": fused_score,
            "contrib_time": contrib_time,
            "contrib_mse": contrib_mse,
            "contrib_var": contrib_var
        }

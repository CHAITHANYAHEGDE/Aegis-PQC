from aegis_ml.fusion import TelemetryFusion
from aegis_ml.models.adaptive_threshold import AdaptiveThresholdManager
from aegis_ml.selector import RuleBasedSelector


def test_adaptive_threshold_manager():
    manager = AdaptiveThresholdManager(initial_threshold=0.5, base_alpha=0.1)
    assert manager.get_threshold() == 0.5

    # Normal run updates threshold
    manager.update(mse=0.4, is_attack=0)
    assert manager.get_threshold() != 0.5

    # Attack run does not update threshold
    thresh_before = manager.get_threshold()
    manager.update(mse=2.0, is_attack=1)
    assert manager.get_threshold() == thresh_before


def test_workload_adaptation():
    manager = AdaptiveThresholdManager(initial_threshold=0.5, base_alpha=0.1)

    # Rapid sequence
    for i in range(10):
        manager.update(mse=0.5, is_attack=0, timestamp=i * 0.01)

    alpha = manager._calculate_workload_alpha()
    assert alpha > 0.1  # Should increase due to high frequency


def test_telemetry_fusion():
    fusion = TelemetryFusion(w_time=0.5, w_mse=0.5, w_var=0.0)

    fusion.update_bounds(timing=100.0, mse=10.0, variance=1.0)
    fusion.update_bounds(timing=200.0, mse=20.0, variance=2.0)

    score, breakdown = fusion.compute_fused_score(timing=150.0, mse=15.0, variance=1.5)

    assert 0.0 <= score <= 1.0
    assert breakdown["contrib_var"] == 0.0


def test_rule_based_selector():
    selector = RuleBasedSelector(window_size=10, fpr_threshold=0.1)

    # All correct normal -> Fixed mode
    for _ in range(10):
        selector.update(prediction=0, ground_truth=0)

    assert selector.use_adaptive is False

    # Introduce false positives -> switch to Adaptive
    for _ in range(5):
        use_adaptive = selector.update(prediction=1, ground_truth=0)

    assert use_adaptive is True

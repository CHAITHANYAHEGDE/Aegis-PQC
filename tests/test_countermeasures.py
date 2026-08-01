import time
import pytest
from aegis_ml.countermeasures.response_policy import ResponsePolicy
from aegis_ml.countermeasures.random_delay import RandomDelay
from aegis_ml.countermeasures.throttling import Throttling
from aegis_ml.countermeasures.forensic_logger import ForensicLogger


def test_random_delay_disabled():
    delay = RandomDelay()
    delay.disable()
    telemetry = {"execution_time_us": 100}
    overhead = delay.execute(telemetry, 0.9)
    assert overhead == 0.0


def test_random_delay_enabled():
    delay = RandomDelay(min_delay_s=0.01, max_delay_s=0.02)
    delay.enable()
    telemetry = {"execution_time_us": 100}
    overhead = delay.execute(telemetry, 0.9)
    assert overhead >= 0.01


def test_throttling_disabled():
    throttle = Throttling()
    throttle.disable()
    telemetry = {"execution_time_us": 100}
    overhead = throttle.execute(telemetry, 0.9)
    assert overhead == 0.0


def test_throttling_enabled():
    throttle = Throttling(max_requests_per_sec=10)
    throttle.enable()
    telemetry = {"execution_time_us": 100}

    overhead = throttle.execute(telemetry, 0.9)
    assert overhead == 0.0  # First request uses a token

    # Drain the bucket
    for _ in range(9):
        throttle.execute(telemetry, 0.9)

    # The next one should throttle
    overhead = throttle.execute(telemetry, 0.9)
    assert overhead > 0.0


def test_response_policy_low_confidence():
    policy = ResponsePolicy()
    telemetry = {"execution_time_us": 100}
    actions, overhead = policy.evaluate_and_react(0.2, telemetry)
    assert "Allow" in actions
    assert overhead == 0.0


def test_response_policy_high_confidence():
    policy = ResponsePolicy()
    telemetry = {"execution_time_us": 100}
    actions, overhead = policy.evaluate_and_react(0.85, telemetry)
    assert "Random Delay" in actions
    assert "Forensic Logging" in actions
    assert "Request Throttling" in actions
    assert "Alert" in actions
    assert "Key Rotation" in actions
    assert overhead > 0.0


def test_response_policy_config_update():
    policy = ResponsePolicy()
    assert policy.cm_random_delay.enabled == True

    policy.update_config({"randomized_delay": False})
    assert policy.cm_random_delay.enabled == False

    config = policy.get_config()
    assert config["randomized_delay"] == False
    assert config["throttling"] == True

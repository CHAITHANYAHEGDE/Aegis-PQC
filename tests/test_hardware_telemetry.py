import pytest
from aegis_ml.hardware import get_default_provider, AegisEngineProvider

def test_hardware_provider_initialization():
    provider = get_default_provider()
    assert isinstance(provider, AegisEngineProvider)

def test_graceful_fallback():
    provider = get_default_provider()
    telemetry = provider.get_telemetry("ML-KEM-512", "none")
    
    # Core software telemetry must exist
    assert "execution_time_us" in telemetry
    assert "max_rss_kb" in telemetry
    
    # HW Telemetry presence
    assert "hw_telemetry_available" in telemetry
    
    hw_avail = telemetry["hw_telemetry_available"]
    assert hw_avail in [0.0, 1.0]
    
    if hw_avail == 0.0:
        # On fallback (e.g. macOS), hardware metrics should be -1.0
        assert telemetry.get("hw_cpu_cycles", 0) == -1.0
        assert telemetry.get("hw_instructions", 0) == -1.0
        assert telemetry.get("hw_cache_misses", 0) == -1.0
    else:
        # On Linux with perf, they should be >= 0
        assert telemetry.get("hw_cpu_cycles", -1) >= 0
        assert telemetry.get("hw_instructions", -1) >= 0

def test_unsupported_algorithm():
    provider = get_default_provider()
    with pytest.raises(RuntimeError):
        provider.get_telemetry("INVALID-ALGO", "none")

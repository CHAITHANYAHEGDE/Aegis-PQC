import abc
from typing import Any

try:
    import aegis_engine
except ImportError:
    aegis_engine = None


class HardwareTelemetryProvider(abc.ABC):
    @abc.abstractmethod
    def get_telemetry(self, algo_name: str, attack_profile: str) -> dict[str, Any]:
        """Execute crypto algorithm and return telemetry."""


class AegisEngineProvider(HardwareTelemetryProvider):
    """
    Interfaces with the C++ aegis_engine which inherently supports Linux perf.
    If Linux perf is unavailable (e.g., on macOS or lacking permissions),
    the engine gracefully falls back to software telemetry and sets
    'hw_telemetry_available' to 0.0.
    """

    def get_telemetry(self, algo_name: str, attack_profile: str) -> dict[str, Any]:
        if not aegis_engine:
            raise RuntimeError(
                "aegis_engine module not found. Build the C++ extension first."
            )
        return aegis_engine.run_crypto(algo_name, attack_profile)


# Future implementations for PCM / PAPI can be added here.
class FutureIntelPCMProvider(HardwareTelemetryProvider):
    def get_telemetry(self, algo_name: str, attack_profile: str) -> dict[str, Any]:
        raise NotImplementedError("Intel PCM provider not yet implemented.")


class FuturePAPIProvider(HardwareTelemetryProvider):
    def get_telemetry(self, algo_name: str, attack_profile: str) -> dict[str, Any]:
        raise NotImplementedError("PAPI provider not yet implemented.")


_default_provider = AegisEngineProvider()


def get_default_provider() -> HardwareTelemetryProvider:
    return _default_provider

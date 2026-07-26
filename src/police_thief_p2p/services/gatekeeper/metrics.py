"""Redacted Gatekeeper telemetry with no request payloads."""

from collections import Counter
from dataclasses import dataclass, field


@dataclass(slots=True)
class GatekeeperMetrics:
    """Count safe service/outcome dimensions and current resource gauges."""

    counters: Counter[tuple[str, str]] = field(default_factory=Counter)
    gauges: dict[tuple[str, str], float] = field(default_factory=dict)

    def increment(self, service: str, metric: str, amount: int = 1) -> None:
        """Increment one provider-safe counter."""
        self.counters[(service, metric)] += amount

    def gauge(self, service: str, metric: str, value: float) -> None:
        """Set one provider-safe resource gauge."""
        self.gauges[(service, metric)] = value

    def snapshot(self) -> dict[str, dict[str, float]]:
        """Return redacted metrics grouped by service."""
        result: dict[str, dict[str, float]] = {}
        for (service, metric), count in self.counters.items():
            result.setdefault(service, {})[metric] = float(count)
        for (service, metric), gauge in self.gauges.items():
            result.setdefault(service, {})[metric] = gauge
        return result

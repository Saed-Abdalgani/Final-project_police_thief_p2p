"""Redacted DOS and repeated-operation anomaly detection."""

from collections import defaultdict, deque

from police_thief_p2p.services.ports.clock import ClockPort


class AnomalyDetector:
    """Detect bursts, loops, identical sends, and sustained errors."""

    __slots__ = ("_calls", "_clock", "_errors", "_signatures")

    def __init__(self, clock: ClockPort) -> None:
        """Create provider-isolated rolling windows."""
        self._clock = clock
        self._calls: dict[str, deque[float]] = defaultdict(deque)
        self._errors: dict[str, deque[float]] = defaultdict(deque)
        self._signatures: dict[tuple[str, str], deque[float]] = defaultdict(deque)

    def admit(
        self,
        service: str,
        signature: str,
        *,
        burst_limit: int,
        repeated_limit: int,
        error_limit: int,
    ) -> tuple[bool, str | None]:
        """Return a redacted rejection code when a rolling threshold trips."""
        now = self._clock.monotonic()
        calls = self._trim(self._calls[service], now, 1.0)
        errors = self._trim(self._errors[service], now, 60.0)
        repeats = self._trim(self._signatures[(service, signature)], now, 60.0)
        if len(calls) >= burst_limit:
            return False, "ANOMALOUS_BURST"
        if len(repeats) >= repeated_limit:
            return False, "REPEATED_IDENTICAL_CALL"
        if len(errors) >= error_limit:
            return False, "SUSTAINED_PROVIDER_ERRORS"
        calls.append(now)
        repeats.append(now)
        return True, None

    def record_error(self, service: str) -> None:
        """Record only service and monotonic time, never payload or secrets."""
        self._errors[service].append(self._clock.monotonic())

    def reset(self, service: str, *, confirmed: bool) -> None:
        """Clear one provider's anomaly history after operator confirmation."""
        if not confirmed:
            raise ValueError("anomaly reset requires operator confirmation")
        self._calls.pop(service, None)
        self._errors.pop(service, None)
        for key in tuple(self._signatures):
            if key[0] == service:
                self._signatures.pop(key)

    @staticmethod
    def _trim(values: deque[float], now: float, window: float) -> deque[float]:
        while values and now - values[0] > window:
            values.popleft()
        return values

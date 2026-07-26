"""Continuous monotonic token-bucket limiter."""

from police_thief_p2p.services.ports.clock import ClockPort


class ContinuousTokenBucket:
    """Continuously refill configured request tokens using monotonic time."""

    __slots__ = ("_capacity", "_clock", "_last", "_rate", "_tokens")

    def __init__(
        self,
        clock: ClockPort,
        *,
        requests_per_minute: int,
        capacity: int,
    ) -> None:
        """Create a bucket without wall-clock sensitivity."""
        if requests_per_minute < 1 or capacity < 1:
            raise ValueError("token-bucket limits are invalid")
        self._clock = clock
        self._rate = requests_per_minute / 60.0
        self._capacity = float(capacity)
        self._tokens = float(capacity)
        self._last = clock.monotonic()

    @property
    def available(self) -> float:
        """Return current continuously refilled token count."""
        self._refill()
        return self._tokens

    def consume_delay(self) -> float:
        """Consume one token or return a positive wait before it is available."""
        self._refill()
        if self._tokens >= 1:
            self._tokens -= 1
            return 0.0
        return (1 - self._tokens) / self._rate

    def consume_after_wait(self) -> None:
        """Consume the token made available after an injected wait."""
        self._refill()
        if self._tokens < 1:
            raise RuntimeError("token-bucket wait did not advance monotonic time")
        self._tokens -= 1

    def _refill(self) -> None:
        now = self._clock.monotonic()
        elapsed = max(0.0, now - self._last)
        self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)
        self._last = now

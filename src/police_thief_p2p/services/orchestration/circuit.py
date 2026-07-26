"""Monotonic circuit breaker for repeated transport failures."""

from enum import StrEnum

from police_thief_p2p.services.ports.clock import ClockPort


class CircuitState(StrEnum):
    """Circuit admission states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half-open"


class CircuitBreaker:
    """Open after a threshold and admit one probe after cooldown."""

    __slots__ = (
        "_clock",
        "_failures",
        "_opened_at",
        "_probe_active",
        "_state",
        "cooldown",
        "threshold",
    )

    def __init__(self, clock: ClockPort, *, threshold: int, cooldown: float) -> None:
        """Create a breaker with positive threshold and cooldown."""
        if threshold < 1 or cooldown <= 0:
            raise ValueError("circuit breaker limits are invalid")
        self._clock = clock
        self.threshold = threshold
        self.cooldown = cooldown
        self._failures = 0
        self._opened_at: float | None = None
        self._probe_active = False
        self._state = CircuitState.CLOSED

    @property
    def state(self) -> CircuitState:
        """Return current state, advancing OPEN to HALF_OPEN after cooldown."""
        if (
            self._state is CircuitState.OPEN
            and self._opened_at is not None
            and self._clock.monotonic() - self._opened_at >= self.cooldown
        ):
            self._state = CircuitState.HALF_OPEN
        return self._state

    def allow(self) -> bool:
        """Return whether one transport attempt may proceed."""
        state = self.state
        if state is CircuitState.OPEN:
            return False
        if state is CircuitState.HALF_OPEN:
            if self._probe_active:
                return False
            self._probe_active = True
        return True

    def success(self) -> None:
        """Close and reset after a successful request/probe."""
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._opened_at = None
        self._probe_active = False

    def failure(self) -> None:
        """Record a failure and open at the configured threshold."""
        self._failures += 1
        if self._state is CircuitState.HALF_OPEN or self._failures >= self.threshold:
            self._state = CircuitState.OPEN
            self._opened_at = self._clock.monotonic()
            self._probe_active = False

    def reset(self, *, confirmed: bool) -> None:
        """Perform an explicit operator-confirmed safe reset."""
        if not confirmed:
            raise ValueError("circuit reset requires operator confirmation")
        self.success()

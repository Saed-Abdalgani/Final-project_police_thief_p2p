"""Independent heartbeat watchdog and redacted recovery snapshots."""

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from threading import Event, Thread

from police_thief_p2p.services.orchestration.phases import GamePhase
from police_thief_p2p.services.ports.clock import ClockPort


class HealthState(StrEnum):
    """Redacted public peer health."""

    ALIVE = "alive"
    READY = "ready"
    DEGRADED = "degraded"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class Heartbeat:
    """Progress signal emitted independently of private game state."""

    phase: GamePhase
    step_number: int
    monotonic_timestamp: float
    progress_token: int


@dataclass(frozen=True, slots=True)
class HealthView:
    """Public safe health view."""

    state: HealthState
    phase: str
    step_number: int
    progress_token: int

    def as_dict(self) -> dict[str, object]:
        """Return the exact redacted SDK/MCP health payload."""
        return {
            "status": self.state.value,
            "phase": self.phase,
            "step_number": self.step_number,
            "progress_token": self.progress_token,
        }


@dataclass(frozen=True, slots=True)
class RecoverySnapshot:
    """Redacted watchdog intervention record with no payload/nonce/key fields."""

    reason: str
    phase: str
    step_number: int
    progress_token: int
    observed_at: str

    def document(self) -> dict[str, object]:
        """Return safe persistence fields."""
        return {
            "reason": self.reason,
            "phase": self.phase,
            "step_number": self.step_number,
            "progress_token": self.progress_token,
            "observed_at": self.observed_at,
        }


class Watchdog:
    """Detect absent or unchanged progress on an independent worker path."""

    __slots__ = ("_clock", "_last_progress_at", "_last_token", "_timeout")

    def __init__(self, clock: ClockPort, timeout: float) -> None:
        """Create a watchdog with one monotonic progress threshold."""
        if timeout <= 0:
            raise ValueError("watchdog timeout must be positive")
        self._clock = clock
        self._timeout = timeout
        self._last_token: int | None = None
        self._last_progress_at = clock.monotonic()

    def check(self, heartbeat: Heartbeat | None) -> str | None:
        """Return an intervention reason for absent or stalled progress."""
        now = self._clock.monotonic()
        if heartbeat is None:
            return "heartbeat-absent" if now - self._last_progress_at >= self._timeout else None
        if heartbeat.progress_token != self._last_token:
            self._last_token = heartbeat.progress_token
            self._last_progress_at = now
            return None
        if now - self._last_progress_at >= self._timeout:
            return "progress-stalled"
        return None

    def start(
        self,
        stop: Event,
        read_heartbeat: Callable[[], Heartbeat | None],
        intervene: Callable[[str, Heartbeat | None], None],
        *,
        poll_interval: float = 0.1,
    ) -> Thread:
        """Start a daemon worker that never shares the gameplay call stack."""
        if poll_interval <= 0:
            raise ValueError("watchdog poll interval must be positive")

        def run() -> None:
            while not stop.wait(poll_interval):
                heartbeat = read_heartbeat()
                reason = self.check(heartbeat)
                if reason is not None:
                    intervene(reason, heartbeat)
                    return

        worker = Thread(target=run, name="peer-watchdog", daemon=True)
        worker.start()
        return worker


def health_view(
    heartbeat: Heartbeat | None,
    *,
    ready: bool,
    failed: bool,
    degraded: bool,
) -> HealthView:
    """Compose alive/ready/degraded/failed state without private payload data."""
    if failed:
        state = HealthState.FAILED
    elif degraded:
        state = HealthState.DEGRADED
    elif ready:
        state = HealthState.READY
    else:
        state = HealthState.ALIVE
    return HealthView(
        state,
        "unknown" if heartbeat is None else heartbeat.phase.value,
        0 if heartbeat is None else heartbeat.step_number,
        0 if heartbeat is None else heartbeat.progress_token,
    )

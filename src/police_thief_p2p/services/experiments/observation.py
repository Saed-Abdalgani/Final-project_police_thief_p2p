"""Deterministic delayed and lossy delivery of emitted opponent evidence."""

from dataclasses import dataclass, field

from police_thief_p2p.services.belief.models import OpponentScentFrame
from police_thief_p2p.services.ports.random_source import RandomSource


@dataclass(slots=True)
class ObservationChannel:
    """Bounded queue modelling observation delay and missing scent evidence."""

    rng: RandomSource
    delay: int = 0
    dropout: float = 0.0
    _pending: list[tuple[int, OpponentScentFrame, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate bounded degradation parameters."""
        if self.delay < 0 or self.delay > 8:
            raise ValueError("observation delay is outside the bounded range")
        if not 0.0 <= self.dropout <= 1.0:
            raise ValueError("observation dropout must be a probability")

    def submit(self, turn: int, frame: OpponentScentFrame, hint: str) -> None:
        """Queue one emitted frame for delivery, dropping it under loss."""
        if self.dropout > 0.0 and self.rng.random() < self.dropout:
            return
        self._pending.append((turn + self.delay, frame, hint))

    def due(self, turn: int) -> tuple[tuple[OpponentScentFrame, str], ...]:
        """Return frames whose delivery turn has arrived, in emission order."""
        ready = tuple((frame, hint) for at, frame, hint in self._pending if at <= turn)
        self._pending = [item for item in self._pending if item[0] > turn]
        return ready

    @property
    def pending(self) -> int:
        """Return the number of undelivered frames."""
        return len(self._pending)

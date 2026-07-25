"""Privacy-safe online opponent features and normalized motion mixture."""

import math
from dataclasses import dataclass, replace
from enum import StrEnum

from police_thief_p2p.domain.values import ActionType, Direction
from police_thief_p2p.services.strategy.contracts import HintVerdict
from police_thief_p2p.services.strategy.request import OpponentSummary


class ObservationSource(StrEnum):
    """Taint classification for strategy adaptation."""

    PUBLIC_REVEAL = "public-reveal"
    AUDITED_FINAL = "audited-final"
    HIDDEN_REPLAY = "hidden-replay"


@dataclass(frozen=True, slots=True)
class OpponentObservation:
    """Legally observable behavior without a live true-position field."""

    source: ObservationSource
    direction: Direction | None
    action_type: ActionType
    step_number: int
    on_boundary: bool | None = None
    revisited: bool | None = None
    hint_verdict: HintVerdict | None = None

    def __post_init__(self) -> None:
        """Reject hidden truth and audit-only fields at live boundaries."""
        if self.source is ObservationSource.HIDDEN_REPLAY:
            raise ValueError("unaudited hidden truth cannot update opponent profiles")
        if self.step_number < 1:
            raise ValueError("opponent observation step must be positive")
        if self.source is ObservationSource.PUBLIC_REVEAL and (
            self.on_boundary is not None or self.revisited is not None
        ):
            raise ValueError("live observations cannot claim hidden path features")


@dataclass(frozen=True, slots=True)
class OpponentProfile:
    """Exponentially decayed, opponent-keyed behavior sufficient statistics."""

    opponent_group: str
    strategy_version: str
    counts: tuple[float, float, float, float, float] = (1.0,) * 5
    observations: int = 0
    hint_truth: float = 1.0
    hint_lie: float = 1.0
    last_direction: Direction | None = None

    def __post_init__(self) -> None:
        """Validate finite positive counters and exact profile identity."""
        if not self.opponent_group or not self.strategy_version:
            raise ValueError("opponent profile key is incomplete")
        numeric = (*self.counts, self.hint_truth, self.hint_lie)
        if any(not math.isfinite(value) or value <= 0 for value in numeric):
            raise ValueError("opponent profile counters must be finite and positive")
        if self.observations < 0:
            raise ValueError("opponent profile observations cannot be negative")

    def update(self, observation: OpponentObservation, decay: float) -> "OpponentProfile":
        """Forget stale behavior and incorporate one legal observation."""
        if not 0 < decay <= 1:
            raise ValueError("opponent decay must be in (0, 1]")
        counts = [max(0.05, value * decay) for value in self.counts]
        counts[0] += 0.25
        if observation.direction is not None:
            counts[1] += 1.0
        if observation.on_boundary:
            counts[2] += 1.0
        if observation.revisited:
            counts[3] += 1.0
        if observation.direction is not None and observation.direction == self.last_direction:
            counts[4] += 1.0
        truth = max(0.05, self.hint_truth * decay)
        lie = max(0.05, self.hint_lie * decay)
        if observation.hint_verdict is HintVerdict.TRUTH:
            truth += 1.0
        elif observation.hint_verdict is HintVerdict.LIE:
            lie += 1.0
        normalized_counts = (counts[0], counts[1], counts[2], counts[3], counts[4])
        return replace(
            self,
            counts=normalized_counts,
            observations=self.observations + 1,
            hint_truth=truth,
            hint_lie=lie,
            last_direction=observation.direction or self.last_direction,
        )

    def summary(self) -> OpponentSummary:
        """Return normalized mixture and smoothed hint trust."""
        total = math.fsum(self.counts)
        values = tuple(value / total for value in self.counts)
        mixture = (values[0], values[1], values[2], values[3], values[4])
        correction = 1.0 - math.fsum(mixture)
        mixture = (mixture[0] + correction, *mixture[1:])
        trust = self.hint_truth / (self.hint_truth + self.hint_lie)
        return OpponentSummary(mixture, trust, self.observations)

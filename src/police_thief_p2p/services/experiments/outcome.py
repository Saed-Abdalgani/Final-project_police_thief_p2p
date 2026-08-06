"""Immutable per-match outcome and safe reliability telemetry."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from police_thief_p2p.domain.values import TerminalReason
from police_thief_p2p.services.strategy.contracts import Decision

CAPTURE_REASONS: Final = frozenset(
    {
        TerminalReason.CAPTURE,
        TerminalReason.BARRIER_CAPTURE,
        TerminalReason.ENCLOSURE,
    }
)
SURVIVAL_REASONS: Final = frozenset({TerminalReason.SURVIVAL, TerminalReason.STEP_CEILING})
FAILURE_REASONS: Final = frozenset({TerminalReason.TECHNICAL, TerminalReason.TAMPER})
_INVALID: Final = "FALLBACK_INVALID"
_DEADLINE: Final = "FALLBACK_DEADLINE"


@dataclass(frozen=True, slots=True)
class MatchOutcome:
    """One verified terminal reason with reproducible reliability counters."""

    reason: TerminalReason
    completed_turns: int
    decisions: int
    fallbacks: int
    invalid_actions: int
    deadline_misses: int
    latencies_ms: tuple[float, ...]

    def __post_init__(self) -> None:
        """Validate non-negative counters and a typed terminal reason."""
        if not isinstance(self.reason, TerminalReason):
            raise TypeError("match reason must be a TerminalReason")
        counters = (
            self.completed_turns,
            self.decisions,
            self.fallbacks,
            self.invalid_actions,
            self.deadline_misses,
        )
        if min(counters) < 0:
            raise ValueError("match counters must be non-negative")

    @property
    def captured(self) -> bool:
        """Return whether the Police achieved a verified capture family."""
        return self.reason in CAPTURE_REASONS

    @property
    def survived(self) -> bool:
        """Return whether the Thief reached a verified survival outcome."""
        return self.reason in SURVIVAL_REASONS

    @property
    def failed(self) -> bool:
        """Return whether this match ended in a technical or tamper sanction."""
        return self.reason in FAILURE_REASONS

    @property
    def max_latency_ms(self) -> float:
        """Return the slowest observed decision latency."""
        return max(self.latencies_ms, default=0.0)


def build_outcome(
    reason: TerminalReason,
    completed_turns: int,
    decisions: Sequence[Decision],
) -> MatchOutcome:
    """Summarize one finished match from its ordered guarded decisions."""
    return MatchOutcome(
        reason=reason,
        completed_turns=completed_turns,
        decisions=len(decisions),
        fallbacks=sum(item.fallback_used for item in decisions),
        invalid_actions=sum(item.reason_code == _INVALID for item in decisions),
        deadline_misses=sum(item.reason_code == _DEADLINE for item in decisions),
        latencies_ms=tuple(item.metrics.latency_ms for item in decisions),
    )

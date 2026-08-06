"""Official-score aggregation and separated reliability gating for tournaments."""

from collections.abc import Sequence
from dataclasses import dataclass

from police_thief_p2p.domain.scoring import score_terminal
from police_thief_p2p.domain.values import Role
from police_thief_p2p.services.experiments.outcome import MatchOutcome
from police_thief_p2p.shared.config_sections import ScoringConfig


@dataclass(frozen=True, slots=True)
class PairedMatch:
    """One candidate result plus the role it played against one opponent."""

    opponent_id: str
    fixture_id: str
    seed: int
    candidate_role: Role
    outcome: MatchOutcome

    def candidate_points(self, scoring: ScoringConfig) -> int:
        """Return the official points the candidate earned in this match."""
        return score_terminal(self.outcome.reason, scoring).for_role(self.candidate_role)

    def opponent_points(self, scoring: ScoringConfig) -> int:
        """Return the official points the opponent earned in this match."""
        return score_terminal(self.outcome.reason, scoring).for_role(self.candidate_role.opponent)


@dataclass(frozen=True, slots=True)
class RoleSummary:
    """Per-role official score and role-specific success rate."""

    matches: int
    points: int
    successes: int

    @property
    def success_rate(self) -> float:
        """Return the role's capture or survival rate."""
        return 0.0 if self.matches == 0 else self.successes / self.matches

    @property
    def mean_points(self) -> float:
        """Return the mean official points per match for this role."""
        return 0.0 if self.matches == 0 else self.points / self.matches


def role_summary(
    matches: Sequence[PairedMatch],
    role: Role,
    scoring: ScoringConfig,
) -> RoleSummary:
    """Summarize official points and role success for one candidate role."""
    selected = [item for item in matches if item.candidate_role is role]
    successes = sum(
        item.outcome.captured if role is Role.POLICE else item.outcome.survived for item in selected
    )
    return RoleSummary(
        matches=len(selected),
        points=sum(item.candidate_points(scoring) for item in selected),
        successes=successes,
    )


@dataclass(frozen=True, slots=True)
class ReliabilityReport:
    """Hard reliability counters that are never averaged into the score."""

    matches: int
    technical_or_tamper: int
    invalid_actions: int
    deadline_misses: int
    fallbacks: int
    max_latency_ms: float

    @property
    def passes(self) -> bool:
        """Return whether every hard reliability counter is exactly zero."""
        return (
            self.technical_or_tamper == 0
            and self.invalid_actions == 0
            and self.deadline_misses == 0
        )

    def as_document(self) -> dict[str, object]:
        """Return the serializable reliability gate result."""
        return {
            "matches": self.matches,
            "technical_or_tamper": self.technical_or_tamper,
            "invalid_actions": self.invalid_actions,
            "deadline_misses": self.deadline_misses,
            "fallbacks": self.fallbacks,
            "max_latency_ms": round(self.max_latency_ms, 3),
            "passes": self.passes,
        }


def reliability_report(matches: Sequence[PairedMatch]) -> ReliabilityReport:
    """Aggregate hard failure counters across every played match."""
    return ReliabilityReport(
        matches=len(matches),
        technical_or_tamper=sum(item.outcome.failed for item in matches),
        invalid_actions=sum(item.outcome.invalid_actions for item in matches),
        deadline_misses=sum(item.outcome.deadline_misses for item in matches),
        fallbacks=sum(item.outcome.fallbacks for item in matches),
        max_latency_ms=max((item.outcome.max_latency_ms for item in matches), default=0.0),
    )


def latency_samples(matches: Sequence[PairedMatch]) -> tuple[float, ...]:
    """Return every observed decision latency across the campaign."""
    return tuple(value for item in matches for value in item.outcome.latencies_ms)


def official_share(matches: Sequence[PairedMatch], scoring: ScoringConfig) -> float:
    """Return the candidate's share of all official points as a percentage."""
    candidate = sum(item.candidate_points(scoring) for item in matches)
    opposing = sum(item.opponent_points(scoring) for item in matches)
    total = candidate + opposing
    return 0.0 if total == 0 else 100.0 * candidate / total

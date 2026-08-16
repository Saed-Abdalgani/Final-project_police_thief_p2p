"""Recovery-arena outcomes, aggregation, and deployment gates."""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass

from police_thief_p2p.services.strategy.compatibility import CompatibilityStrategyProfile


@dataclass(frozen=True, slots=True)
class CompatibilityMatchOutcome:
    """Official result and reliability diagnostics for one sub-game."""

    family: str
    role: str
    outcome: str
    steps: int
    our_score: int
    opponent_score: int
    illegal_actions: int
    technical_failures: int
    audit_failures: int
    deadline_misses: int
    decision_latencies_ms: tuple[float, ...]
    barriers_placed: int
    useful_barriers: int

    @property
    def won_objective(self) -> bool:
        """Return capture success for Police or survival success for Thief."""
        return (self.role == "police" and self.outcome == "capture") or (
            self.role == "thief" and self.outcome == "survival"
        )


@dataclass(frozen=True, slots=True)
class CompatibilityFamilyMetrics:
    """Per-family deployment gate inputs aggregated over both roles."""

    family: str
    police_capture_rate: float
    thief_survival_rate: float
    score_share: float
    illegal_actions: int
    technical_failures: int
    audit_failures: int
    deadline_misses: int
    latency_p95_ms: float
    barrier_efficiency: float

    @property
    def passed(self) -> bool:
        """Apply the recovery deployment gate exactly as declared."""
        return (
            self.police_capture_rate >= 0.80
            and self.thief_survival_rate >= 0.80
            and self.score_share > 0.50
            and self.illegal_actions == 0
            and self.technical_failures == 0
            and self.audit_failures == 0
            and self.deadline_misses == 0
            and self.latency_p95_ms <= 250.0
        )


@dataclass(frozen=True, slots=True)
class CompatibilityCampaignResult:
    """Candidate result with a reliability-first lexicographic rank."""

    profile: CompatibilityStrategyProfile
    families: tuple[CompatibilityFamilyMetrics, ...]
    matches: tuple[CompatibilityMatchOutcome, ...]

    @property
    def rank(self) -> tuple[float, ...]:
        """Rank reliability, worst role rate/share, mean share, latency, barriers."""
        failures = sum(
            item.illegal_actions
            + item.technical_failures
            + item.audit_failures
            + item.deadline_misses
            for item in self.families
        )
        worst_role = min(
            min(item.police_capture_rate, item.thief_survival_rate) for item in self.families
        )
        worst_share = min(item.score_share for item in self.families)
        mean_share = statistics.fmean(item.score_share for item in self.families)
        latency = max(item.latency_p95_ms for item in self.families)
        efficiency = statistics.fmean(item.barrier_efficiency for item in self.families)
        return (
            1.0 if failures == 0 else 0.0,
            -float(failures),
            worst_role,
            worst_share,
            mean_share,
            -latency,
            efficiency,
        )

    @property
    def passed(self) -> bool:
        """Return true only when every family passes independently."""
        return all(item.passed for item in self.families)


def match_outcome(
    family: str,
    role: str,
    outcome: str,
    steps: int,
    illegal: int,
    latencies: list[float],
    barriers_placed: int,
    useful_barriers: int,
) -> CompatibilityMatchOutcome:
    """Build official score and deadline diagnostics for one match."""
    police_score, thief_score = (20, 5) if outcome == "capture" else (5, 10)
    ours = police_score if role == "police" else thief_score
    theirs = thief_score if role == "police" else police_score
    return CompatibilityMatchOutcome(
        family,
        role,
        outcome,
        steps,
        ours,
        theirs,
        illegal,
        0,
        0,
        sum(latency > 250.0 for latency in latencies),
        tuple(latencies),
        barriers_placed,
        useful_barriers,
    )


def family_metrics(
    family: str, matches: tuple[CompatibilityMatchOutcome, ...]
) -> CompatibilityFamilyMetrics:
    """Aggregate one family's role rates, score share, latency, and reliability."""
    selected = [match for match in matches if match.family == family]
    police = [match for match in selected if match.role == "police"]
    thief = [match for match in selected if match.role == "thief"]
    latencies = [latency for match in selected for latency in match.decision_latencies_ms]
    placed = sum(match.barriers_placed for match in selected)
    return CompatibilityFamilyMetrics(
        family,
        sum(match.outcome == "capture" for match in police) / len(police),
        sum(match.outcome == "survival" for match in thief) / len(thief),
        sum(match.our_score for match in selected)
        / sum(match.our_score + match.opponent_score for match in selected),
        sum(match.illegal_actions for match in selected),
        sum(match.technical_failures for match in selected),
        sum(match.audit_failures for match in selected),
        sum(match.deadline_misses for match in selected),
        percentile(latencies, 0.95),
        sum(match.useful_barriers for match in selected) / placed if placed else 1.0,
    )


def percentile(values: list[float], quantile: float) -> float:
    """Return the nearest-rank percentile for a bounded latency sample."""
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[max(0, math.ceil(quantile * len(ordered)) - 1)]

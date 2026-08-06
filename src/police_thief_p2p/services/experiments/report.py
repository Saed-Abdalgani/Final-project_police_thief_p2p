"""Aggregated tournament report with paired uplift, intervals, and ranking."""

from collections.abc import Sequence
from dataclasses import dataclass

from police_thief_p2p.domain.values import Role
from police_thief_p2p.services.experiments.metrics import (
    PairedMatch,
    ReliabilityReport,
    latency_samples,
    official_share,
    reliability_report,
    role_summary,
)
from police_thief_p2p.services.experiments.spec import TournamentSpec
from police_thief_p2p.services.experiments.statistics import (
    Interval,
    bootstrap_interval,
    elo_ratings,
    paired_difference_interval,
    percentile,
)
from police_thief_p2p.services.ports.random_source import RandomSource
from police_thief_p2p.shared.config_sections import ScoringConfig


@dataclass(frozen=True, slots=True)
class TournamentReport:
    """Immutable machine-readable outcome of one declared campaign."""

    spec: TournamentSpec
    matches: tuple[PairedMatch, ...]
    reliability: ReliabilityReport
    score_share: float
    score_interval: Interval
    uplift_interval: Interval
    per_opponent: tuple[tuple[str, float], ...]
    per_fixture: tuple[tuple[str, float], ...]
    police_success: float
    thief_success: float
    latency_p95_ms: float
    latency_max_ms: float
    ratings: tuple[tuple[str, float], ...]

    @property
    def worst_fixture_drop(self) -> float:
        """Return the largest fixture-family shortfall against the aggregate."""
        if not self.per_fixture:
            return 0.0
        return max(self.score_share - value for _, value in self.per_fixture)

    def as_document(self) -> dict[str, object]:
        """Return the canonical serializable campaign report."""
        return {
            "spec": self.spec.as_document(),
            "match_count": len(self.matches),
            "score_share_percent": round(self.score_share, 3),
            "score_interval": self.score_interval.as_document(),
            "uplift_interval": self.uplift_interval.as_document(),
            "police_capture_rate": round(self.police_success, 4),
            "thief_survival_rate": round(self.thief_success, 4),
            "per_opponent_share": {name: round(value, 3) for name, value in self.per_opponent},
            "per_fixture_share": {name: round(value, 3) for name, value in self.per_fixture},
            "worst_fixture_drop": round(self.worst_fixture_drop, 3),
            "latency_p95_ms": round(self.latency_p95_ms, 3),
            "latency_max_ms": round(self.latency_max_ms, 3),
            "ratings": {name: value for name, value in self.ratings},
            "reliability": self.reliability.as_document(),
        }


def _grouped_share(
    matches: Sequence[PairedMatch],
    scoring: ScoringConfig,
    key: str,
) -> tuple[tuple[str, float], ...]:
    names = sorted({str(getattr(item, key)) for item in matches})
    return tuple(
        (
            name,
            official_share([item for item in matches if str(getattr(item, key)) == name], scoring),
        )
        for name in names
    )


def _pairwise_wins(
    matches: Sequence[PairedMatch],
    scoring: ScoringConfig,
    candidate_id: str,
) -> dict[tuple[str, str], int]:
    wins: dict[tuple[str, str], int] = {}
    for item in matches:
        candidate = item.candidate_points(scoring)
        rival = item.opponent_points(scoring)
        if candidate == rival:
            continue
        winner, loser = (
            (candidate_id, item.opponent_id)
            if candidate > rival
            else (item.opponent_id, candidate_id)
        )
        wins[(winner, loser)] = wins.get((winner, loser), 0) + 1
    return wins


def build_report(
    spec: TournamentSpec,
    matches: Sequence[PairedMatch],
    scoring: ScoringConfig,
    rng: RandomSource,
) -> TournamentReport:
    """Aggregate played matches into official, reliability, and ranking views."""
    if not matches:
        raise ValueError("tournament report requires at least one played match")
    ordered = tuple(matches)
    points = [float(item.candidate_points(scoring)) for item in ordered]
    rival_points = [float(item.opponent_points(scoring)) for item in ordered]
    latencies = latency_samples(ordered)
    competitors = [spec.candidate_id, *spec.opponent_ids]
    return TournamentReport(
        spec=spec,
        matches=ordered,
        reliability=reliability_report(ordered),
        score_share=official_share(ordered, scoring),
        score_interval=bootstrap_interval(points, rng, resamples=1_000),
        uplift_interval=paired_difference_interval(points, rival_points, rng, resamples=1_000),
        per_opponent=_grouped_share(ordered, scoring, "opponent_id"),
        per_fixture=_grouped_share(ordered, scoring, "fixture_id"),
        police_success=role_summary(ordered, Role.POLICE, scoring).success_rate,
        thief_success=role_summary(ordered, Role.THIEF, scoring).success_rate,
        latency_p95_ms=percentile(latencies, 0.95) if latencies else 0.0,
        latency_max_ms=max(latencies, default=0.0),
        ratings=tuple(
            sorted(
                elo_ratings(
                    _pairwise_wins(ordered, scoring, spec.candidate_id), competitors
                ).items()
            )
        ),
    )

"""Overfitting, competitive, and reliability gates applied before promotion."""

from collections.abc import Sequence
from typing import Final

from police_thief_p2p.services.experiments.gate_result import GateReport, GateResult
from police_thief_p2p.services.experiments.generalization import overfitting_gate, robustness_gate
from police_thief_p2p.services.experiments.report import TournamentReport

MINIMUM_UPLIFT_POINTS: Final = 20.0
MINIMUM_SHARE: Final = 50.0 + MINIMUM_UPLIFT_POINTS / 2.0
MINIMUM_ROLE_SUCCESS: Final = 0.70
MAXIMUM_FIXTURE_DROP: Final = 15.0
MAXIMUM_LATENCY_P95_MS: Final = 250.0


def reliability_gates(report: TournamentReport) -> tuple[GateResult, ...]:
    """Return the zero-tolerance hard reliability gates for one campaign."""
    metrics = report.reliability
    return (
        GateResult(
            "R02-TECHNICAL",
            "zero technical failures or tamper events",
            metrics.technical_or_tamper,
            metrics.technical_or_tamper == 0,
        ),
        GateResult(
            "R02-INVALID",
            "zero invalid submitted actions",
            metrics.invalid_actions,
            metrics.invalid_actions == 0,
        ),
        GateResult(
            "R02-DEADLINE",
            "zero decision deadline misses",
            metrics.deadline_misses,
            metrics.deadline_misses == 0,
        ),
        GateResult(
            "P01-LATENCY",
            f"p95 decision latency at or below {MAXIMUM_LATENCY_P95_MS:.0f} ms",
            report.latency_p95_ms,
            report.latency_p95_ms <= MAXIMUM_LATENCY_P95_MS,
        ),
    )


def competitive_gates(report: TournamentReport) -> tuple[GateResult, ...]:
    """Return the competitive strength gates for one campaign."""
    lower = report.uplift_interval.lower
    worst_opponent = min((value for _, value in report.per_opponent), default=0.0)
    return (
        GateResult(
            "S01-SHARE",
            f"official score share at or above {MINIMUM_SHARE:.0f} percent",
            report.score_share,
            report.score_share >= MINIMUM_SHARE,
        ),
        GateResult(
            "S02-UPLIFT",
            "paired point-uplift bootstrap interval excludes zero from above",
            lower,
            lower > 0.0,
        ),
        GateResult(
            "S03-POLICE",
            f"Police capture rate at or above {MINIMUM_ROLE_SUCCESS:.0%}",
            report.police_success,
            report.police_success >= MINIMUM_ROLE_SUCCESS,
        ),
        GateResult(
            "S03-THIEF",
            f"Thief survival rate at or above {MINIMUM_ROLE_SUCCESS:.0%}",
            report.thief_success,
            report.thief_success >= MINIMUM_ROLE_SUCCESS,
        ),
        GateResult(
            "S05-FIXTURE",
            f"worst fixture family within {MAXIMUM_FIXTURE_DROP:.0f} points of aggregate",
            report.worst_fixture_drop,
            report.worst_fixture_drop <= MAXIMUM_FIXTURE_DROP,
        ),
        GateResult(
            "S05-OPPONENT",
            "no single-opponent specialization below an even split",
            worst_opponent,
            worst_opponent >= 50.0,
        ),
    )


def promotion_report(
    report: TournamentReport,
    *,
    train_share: float | None = None,
    degraded_shares: Sequence[float] = (),
) -> GateReport:
    """Combine reliability, competitive, and generalization gates."""
    gates = [*reliability_gates(report), *competitive_gates(report)]
    if train_share is not None:
        gates.append(overfitting_gate(train_share, report.score_share))
    if degraded_shares:
        gates.append(robustness_gate(degraded_shares))
    return GateReport(tuple(gates))

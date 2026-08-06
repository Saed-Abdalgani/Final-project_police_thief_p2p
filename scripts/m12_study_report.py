"""Evidence document assembly for the M12 ablation and robustness studies."""

from collections.abc import Mapping, Sequence

from police_thief_p2p.services.experiments.gate_result import GateResult
from police_thief_p2p.services.experiments.report import TournamentReport
from police_thief_p2p.services.experiments.resources import ResourceUsage
from police_thief_p2p.services.experiments.studies import Ablation, RobustnessCase


def ablation_rows(
    results: Sequence[tuple[Ablation, TournamentReport]],
    intact: float,
) -> list[dict[str, object]]:
    """Return one measured row per declared component removal."""
    return [
        {
            "study_id": study.study_id,
            "component": study.component,
            "description": study.description,
            "removed": dict(study.point),
            "share_percent": round(report.score_share, 3),
            "share_delta": round(report.score_share - intact, 3),
            "uplift_interval": report.uplift_interval.as_document(),
            "police_capture_rate": round(report.police_success, 4),
            "thief_survival_rate": round(report.thief_success, 4),
            "latency_p95_ms": round(report.latency_p95_ms, 3),
            "reliability": report.reliability.as_document(),
        }
        for study, report in results
    ]


def robustness_rows(
    results: Sequence[tuple[RobustnessCase, TournamentReport]],
    intact: float,
) -> list[dict[str, object]]:
    """Return one measured row per degraded-environment case."""
    return [
        {
            **case.as_document(),
            "share_percent": round(report.score_share, 3),
            "share_delta": round(report.score_share - intact, 3),
            "latency_p95_ms": round(report.latency_p95_ms, 3),
            "reliability": report.reliability.as_document(),
        }
        for case, report in results
    ]


def study_document(
    *,
    schema_version: str,
    commit_sha: str,
    intact: float,
    intact_report: TournamentReport,
    ablations: Sequence[tuple[Ablation, TournamentReport]],
    robustness: Sequence[tuple[RobustnessCase, TournamentReport]],
    adversarial: Sequence[Mapping[str, object]],
    gate: GateResult,
    resources: ResourceUsage,
) -> dict[str, object]:
    """Assemble the complete study evidence document."""
    return {
        "schema_version": schema_version,
        "commit_sha": commit_sha,
        "split": "validation",
        "resources": resources.as_document(),
        "intact_share_percent": round(intact, 3),
        "ablations": ablation_rows(ablations, intact),
        "robustness": robustness_rows(robustness, intact),
        "adversarial_search": {
            "method": (
                "Exhaustive sweep of every registered adversary over all validation board "
                "geometries; the worst two are retained as validation-only regression cases."
            ),
            "results": [dict(row) for row in adversarial],
            "worst_case_opponent_ids": [str(row["opponent_id"]) for row in adversarial[:2]],
        },
        "geometry_robustness": {
            "note": (
                "Board size, start, origin corner, axis index, barrier quota, and step ceiling "
                "variation is exercised through the disjoint validation fixture families."
            ),
            "per_fixture_share": {
                name: round(value, 3) for name, value in intact_report.per_fixture
            },
        },
        "gates": {
            "robustness": gate.as_document(),
            "every_ablation_reliable": all(report.reliability.passes for _, report in ablations),
            "every_adversary_reliable": all(bool(row["reliability_passes"]) for row in adversarial),
            "result": "PASS" if gate.passed else "FAIL",
        },
    }

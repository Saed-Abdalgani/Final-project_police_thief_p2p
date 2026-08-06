"""Run the M12 ablation, robustness, and adversarial-search studies."""

import json

from police_thief_p2p.services.experiments.belief_track import DEFAULT_BELIEF_PROFILE, BeliefProfile
from police_thief_p2p.services.experiments.generalization import robustness_gate
from police_thief_p2p.services.experiments.profiles import derive_pair
from police_thief_p2p.services.experiments.report import TournamentReport
from police_thief_p2p.services.experiments.resources import measure
from police_thief_p2p.services.experiments.roster import opponents_by_classification
from police_thief_p2p.services.experiments.studies import (
    ABLATIONS,
    ROBUSTNESS_CASES,
    Ablation,
    RobustnessCase,
)
from police_thief_p2p.shared.config_models import SharedConfig
from police_thief_p2p.shared.strategy_config import StrategyConfig
from scripts.m12_campaign_support import (
    BENCHMARKS,
    SCHEMA_VERSION,
    SplitPlan,
    build_runner,
    commit_sha,
    load_configs,
    load_freeze,
    write_evidence,
)
from scripts.m12_study_report import study_document

STUDY_SEEDS = 1
STUDY_OPPONENTS = 2
SWEEP_SEEDS = 1


def _progress(label: str, report: TournamentReport) -> TournamentReport:
    """Log one measured study so a long campaign is observable while it runs."""
    print(
        f"{label} matches={len(report.matches)} share={report.score_share:.1f} "
        f"p95={report.latency_p95_ms:.0f}ms",
        flush=True,
    )
    return report


def _ablation_report(
    shared: SharedConfig,
    strategy: StrategyConfig,
    belief: BeliefProfile,
    plan: SplitPlan,
    study: Ablation,
) -> TournamentReport:
    varied, belief_varied = derive_pair(strategy, study.point, belief)
    spec = plan.spec(
        f"ablation-{study.study_id.lower()}",
        opponents=plan.opponent_ids[:STUDY_OPPONENTS],
        seeds=plan.seeds[:STUDY_SEEDS],
    )
    return _progress(study.study_id, build_runner(shared, varied, belief_varied).run(spec))


def _robustness_report(
    shared: SharedConfig,
    strategy: StrategyConfig,
    belief: BeliefProfile,
    plan: SplitPlan,
    case: RobustnessCase,
) -> TournamentReport:
    spec = plan.spec(
        f"robustness-{case.case_id.lower()}",
        opponents=case.opponent_ids or plan.opponent_ids[:STUDY_OPPONENTS],
        seeds=plan.seeds[:STUDY_SEEDS],
        decision_budget_ms=case.decision_budget_ms,
        observation_delay=case.observation_delay,
        scent_dropout=case.scent_dropout,
    )
    return _progress(case.case_id, build_runner(shared, strategy, belief).run(spec))


def _adversarial_sweep(
    shared: SharedConfig,
    strategy: StrategyConfig,
    belief: BeliefProfile,
    plan: SplitPlan,
) -> list[dict[str, object]]:
    """Search the declared adversary space for the worst case against the candidate."""
    rows: list[dict[str, object]] = []
    for opponent_id in opponents_by_classification("adversary"):
        spec = plan.spec(
            f"adversarial-{opponent_id.lower()}",
            opponents=(opponent_id,),
            seeds=plan.seeds[:SWEEP_SEEDS],
        )
        report = _progress(opponent_id, build_runner(shared, strategy, belief).run(spec))
        rows.append(
            {
                "opponent_id": opponent_id,
                "share_percent": round(report.score_share, 3),
                "police_capture_rate": round(report.police_success, 4),
                "thief_survival_rate": round(report.thief_success, 4),
                "worst_fixture_drop": round(report.worst_fixture_drop, 3),
                "per_fixture_share": {name: round(value, 3) for name, value in report.per_fixture},
                "reliability_passes": report.reliability.passes,
            }
        )
    return sorted(rows, key=lambda row: float(str(row["share_percent"])))


def main() -> int:
    """Measure component ablations, degraded environments, and worst-case adversaries."""
    shared, base = load_configs()
    strategy, belief = derive_pair(base, load_freeze(), DEFAULT_BELIEF_PROFILE)
    plan = SplitPlan.load("validation")
    with measure() as ledger:
        ablations = [
            (study, _ablation_report(shared, strategy, belief, plan, study)) for study in ABLATIONS
        ]
        robustness = [
            (case, _robustness_report(shared, strategy, belief, plan, case))
            for case in ROBUSTNESS_CASES
        ]
        adversarial = _adversarial_sweep(shared, strategy, belief, plan)
    intact_report = next(report for study, report in ablations if study.study_id == "ABL-FULL")
    degraded = [report.score_share for case, report in robustness if case.case_id != "ROB-CLEAN"]
    gate = robustness_gate(degraded)
    document = study_document(
        schema_version=SCHEMA_VERSION,
        commit_sha=commit_sha(),
        intact=intact_report.score_share,
        intact_report=intact_report,
        ablations=ablations,
        robustness=robustness,
        adversarial=adversarial,
        gate=gate,
        resources=ledger.usage(),
    )
    write_evidence(BENCHMARKS / "m12_studies.json", document)
    print(json.dumps(document["gates"], sort_keys=True))
    return 0 if gate.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

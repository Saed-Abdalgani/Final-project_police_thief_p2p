"""Validate the frozen candidate, then spend the one-shot sealed holdout run."""

import json

from police_thief_p2p.services.experiments.belief_track import DEFAULT_BELIEF_PROFILE
from police_thief_p2p.services.experiments.gates import promotion_report
from police_thief_p2p.services.experiments.generalization import overfitting_gate
from police_thief_p2p.services.experiments.manifest import CandidateFreeze, ReproducibilityManifest
from police_thief_p2p.services.experiments.profiles import derive_pair
from police_thief_p2p.services.experiments.resources import measure
from police_thief_p2p.services.experiments.splits import SealedHoldout
from scripts.m12_campaign_support import (
    BENCHMARKS,
    SCHEMA_VERSION,
    SplitPlan,
    build_runner,
    commit_sha,
    load_configs,
    load_freeze,
    report_summary,
    write_evidence,
)

VALIDATION_SEEDS = 2
HOLDOUT_SEEDS = 2


def main() -> int:
    """Run validation, apply the overfitting gate, then open the sealed holdout once."""
    shared, base = load_configs()
    point = load_freeze()
    strategy, belief = derive_pair(base, point, DEFAULT_BELIEF_PROFILE)
    tuning = json.loads((BENCHMARKS / "m12_tuning.json").read_text(encoding="utf-8"))
    train_share = float(tuning["training_confirmation"]["score_share_percent"])
    runner = build_runner(shared, strategy, belief)
    validation_plan = SplitPlan.load("validation")
    with measure() as ledger:
        validation = runner.run(
            validation_plan.spec("m12-validation", seeds=validation_plan.seeds[:VALIDATION_SEEDS])
        )
    overfitting = overfitting_gate(train_share, validation.score_share)
    validation_gates = promotion_report(validation, train_share=train_share)
    freeze = CandidateFreeze(
        candidate_id="candidate-advanced",
        strategy=strategy,
        belief=belief,
        selection_split="validation",
        selection_objective=validation.uplift_interval.lower,
        trial_id=int(tuning["manifest"]["candidate"]["trial_id"]),
    )
    seal = SealedHoldout()
    manifest = seal.open(freeze.digest())
    holdout_plan = SplitPlan.load("holdout")
    with measure() as holdout_ledger:
        holdout = runner.run(
            holdout_plan.spec(
                "m12-holdout",
                opponents=manifest.opponent_ids,
                seeds=manifest.seeds[:HOLDOUT_SEEDS],
            )
        )
    holdout_gates = promotion_report(holdout, train_share=train_share)
    record = ReproducibilityManifest(
        campaign_id="m12-selection",
        commit_sha=commit_sha(),
        split="validation",
        freeze=freeze,
        metrics={
            "train_share_percent": round(train_share, 3),
            "validation": report_summary(validation),
            "holdout": report_summary(holdout),
        },
        notes="Holdout opened exactly once against the validation-selected freeze.",
        resources=ledger.usage(),
    )
    document = {
        "schema_version": SCHEMA_VERSION,
        "commit_sha": record.commit_sha,
        "train_share_percent": round(train_share, 3),
        "validation": validation.as_document(),
        "validation_gates": validation_gates.as_document(),
        "overfitting_gate": overfitting.as_document(),
        "sealed_holdout": {
            "split_sha256": manifest.digest(),
            "opened_for_freeze_sha256": seal.opened_for,
            "one_shot": True,
        },
        "holdout": holdout.as_document(),
        "holdout_resources": holdout_ledger.usage().as_document(),
        "holdout_gates": holdout_gates.as_document(),
        "manifest": record.as_document(),
        "gates": {
            "validation_passed": validation_gates.passed,
            "overfitting_passed": overfitting.passed,
            "holdout_passed": holdout_gates.passed,
            "result": (
                "PASS"
                if validation_gates.passed and overfitting.passed and holdout_gates.passed
                else "FAIL"
            ),
        },
    }
    write_evidence(BENCHMARKS / "m12_selection.json", document)
    print(json.dumps(document["gates"], sort_keys=True))
    return 0 if document["gates"]["result"] == "PASS" else 1  # type: ignore[index]


if __name__ == "__main__":
    raise SystemExit(main())

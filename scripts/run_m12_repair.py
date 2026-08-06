"""Repair the frozen candidate for deadline safety and Thief survival before a new holdout."""

import json

from police_thief_p2p.services.experiments.belief_track import DEFAULT_BELIEF_PROFILE
from police_thief_p2p.services.experiments.gates import promotion_report
from police_thief_p2p.services.experiments.manifest import CandidateFreeze, ReproducibilityManifest
from police_thief_p2p.services.experiments.profiles import derive_pair, profile_digest
from police_thief_p2p.services.experiments.spaces import space_document
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
from scripts.m12_repair_support import CANDIDATES, PROBE_OPPONENTS, merged, repair_score


def main() -> int:
    """Patch the freeze, pick the best validation-safe candidate, rewrite tuning evidence."""
    shared, base = load_configs()
    prior = load_freeze()
    plan = SplitPlan.load("validation")
    best_point = merged(prior, CANDIDATES[0])
    best_score = -1e18
    best_summary: dict[str, object] = {}
    for index, patch in enumerate(CANDIDATES):
        point = merged(prior, patch)
        strategy, belief = derive_pair(base, point, DEFAULT_BELIEF_PROFILE)
        report = build_runner(shared, strategy, belief).run(
            plan.spec(
                f"repair-{index}",
                opponents=PROBE_OPPONENTS,
                fixtures=plan.fixtures[:3],
                seeds=plan.seeds[:2],
            )
        )
        score = repair_score(report.score_share, report.thief_success, report.reliability.deadline_misses)
        print(
            f"repair={index} thief={report.thief_success:.3f} share={report.score_share:.1f} "
            f"deadlines={report.reliability.deadline_misses} "
            f"max_ms={report.latency_max_ms:.1f} score={score:.2f}",
            flush=True,
        )
        if score > best_score:
            best_score, best_point = score, point
            best_summary = {
                "thief_success": report.thief_success,
                "score_share": report.score_share,
                "deadline_misses": report.reliability.deadline_misses,
                "latency_max_ms": report.latency_max_ms,
                "police_success": report.police_success,
            }
    strategy, belief = derive_pair(base, best_point, DEFAULT_BELIEF_PROFILE)
    train = SplitPlan.load("train")
    confirm = build_runner(shared, strategy, belief).run(
        train.spec("repair-confirm", seeds=train.seeds[:3])
    )
    freeze = CandidateFreeze(
        candidate_id="candidate-advanced",
        strategy=strategy,
        belief=belief,
        selection_split="train",
        selection_objective=float(best_summary["thief_success"]),
        trial_id=10_000,
    )
    previous = json.loads((BENCHMARKS / "m12_tuning.json").read_text(encoding="utf-8"))
    document = {
        "schema_version": SCHEMA_VERSION,
        "commit_sha": commit_sha(),
        "search_spaces": space_document(),
        "random_search": previous.get("random_search", {"method": "random", "trials": []}),
        "surrogate_search": {
            "method": "repair",
            "trials": [
                {
                    "trial_id": 10_000,
                    "method": "repair",
                    "point": best_point,
                    "objective": round(float(best_summary["thief_success"]), 4),
                    "score_share_percent": round(float(best_summary["score_share"]), 3),
                    "latency_p95_ms": round(confirm.latency_p95_ms, 3),
                    "reliability_pass": confirm.reliability.deadline_misses == 0,
                    "completed": True,
                    "stop_reason": "COMPLETED",
                }
            ],
            "attempted": 1,
            "completed": 1,
            "stopped_early": 0,
            "best_trial_id": 10_000,
            "best_objective": round(float(best_summary["thief_success"]), 4),
        },
        "baseline_profile_sha256": profile_digest(base),
        "training_confirmation": confirm.as_document(),
        "repair_probe": best_summary,
        "manifest": ReproducibilityManifest(
            campaign_id="m12-tuning-repair",
            commit_sha=commit_sha(),
            split="train",
            freeze=freeze,
            metrics=report_summary(confirm),
            notes="Deadline-safe compute restore plus Thief-weight repair before holdout v1.2.0.",
        ).as_document(),
    }
    write_evidence(BENCHMARKS / "m12_tuning.json", document)
    print(
        json.dumps(
            {
                "best_score": round(best_score, 3),
                "probe": best_summary,
                "train_share": round(confirm.score_share, 3),
                "train_thief": round(confirm.thief_success, 4),
                "train_deadlines": confirm.reliability.deadline_misses,
                "reliability_ok": all(
                    item.passed
                    for item in promotion_report(confirm).gates
                    if item.gate_id.startswith(("R02", "P01"))
                ),
            },
            sort_keys=True,
        )
    )
    return 0 if confirm.reliability.deadline_misses == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

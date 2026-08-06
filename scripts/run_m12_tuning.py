"""Run the M12 random then surrogate-guided hyperparameter search on training data."""

import json
import time
from collections.abc import Mapping

from police_thief_p2p.adapters.system.deterministic_random import DeterministicRandomSource
from police_thief_p2p.services.experiments.belief_track import DEFAULT_BELIEF_PROFILE
from police_thief_p2p.services.experiments.gates import promotion_report
from police_thief_p2p.services.experiments.manifest import CandidateFreeze, ReproducibilityManifest
from police_thief_p2p.services.experiments.profiles import derive_pair, profile_digest
from police_thief_p2p.services.experiments.resources import ResourceLedger, measure
from police_thief_p2p.services.experiments.spaces import (
    BELIEF_SPACE,
    space_document,
    strategy_dimensions,
)
from police_thief_p2p.services.experiments.splits import assert_tunable
from police_thief_p2p.services.experiments.surrogate import surrogate_search
from police_thief_p2p.services.experiments.tuning import (
    FULL_STAGE,
    SearchOutcome,
    TrialResult,
    random_search,
)
from scripts.m12_campaign_support import (
    BENCHMARKS,
    SCHEMA_VERSION,
    SplitPlan,
    build_runner,
    commit_sha,
    load_configs,
    report_summary,
    write_evidence,
)

RANDOM_TRIALS = 12
SURROGATE_TRIALS = 5
SEARCH_SEED = 912_001
SCREEN_OPPONENTS = 1
SCREEN_FIXTURES = 1
SCREEN_SEEDS = 1
FULL_FIXTURES = 2
FULL_SEEDS = 1
CONFIRM_SEEDS = 3


class Evaluator:
    """Evaluate one search point as a paired training mini-tournament."""

    __slots__ = ("_plan", "_shared", "_strategy")

    def __init__(self) -> None:
        """Load configs and the frozen training split once."""
        self._shared, self._strategy = load_configs()
        assert_tunable("train")
        self._plan = SplitPlan.load("train")

    def __call__(self, point: Mapping[str, float | int], stage: int) -> TrialResult:
        """Play one staged evaluation and return its objective and gate view."""
        strategy, belief = derive_pair(self._strategy, point, DEFAULT_BELIEF_PROFILE)
        full = stage == FULL_STAGE
        spec = self._plan.spec(
            f"tune-stage{stage}",
            opponents=None if full else self._plan.opponent_ids[:SCREEN_OPPONENTS],
            fixtures=self._plan.fixtures[: FULL_FIXTURES if full else SCREEN_FIXTURES],
            seeds=self._plan.seeds[: FULL_SEEDS if full else SCREEN_SEEDS],
        )
        started = time.perf_counter()
        report = build_runner(self._shared, strategy, belief).run(spec)
        gates = promotion_report(report)
        result = TrialResult(
            objective=report.uplift_interval.lower,
            score_share=report.score_share,
            reliability_pass=all(
                item.passed for item in gates.gates if item.gate_id.startswith(("R02", "P01"))
            ),
            latency_p95_ms=report.latency_p95_ms,
            matches=len(report.matches),
        )
        print(
            f"stage={stage} matches={result.matches} objective={result.objective:.2f} "
            f"share={result.score_share:.1f} elapsed={time.perf_counter() - started:.1f}s",
            flush=True,
        )
        return result


def _search(ledger: ResourceLedger) -> tuple[SearchOutcome, SearchOutcome]:
    """Run broad random search then surrogate refinement, accounting for every trial."""
    evaluator = Evaluator()
    dimensions = (*strategy_dimensions(), *BELIEF_SPACE)
    rng = DeterministicRandomSource(SEARCH_SEED)
    broad = random_search(dimensions, evaluator, rng, trials=RANDOM_TRIALS)
    refined = surrogate_search(
        dimensions,
        evaluator,
        rng,
        trials=SURROGATE_TRIALS,
        prior=broad.trials,
        first_id=RANDOM_TRIALS,
    )
    for trial in (*broad.trials, *refined.trials):
        ledger.record_call(0, trial.deepest.latency_p95_ms)
    return broad, refined


def main() -> int:
    """Search the declared spaces, then freeze and record the winning candidate."""
    with measure() as ledger:
        broad, refined = _search(ledger)
    best = max((broad.best, refined.best), key=lambda item: item.objective)
    shared, base = load_configs()
    strategy, belief = derive_pair(base, best.point, DEFAULT_BELIEF_PROFILE)
    plan = SplitPlan.load("train")
    confirm = build_runner(shared, strategy, belief).run(
        plan.spec("tune-confirm", seeds=plan.seeds[:CONFIRM_SEEDS])
    )
    freeze = CandidateFreeze(
        candidate_id="candidate-advanced",
        strategy=strategy,
        belief=belief,
        selection_split="train",
        selection_objective=best.objective,
        trial_id=best.trial_id,
    )
    manifest = ReproducibilityManifest(
        campaign_id="m12-tuning",
        commit_sha=commit_sha(),
        split="train",
        freeze=freeze,
        metrics=report_summary(confirm),
        notes="Random search then surrogate refinement on the frozen training split only.",
        resources=ledger.usage(),
    )
    document = {
        "schema_version": SCHEMA_VERSION,
        "commit_sha": manifest.commit_sha,
        "search_spaces": space_document(),
        "random_search": broad.as_document(),
        "surrogate_search": refined.as_document(),
        "baseline_profile_sha256": profile_digest(base),
        "training_confirmation": confirm.as_document(),
        "manifest": manifest.as_document(),
    }
    write_evidence(BENCHMARKS / "m12_tuning.json", document)
    print(
        json.dumps(
            {
                "attempted": RANDOM_TRIALS + SURROGATE_TRIALS,
                "best_trial_id": best.trial_id,
                "best_objective": round(best.objective, 3),
                "train_share": round(confirm.score_share, 3),
                "freeze_sha256": freeze.digest()[:16],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

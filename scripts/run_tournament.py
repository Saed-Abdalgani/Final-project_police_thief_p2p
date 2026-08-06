"""Run one declared offline tournament and write its reproducible report."""

import argparse
import json

from police_thief_p2p.sdk import SimulationSdk
from police_thief_p2p.services.experiments.gates import promotion_report
from police_thief_p2p.services.experiments.splits import assert_tunable
from scripts.m12_campaign_support import (
    SCHEMA_VERSION,
    TOURNAMENTS,
    SplitPlan,
    commit_sha,
    load_configs,
    write_evidence,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one offline tournament campaign.")
    parser.add_argument("--split", default="train", help="frozen split to draw assets from")
    parser.add_argument("--campaign-id", default=None, help="campaign identifier for evidence")
    parser.add_argument("--opponents", nargs="*", default=None, help="subset of split opponents")
    parser.add_argument("--seeds", nargs="*", type=int, default=None, help="subset of split seeds")
    parser.add_argument("--budget-ms", type=int, default=250, help="per-decision compute budget")
    parser.add_argument("--delay", type=int, default=0, help="opponent scent delivery delay")
    parser.add_argument("--dropout", type=float, default=0.0, help="opponent scent loss rate")
    parser.add_argument(
        "--allow-holdout",
        action="store_true",
        help="acknowledge that a holdout run consumes the one-shot budget",
    )
    return parser.parse_args()


def main() -> int:
    """Execute one tournament through the SDK facade and record the evidence."""
    args = _arguments()
    if args.split == "holdout" and not args.allow_holdout:
        print("refusing to touch the sealed holdout without --allow-holdout")
        return 2
    if args.split != "holdout":
        assert_tunable(args.split)
    shared, strategy = load_configs()
    plan = SplitPlan.load(args.split)
    campaign_id = args.campaign_id or f"cli-{args.split}"
    spec = plan.spec(
        campaign_id,
        opponents=args.opponents,
        seeds=args.seeds,
        decision_budget_ms=args.budget_ms,
        observation_delay=args.delay,
        scent_dropout=args.dropout,
    )
    report = SimulationSdk().run_tournament(spec, shared, strategy)
    gates = promotion_report(report)
    document = {
        "schema_version": SCHEMA_VERSION,
        "commit_sha": commit_sha(),
        "report": report.as_document(),
        "gates": gates.as_document(),
    }
    write_evidence(TOURNAMENTS / f"{campaign_id}.json", document)
    print(
        json.dumps(
            {
                "campaign_id": campaign_id,
                "matches": spec.match_count,
                "score_share_percent": report.score_share,
                "gates_passed": gates.passed,
                "failures": list(gates.failures),
            },
            sort_keys=True,
        )
    )
    return 0 if gates.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

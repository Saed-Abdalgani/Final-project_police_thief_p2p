"""Train, validate, and gate the thief-first league-recovery strategy profile."""

from __future__ import annotations

import argparse
import json
import random
import secrets
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Any

from police_thief_p2p.services.experiments.compatibility_arena import TRAINING_FAMILIES
from scripts.league_recovery_support import (
    best_result,
    broad_candidate,
    campaign_seed,
    evaluate_profile,
    git_commit,
    refined_candidates,
    result_summary,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "results" / "league-recovery" / "campaign.json"
ROLLBACK_COMMIT = "622dc23"
SEARCH_SEED = 2_026_081_6


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="Run a bounded pipeline smoke test")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--holdout-seal", default=None, help=argparse.SUPPRESS)
    parser.add_argument(
        "--scent-model",
        choices=("multiplicative_kernel_v1", "subtractive_chebyshev_v1"),
        default="multiplicative_kernel_v1",
    )
    return parser


def run_campaign(*, quick: bool, scent_model: str, holdout_seal: str) -> dict[str, Any]:
    """Run selection on training/validation, then touch sealed holdout once."""
    rng = random.Random(SEARCH_SEED)  # noqa: S311 - deterministic candidate generation
    broad_count = 4 if quick else 64
    refined_count = 2 if quick else 24
    full_count = 2 if quick else 8
    validation_count = 1 if quick else 5
    train_seed_count = 1 if quick else 12
    validation_seed_count = 2 if quick else 20
    holdout_seed_count = 3 if quick else 50
    screen_families = TRAINING_FAMILIES[:2] if quick else TRAINING_FAMILIES[:3]
    full_families = TRAINING_FAMILIES[:2] if quick else TRAINING_FAMILIES

    screen_seeds = [campaign_seed("screen", index) for index in range(1 if quick else 2)]
    broad = [
        evaluate_profile(broad_candidate(rng, index), screen_families, screen_seeds, scent_model)
        for index in range(broad_count)
    ]
    broad_elite = sorted(broad, key=lambda item: item.rank, reverse=True)[:full_count]
    train_seeds = [campaign_seed("training", index) for index in range(train_seed_count)]
    full = [
        evaluate_profile(item.profile, full_families, train_seeds, scent_model)
        for item in broad_elite
    ]
    refined_profiles = refined_candidates(
        sorted(full, key=lambda item: item.rank, reverse=True), rng, refined_count
    )
    refined = [
        evaluate_profile(profile, full_families, train_seeds, scent_model)
        for profile in refined_profiles
    ]
    selected = sorted((*full, *refined), key=lambda item: item.rank, reverse=True)[
        :validation_count
    ]
    validation_seeds = [
        campaign_seed("validation", index) for index in range(validation_seed_count)
    ]
    validation = [
        evaluate_profile(item.profile, full_families, validation_seeds, scent_model)
        for item in selected
    ]
    frozen = best_result(validation)

    # Candidate selection is complete before the sealed holdout seed material is derived.
    holdout_seeds = [
        campaign_seed("sealed-holdout", index, holdout_seal) for index in range(holdout_seed_count)
    ]
    holdout = evaluate_profile(frozen.profile, full_families, holdout_seeds, scent_model)
    failed_families = [item.family for item in holdout.families if not item.passed]
    return {
        "schema_version": "league-recovery-1",
        "quick": quick,
        "commit_sha": git_commit(ROOT),
        "rollback_commit": ROLLBACK_COMMIT,
        "scent_model": scent_model,
        "campaign": {
            "broad_candidates": broad_count,
            "fully_evaluated": full_count,
            "surrogate_refined": refined_count,
            "validation_finalists": validation_count,
            "training_families": list(full_families),
            "training_seeds": train_seed_count,
            "validation_seeds": validation_seed_count,
            "holdout_seeds_per_role_family": holdout_seed_count,
        },
        "frozen_profile": asdict(frozen.profile),
        "frozen_profile_digest": frozen.profile.digest(),
        "validation": result_summary(frozen),
        "holdout": result_summary(holdout),
        "holdout_seal_revealed_after_evaluation": holdout_seal,
        "deployment": {
            "approved": holdout.passed,
            "failed_families_promoted_to_next_validation": failed_families,
            "active_commit": git_commit(ROOT) if holdout.passed else ROLLBACK_COMMIT,
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Execute the campaign and persist a local ignored evidence document."""
    args = _parser().parse_args(argv)
    seal = args.holdout_seal or secrets.token_hex(16)
    document = run_campaign(quick=args.quick, scent_model=args.scent_model, holdout_seal=seal)
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(output),
                "approved": document["deployment"]["approved"],
                "profile_digest": document["frozen_profile_digest"],
                "failed_families": document["deployment"][
                    "failed_families_promoted_to_next_validation"
                ],
            },
            sort_keys=True,
        )
    )
    return 0 if document["deployment"]["approved"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

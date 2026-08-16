"""Candidate generation and serialization helpers for league recovery."""

from __future__ import annotations

import hashlib
import random
import statistics
import subprocess
from collections.abc import Iterable, Sequence
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any, Final

from police_thief_p2p.adapters.amireman.terms import default_terms
from police_thief_p2p.services.experiments.compatibility_arena import (
    CompatibilityArena,
    CompatibilityCampaignResult,
)
from police_thief_p2p.services.strategy.compatibility import CompatibilityStrategyProfile

FLOAT_RANGES: Final[dict[str, tuple[float, float]]] = {
    "observation_sharpness": (5.0, 30.0),
    "opponent_decay": (0.65, 0.98),
    "cvar_tail": (0.10, 0.50),
    "near_tie_epsilon": (0.005, 0.08),
    "police_pursuit": (2.0, 14.0),
    "police_intercept": (1.0, 16.0),
    "police_cut": (3.0, 30.0),
    "police_enclosure": (5.0, 40.0),
    "police_risk": (0.10, 0.70),
    "police_budget": (0.2, 4.0),
    "police_cycle": (1.0, 16.0),
    "thief_territory": (0.5, 5.0),
    "thief_routes": (4.0, 30.0),
    "thief_trap": (60.0, 300.0),
    "thief_scent": (0.5, 12.0),
    "thief_boundary": (3.0, 24.0),
    "thief_unpredictability": (2.0, 20.0),
    "hint_urgency": (0.35, 0.85),
}


def campaign_seed(namespace: str, index: int, seal: str = "") -> int:
    """Derive one deterministic split seed without state shared across splits."""
    raw = hashlib.sha256(f"{namespace}:{index}:{seal}".encode()).digest()
    return int.from_bytes(raw[:8], "big")


def broad_candidate(rng: random.Random, index: int) -> CompatibilityStrategyProfile:
    """Sample one bounded broad-search profile."""
    values: dict[str, Any] = {
        name: rng.uniform(low, high) for name, (low, high) in FLOAT_RANGES.items()
    }
    values.update(
        {
            "profile": "league-recovery",
            "profile_version": f"2.0.{index}",
            "particle_count": rng.choice((32, 48, 64, 96)),
            "lookahead_depth": rng.choice((3, 4)),
            "max_consecutive_lies": rng.choice((1, 2, 3)),
        }
    )
    return CompatibilityStrategyProfile(**values)


def refined_candidates(
    elite: Sequence[CompatibilityCampaignResult], rng: random.Random, count: int
) -> list[CompatibilityStrategyProfile]:
    """Generate surrogate-centroid candidates with bounded refinement."""
    profiles: list[CompatibilityStrategyProfile] = []
    anchor = elite[0].profile
    documents = [asdict(item.profile) for item in elite]
    for index in range(count):
        values: dict[str, Any] = {}
        for name, (low, high) in FLOAT_RANGES.items():
            centre = statistics.fmean(float(document[name]) for document in documents)
            values[name] = min(high, max(low, centre + rng.gauss(0.0, (high - low) * 0.08)))
        profiles.append(
            replace(
                anchor,
                **values,
                profile_version=f"2.1.{index}",
                particle_count=rng.choice(
                    tuple(sorted({item.profile.particle_count for item in elite}))
                ),
                lookahead_depth=rng.choice(
                    tuple(sorted({item.profile.lookahead_depth for item in elite}))
                ),
            )
        )
    return profiles


def evaluate_profile(
    profile: CompatibilityStrategyProfile,
    families: Sequence[str],
    seeds: Iterable[int],
    scent_model: str,
) -> CompatibilityCampaignResult:
    """Evaluate one profile in the compatibility arena."""
    return CompatibilityArena(default_terms(), profile, scent_model=scent_model).evaluate(
        families, seeds
    )


def best_result(results: Iterable[CompatibilityCampaignResult]) -> CompatibilityCampaignResult:
    """Select the reliability-first lexicographic winner."""
    return max(results, key=lambda item: item.rank)


def git_commit(root: Path) -> str:
    """Return the current commit without failing local unversioned runs."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],  # noqa: S607
            cwd=root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def result_summary(result: CompatibilityCampaignResult) -> dict[str, Any]:
    """Serialize one campaign result without private runtime state."""
    return {
        "profile_digest": result.profile.digest(),
        "rank": list(result.rank),
        "passed": result.passed,
        "matches": len(result.matches),
        "families": [asdict(item) | {"passed": item.passed} for item in result.families],
    }

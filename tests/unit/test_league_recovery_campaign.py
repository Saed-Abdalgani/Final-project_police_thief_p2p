from __future__ import annotations

import random
from pathlib import Path
from typing import Any

import pytest

from police_thief_p2p.services.experiments.compatibility_results import (
    CompatibilityCampaignResult,
    CompatibilityFamilyMetrics,
)
from police_thief_p2p.services.strategy.compatibility import CompatibilityStrategyProfile
from scripts import league_recovery_support, run_league_recovery


def _metrics(family: str, *, passed: bool = True) -> CompatibilityFamilyMetrics:
    rate = 1.0 if passed else 0.0
    return CompatibilityFamilyMetrics(
        family, rate, 1.0, 0.75 if passed else 0.5, 0, 0, 0, 0, 10.0, 1.0
    )


def test_candidate_generation_and_split_seeds_are_reproducible() -> None:
    left = league_recovery_support.campaign_seed("train", 1)
    right = league_recovery_support.campaign_seed("train", 1)
    holdout = league_recovery_support.campaign_seed("holdout", 1, "sealed")
    assert left == right
    assert left != holdout
    candidate = league_recovery_support.broad_candidate(random.Random(3), 4)
    result = CompatibilityCampaignResult(candidate, (_metrics("smngrp05"),), ())
    refined = league_recovery_support.refined_candidates([result], random.Random(4), 2)
    assert len(refined) == 2
    assert all(profile.profile_version.startswith("2.1.") for profile in refined)


def test_quick_campaign_selects_before_holdout_and_refuses_failed_family(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[tuple[str, ...], tuple[int, ...]]] = []

    def fake_evaluate(
        profile: CompatibilityStrategyProfile,
        families: tuple[str, ...],
        seeds: list[int],
        _scent_model: str,
    ) -> CompatibilityCampaignResult:
        calls.append((tuple(families), tuple(seeds)))
        final = len(calls) == 10
        metrics = tuple(
            _metrics(family, passed=not (final and family == "ahk-yosi")) for family in families
        )
        return CompatibilityCampaignResult(profile, metrics, ())

    monkeypatch.setattr(run_league_recovery, "evaluate_profile", fake_evaluate)
    monkeypatch.setattr(run_league_recovery, "git_commit", lambda _root: "abc123")
    document = run_league_recovery.run_campaign(
        quick=True,
        scent_model="multiplicative_kernel_v1",
        holdout_seal="sealed",
    )
    assert len(calls) == 10
    assert calls[-1][1] != calls[-2][1]
    assert document["deployment"]["approved"] is False
    assert document["deployment"]["active_commit"] == "622dc23"
    assert document["deployment"]["failed_families_promoted_to_next_validation"] == ["ahk-yosi"]


def test_campaign_cli_persists_failure_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    document: dict[str, Any] = {
        "frozen_profile_digest": "digest",
        "deployment": {
            "approved": False,
            "failed_families_promoted_to_next_validation": ["cycle"],
        },
    }
    monkeypatch.setattr(run_league_recovery, "run_campaign", lambda **_kwargs: document)
    output = tmp_path / "campaign.json"
    status = run_league_recovery.main(
        ["--quick", "--holdout-seal", "sealed", "--output", str(output)]
    )
    assert status == 1
    assert '"approved": false' in output.read_text(encoding="utf-8")

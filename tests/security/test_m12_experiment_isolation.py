import asyncio
from pathlib import Path

import pytest

from police_thief_p2p.services.experiments.splits import (
    HOLDOUT_OPPONENTS,
    SealedHoldout,
    assert_tunable,
    split_manifest,
)
from police_thief_p2p.services.strategy.contracts import HintIntent, HintVerdict, SemanticRegion
from police_thief_p2p.services.strategy.language import OptionalParaphraser
from scripts.m12_language_support import (
    HOSTILE_HINTS,
    malformed_cloud_stub,
    unavailable_stub,
    unsafe_cloud_stub,
)

pytestmark = pytest.mark.security

ROOT = Path(__file__).parents[2]
TUNING_SCRIPTS = (
    ROOT / "scripts/run_m12_tuning.py",
    ROOT / "scripts/run_m12_studies.py",
)
INTENT = HintIntent(HintVerdict.TRUTH, SemanticRegion.NORTH)


def test_tuning_and_study_scripts_never_name_holdout_assets() -> None:
    for path in TUNING_SCRIPTS:
        source = path.read_text(encoding="utf-8")
        assert "holdout" not in source.lower(), path.name


def test_holdout_opponents_and_fixtures_stay_out_of_tunable_splits() -> None:
    holdout = split_manifest("holdout")
    train = split_manifest("train")
    validation = split_manifest("validation")
    assert not set(holdout.fixture_ids) & set(train.fixture_ids)
    assert not set(holdout.fixture_ids) & set(validation.fixture_ids)
    assert not set(holdout.seeds) & set(train.seeds) | set(holdout.seeds) & set(validation.seeds)
    assert "BL-PREV" in HOLDOUT_OPPONENTS
    with pytest.raises(ValueError, match="holdout"):
        assert_tunable("holdout")


def test_sealed_holdout_never_reveals_contents_before_a_freeze() -> None:
    seal = SealedHoldout()
    assert len(seal.digest) == 64
    assert seal.opened_for is None
    assert not hasattr(seal, "seeds")
    assert not hasattr(seal, "fixtures")


def _paraphrase(provider: object, hint: str) -> tuple[str, int, bool]:
    return asyncio.run(
        OptionalParaphraser(provider).paraphrase(  # type: ignore[arg-type]
            INTENT,
            map_area="Kadikoy waterfront",
            maximum_words=20,
            opponent_hint=hint,
        )
    )


@pytest.mark.parametrize("hint", HOSTILE_HINTS)
def test_hostile_opponent_hints_never_alter_our_emitted_surface(hint: str) -> None:
    baseline_text, tokens, fell_back = _paraphrase(unavailable_stub(), "")
    text, hostile_tokens, hostile_fallback = _paraphrase(unavailable_stub(), hint)
    assert text == baseline_text
    assert (tokens, hostile_tokens) == (0, 0)
    assert fell_back
    assert hostile_fallback


def test_unsafe_or_malformed_provider_output_is_rejected_with_zero_tokens() -> None:
    for provider in (unsafe_cloud_stub(), malformed_cloud_stub()):
        text, tokens, fell_back = _paraphrase(provider, HOSTILE_HINTS[0])
        assert fell_back
        assert tokens == 0
        assert "row" not in text
        assert "ignore" not in text.lower()
        assert not any(character.isdigit() for character in text)

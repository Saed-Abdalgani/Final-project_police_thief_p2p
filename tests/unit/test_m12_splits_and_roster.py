import pytest

from police_thief_p2p.domain import Role
from police_thief_p2p.services.experiments.fixtures import disjoint_families, fixtures_for
from police_thief_p2p.services.experiments.opponents import OpponentEntry, entry
from police_thief_p2p.services.experiments.roster import (
    CANDIDATE_ID,
    ROSTER,
    opponent,
    opponents_by_classification,
)
from police_thief_p2p.services.experiments.spec import BoardFixture, TournamentSpec
from police_thief_p2p.services.experiments.splits import (
    HOLDOUT_SEEDS,
    TRAIN_SEEDS,
    VALIDATION_SEEDS,
    SealedHoldout,
    assert_tunable,
    seeds_are_disjoint,
    split_manifest,
)


def test_every_split_is_frozen_disjoint_and_digest_stable() -> None:
    assert seeds_are_disjoint()
    assert disjoint_families()
    assert not set(TRAIN_SEEDS) & set(VALIDATION_SEEDS)
    assert not set(TRAIN_SEEDS) & set(HOLDOUT_SEEDS)
    for split in ("train", "validation", "holdout", "rehearsal"):
        manifest = split_manifest(split)
        assert manifest.digest() == split_manifest(split).digest()
        assert manifest.fixture_ids == tuple(item.fixture_id for item in fixtures_for(split))


def test_tuning_cannot_target_the_sealed_holdout() -> None:
    assert_tunable("train")
    assert_tunable("validation")
    with pytest.raises(ValueError, match="holdout"):
        assert_tunable("holdout")
    with pytest.raises(KeyError):
        assert_tunable("nonexistent")


def test_sealed_holdout_opens_once_for_one_candidate_freeze() -> None:
    seal = SealedHoldout()
    assert seal.opened_for is None
    freeze = "a" * 64
    manifest = seal.open(freeze)
    assert manifest.split == "holdout"
    assert seal.open(freeze).digest() == manifest.digest()
    with pytest.raises(ValueError, match="another candidate"):
        seal.open("b" * 64)
    with pytest.raises(ValueError, match="full candidate freeze"):
        SealedHoldout().open("short")


def test_roster_covers_every_required_classification_and_both_roles() -> None:
    assert CANDIDATE_ID in ROSTER
    for classification in ("candidate", "baseline", "adversary", "regression"):
        assert opponents_by_classification(classification)
    for identifier, item in ROSTER.items():
        assert item.brain(Role.POLICE).role is Role.POLICE, identifier
        assert item.brain(Role.THIEF).role is Role.THIEF, identifier
    assert opponent("BL-PREV").version == "0.10.0"
    with pytest.raises(KeyError, match="unknown experiment opponent"):
        opponent("BL-DOES-NOT-EXIST")


def test_roster_entries_reject_unclassified_or_undocumented_policies() -> None:
    police = ROSTER[CANDIDATE_ID].police
    thief = ROSTER[CANDIDATE_ID].thief
    with pytest.raises(ValueError, match="classification"):
        entry("BL-X", "mystery", police, thief, "summary")
    with pytest.raises(ValueError, match="documented summary"):
        OpponentEntry("BL-X", "1.0.0", "baseline", police, thief, "")


def test_board_fixture_honours_axis_start_index_and_rejects_weakening() -> None:
    shifted = BoardFixture("f-1", axis_start_index=1, thief_start=(7, 7), cop_start=(1, 1))
    assert shifted.thief_start == (7, 7)
    with pytest.raises(ValueError, match="outside the board"):
        BoardFixture("f-2", thief_start=(7, 0))
    with pytest.raises(ValueError, match="weakens a minimum parameter"):
        BoardFixture("f-3", grid_size=6)
    with pytest.raises(ValueError, match="weakens a minimum step parameter"):
        BoardFixture("f-4", max_moves=10)
    with pytest.raises(ValueError, match="must be distinct"):
        BoardFixture("f-5", thief_start=(0, 0), cop_start=(0, 0))


def test_tournament_spec_counts_paired_matches_and_rejects_duplicates() -> None:
    spec = TournamentSpec(
        campaign_id="c",
        split="train",
        candidate_id=CANDIDATE_ID,
        opponent_ids=("BL-REF", "BL-RND"),
        fixtures=fixtures_for("train")[:2],
        seeds=(1, 2, 3),
        repetitions=2,
    )
    assert spec.match_count == 2 * 2 * 3 * 2 * 2
    assert spec.as_document()["match_count"] == spec.match_count
    with pytest.raises(ValueError, match="unique opponents"):
        TournamentSpec(
            campaign_id="c",
            split="train",
            candidate_id=CANDIDATE_ID,
            opponent_ids=("BL-REF", "BL-REF"),
            fixtures=fixtures_for("train")[:1],
            seeds=(1,),
        )
    with pytest.raises(ValueError, match="unique seeds"):
        TournamentSpec(
            campaign_id="c",
            split="train",
            candidate_id=CANDIDATE_ID,
            opponent_ids=("BL-REF",),
            fixtures=fixtures_for("train")[:1],
            seeds=(1, 1),
        )

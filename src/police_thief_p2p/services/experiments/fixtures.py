"""Disjoint board fixture families for training, validation, and holdout."""

from typing import Final

from police_thief_p2p.services.experiments.spec import BoardFixture

TRAIN_FIXTURES: Final = (
    BoardFixture("train-default-7"),
    BoardFixture("train-corner-7", thief_start=(6, 6), cop_start=(0, 0)),
    BoardFixture("train-wide-9", grid_size=9, thief_start=(4, 4), cop_start=(8, 0)),
)
VALIDATION_FIXTURES: Final = (
    BoardFixture("validation-offset-7", thief_start=(1, 5), cop_start=(5, 1)),
    BoardFixture("validation-quota-8", grid_size=8, thief_start=(4, 3), max_barriers=20),
    BoardFixture(
        "validation-long-9",
        grid_size=9,
        thief_start=(2, 6),
        cop_start=(8, 8),
        max_moves=45,
        survival_threshold=45,
    ),
)
HOLDOUT_FIXTURES: Final = (
    BoardFixture(
        "holdout-bottom-index-7", axis_start_index=1, thief_start=(4, 2), cop_start=(1, 6)
    ),
    BoardFixture(
        "holdout-origin-8",
        grid_size=8,
        axis_origin_corner="bottom-left",
        thief_start=(5, 2),
        cop_start=(0, 7),
    ),
    BoardFixture(
        "holdout-dense-10",
        grid_size=10,
        thief_start=(5, 5),
        cop_start=(9, 0),
        max_barriers=25,
        max_moves=40,
        survival_threshold=40,
    ),
)
REHEARSAL_FIXTURES: Final = (BoardFixture("rehearsal-default-7"),)
EVALUATION_SPLITS: Final = ("train", "validation", "holdout")
_FAMILIES: Final = {
    "train": TRAIN_FIXTURES,
    "validation": VALIDATION_FIXTURES,
    "holdout": HOLDOUT_FIXTURES,
    "rehearsal": REHEARSAL_FIXTURES,
}


def fixtures_for(split: str) -> tuple[BoardFixture, ...]:
    """Return the immutable fixture family owned by one split."""
    try:
        return _FAMILIES[split]
    except KeyError as exc:
        raise KeyError(f"unknown fixture split: {split!r}") from exc


def fixture_ids() -> dict[str, tuple[str, ...]]:
    """Return every split's fixture identifiers for manifest declaration."""
    return {split: tuple(item.fixture_id for item in family) for split, family in _FAMILIES.items()}


def disjoint_families() -> bool:
    """Return whether no evaluation fixture identifier or geometry is shared.

    The rehearsal family is excluded on purpose: the dress rehearsal must be played on the
    ordinary negotiated default board, so it deliberately reuses the default geometry.
    """
    families = [family for split, family in _FAMILIES.items() if split in EVALUATION_SPLITS]
    identifiers = [item.fixture_id for family in families for item in family]
    geometries = [
        (item.grid_size, item.thief_start, item.cop_start, item.max_barriers, item.max_moves)
        for family in families
        for item in family
    ]
    all_identifiers = [item.fixture_id for family in _FAMILIES.values() for item in family]
    return (
        len(set(all_identifiers)) == len(all_identifiers)
        and len(set(identifiers)) == len(identifiers)
        and len(set(geometries)) == len(geometries)
    )

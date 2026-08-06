"""Frozen disjoint experiment splits with a one-shot sealed holdout."""

from dataclasses import dataclass
from typing import Final

from police_thief_p2p.services.experiments.fixtures import fixtures_for
from police_thief_p2p.services.experiments.roster import opponent
from police_thief_p2p.shared.canonical_json import sha256_digest

SPLIT_VERSION: Final = "1.0.0"
_DIGEST_LENGTH: Final = 64
TRAIN_SEEDS: Final = tuple(range(10_000, 10_024))
VALIDATION_SEEDS: Final = tuple(range(20_000, 20_016))
HOLDOUT_SEEDS: Final = tuple(range(30_000, 30_012))
REHEARSAL_SEEDS: Final = tuple(range(40_001, 40_007))
TRAIN_OPPONENTS: Final = ("BL-REF", "BL-RND", "BL-SCR")
VALIDATION_OPPONENTS: Final = (
    "BL-POST",
    "BL-ADV-CORNER",
    "BL-ADV-CYCLE",
    "BL-ADV-LIAR",
    "BL-ADV-TRUST",
)
HOLDOUT_OPPONENTS: Final = ("BL-REF", "BL-ADV-BOUNDARY", "BL-ADV-SWITCH", "BL-PREV")
_SEEDS: Final = {
    "train": TRAIN_SEEDS,
    "validation": VALIDATION_SEEDS,
    "holdout": HOLDOUT_SEEDS,
    "rehearsal": REHEARSAL_SEEDS,
}
_OPPONENTS: Final = {
    "train": TRAIN_OPPONENTS,
    "validation": VALIDATION_OPPONENTS,
    "holdout": HOLDOUT_OPPONENTS,
    "rehearsal": ("BL-REF",),
}


@dataclass(frozen=True, slots=True)
class SplitManifest:
    """Immutable versioned declaration of one split's frozen fixture set."""

    split: str
    version: str
    seeds: tuple[int, ...]
    opponent_ids: tuple[str, ...]
    fixture_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        """Validate registered opponents and non-empty frozen collections."""
        if not self.seeds or not self.opponent_ids or not self.fixture_ids:
            raise ValueError("split manifest requires seeds, opponents, and fixtures")
        for identifier in self.opponent_ids:
            opponent(identifier)

    def as_document(self) -> dict[str, object]:
        """Return the canonical serializable split declaration."""
        return {
            "split": self.split,
            "version": self.version,
            "seeds": list(self.seeds),
            "opponent_ids": list(self.opponent_ids),
            "fixture_ids": list(self.fixture_ids),
        }

    def digest(self) -> str:
        """Return the canonical SHA-256 digest binding this split."""
        return sha256_digest(self.as_document())


def split_manifest(split: str) -> SplitManifest:
    """Return the frozen manifest for one declared split."""
    if split not in _SEEDS:
        raise KeyError(f"unknown experiment split: {split!r}")
    return SplitManifest(
        split=split,
        version=SPLIT_VERSION,
        seeds=_SEEDS[split],
        opponent_ids=_OPPONENTS[split],
        fixture_ids=tuple(item.fixture_id for item in fixtures_for(split)),
    )


def seeds_are_disjoint() -> bool:
    """Return whether no seed is shared between any two splits."""
    total = sum(len(values) for values in _SEEDS.values())
    return len({seed for values in _SEEDS.values() for seed in values}) == total


class SealedHoldout:
    """Guard that reveals holdout fixtures only against a candidate freeze."""

    __slots__ = ("_freeze", "_manifest")

    def __init__(self) -> None:
        """Seal the holdout manifest behind an unopened freeze requirement."""
        self._manifest = split_manifest("holdout")
        self._freeze: str | None = None

    @property
    def digest(self) -> str:
        """Return the sealed manifest digest without revealing its contents."""
        return self._manifest.digest()

    @property
    def opened_for(self) -> str | None:
        """Return the freeze digest this seal was opened for, if any."""
        return self._freeze

    def open(self, candidate_freeze_sha256: str) -> SplitManifest:
        """Reveal the holdout exactly once for one frozen candidate digest."""
        if len(candidate_freeze_sha256) != _DIGEST_LENGTH:
            raise ValueError("holdout requires a full candidate freeze digest")
        if self._freeze is not None and self._freeze != candidate_freeze_sha256:
            raise ValueError("sealed holdout was already opened for another candidate")
        self._freeze = candidate_freeze_sha256
        return self._manifest


def assert_tunable(split: str) -> None:
    """Fail closed when tuning code targets the sealed holdout split."""
    if split == "holdout":
        raise ValueError("holdout fixtures cannot be used for tuning or selection")
    if split not in _SEEDS:
        raise KeyError(f"unknown experiment split: {split!r}")

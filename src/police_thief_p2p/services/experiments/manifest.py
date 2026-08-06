"""Reproducibility manifests and the immutable frozen-candidate record."""

import platform
import sys
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Final

from police_thief_p2p.services.experiments.belief_track import BeliefProfile
from police_thief_p2p.services.experiments.profiles import (
    canonical_numbers,
    profile_digest,
    profile_overrides,
)
from police_thief_p2p.services.experiments.resources import ResourceUsage
from police_thief_p2p.services.experiments.splits import split_manifest
from police_thief_p2p.shared.canonical_json import sha256_digest
from police_thief_p2p.shared.strategy_config import StrategyConfig

MANIFEST_VERSION: Final = "1.0.0"


def runtime_facts() -> dict[str, str]:
    """Return the deterministic subset of host and interpreter facts."""
    return {
        "python": sys.version.split()[0],
        "implementation": platform.python_implementation(),
        "platform": platform.system(),
        "machine": platform.machine(),
    }


@dataclass(frozen=True, slots=True)
class CandidateFreeze:
    """One immutable tuned candidate bound to the split it was selected on."""

    candidate_id: str
    strategy: StrategyConfig
    belief: BeliefProfile
    selection_split: str
    selection_objective: float
    trial_id: int

    def __post_init__(self) -> None:
        """Reject a freeze selected on the sealed holdout split."""
        if self.selection_split == "holdout":
            raise ValueError("a candidate cannot be frozen from holdout results")
        split_manifest(self.selection_split)

    def as_document(self) -> dict[str, object]:
        """Return the canonical serializable freeze record."""
        return {
            "candidate_id": self.candidate_id,
            "selection_split": self.selection_split,
            "selection_objective": round(self.selection_objective, 4),
            "trial_id": self.trial_id,
            "strategy_profile_sha256": profile_digest(self.strategy),
            "strategy": profile_overrides(self.strategy),
            "belief": {
                "chase": self.belief.chase,
                "evade": self.belief.evade,
                "boundary": self.belief.boundary,
                "revisit": self.belief.revisit,
                "cycle": self.belief.cycle,
                "hint_ratio_cap": self.belief.hint_ratio_cap,
                "prior_alpha": self.belief.prior_alpha,
                "prior_beta": self.belief.prior_beta,
                "recency": self.belief.recency,
            },
        }

    def digest(self) -> str:
        """Return the canonical digest that seals this candidate."""
        return sha256_digest(canonical_numbers(self.as_document()))


@dataclass(frozen=True, slots=True)
class ReproducibilityManifest:
    """Complete replay record for one experiment campaign."""

    campaign_id: str
    commit_sha: str
    split: str
    freeze: CandidateFreeze
    metrics: Mapping[str, object]
    notes: str = ""
    version: str = MANIFEST_VERSION
    runtime: Mapping[str, str] = field(default_factory=runtime_facts)
    resources: ResourceUsage | None = None

    def as_document(self) -> dict[str, object]:
        """Return the canonical serializable manifest document."""
        split = split_manifest(self.split)
        freeze = self.freeze.as_document()
        return {
            "manifest_version": self.version,
            "campaign_id": self.campaign_id,
            "commit_sha": self.commit_sha,
            "runtime": dict(self.runtime),
            "split": split.as_document(),
            "split_sha256": split.digest(),
            "candidate_freeze_sha256": self.freeze.digest(),
            "candidate": freeze,
            "metrics": dict(self.metrics),
            "resources": None if self.resources is None else self.resources.as_document(),
            "notes": self.notes,
        }

    def digest(self) -> str:
        """Return the canonical digest of the replayable manifest fields."""
        document = self.as_document()
        del document["resources"]
        return sha256_digest(canonical_numbers(document))

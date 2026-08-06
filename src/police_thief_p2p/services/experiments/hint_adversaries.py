"""Adversaries that keep scripted movement but vary only hint honesty."""

from typing import Final

from police_thief_p2p.services.experiments.opponents import BrainFactory, OpponentEntry, entry
from police_thief_p2p.services.strategy.brain import StrategyBrain
from police_thief_p2p.services.strategy.hint_profiles import (
    HintProfile,
    HintProfiledPoliceBrain,
    HintProfiledThiefBrain,
)
from police_thief_p2p.services.strategy.scripted import (
    MaximumDistanceThiefBrain,
    ShortestPathPoliceBrain,
)


def _police(profile: HintProfile) -> BrainFactory:
    def build() -> StrategyBrain:
        return HintProfiledPoliceBrain(ShortestPathPoliceBrain(), profile)

    return build


def _thief(profile: HintProfile) -> BrainFactory:
    def build() -> StrategyBrain:
        return HintProfiledThiefBrain(MaximumDistanceThiefBrain(), profile)

    return build


def _profiled(opponent_id: str, profile: HintProfile, summary: str) -> OpponentEntry:
    return entry(opponent_id, "adversary", _police(profile), _thief(profile), summary)


HINT_ADVERSARIES: Final[tuple[OpponentEntry, ...]] = (
    _profiled(
        "BL-ADV-LIAR",
        HintProfile.ALWAYS_LIE,
        "scripted movement with always-inverted hints",
    ),
    _profiled(
        "BL-ADV-PERIODIC",
        HintProfile.PERIODIC_LIE,
        "scripted movement with periodic hint deception",
    ),
    _profiled(
        "BL-ADV-TRUST",
        HintProfile.TRUST_SWITCH,
        "honest early hints that switch to deception once trusted",
    ),
)

"""Deterministic opponent hint honesty profiles used by experiment adversaries."""

from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Final

from police_thief_p2p.domain.values import Role
from police_thief_p2p.services.strategy.brain import StrategyBrain
from police_thief_p2p.services.strategy.contracts import Decision, HintIntent, HintVerdict
from police_thief_p2p.services.strategy.hints import (
    opposite_region,
    realize_hint,
    semantic_region,
)
from police_thief_p2p.services.strategy.request import StrategyRequest

_PERIOD: Final = 3
_TRUST_SWITCH_STEP: Final = 15


class HintProfile(StrEnum):
    """Declared opponent honesty schedules for hint-robustness experiments."""

    ALWAYS_HONEST = "always-honest"
    ALWAYS_LIE = "always-lie"
    PERIODIC_LIE = "periodic-lie"
    TRUST_SWITCH = "trust-switch"


def lies_at(profile: HintProfile, step_number: int) -> bool:
    """Return whether the profile deceives at one actor step."""
    if step_number < 0:
        raise ValueError("hint profile step must be non-negative")
    if profile is HintProfile.ALWAYS_HONEST:
        return False
    if profile is HintProfile.ALWAYS_LIE:
        return True
    if profile is HintProfile.PERIODIC_LIE:
        return step_number % _PERIOD == 0
    return step_number >= _TRUST_SWITCH_STEP


def profiled_intent(profile: HintProfile, request: StrategyRequest) -> HintIntent:
    """Return the honest or inverted coarse region for the actor's own cell."""
    truthful = semantic_region(request.state.position, request.state.rules.board.size)
    if not lies_at(profile, request.state.step_number):
        return HintIntent(HintVerdict.TRUTH, truthful)
    return HintIntent(HintVerdict.LIE, opposite_region(truthful))


@dataclass(frozen=True, slots=True)
class _HintProfiled(StrategyBrain):
    """Wrap any brain so only its hint honesty schedule changes."""

    inner: StrategyBrain
    profile: HintProfile = HintProfile.ALWAYS_HONEST

    def __post_init__(self) -> None:
        """Reject a wrapped brain declaring a different role."""
        if self.inner.role is not self.role:
            raise ValueError("hint profile wrapper must keep the wrapped brain role")

    def decide(self, request: StrategyRequest) -> Decision:
        """Keep the wrapped movement choice and replace only the hint plan."""
        decision = self.inner.decide(request)
        intent = profiled_intent(self.profile, request)
        return replace(
            decision,
            hint_intent=intent,
            hint=realize_hint(intent, request.map_area, request.hint_max_words),
        )


@dataclass(frozen=True, slots=True)
class HintProfiledPoliceBrain(_HintProfiled):
    """Police wrapper applying one declared honesty schedule."""

    role = Role.POLICE


@dataclass(frozen=True, slots=True)
class HintProfiledThiefBrain(_HintProfiled):
    """Thief wrapper applying one declared honesty schedule."""

    role = Role.THIEF

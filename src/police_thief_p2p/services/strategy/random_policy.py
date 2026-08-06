"""Seeded uniformly random legal policies used as a lower-bound sanity check."""

from police_thief_p2p.domain.values import Role
from police_thief_p2p.services.strategy.adversary_support import (
    movement_candidates,
    packed_decision,
)
from police_thief_p2p.services.strategy.brain import StrategyBrain
from police_thief_p2p.services.strategy.contracts import Decision
from police_thief_p2p.services.strategy.request import StrategyRequest


class RandomLegalPoliceBrain(StrategyBrain):
    """Sample uniformly from every engine-provided legal Police candidate."""

    role = Role.POLICE

    def decide(self, request: StrategyRequest) -> Decision:
        """Choose one legal move, stay, or barrier with the seeded source."""
        candidates = request.legal_actions
        chosen = candidates[request.rng.randbelow(len(candidates))]
        return packed_decision(request, chosen, reason="RANDOM_LEGAL_POLICE")


class RandomLegalThiefBrain(StrategyBrain):
    """Sample uniformly from every engine-provided legal Thief candidate."""

    role = Role.THIEF

    def decide(self, request: StrategyRequest) -> Decision:
        """Choose one legal move or stay with the seeded source."""
        candidates = movement_candidates(request)
        chosen = candidates[request.rng.randbelow(len(candidates))]
        return packed_decision(request, chosen, reason="RANDOM_LEGAL_THIEF")

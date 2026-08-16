"""Stateful hybrid strategy for the thief-first compatibility protocol.

The session consumes only public wire observations. Exact trajectories may
influence later sub-games only after their commitments have passed audit.
"""

from police_thief_p2p.services.strategy.compatibility_decision import _DecisionMixin
from police_thief_p2p.services.strategy.compatibility_filter import _ParticleFilterMixin
from police_thief_p2p.services.strategy.compatibility_graph import _GraphMixin
from police_thief_p2p.services.strategy.compatibility_hints import _HintPolicyMixin
from police_thief_p2p.services.strategy.compatibility_learning import _LearningMixin
from police_thief_p2p.services.strategy.compatibility_lifecycle import _LifecycleMixin
from police_thief_p2p.services.strategy.compatibility_likelihood import _LikelihoodMixin
from police_thief_p2p.services.strategy.compatibility_police import _PolicePolicyMixin
from police_thief_p2p.services.strategy.compatibility_profile import CompatibilityStrategyProfile
from police_thief_p2p.services.strategy.compatibility_thief import _ThiefPolicyMixin


class CompatibilityStrategySession(
    _LifecycleMixin,
    _GraphMixin,
    _LikelihoodMixin,
    _LearningMixin,
    _ParticleFilterMixin,
    _PolicePolicyMixin,
    _ThiefPolicyMixin,
    _HintPolicyMixin,
    _DecisionMixin,
):
    """Six-sub-game strategy state with bounded SMC inference and lookahead."""


__all__ = ["CompatibilityStrategyProfile", "CompatibilityStrategySession"]

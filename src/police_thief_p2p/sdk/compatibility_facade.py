"""SDK factory for the stateful thief-first compatibility strategy."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from police_thief_p2p.services.strategy.compatibility import CompatibilityStrategySession


class CompatibilityStrategyFacade:
    """Expose the compatibility session without leaking adapter internals."""

    def create_compatibility_strategy(
        self,
        terms: Mapping[str, Any],
        strategy: Any = None,
        opponent_id: str = "",
        seed: int = 0,
        *,
        scent_model: str = "multiplicative_kernel_v1",
    ) -> CompatibilityStrategySession:
        """Create one stateful session shared by all six compatibility games."""
        from police_thief_p2p.services.strategy.compatibility import (
            CompatibilityStrategyProfile,
            CompatibilityStrategySession,
        )

        values = _profile_values(strategy)
        profile = CompatibilityStrategyProfile(**values)
        return CompatibilityStrategySession(
            terms,
            profile,
            opponent_id,
            seed,
            scent_model=scent_model,
        )


def _profile_values(strategy: Any) -> dict[str, Any]:
    if strategy is None:
        return {}
    if isinstance(strategy, Mapping):
        source = dict(strategy)
    elif hasattr(strategy, "model_dump"):
        source = strategy.model_dump(mode="python")
    else:
        source = vars(strategy)

    police = _nested(source.get("police"))
    thief = _nested(source.get("thief"))
    hints = _nested(source.get("hints"))
    return {
        key: value
        for key, value in {
            "profile": source.get("profile"),
            "profile_version": source.get("profile_version"),
            "particle_count": source.get("particle_count", source.get("posterior_samples")),
            "observation_sharpness": source.get("observation_sharpness"),
            "opponent_decay": source.get("opponent_decay"),
            "lookahead_depth": source.get("search_horizon"),
            "cvar_tail": source.get("cvar_tail"),
            "near_tie_epsilon": source.get("near_tie_epsilon"),
            "decision_budget_ms": source.get("decision_budget_ms"),
            "police_capture": police.get("capture"),
            "police_pursuit": police.get("distance"),
            "police_intercept": police.get("intercept", police.get("distance")),
            "police_cut": police.get("cut"),
            "police_enclosure": police.get("enclosure", police.get("cut")),
            "police_risk": police.get("risk"),
            "police_budget": police.get("budget"),
            "police_cycle": police.get("cycle"),
            "thief_immediate_risk": thief.get("survival"),
            "thief_territory": thief.get("space"),
            "thief_routes": thief.get("routes"),
            "thief_trap": thief.get("traps"),
            "thief_scent": thief.get("scent"),
            "thief_boundary": thief.get("corner"),
            "thief_unpredictability": thief.get("cycle"),
            "hint_urgency": source.get("hint_urgency", hints.get("trust_threshold")),
            "max_consecutive_lies": hints.get("max_consecutive_lies"),
        }.items()
        if value is not None
    }


def _nested(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "model_dump"):
        return dict(value.model_dump(mode="python"))
    return dict(vars(value))

"""Strict private-only configuration for competitive strategy."""

import re
from typing import Annotated

from pydantic import Field, StrictInt, StrictStr, field_validator, model_validator

from police_thief_p2p.shared.config_sections import FrozenModel
from police_thief_p2p.shared.version import is_semantic_version

_CLASS_NAME = re.compile(
    r"^police_thief_p2p\.services\.strategy\.[a-z_][a-z0-9_]*\."
    r"[A-Z][A-Za-z0-9]{0,79}$"
)

Weight = Annotated[float, Field(ge=0.0, le=10_000.0, allow_inf_nan=False)]


class PoliceWeightsConfig(FrozenModel):
    """Bounded Police feature weights owned only by private TOML."""

    capture: Weight = 1_000.0
    distance: Weight = 5.0
    escape: Weight = 2.0
    cut: Weight = 8.0
    information: Weight = 0.5
    self_trap: Weight = 250.0
    budget: Weight = 1.5
    risk: Annotated[float, Field(ge=0.0, le=1.0, allow_inf_nan=False)] = 0.25
    cycle: Weight = 3.0


class ThiefWeightsConfig(FrozenModel):
    """Bounded Thief feature weights owned only by private TOML."""

    survival: Weight = 1_000.0
    risk_distance: Weight = 8.0
    space: Weight = 1.5
    routes: Weight = 12.0
    entropy: Weight = 0.5
    traps: Weight = 100.0
    scent: Weight = 3.0
    corner: Weight = 8.0
    cycle: Weight = 5.0
    risk: Annotated[float, Field(ge=0.0, le=1.0, allow_inf_nan=False)] = 0.35


class HintPolicyConfig(FrozenModel):
    """Bounded private hint honesty cadence and surface-diversity settings."""

    trust_threshold: Annotated[float, Field(ge=0.0, le=1.0, allow_inf_nan=False)] = 0.55
    max_consecutive_lies: Annotated[StrictInt, Field(ge=1, le=8)] = 2
    deceive_while_mobile: bool = True
    template_variant: Annotated[StrictInt, Field(ge=0, le=1)] = 0


class StrategyConfig(FrozenModel):
    """Private selectors, deterministic seed, search bounds, and typed weights."""

    police_class: StrictStr
    thief_class: StrictStr
    profile: Annotated[StrictStr, Field(pattern=r"^[a-z][a-z0-9-]{0,63}$")]
    profile_version: StrictStr = "1.0.0"
    seed: Annotated[StrictInt, Field(ge=0, le=2_147_483_647)] = 7
    decision_budget_ms: Annotated[StrictInt, Field(ge=20, le=5_000)] = 250
    guard_margin_ms: Annotated[StrictInt, Field(ge=1, le=1_000)] = 40
    search_horizon: Annotated[StrictInt, Field(ge=1, le=8)] = 3
    posterior_samples: Annotated[StrictInt, Field(ge=1, le=256)] = 16
    cache_entries: Annotated[StrictInt, Field(ge=1, le=65_536)] = 512
    near_tie_epsilon: Annotated[float, Field(ge=0.0, le=0.25, allow_inf_nan=False)] = 0.02
    opponent_decay: Annotated[float, Field(gt=0.0, le=1.0, allow_inf_nan=False)] = 0.9
    police: PoliceWeightsConfig = PoliceWeightsConfig()
    thief: ThiefWeightsConfig = ThiefWeightsConfig()
    hints: HintPolicyConfig = HintPolicyConfig()

    @field_validator("police_class", "thief_class")
    @classmethod
    def safe_strategy_class(cls, value: str) -> str:
        """Permit only explicit local strategy modules and class-shaped names."""
        if _CLASS_NAME.fullmatch(value) is None:
            raise ValueError("strategy class is outside the allowlisted local namespace")
        return value

    @field_validator("profile_version")
    @classmethod
    def semantic_profile_version(cls, value: str) -> str:
        """Require a reproducible semantic strategy-profile version."""
        if not is_semantic_version(value):
            raise ValueError("profile_version must be semantic")
        return value

    @model_validator(mode="after")
    def deadline_reserves_guard(self) -> "StrategyConfig":
        """Keep a meaningful persistence/commitment reserve inside the budget."""
        if self.guard_margin_ms >= self.decision_budget_ms:
            raise ValueError("guard_margin_ms must be below decision_budget_ms")
        return self

"""Validated strategy-profile derivation for experiment trials and ablations."""

from collections.abc import Mapping
from dataclasses import fields, replace
from typing import Final

from police_thief_p2p.services.experiments.belief_track import BeliefProfile
from police_thief_p2p.shared.canonical_json import sha256_digest
from police_thief_p2p.shared.strategy_config import StrategyConfig

_NESTED: Final = ("police", "thief", "hints")
_GUARD_SHARE: Final = 4


def derive_profile(base: StrategyConfig, overrides: Mapping[str, object]) -> StrategyConfig:
    """Return a fully revalidated profile with dotted overrides applied."""
    document = base.model_dump(mode="json")
    for key, value in overrides.items():
        section, separator, field = key.partition(".")
        if separator and section in _NESTED:
            nested = dict(document[section])
            if field not in nested:
                raise KeyError(f"unknown strategy weight: {key!r}")
            nested[field] = value
            document[section] = nested
            continue
        if key not in document or separator:
            raise KeyError(f"unknown strategy field: {key!r}")
        document[key] = value
    return StrategyConfig.model_validate(document)


def with_decision_budget(base: StrategyConfig, budget_ms: int) -> StrategyConfig:
    """Return the profile at a declared compute budget with a valid guard margin.

    The guard is at least ``budget // 4`` so search stops early enough to avoid a
    hard ``FALLBACK_DEADLINE`` miss after an expensive deepening step.
    """
    if budget_ms < 2:
        raise ValueError("decision budget must leave room for a positive guard margin")
    floor = max(1, budget_ms // _GUARD_SHARE)
    guard = min(budget_ms - 1, max(base.guard_margin_ms, floor))
    return derive_profile(base, {"decision_budget_ms": budget_ms, "guard_margin_ms": guard})


def canonical_numbers(value: object) -> object:
    """Return the value with every non-integer number as an exact decimal string."""
    if isinstance(value, bool | int) or value is None:
        return value
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, Mapping):
        return {str(key): canonical_numbers(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [canonical_numbers(item) for item in value]
    return value


def profile_digest(config: StrategyConfig) -> str:
    """Return the canonical digest of one strategy profile."""
    return sha256_digest(canonical_numbers(config.model_dump(mode="json")))


def split_point(
    point: Mapping[str, float | int],
) -> tuple[dict[str, object], dict[str, float]]:
    """Split one search point into strategy overrides and belief settings."""
    belief_names = {item.name for item in fields(BeliefProfile)}
    strategy: dict[str, object] = {}
    belief: dict[str, float] = {}
    for key, value in point.items():
        if key in belief_names:
            belief[key] = float(value)
            continue
        strategy[key] = value
    return strategy, belief


def derive_pair(
    base: StrategyConfig,
    point: Mapping[str, float | int],
    belief_base: BeliefProfile,
) -> tuple[StrategyConfig, BeliefProfile]:
    """Return the revalidated strategy profile and belief profile for one point."""
    overrides, belief = split_point(point)
    return derive_profile(base, overrides), replace(belief_base, **belief)


def profile_overrides(config: StrategyConfig) -> dict[str, object]:
    """Return every tunable field of a profile as flat dotted overrides."""
    document = config.model_dump(mode="json")
    flat: dict[str, object] = {}
    for key, value in document.items():
        if key in _NESTED and isinstance(value, Mapping):
            flat.update({f"{key}.{name}": item for name, item in value.items()})
            continue
        flat[key] = value
    return flat

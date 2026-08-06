"""Bounded declared hyperparameter spaces for Police, Thief, belief, and hints."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from police_thief_p2p.services.ports.random_source import RandomSource


@dataclass(frozen=True, slots=True)
class Dimension:
    """One bounded numeric or ordinal search dimension."""

    name: str
    low: float
    high: float
    integer: bool = False

    def __post_init__(self) -> None:
        """Reject inverted or degenerate bounds."""
        if self.high < self.low:
            raise ValueError(f"dimension {self.name} has inverted bounds")
        if self.integer and (self.low != int(self.low) or self.high != int(self.high)):
            raise ValueError(f"integer dimension {self.name} needs integral bounds")

    def sample(self, rng: RandomSource) -> float | int:
        """Draw one uniformly random value inside the declared bounds."""
        if self.integer:
            span = int(self.high) - int(self.low) + 1
            return int(self.low) + rng.randbelow(span)
        return self.low + (self.high - self.low) * rng.random()

    def clamp(self, value: float) -> float | int:
        """Return the value projected back inside the declared bounds."""
        bounded = min(self.high, max(self.low, value))
        return round(bounded) if self.integer else bounded


POLICE_SPACE: Final = (
    Dimension("police.capture", 500.0, 2_000.0),
    Dimension("police.distance", 1.0, 20.0),
    Dimension("police.cut", 0.0, 30.0),
    Dimension("police.information", 0.0, 5.0),
    Dimension("police.budget", 0.0, 6.0),
    Dimension("police.risk", 0.0, 0.6),
    Dimension("search_horizon", 2, 4, integer=True),
    Dimension("posterior_samples", 8, 32, integer=True),
)
THIEF_SPACE: Final = (
    Dimension("thief.survival", 500.0, 2_000.0),
    Dimension("thief.risk_distance", 1.0, 25.0),
    Dimension("thief.space", 0.0, 8.0),
    Dimension("thief.routes", 0.0, 30.0),
    Dimension("thief.entropy", 0.0, 5.0),
    Dimension("thief.scent", 0.0, 12.0),
    Dimension("thief.corner", 0.0, 25.0),
    Dimension("thief.cycle", 0.0, 15.0),
    Dimension("thief.risk", 0.0, 0.7),
)
BELIEF_SPACE: Final = (
    Dimension("chase", 0.0, 1.0),
    Dimension("evade", 0.0, 1.5),
    Dimension("boundary", 0.0, 0.6),
    Dimension("revisit", 0.0, 0.6),
    Dimension("cycle", 0.0, 0.6),
    Dimension("hint_ratio_cap", 1.0, 6.0),
    Dimension("prior_alpha", 1.0, 6.0),
    Dimension("prior_beta", 1.0, 6.0),
    Dimension("recency", 0.7, 1.0),
)
HINT_SPACE: Final = (
    Dimension("hints.trust_threshold", 0.2, 0.9),
    Dimension("hints.max_consecutive_lies", 1, 4, integer=True),
    Dimension("hints.template_variant", 0, 1, integer=True),
)
_SPACES: Final[Mapping[str, tuple[Dimension, ...]]] = MappingProxyType(
    {
        "police": POLICE_SPACE,
        "thief": THIEF_SPACE,
        "belief": BELIEF_SPACE,
        "hint": HINT_SPACE,
    }
)


def space(name: str) -> tuple[Dimension, ...]:
    """Return one declared search space by name."""
    try:
        return _SPACES[name]
    except KeyError as exc:
        raise KeyError(f"unknown search space: {name!r}") from exc


def strategy_dimensions() -> tuple[Dimension, ...]:
    """Return every dimension owned by the private strategy profile."""
    return (*POLICE_SPACE, *THIEF_SPACE, *HINT_SPACE)


def sample_point(
    dimensions: Sequence[Dimension],
    rng: RandomSource,
) -> dict[str, float | int]:
    """Draw one uniformly random configuration from a space."""
    return {item.name: item.sample(rng) for item in dimensions}


def clamp_point(
    dimensions: Sequence[Dimension],
    point: Mapping[str, float],
) -> dict[str, float | int]:
    """Project one candidate point back into every declared bound."""
    index = {item.name: item for item in dimensions}
    return {name: index[name].clamp(value) for name, value in point.items() if name in index}


def space_document() -> dict[str, list[dict[str, object]]]:
    """Return the serializable declaration of every search space."""
    return {
        name: [
            {
                "name": item.name,
                "low": item.low,
                "high": item.high,
                "integer": item.integer,
            }
            for item in dimensions
        ]
        for name, dimensions in _SPACES.items()
    }

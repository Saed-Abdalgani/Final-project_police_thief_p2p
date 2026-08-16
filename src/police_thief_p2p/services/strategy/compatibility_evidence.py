"""Particle and opponent-evidence support for compatibility strategy."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Final

from police_thief_p2p.services.strategy.compatibility_scent import Cell, Grid

FAMILIES: Final[tuple[str, ...]] = (
    "containment",
    "velocity-intercept",
    "open-space",
    "risk-juke",
    "boundary",
    "cycle",
    "aggressive-barrier",
    "random",
)


@dataclass(slots=True)
class Particle:
    """One bounded opponent path and scent hypothesis."""

    position: Cell
    previous: Cell
    scent: Grid
    heading: Cell
    family: str
    weight: float


@dataclass(slots=True)
class Evidence:
    """Behavioral counts derived from public or successfully audited actions."""

    moves: int = 0
    straight: int = 0
    turns: int = 0
    reversals: int = 0
    stays: int = 0
    boundary: int = 0
    revisits: int = 0
    barriers: int = 0
    position_counts: Counter[Cell] = field(default_factory=Counter)
    last_heading: Cell | None = None


def normalize(values: Mapping[Any, float]) -> dict[Any, float]:
    """Normalize finite non-negative masses, falling back to uniform."""
    total = sum(values.values())
    if total <= 0.0:
        weight = 1.0 / max(1, len(values))
        return {key: weight for key in values}
    return {key: value / total for key, value in values.items()}


def weighted_lower_tail(values: Sequence[tuple[float, float]], tail: float) -> float:
    """Return lower-tail conditional value at risk."""
    remaining = tail
    result = 0.0
    for value, probability in sorted(values):
        take = min(remaining, probability)
        result += value * take
        remaining -= take
        if remaining <= 1e-12:
            break
    if remaining > 0.0:
        result += min(value for value, _ in values) * remaining
    return result / tail


def add_evidence(evidence: Evidence, previous: Cell, current: Cell, size: int) -> None:
    """Update movement-shape evidence from one exact or inferred transition."""
    evidence.moves += 1
    evidence.position_counts[current] += 1
    heading = (current[0] - previous[0], current[1] - previous[1])
    evidence.stays += int(heading == (0, 0))
    evidence.boundary += int(current[0] in {0, size - 1} or current[1] in {0, size - 1})
    evidence.revisits += int(evidence.position_counts[current] > 1)
    if evidence.last_heading is not None and heading != (0, 0):
        evidence.straight += int(heading == evidence.last_heading)
        evidence.turns += int(heading != evidence.last_heading)
        evidence.reversals += int(heading == (-evidence.last_heading[0], -evidence.last_heading[1]))
    if heading != (0, 0):
        evidence.last_heading = heading


def evidence_mixture(evidence: Evidence) -> dict[str, float]:
    """Convert bounded evidence counts into an archetype mixture."""
    moves = max(1, evidence.moves)
    raw = {
        "containment": 1.0 + 2.0 * evidence.stays / moves + evidence.barriers / moves,
        "velocity-intercept": 1.0 + 2.0 * evidence.straight / moves,
        "open-space": 1.0 + max(0.0, 1.0 - evidence.boundary / moves),
        "risk-juke": 1.0 + 2.0 * evidence.turns / moves + evidence.reversals / moves,
        "boundary": 1.0 + 3.0 * evidence.boundary / moves,
        "cycle": 1.0 + 3.0 * evidence.revisits / moves,
        "aggressive-barrier": 1.0 + 5.0 * evidence.barriers / moves,
        "random": 1.0 + min(1.0, (evidence.turns + evidence.stays) / moves),
    }
    return normalize(raw)

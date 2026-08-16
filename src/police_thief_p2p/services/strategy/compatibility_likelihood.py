"""Bounded behavior-transition and hint likelihoods for particles."""

from __future__ import annotations

from typing import Any

from police_thief_p2p.services.strategy.compatibility_hints import REGION_CENTRES, region
from police_thief_p2p.services.strategy.compatibility_scent import Cell


class _LikelihoodMixin:
    """Score archetype transitions and parser-safe coarse hints."""

    def _transition_likelihood(
        self: Any, family: str, previous: Cell, current: Cell, old_heading: Cell
    ) -> float:
        heading = (current[0] - previous[0], current[1] - previous[1])
        straight = heading == old_heading and heading != (0, 0)
        reversal = heading == (-old_heading[0], -old_heading[1]) and heading != (0, 0)
        boundary = self._boundary_penalty(current) > 0
        base = 0.20
        if family == "velocity-intercept":
            base += 0.55 * straight + 0.10 * (not reversal)
        elif family == "risk-juke":
            base += 0.40 * (not straight) + 0.20 * (not reversal)
        elif family == "boundary":
            base += 0.55 * boundary
        elif family == "cycle":
            base += 0.45 * (current in self._live_evidence.position_counts)
        elif family == "open-space":
            base += 0.12 * self._degree(current)
        elif family in {"containment", "aggressive-barrier"}:
            base += 0.20 * (current == previous)
        else:
            base += 0.25
        return float(max(0.05, base) * self._mixture.get(family, 0.01))

    def _hint_likelihood(self: Any, hint: str, cell: Cell) -> float:
        text = hint.lower()
        mentioned = region(cell, self.size).replace("-", " ") in text
        trust = min(0.75, max(0.25, self._hint_reliability))
        if mentioned:
            return float(0.75 + trust)
        if any(name.replace("-", " ") in text for name in REGION_CENTRES):
            return float(max(0.5, 1.25 - trust))
        return 1.0

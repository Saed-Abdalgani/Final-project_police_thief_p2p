"""Bounded lawful coarse-region hint deception."""

from __future__ import annotations

from typing import Any, Final

from police_thief_p2p.services.strategy.compatibility_graph import manhattan
from police_thief_p2p.services.strategy.compatibility_scent import Cell

REGION_CENTRES: Final[dict[str, Any]] = {
    "north-west": lambda size: (0, 0),
    "north": lambda size: (0, size // 2),
    "north-east": lambda size: (0, size - 1),
    "west": lambda size: (size // 2, 0),
    "central": lambda size: (size // 2, size // 2),
    "east": lambda size: (size // 2, size - 1),
    "south-west": lambda size: (size - 1, 0),
    "south": lambda size: (size - 1, size // 2),
    "south-east": lambda size: (size - 1, size - 1),
}


class _HintPolicyMixin:
    """Supply valid coarse hints with explicit truth/lie intent."""

    def _choose_hint(self: Any, hint_position: Cell) -> tuple[str, str]:
        actual = region(hint_position, self.size)
        posterior = self._posterior()
        urgency = max(max(posterior.values(), default=0.0), 1.0 - self._degree(hint_position) / 4.0)
        can_lie = self._consecutive_lies < self.profile.max_consecutive_lies
        if can_lie and urgency >= self.profile.hint_urgency:
            choices = [name for name in REGION_CENTRES if name != actual]
            decoy = max(
                choices,
                key=lambda name: sum(
                    probability * manhattan(REGION_CENTRES[name](self.size), cell)
                    for cell, probability in posterior.items()
                ),
            )
            hint = f"Activity seems near the {decoy.replace('-', ' ')} {self.setting} district"
            self._consecutive_lies += 1
            return limit_words(hint, self.hint_max_words), "lie"
        self._consecutive_lies = 0
        hint = f"Movement remains in the {actual.replace('-', ' ')} {self.setting} district"
        return limit_words(hint, self.hint_max_words), "truth"


def limit_words(text: str, maximum: int) -> str:
    """Enforce the negotiated hint word cap."""
    return " ".join(text.split()[:maximum])


def region(cell: Cell, size: int) -> str:
    """Map one cell to a coarse three-by-three semantic region."""
    third = max(1, size // 3)
    vertical = "north" if cell[0] < third else "south" if cell[0] >= size - third else "central"
    horizontal = "west" if cell[1] < third else "east" if cell[1] >= size - third else "central"
    if vertical == horizontal == "central":
        return "central"
    if vertical == "central":
        return horizontal
    if horizontal == "central":
        return vertical
    return f"{vertical}-{horizontal}"

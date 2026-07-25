"""Locale-safe deterministic semantic cue parser."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from police_thief_p2p.services.ports.hint_parser import SemanticHintEvidence

_PROHIBITED = re.compile(
    r"(?i)(?:\d|[\[\]{}]|https?://|ignore\s+previous|system\s+prompt|"
    r"\b(?:api|mcp|tool|coordinate|row|column|execute|password|token)\b)"
)
_WORDS = re.compile(r"[a-z]+", re.ASCII)


class CueCategory(StrEnum):
    """Supported coarse spatial semantics."""

    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
    CENTER = "center"
    EDGE = "edge"
    CORNER = "corner"
    NEUTRAL = "neutral"


_CUES: tuple[tuple[CueCategory, frozenset[str]], ...] = (
    (CueCategory.NORTH, frozenset({"north", "upper", "above", "top"})),
    (CueCategory.SOUTH, frozenset({"south", "lower", "below", "bottom"})),
    (CueCategory.EAST, frozenset({"east", "right"})),
    (CueCategory.WEST, frozenset({"west", "left"})),
    (CueCategory.CENTER, frozenset({"center", "central", "middle"})),
    (CueCategory.CORNER, frozenset({"corner", "corners"})),
    (CueCategory.EDGE, frozenset({"edge", "border", "boundary"})),
)


@dataclass(frozen=True, slots=True)
class TemplateCueParser:
    """Parse one coarse cue; ambiguous or injection-like text is neutral."""

    max_words: int = 15
    raw_ratio: float = 2.0

    def __post_init__(self) -> None:
        """Validate parser word and ratio bounds."""
        if self.max_words < 1 or not 1 <= self.raw_ratio <= 3:
            raise ValueError("hint parser bounds are invalid")

    def parse(self, text: str, board_size: int) -> SemanticHintEvidence:
        """Return row-major likelihoods without interpreting commands."""
        if board_size < 1:
            raise ValueError("hint board size must be positive")
        words = _WORDS.findall(text.casefold())
        if not words or len(words) > self.max_words or _PROHIBITED.search(text):
            return _neutral(board_size)
        matched = [category for category, cues in _CUES if cues.intersection(words)]
        if len(matched) != 1:
            return _neutral(board_size)
        category = matched[0]
        values = tuple(
            self.raw_ratio if _matches(category, row, col, board_size) else 1.0
            for row in range(board_size)
            for col in range(board_size)
        )
        return SemanticHintEvidence(category.value, values, False)


def _matches(category: CueCategory, row: int, col: int, size: int) -> bool:
    midpoint = (size - 1) / 2
    third = max(1, size // 3)
    return {
        CueCategory.NORTH: row < third,
        CueCategory.SOUTH: row >= size - third,
        CueCategory.WEST: col < third,
        CueCategory.EAST: col >= size - third,
        CueCategory.CENTER: abs(row - midpoint) <= 1 and abs(col - midpoint) <= 1,
        CueCategory.EDGE: row in {0, size - 1} or col in {0, size - 1},
        CueCategory.CORNER: row in {0, size - 1} and col in {0, size - 1},
        CueCategory.NEUTRAL: False,
    }[category]


def _neutral(board_size: int) -> SemanticHintEvidence:
    return SemanticHintEvidence(CueCategory.NEUTRAL.value, (1.0,) * (board_size**2), True)

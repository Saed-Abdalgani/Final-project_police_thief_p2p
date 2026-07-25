"""Movement-independent, zero-token semantic hint policy."""

import re
import unicodedata
from dataclasses import dataclass

from police_thief_p2p.domain.values import Position
from police_thief_p2p.services.strategy.contracts import (
    BehaviorMode,
    HintIntent,
    HintVerdict,
    SemanticRegion,
)

_WORDS = re.compile(r"[^\W\d_]+(?:['-][^\W\d_]+)?", re.UNICODE)
_NUMBER_OR_COORDINATE = re.compile(
    r"(?i)(?:\d|[\[\]{}]|(?:row|column|coordinate|latitude|longitude)\b)"
)
_OPPOSITE = {
    SemanticRegion.NORTH: SemanticRegion.SOUTH,
    SemanticRegion.SOUTH: SemanticRegion.NORTH,
    SemanticRegion.EAST: SemanticRegion.WEST,
    SemanticRegion.WEST: SemanticRegion.EAST,
    SemanticRegion.CENTER: SemanticRegion.EDGE,
    SemanticRegion.EDGE: SemanticRegion.CENTER,
    SemanticRegion.CORNER: SemanticRegion.CENTER,
    SemanticRegion.NEUTRAL: SemanticRegion.EDGE,
}
_PHRASES = {
    SemanticRegion.NORTH: "under the quiet northern sky",
    SemanticRegion.SOUTH: "where the southern streets feel warmer",
    SemanticRegion.EAST: "toward the bright eastern side",
    SemanticRegion.WEST: "among the shaded western paths",
    SemanticRegion.CENTER: "near the busy central landmarks",
    SemanticRegion.EDGE: "close to the outer boundary",
    SemanticRegion.CORNER: "near a secluded corner",
    SemanticRegion.NEUTRAL: "somewhere among the open paths",
}


def semantic_region(position: Position, size: int) -> SemanticRegion:
    """Classify a true own cell into a coarse, non-numeric region."""
    edge_row = position.row in {0, size - 1}
    edge_col = position.col in {0, size - 1}
    if edge_row and edge_col:
        return SemanticRegion.CORNER
    if edge_row or edge_col:
        return SemanticRegion.EDGE
    third = max(1, size // 3)
    if position.row < third:
        return SemanticRegion.NORTH
    if position.row >= size - third:
        return SemanticRegion.SOUTH
    if position.col < third:
        return SemanticRegion.WEST
    if position.col >= size - third:
        return SemanticRegion.EAST
    return SemanticRegion.CENTER


def count_words(text: str) -> int:
    """Count Unicode letter words; punctuation and emoji are not words."""
    return len(_WORDS.findall(unicodedata.normalize("NFC", text)))


def cap_words(text: str, maximum: int) -> str:
    """Normalize and truncate after the negotiated Unicode-aware word cap."""
    if maximum < 1:
        raise ValueError("hint word cap must be positive")
    normalized = " ".join(unicodedata.normalize("NFC", text).split())
    matches = list(_WORDS.finditer(normalized))
    if not matches:
        raise ValueError("hint must contain natural-language words")
    if len(matches) <= maximum:
        return normalized
    return normalized[: matches[maximum - 1].end()].rstrip(" ,;:-")


def realize_hint(intent: HintIntent, map_area: str, maximum: int) -> str:
    """Render a deterministic map-aware template and enforce the final cap."""
    area_words = _WORDS.findall(map_area)
    prefix = f"Around {' '.join(area_words[:4])}, " if area_words else ""
    hint = f"{prefix}I am {_PHRASES[intent.region]}."
    if _NUMBER_OR_COORDINATE.search(hint):
        raise ValueError("hint templates cannot encode coordinates")
    return cap_words(hint, maximum)


@dataclass(frozen=True, slots=True)
class HintIntentPolicy:
    """Schedule plausible deception from trust, safety mode, and prior verdicts."""

    def choose(
        self,
        position: Position,
        size: int,
        *,
        trust: float,
        mode: BehaviorMode,
        prior_verdicts: tuple[HintVerdict, ...] = (),
    ) -> HintIntent:
        """Choose truth/lie separately from movement and surface wording."""
        truthful = semantic_region(position, size)
        repeated_lies = len(prior_verdicts) >= 2 and all(
            verdict is HintVerdict.LIE for verdict in prior_verdicts[-2:]
        )
        safe_to_deceive = mode in {BehaviorMode.DECEPTION, BehaviorMode.MOBILITY}
        lie = trust >= 0.55 and safe_to_deceive and not repeated_lies
        if lie:
            return HintIntent(HintVerdict.LIE, _OPPOSITE[truthful])
        return HintIntent(HintVerdict.TRUTH, truthful)

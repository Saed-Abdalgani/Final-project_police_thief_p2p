"""Port for bounded semantic hint likelihoods, never commands."""

import math
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class SemanticHintEvidence:
    """Category and row-major bounded likelihood ratios."""

    category: str
    likelihoods: tuple[float, ...]
    neutral: bool

    def __post_init__(self) -> None:
        """Reject empty, non-finite, or non-positive semantic evidence."""
        if (
            not self.category
            or not self.likelihoods
            or any(not math.isfinite(value) or value <= 0 for value in self.likelihoods)
        ):
            raise ValueError("semantic hint evidence must be finite and positive")


@runtime_checkable
class HintParserPort(Protocol):
    """Parse natural language into bounded semantic evidence."""

    def parse(self, text: str, board_size: int) -> SemanticHintEvidence:
        """Return likelihood evidence without actions, tools, or coordinates."""
        ...

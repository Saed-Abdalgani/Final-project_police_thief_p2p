"""Coordinate-origin conversion for signed board configurations."""

from dataclasses import dataclass
from enum import StrEnum


class OriginCorner(StrEnum):
    """Supported external coordinate origins."""

    TOP_LEFT = "top-left"
    TOP_RIGHT = "top-right"
    BOTTOM_LEFT = "bottom-left"
    BOTTOM_RIGHT = "bottom-right"


@dataclass(frozen=True, slots=True)
class Position:
    """Canonical zero-based position measured from the top-left."""

    row: int
    col: int

    def __post_init__(self) -> None:
        """Require integer semantics while leaving board bounds contextual."""
        if any(
            isinstance(value, bool) or not isinstance(value, int) for value in (self.row, self.col)
        ):
            raise TypeError("position row and column must be integers")


@dataclass(frozen=True, slots=True)
class CoordinateTransform:
    """Bidirectional transform between external and canonical coordinates."""

    grid_size: int
    origin: OriginCorner
    start_index: int

    def __post_init__(self) -> None:
        """Reject unusable board conventions."""
        if self.grid_size < 1:
            raise ValueError("grid_size must be positive")
        if self.start_index not in (0, 1):
            raise ValueError("start_index must be 0 or 1")

    def to_canonical(self, coordinate: tuple[int, int]) -> Position:
        """Convert an external coordinate to canonical top-left zero-based form."""
        row, col = (part - self.start_index for part in coordinate)
        if not 0 <= row < self.grid_size or not 0 <= col < self.grid_size:
            raise ValueError("coordinate is outside the configured board")
        if self.origin in (OriginCorner.BOTTOM_LEFT, OriginCorner.BOTTOM_RIGHT):
            row = self.grid_size - 1 - row
        if self.origin in (OriginCorner.TOP_RIGHT, OriginCorner.BOTTOM_RIGHT):
            col = self.grid_size - 1 - col
        return Position(row=row, col=col)

    def from_canonical(self, position: Position) -> tuple[int, int]:
        """Convert a canonical position to the configured external convention."""
        if not 0 <= position.row < self.grid_size or not 0 <= position.col < self.grid_size:
            raise ValueError("canonical position is outside the configured board")
        row, col = position.row, position.col
        if self.origin in (OriginCorner.BOTTOM_LEFT, OriginCorner.BOTTOM_RIGHT):
            row = self.grid_size - 1 - row
        if self.origin in (OriginCorner.TOP_RIGHT, OriginCorner.BOTTOM_RIGHT):
            col = self.grid_size - 1 - col
        return row + self.start_index, col + self.start_index

"""Immutable normalized belief distribution and diagnostics."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final

from police_thief_p2p.domain.board import EMPTY_BARRIERS, BarrierSet, Board
from police_thief_p2p.domain.values import Position
from police_thief_p2p.shared.canonical_json import sha256_digest

NORMALIZATION_TOLERANCE: Final = 1e-12
MAX_BELIEF_CELLS: Final = 1_000_000


@dataclass(frozen=True, slots=True)
class BeliefGrid:
    """Finite non-negative normalized probability for each board cell."""

    size: int
    probabilities: tuple[float, ...]
    masked: frozenset[Position] = frozenset()

    def __post_init__(self) -> None:
        """Enforce dimensions, masks, finiteness, and normalization."""
        if self.size < 1 or self.size * self.size > MAX_BELIEF_CELLS:
            raise ValueError("belief dimensions are outside the bounded range")
        if len(self.probabilities) != self.size * self.size:
            raise ValueError("belief probability count differs from dimensions")
        if any(not math.isfinite(value) or value < 0 for value in self.probabilities):
            raise ValueError("belief values must be finite and non-negative")
        if any(not self._contains(cell) or self.probability(cell) != 0 for cell in self.masked):
            raise ValueError("masked belief cells must be on-board and zero")
        if not math.isclose(
            math.fsum(self.probabilities),
            1.0,
            rel_tol=0.0,
            abs_tol=NORMALIZATION_TOLERANCE,
        ):
            raise ValueError("belief probabilities must be normalized")

    @classmethod
    def from_weights(
        cls,
        size: int,
        weights: dict[Position, float],
        *,
        masked: frozenset[Position] = frozenset(),
    ) -> BeliefGrid:
        """Normalize finite non-negative weights in deterministic row-major order."""
        if size < 1 or size * size > MAX_BELIEF_CELLS:
            raise ValueError("belief dimensions are outside the bounded range")
        if any(not math.isfinite(value) or value < 0 for value in weights.values()):
            raise ValueError("belief weights must be finite and non-negative")
        cells = tuple(Position(row, col) for row in range(size) for col in range(size))
        values = [0.0 if cell in masked else weights.get(cell, 0.0) for cell in cells]
        total = math.fsum(values)
        if total <= 0:
            legal = [cell for cell in cells if cell not in masked]
            if not legal:
                raise ValueError("belief has no reachable legal cell")
            uniform = 1.0 / len(legal)
            values = [uniform if cell in legal else 0.0 for cell in cells]
        else:
            values = [value / total for value in values]
        correction = 1.0 - math.fsum(values)
        index = max(range(len(values)), key=values.__getitem__)
        values[index] += correction
        return cls(size, tuple(values), masked)

    @classmethod
    def uniform(
        cls,
        board: Board,
        barriers: BarrierSet = EMPTY_BARRIERS,
        reachable: frozenset[Position] | None = None,
    ) -> BeliefGrid:
        """Create a uniform prior over reachable non-barrier cells."""
        allowed = frozenset(board.cells()) if reachable is None else reachable
        masked = frozenset(
            cell for cell in board.cells() if cell not in allowed or cell in barriers
        )
        return cls.from_weights(board.size, {cell: 1.0 for cell in allowed}, masked=masked)

    def probability(self, position: Position) -> float:
        """Return one cell probability."""
        if not self._contains(position):
            raise ValueError("belief position is outside board")
        return self.probabilities[position.row * self.size + position.col]

    def items(self) -> tuple[tuple[Position, float], ...]:
        """Return deterministic row-major cells and probabilities."""
        return tuple(
            (Position(index // self.size, index % self.size), value)
            for index, value in enumerate(self.probabilities)
        )

    def remask(self, masked: frozenset[Position]) -> BeliefGrid:
        """Zero newly impossible cells and renormalize or recover uniformly."""
        return self.from_weights(
            self.size,
            dict(self.items()),
            masked=self.masked | masked,
        )

    def entropy_bits(self) -> float:
        """Return Shannon entropy in bits."""
        return -math.fsum(value * math.log2(value) for value in self.probabilities if value > 0)

    def most_likely(self) -> Position:
        """Return the deterministic diagnostic argmax."""
        return min(self.items(), key=lambda item: (-item[1], item[0].row, item[0].col))[0]

    def credible_region(self, target: float = 0.9) -> tuple[Position, ...]:
        """Return the smallest deterministic cell prefix reaching target mass."""
        if not 0 < target <= 1:
            raise ValueError("credible target must be in (0, 1]")
        ordered = sorted(self.items(), key=lambda item: (-item[1], item[0].row, item[0].col))
        selected = []
        cumulative = 0.0
        for cell, value in ordered:
            if value <= 0:
                continue
            selected.append(cell)
            cumulative += value
            if cumulative + NORMALIZATION_TOLERANCE >= target:
                break
        return tuple(selected)

    def serialized(self, decimal_places: int = 12) -> tuple[str, ...]:
        """Quantize only at a diagnostic/audit boundary."""
        return tuple(f"{value:.{decimal_places}f}" for value in self.probabilities)

    def digest(self) -> str:
        """Return a cross-platform quantized diagnostic digest."""
        return sha256_digest({"size": self.size, "probabilities": self.serialized()})

    def _contains(self, position: Position) -> bool:
        return 0 <= position.row < self.size and 0 <= position.col < self.size


def reachable_cells(
    board: Board,
    start: Position,
    barriers: BarrierSet = EMPTY_BARRIERS,
) -> frozenset[Position]:
    """Return the deterministic connected legal component containing start."""
    if not board.contains(start) or start in barriers:
        return frozenset()
    seen = {start}
    frontier = [start]
    while frontier:
        current = frontier.pop()
        for neighbor in board.neighbors(current, barriers):
            if neighbor not in seen:
                seen.add(neighbor)
                frontier.append(neighbor)
    return frozenset(seen)

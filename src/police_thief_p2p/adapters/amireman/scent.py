"""Fixed 5x5 radial scent kernel and additive update (amireman wire)."""

from __future__ import annotations

from typing import Final

Cell = tuple[int, int]
Grid = dict[Cell, float]
MAX_INTENSITY: Final = 0.9
KERNEL: Final[dict[tuple[int, int], float]] = {
    (0, 0): 0.90,
    (0, 1): 0.62,
    (1, 0): 0.62,
    (1, 1): 0.42,
    (0, 2): 0.20,
    (2, 0): 0.20,
    (1, 2): 0.14,
    (2, 1): 0.14,
    (2, 2): 0.04,
}


def _in_bounds(cell: Cell, size: int) -> bool:
    return 0 <= cell[0] < size and 0 <= cell[1] < size


def emission_delta(centre: Cell, size: int) -> Grid:
    """5x5 kernel around centre, clipped to the board."""
    delta: Grid = {}
    for dr in range(-2, 3):
        for dc in range(-2, 3):
            cell = (centre[0] + dr, centre[1] + dc)
            if _in_bounds(cell, size):
                delta[cell] = KERNEL[(abs(dr), abs(dc))]
    return delta


def step_update(grid: Grid, centre: Cell, size: int, rho: float) -> Grid:
    """tau_next = min(0.9, max(0, (1-rho)*tau_old + delta))."""
    delta = emission_delta(centre, size)
    out: Grid = {}
    for cell in set(grid) | set(delta):
        value = max(0.0, (1.0 - rho) * grid.get(cell, 0.0) + delta.get(cell, 0.0))
        value = min(MAX_INTENSITY, value)
        if value > 1e-9:
            out[cell] = value
    return out


def grid_out(grid: Grid) -> dict[str, float]:
    """Wire shape {"r,c": intensity}."""
    return {f"{row},{col}": value for (row, col), value in grid.items()}


def grid_in(data: dict[str, float] | None) -> Grid:
    """Parse wire smell_grid into cell tuples."""
    out: Grid = {}
    for key, value in (data or {}).items():
        row_text, col_text = str(key).split(",")
        out[(int(row_text), int(col_text))] = float(value)
    return out

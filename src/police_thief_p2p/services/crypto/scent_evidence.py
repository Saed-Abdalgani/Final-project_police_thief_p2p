"""Deterministic clipped scent evidence for audit-bound commitments."""

from dataclasses import dataclass

from police_thief_p2p.domain.values import Position
from police_thief_p2p.shared.canonical_json import sha256_digest
from police_thief_p2p.shared.scent import KERNEL_TEXT, ScentPolicy


def scent_model_digest(policy: ScentPolicy) -> str:
    """Bind the exact formula, kernel, decimal, and decay policy."""
    return sha256_digest(
        {
            "formula": "center_intensity * kernel_weight",
            "kernel": KERNEL_TEXT,
            "center_intensity": str(policy.center_intensity),
            "decay": str(policy.decay),
            "decimal_places": policy.decimal_places,
            "rounding": policy.rounding.value,
            "numeric_example": {
                "center": str(policy.quantize(policy.center_intensity)),
                "after_full_turn": str(policy.after_full_turn(policy.center_intensity)),
            },
        }
    )


@dataclass(frozen=True, slots=True)
class ScentFrame:
    """Sparse row-major scent emission clipped to one board."""

    cells: tuple[tuple[int, int, str], ...]

    def digest(self) -> str:
        """Return the canonical evidence digest."""
        return sha256_digest({"cells": self.cells})


def scent_frame(board_size: int, position: Position, policy: ScentPolicy) -> ScentFrame:
    """Emit the signed 5x5 kernel centered on local truth without wraparound."""
    if board_size < 1 or not 0 <= position.row < board_size or not 0 <= position.col < board_size:
        raise ValueError("scent origin must be on a positive board")
    emission = policy.emission()
    cells = []
    for kernel_row, row in enumerate(emission):
        for kernel_col, value in enumerate(row):
            board_row = position.row + kernel_row - 2
            board_col = position.col + kernel_col - 2
            if 0 <= board_row < board_size and 0 <= board_col < board_size:
                cells.append((board_row, board_col, format(value, "f")))
    return ScentFrame(tuple(cells))

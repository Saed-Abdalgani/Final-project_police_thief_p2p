"""Exact sparse scent accumulation and full-turn decay."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from police_thief_p2p.domain.values import Position, Role
from police_thief_p2p.services.belief.models import OpponentScentFrame, ScentCell
from police_thief_p2p.shared.scent import ScentPolicy


@dataclass(frozen=True, slots=True)
class ScentField:
    """Sparse exact-decimal field with values clamped to one."""

    board_size: int
    entries: tuple[tuple[Position, Decimal], ...] = ()

    def __post_init__(self) -> None:
        """Validate sparse field identity, bounds, and range."""
        if self.board_size < 1:
            raise ValueError("scent board size must be positive")
        positions = {position for position, _ in self.entries}
        if len(positions) != len(self.entries):
            raise ValueError("scent field positions must be unique")
        if any(
            not 0 <= position.row < self.board_size
            or not 0 <= position.col < self.board_size
            or not value.is_finite()
            or not Decimal(0) <= value <= Decimal(1)
            for position, value in self.entries
        ):
            raise ValueError("scent field entry is invalid")

    def value_at(self, position: Position) -> Decimal:
        """Return one exact value or zero."""
        return dict(self.entries).get(position, Decimal(0))

    def emit(self, position: Position, policy: ScentPolicy) -> ScentField:
        """Accumulate one clipped 5x5 emission and clamp each cell to one."""
        if not 0 <= position.row < self.board_size or not 0 <= position.col < self.board_size:
            raise ValueError("scent origin is outside board")
        values = dict(self.entries)
        for kernel_row, row in enumerate(policy.emission()):
            for kernel_col, emission in enumerate(row):
                target = Position(position.row + kernel_row - 2, position.col + kernel_col - 2)
                if 0 <= target.row < self.board_size and 0 <= target.col < self.board_size:
                    values[target] = min(Decimal(1), values.get(target, Decimal(0)) + emission)
        return ScentField(self.board_size, _ordered(values))

    def decay_after_full_turn(self, policy: ScentPolicy) -> ScentField:
        """Apply the exact signed decay once after both actors complete a turn."""
        values = {
            position: policy.after_full_turn(value) for position, value in self.entries if value > 0
        }
        return ScentField(self.board_size, _ordered(values))

    def to_frame(
        self,
        *,
        game_uid: str,
        sub_game_number: int,
        step_number: int,
        actor: Role,
        scent_model_sha256: str,
        policy: ScentPolicy,
    ) -> OpponentScentFrame:
        """Quantize only at the opponent-facing serialization boundary."""
        cells = tuple(
            ScentCell(row=position.row, col=position.col, value=policy.serialize(value))
            for position, value in self.entries
        )
        return OpponentScentFrame.create(
            game_uid=game_uid,
            sub_game_number=sub_game_number,
            step_number=step_number,
            actor=actor,
            rows=self.board_size,
            cols=self.board_size,
            scent_model_sha256=scent_model_sha256,
            cells=[cell.model_dump(mode="json") for cell in cells],
        )


def _ordered(values: dict[Position, Decimal]) -> tuple[tuple[Position, Decimal], ...]:
    return tuple(sorted(values.items(), key=lambda item: (item[0].row, item[0].col)))

"""Durable private scent history with strict restart-time validation."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import Field, StrictInt, StrictStr

from police_thief_p2p.domain.values import Position, Role
from police_thief_p2p.services.belief.scent_field import ScentField
from police_thief_p2p.services.ports.repository import RepositoryPort
from police_thief_p2p.services.protocol.envelope import ProtocolModel
from police_thief_p2p.shared.canonical_json import canonical_json_bytes
from police_thief_p2p.shared.identifiers import GameUid

MAX_STORED_CELLS = 10_000
MAX_STORED_STEPS = 100_000


class _StoredCell(ProtocolModel):
    row: Annotated[StrictInt, Field(ge=0)]
    col: Annotated[StrictInt, Field(ge=0)]
    value: StrictStr


class _StoredStep(ProtocolModel):
    step_number: Annotated[StrictInt, Field(ge=1)]
    row: Annotated[StrictInt, Field(ge=0)]
    col: Annotated[StrictInt, Field(ge=0)]


class _StoredHistory(ProtocolModel):
    storage_version: Literal["1.0.0"] = "1.0.0"
    game_uid: StrictStr
    sub_game_number: Annotated[StrictInt, Field(ge=1, le=6)]
    role: Role
    board_size: Annotated[StrictInt, Field(ge=1, le=10_000)]
    last_step: Annotated[StrictInt, Field(ge=0)]
    last_turn: Annotated[StrictInt, Field(ge=0)]
    field: Annotated[tuple[_StoredCell, ...], Field(max_length=MAX_STORED_CELLS)]
    history: Annotated[tuple[_StoredStep, ...], Field(max_length=MAX_STORED_STEPS)]


@dataclass(frozen=True, slots=True)
class ScentHistorySnapshot:
    """Validated secret state restored by the local composition root."""

    field: ScentField
    history: tuple[tuple[int, Position], ...]
    last_step: int
    last_turn: int


@dataclass(frozen=True, slots=True)
class SecretScentStore:
    """Persist own path and exact scent state behind an opaque repository port."""

    repository: RepositoryPort

    def load(
        self,
        game_uid: str,
        sub_game_number: int,
        role: Role,
    ) -> ScentHistorySnapshot | None:
        """Load one identity-bound snapshot and reject corrupt private data."""
        raw = self.repository.load(_storage_key(game_uid, sub_game_number, role))
        if raw is None:
            return None
        document = _StoredHistory.model_validate_json(raw)
        if (
            document.game_uid != game_uid
            or document.sub_game_number != sub_game_number
            or document.role is not role
        ):
            raise ValueError("stored scent history identity differs")
        entries = tuple(
            (Position(cell.row, cell.col), Decimal(cell.value)) for cell in document.field
        )
        history = tuple(
            (step.step_number, Position(step.row, step.col)) for step in document.history
        )
        if tuple(step for step, _ in history) != tuple(range(1, document.last_step + 1)):
            raise ValueError("stored scent history steps are not contiguous")
        if any(
            cell.row >= document.board_size or cell.col >= document.board_size
            for _, cell in history
        ):
            raise ValueError("stored scent path is outside board dimensions")
        return ScentHistorySnapshot(
            ScentField(document.board_size, entries),
            history,
            document.last_step,
            document.last_turn,
        )

    def save(
        self,
        game_uid: str,
        sub_game_number: int,
        role: Role,
        snapshot: ScentHistorySnapshot,
    ) -> None:
        """Atomically save canonical exact-decimal private state."""
        GameUid(game_uid)
        document = _StoredHistory(
            game_uid=game_uid,
            sub_game_number=sub_game_number,
            role=role,
            board_size=snapshot.field.board_size,
            last_step=snapshot.last_step,
            last_turn=snapshot.last_turn,
            field=tuple(
                _StoredCell(row=cell.row, col=cell.col, value=str(value))
                for cell, value in snapshot.field.entries
            ),
            history=tuple(
                _StoredStep(step_number=step, row=cell.row, col=cell.col)
                for step, cell in snapshot.history
            ),
        )
        self.repository.save(
            _storage_key(game_uid, sub_game_number, role),
            canonical_json_bytes(document.model_dump(mode="json")),
        )


def _storage_key(game_uid: str, sub_game_number: int, role: Role) -> str:
    GameUid(game_uid)
    return f"scent-{game_uid}-{sub_game_number}-{role.value}"

"""Local-only scent history lifecycle and audited recomputation."""

from __future__ import annotations

from dataclasses import dataclass

from police_thief_p2p.domain.state import LocalGameState
from police_thief_p2p.domain.values import Action, ActionType, Position, Role
from police_thief_p2p.services.belief.history_store import (
    ScentHistorySnapshot,
    SecretScentStore,
)
from police_thief_p2p.services.belief.models import OpponentScentFrame
from police_thief_p2p.services.belief.scent_field import ScentField
from police_thief_p2p.shared.scent import ScentPolicy

type ScentKey = tuple[str, int, Role]


@dataclass(frozen=True, slots=True)
class HiddenScentRecord:
    """Secret local path entry never returned by the live SDK."""

    step_number: int
    position: Position


class OwnScentEngine:
    """Emit only from local own state and decay on explicit full-turn completion."""

    __slots__ = ("_fields", "_history", "_last_step", "_last_turn", "_policy", "_store")

    def __init__(
        self,
        policy: ScentPolicy | None = None,
        store: SecretScentStore | None = None,
    ) -> None:
        """Create an empty local-only engine."""
        self._policy = ScentPolicy() if policy is None else policy
        self._store = store
        self._fields: dict[ScentKey, ScentField] = {}
        self._history: dict[ScentKey, list[HiddenScentRecord]] = {}
        self._last_step: dict[ScentKey, int] = {}
        self._last_turn: dict[tuple[str, int], int] = {}

    def emit_after_action(
        self,
        *,
        game_uid: str,
        sub_game_number: int,
        state: LocalGameState,
        action: Action,
        scent_model_sha256: str,
    ) -> OpponentScentFrame:
        """Emit after a local MOVE/STAY and return only opponent-safe evidence."""
        key = (game_uid, sub_game_number, state.role)
        self._restore(key, state.rules.board.size)
        expected = self._last_step.get(key, 0) + 1
        if state.step_number != expected:
            raise ValueError("scent step is not the next local actor step")
        field = self._fields.get(key, ScentField(state.rules.board.size))
        if action.action_type in {ActionType.MOVE, ActionType.STAY}:
            field = field.emit(state.position, self._policy)
        self._fields[key] = field
        self._last_step[key] = state.step_number
        self._history.setdefault(key, []).append(
            HiddenScentRecord(state.step_number, state.position)
        )
        self._persist(key)
        return field.to_frame(
            game_uid=game_uid,
            sub_game_number=sub_game_number,
            step_number=state.step_number,
            actor=state.role,
            scent_model_sha256=scent_model_sha256,
            policy=self._policy,
        )

    def complete_turn(self, game_uid: str, sub_game_number: int, turn_number: int) -> None:
        """Decay local fields exactly once after one Police-plus-Thief turn."""
        turn_key = (game_uid, sub_game_number)
        if turn_number != self._last_turn.get(turn_key, 0) + 1:
            raise ValueError("full-turn completion is duplicate or out of order")
        for key, field in tuple(self._fields.items()):
            if key[:2] == turn_key:
                self._fields[key] = field.decay_after_full_turn(self._policy)
        self._last_turn[turn_key] = turn_number
        for key in tuple(self._fields):
            if key[:2] == turn_key:
                self._persist(key)

    def offline_history(self, key: ScentKey) -> tuple[HiddenScentRecord, ...]:
        """Return path truth only to the offline audit composition root."""
        return tuple(self._history.get(key, ()))

    def _restore(self, key: ScentKey, board_size: int) -> None:
        if key in self._fields or self._store is None:
            return
        game_uid, sub_game_number, role = key
        snapshot = self._store.load(game_uid, sub_game_number, role)
        if snapshot is None:
            return
        if snapshot.field.board_size != board_size:
            raise ValueError("stored scent board dimensions differ")
        self._fields[key] = snapshot.field
        self._history[key] = [
            HiddenScentRecord(step, position) for step, position in snapshot.history
        ]
        self._last_step[key] = snapshot.last_step
        self._last_turn[(game_uid, sub_game_number)] = snapshot.last_turn

    def _persist(self, key: ScentKey) -> None:
        if self._store is None:
            return
        game_uid, sub_game_number, role = key
        snapshot = ScentHistorySnapshot(
            field=self._fields[key],
            history=tuple((record.step_number, record.position) for record in self._history[key]),
            last_step=self._last_step[key],
            last_turn=self._last_turn.get((game_uid, sub_game_number), 0),
        )
        self._store.save(game_uid, sub_game_number, role, snapshot)


def recompute_scent_history(
    board_size: int,
    positions: tuple[Position, ...],
    policy: ScentPolicy,
) -> tuple[ScentField, ...]:
    """Recompute frames from final audited path, decaying after each full turn."""
    field = ScentField(board_size)
    frames = []
    for position in positions:
        field = field.emit(position, policy)
        frames.append(field)
        field = field.decay_after_full_turn(policy)
    return tuple(frames)

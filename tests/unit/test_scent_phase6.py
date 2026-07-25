import json
from decimal import Decimal
from pathlib import Path

import pytest

from police_thief_p2p.adapters.persistence import AtomicFileRepository
from police_thief_p2p.domain import Action, Position, Role, initial_local_state, transition
from police_thief_p2p.sdk import SimulationSdk
from police_thief_p2p.services.belief.evidence import verify_scent_reveal
from police_thief_p2p.services.belief.history_store import SecretScentStore
from police_thief_p2p.services.belief.models import OpponentScentFrame
from police_thief_p2p.services.belief.scent_engine import (
    HiddenScentRecord,
    OwnScentEngine,
    recompute_scent_history,
)
from police_thief_p2p.services.belief.scent_field import ScentField
from police_thief_p2p.shared.config_models import SharedConfig
from police_thief_p2p.shared.scent import ScentPolicy
from tests.helpers.belief import DIGEST, GAME_UID, make_scent_frame, make_scent_reveal

ROOT = Path(__file__).parents[2]


def test_exact_center_edge_corner_overlap_repeat_and_decay_vectors() -> None:
    policy = ScentPolicy()
    center = ScentField(7).emit(Position(3, 3), policy)
    assert len(center.entries) == 25
    assert center.value_at(Position(3, 3)) == Decimal("0.9")
    corner = ScentField(7).emit(Position(0, 0), policy)
    assert len(corner.entries) == 9
    assert corner.value_at(Position(0, 0)) == Decimal("0.9")
    overlap = center.emit(Position(3, 4), policy)
    assert overlap.value_at(Position(3, 3)) == Decimal(1)
    repeated = center.emit(Position(3, 3), policy)
    assert repeated.value_at(Position(3, 3)) == Decimal(1)
    decayed = center.decay_after_full_turn(policy)
    assert decayed.value_at(Position(3, 3)) == Decimal("0.810")
    assert policy.serialize(decayed.value_at(Position(1, 1))) == "0.050625"


def test_signed_scent_conformance_cases_are_exact() -> None:
    vector = json.loads(
        (ROOT / "data/conformance/scent/emission_decay.json").read_text(encoding="utf-8")
    )
    policy = ScentPolicy()
    for case in vector["cases"]:
        field = ScentField(7)
        for row, col in case["positions"]:
            field = field.emit(Position(row, col), policy)
        if case["full_turn_decay"]:
            field = field.decay_after_full_turn(policy)
        assert len(field.entries) == case["expected_cell_count"], case["name"]
        for row, col, expected in case["probes"]:
            assert policy.serialize(field.value_at(Position(row, col))) == expected


def test_decay_occurs_only_after_explicit_complete_turn(
    shared_config: SharedConfig,
) -> None:
    policy = ScentPolicy()
    state = initial_local_state(shared_config, Role.THIEF)
    first = transition(state, Action.stay()).state
    second = transition(first, Action.stay()).state
    without_decay = OwnScentEngine(policy)
    without_decay.emit_after_action(
        game_uid=GAME_UID,
        sub_game_number=1,
        state=first,
        action=Action.stay(),
        scent_model_sha256=DIGEST,
    )
    frame_no_decay = without_decay.emit_after_action(
        game_uid=GAME_UID,
        sub_game_number=1,
        state=second,
        action=Action.stay(),
        scent_model_sha256=DIGEST,
    )
    with_decay = OwnScentEngine(policy)
    with_decay.emit_after_action(
        game_uid=GAME_UID,
        sub_game_number=1,
        state=first,
        action=Action.stay(),
        scent_model_sha256=DIGEST,
    )
    with_decay.complete_turn(GAME_UID, 1, 1)
    frame_decay = with_decay.emit_after_action(
        game_uid=GAME_UID,
        sub_game_number=1,
        state=second,
        action=Action.stay(),
        scent_model_sha256=DIGEST,
    )
    values_no = {(cell.row, cell.col): cell.value for cell in frame_no_decay.cells}
    values_yes = {(cell.row, cell.col): cell.value for cell in frame_decay.cells}
    assert values_no[(1, 1)] == "0.112500"
    assert values_yes[(1, 1)] == "0.106875"
    with pytest.raises(ValueError, match="duplicate"):
        with_decay.complete_turn(GAME_UID, 1, 1)


def test_frame_requires_exact_reveal_context_dimensions_range_and_digest() -> None:
    frame = make_scent_frame(7, ((3, 3, "0.900000"),))
    reveal = make_scent_reveal(frame)
    assert verify_scent_reveal(frame, reveal).frame == frame
    wrong_body = reveal.body.model_copy(update={"scent_frame_sha256": "f" * 64})
    with pytest.raises(ValueError, match="not bound"):
        verify_scent_reveal(frame, reveal.model_copy(update={"body": wrong_body}))
    with pytest.raises(ValueError, match="outside"):
        make_scent_frame(7, ((7, 0, "0.1"),))
    with pytest.raises(ValueError, match="between"):
        make_scent_frame(7, ((0, 0, "1.1"),))
    with pytest.raises(ValueError, match="plain decimal"):
        make_scent_frame(7, ((0, 0, "9e-1"),))
    with pytest.raises(ValueError, match="digest"):
        OpponentScentFrame.model_validate(
            {**frame.model_dump(mode="json"), "frame_sha256": "f" * 64}
        )


def test_hidden_history_is_not_available_through_live_sdk(
    shared_config: SharedConfig,
) -> None:
    assert "offline_history" not in dir(SimulationSdk)
    state = initial_local_state(shared_config, Role.POLICE)
    placed = transition(state, Action.barrier(state.position)).state
    engine = OwnScentEngine()
    frame = engine.emit_after_action(
        game_uid=GAME_UID,
        sub_game_number=1,
        state=placed,
        action=Action.barrier(state.position),
        scent_model_sha256=DIGEST,
    )
    assert frame.cells == ()
    assert engine.offline_history((GAME_UID, 1, Role.POLICE)) == (
        HiddenScentRecord(1, placed.position),
    )


def test_secret_scent_history_survives_process_restart(
    shared_config: SharedConfig,
    tmp_path: Path,
) -> None:
    store = SecretScentStore(AtomicFileRepository(tmp_path))
    state = initial_local_state(shared_config, Role.THIEF)
    first = transition(state, Action.stay()).state
    engine = OwnScentEngine(store=store)
    engine.emit_after_action(
        game_uid=GAME_UID,
        sub_game_number=1,
        state=first,
        action=Action.stay(),
        scent_model_sha256=DIGEST,
    )
    engine.complete_turn(GAME_UID, 1, 1)

    second = transition(first, Action.stay()).state
    restarted = OwnScentEngine(store=store)
    frame = restarted.emit_after_action(
        game_uid=GAME_UID,
        sub_game_number=1,
        state=second,
        action=Action.stay(),
        scent_model_sha256=DIGEST,
    )
    values = {(cell.row, cell.col): cell.value for cell in frame.cells}
    assert values[(1, 1)] == "0.106875"
    assert restarted.offline_history((GAME_UID, 1, Role.THIEF)) == (
        HiddenScentRecord(1, first.position),
        HiddenScentRecord(2, second.position),
    )


def test_audit_recomputation_detects_wrong_decay() -> None:
    policy = ScentPolicy()
    positions = (Position(3, 3), Position(3, 3))
    frames = recompute_scent_history(7, positions, policy)
    assert frames[1].value_at(Position(1, 1)) == Decimal("0.1068750")
    wrong = ScentPolicy(decay=Decimal("0.11"))
    assert recompute_scent_history(7, positions, wrong)[1] != frames[1]

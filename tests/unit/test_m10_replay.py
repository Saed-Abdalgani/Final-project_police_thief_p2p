import json
from collections.abc import Callable
from typing import Any, cast

import pytest

from police_thief_p2p import SimulationSdk
from police_thief_p2p.sdk import ReplayIntegrity, ReplayMode
from police_thief_p2p.services.artifacts.records import SealedLogEntry
from police_thief_p2p.shared.canonical_json import canonical_json_bytes
from police_thief_p2p.shared.config_models import SharedConfig
from tests.helpers.replay import GROUPS, ReplayFixture, build_replay_fixture


def test_valid_single_and_dual_replay_verify_every_step_and_hide_objective_truth(
    shared_config: SharedConfig,
) -> None:
    fixture = build_replay_fixture(shared_config)
    sdk = SimulationSdk()
    single = sdk.verify_log(
        fixture.log_bytes,
        fixture.config_bytes,
        viewer_group=GROUPS[0],
    )
    assert single.integrity is ReplayIntegrity.VERIFIED_OK
    assert single.mode is ReplayMode.SINGLE_LOG
    assert single.verified_steps == single.expected_steps == 11
    assert all(frame.police_position is None for frame in single.frames)
    assert all(frame.thief_position is None for frame in single.frames)
    assert all(frame.belief_heatmap for frame in single.frames)
    dual = sdk.verify_dual_log(
        fixture.log_bytes,
        fixture.config_bytes,
        fixture.log_bytes,
        fixture.config_bytes,
        viewer_group=GROUPS[0],
    )
    assert dual.integrity is ReplayIntegrity.VERIFIED_OK
    assert dual.mode is ReplayMode.OBJECTIVE
    assert all(frame.police_position is not None for frame in dual.frames)
    assert all(frame.thief_position is not None for frame in dual.frames)
    with pytest.raises(ValueError, match="dual-log"):
        sdk.verify_log(
            fixture.log_bytes,
            fixture.config_bytes,
            viewer_group=GROUPS[0],
            objective=True,
        )


def mutate_entry(fixture: ReplayFixture, index: int, **changes: Any) -> bytes:
    entries = list(fixture.log.entries)
    entries[index] = entries[index].model_copy(update=changes)
    return canonical_json_bytes(
        fixture.log.model_copy(update={"entries": tuple(entries)}).model_dump(mode="json")
    )


@pytest.mark.parametrize(
    ("family", "mutator", "expected"),
    [
        (
            "commitment",
            lambda fixture: mutate_entry(fixture, 0, commitment_sha256="f" * 64),
            "COMMITMENT",
        ),
        (
            "order",
            lambda fixture: mutate_entry(fixture, 0, sequence=2),
            "ENTRY_ORDER",
        ),
        (
            "nonce",
            lambda fixture: _mutate_reveal(fixture, 0, "nonce_hex", "ff" * 32),
            "COMMITMENT",
        ),
        (
            "field",
            lambda fixture: _mutate_body(fixture, 0, "hint", "mutated"),
            "COMMITMENT",
        ),
        (
            "topology-digest",
            lambda fixture: _mutate_config(fixture),
            "CONFIG_DIGEST",
        ),
        (
            "score-terminal",
            lambda fixture: canonical_json_bytes(
                fixture.log.model_copy(update={"terminal_reason": "survival"}).model_dump(
                    mode="json"
                )
            ),
            "TERMINAL",
        ),
    ],
)
def test_replay_mutation_families_stop_at_first_invalid_step(
    shared_config: SharedConfig,
    family: str,
    mutator: Callable[[ReplayFixture], bytes],
    expected: str,
) -> None:
    del family
    fixture = build_replay_fixture(shared_config)
    log_bytes = fixture.log_bytes
    config_bytes = fixture.config_bytes
    if expected == "CONFIG_DIGEST":
        config_bytes = mutator(fixture)
    else:
        log_bytes = mutator(fixture)
    result = SimulationSdk().verify_log(
        log_bytes,
        config_bytes,
        viewer_group=GROUPS[0],
    )
    assert result.integrity is ReplayIntegrity.TAMPERED
    assert result.first_failure is not None
    assert result.first_failure.code == expected
    assert result.police_points == result.thief_points == 0


def _mutate_reveal(
    fixture: ReplayFixture,
    index: int,
    field: str,
    value: object,
) -> bytes:
    entry = fixture.log.entries[index]
    reveal = dict(entry.reveal or {})
    reveal[field] = value
    return mutate_entry(fixture, index, reveal=reveal)


def _mutate_body(
    fixture: ReplayFixture,
    index: int,
    field: str,
    value: object,
) -> bytes:
    entry = fixture.log.entries[index]
    reveal = dict(entry.reveal or {})
    body = dict(cast(dict[str, object], reveal["body"]))
    body[field] = value
    reveal["body"] = body
    return mutate_entry(fixture, index, reveal=reveal)


def _mutate_config(fixture: ReplayFixture) -> bytes:
    document = json.loads(fixture.config_bytes)
    shared = document["shared_config"]
    shared["board_and_agents"]["cop_start"] = [0, 1]
    return canonical_json_bytes(document)


def test_replay_navigation_export_and_unequal_track_banner(
    shared_config: SharedConfig,
) -> None:
    fixture = build_replay_fixture(shared_config)
    sdk = SimulationSdk()
    result = sdk.verify_log(fixture.log_bytes, fixture.config_bytes, viewer_group=GROUPS[0])
    cursor = sdk.replay_cursor(result)
    cursor = sdk.navigate_replay(cursor, "next")
    assert cursor.index == 1
    assert sdk.navigate_replay(cursor, "previous").index == 0
    assert sdk.navigate_replay(cursor, "go-to-step", step=5).index == 5
    assert sdk.navigate_replay(cursor, "restart").index == 0
    with pytest.raises(ValueError, match="invalid replay"):
        sdk.navigate_replay(cursor, "go-to-step", step=99)
    machine, human = sdk.export_replay(result)
    assert json.loads(machine)["integrity"] == "Verified OK"
    assert b"<!doctype html>" in human
    assert b"Verified OK" in human

    audit_entry = SealedLogEntry(
        sequence=12,
        step_number=1,
        phase="audit",
        actor="system",
        timestamp="2026-07-26T10:00:12Z",
        public_effects={"status": "verified"},
        audit_status="verified",
    )
    sibling = fixture.log.model_copy(update={"entries": (*fixture.log.entries, audit_entry)})
    unequal = sdk.verify_dual_log(
        fixture.log_bytes,
        fixture.config_bytes,
        canonical_json_bytes(sibling.model_dump(mode="json")),
        fixture.config_bytes,
        viewer_group=GROUPS[0],
    )
    assert unequal.integrity is ReplayIntegrity.VERIFIED_OK
    assert unequal.track_banner == "Unequal tracks 11/12; shorter track is frozen."


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("commitment_version", "1.0.0"),
        ("game_uid", "22345678-1234-4234-8234-123456789abc"),
        ("sub_game_number", 2),
        ("step_number", 2),
        ("actor", "thief"),
        ("pre_action_state_digest", "d" * 64),
        ("action", {"action_type": "MOVE", "direction": "E", "target": None}),
        ("hint", "changed"),
        ("verdict", "lie"),
        ("hint_semantic_intent", "south"),
        ("public_effects", [{"effect_type": "barrier_placed", "target": [0, 0]}]),
        ("token_count", 99),
        ("model_provider", "changed"),
        ("model_name", "changed"),
        ("config_sha256", "d" * 64),
        ("protocol_version", "9.9.9"),
        ("scent_model_sha256", "d" * 64),
        ("scent_frame_sha256", "d" * 64),
    ],
)
def test_every_commitment_body_field_mutation_is_detected_by_replay(
    shared_config: SharedConfig,
    field: str,
    value: object,
) -> None:
    fixture = build_replay_fixture(shared_config)
    result = SimulationSdk().verify_log(
        _mutate_body(fixture, 0, field, value),
        fixture.config_bytes,
        viewer_group=GROUPS[0],
    )
    assert result.integrity is ReplayIntegrity.TAMPERED
    assert result.first_failure is not None

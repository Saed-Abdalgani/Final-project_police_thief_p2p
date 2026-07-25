from pathlib import Path

import pytest

from police_thief_p2p.adapters.persistence import AtomicFileRepository
from police_thief_p2p.domain import Role
from police_thief_p2p.sdk import (
    ProtocolEnvelope,
    ProtocolLimits,
    ProtocolResponse,
    SenderIdentity,
    SimulationSdk,
    create_protocol_runtime,
)
from police_thief_p2p.services.protocol.idempotency import (
    IdempotencyKey,
    IdempotencyRepository,
)
from police_thief_p2p.shared.config_models import SharedConfig
from tests.helpers.protocol import (
    GROUP_A,
    GROUP_B,
    make_acceptance,
    make_envelope,
    make_proposal,
)

pytestmark = pytest.mark.integration


def _sdk(root: Path, shared_bytes: bytes, *, local_group: str = GROUP_B) -> SimulationSdk:
    runtime = create_protocol_runtime(
        local_group=local_group,
        shared_document=shared_bytes,
        storage_root=root,
        limits=ProtocolLimits(reorder_window=4),
    )
    return SimulationSdk(runtime)


def _send(sdk: SimulationSdk, envelope: ProtocolEnvelope) -> ProtocolResponse:
    return sdk.receive_protocol_request(
        envelope.message_type,
        envelope.canonical_bytes(),
    )


def test_full_basic_session_reaches_same_public_terminal_phase(
    tmp_path: Path,
    shared_config: SharedConfig,
    shared_config_bytes: bytes,
) -> None:
    sdk = _sdk(tmp_path, shared_config_bytes)
    proposal = make_proposal(shared_config, shared_config_bytes)
    proposal_request = make_envelope(
        proposal,
        "propose_match_v1",
        proposal.model_dump(mode="json"),
        sequence=1,
    )
    proposed = _send(sdk, proposal_request)
    assert proposed.ok
    assert sdk.protocol_pipeline_trace() == (
        "parse",
        "session",
        "identity",
        "idempotency",
        "phase",
        "persist",
        "sdk",
        "response",
    )
    acceptance = make_acceptance(proposal)
    accepted = _send(
        sdk,
        make_envelope(
            proposal,
            "accept_match_v1",
            acceptance.model_dump(mode="json"),
            sequence=2,
        ),
    )
    assert accepted.payload["phase"] == "ready"

    requests: tuple[tuple[str, dict[str, object]], ...] = (
        ("commit_step_v1", {"commitment": "0" * 64}),
        ("acknowledge_step_v1", {"acknowledged": True}),
        (
            "reveal_step_v1",
            {"terminal_reason": "barrier_capture", "public_outcome": "police_capture"},
        ),
        ("final_reveal_v1", {"manifest": "deferred-to-m5"}),
        ("audit_result_v1", {"audit": "m4-conformance"}),
        ("agree_result_v1", {"result": "police_capture"}),
    )
    responses = [
        _send(sdk, make_envelope(proposal, tool, payload, sequence=index))
        for index, (tool, payload) in enumerate(requests, start=3)
    ]
    assert all(response.ok for response in responses)
    assert responses[-1].payload["phase"] == "completed"
    status = _send(
        sdk,
        make_envelope(proposal, "peer_status_v1", {}, sequence=999),
    )
    assert status.payload == {"phase": "completed", "terminal": True}


def test_duplicate_has_exactly_one_effect_and_conflicting_reuse_fails(
    tmp_path: Path,
    shared_config: SharedConfig,
    shared_config_bytes: bytes,
) -> None:
    sdk = _sdk(tmp_path, shared_config_bytes)
    proposal = make_proposal(shared_config, shared_config_bytes)
    request = make_envelope(
        proposal,
        "propose_match_v1",
        proposal.model_dump(mode="json"),
        sequence=1,
    )
    first = _send(sdk, request)
    duplicate = _send(sdk, request)
    assert duplicate == first
    assert len(list(tmp_path.glob("session-*.json"))) == 1

    conflict = request.model_copy(update={"payload": {**request.payload, "warmup_name": "changed"}})
    result = _send(sdk, conflict)
    assert not result.ok
    assert result.code == "IDEMPOTENCY_CONFLICT"


def test_restart_replays_response_and_repairs_pending_receipt(
    tmp_path: Path,
    shared_config: SharedConfig,
    shared_config_bytes: bytes,
) -> None:
    proposal = make_proposal(shared_config, shared_config_bytes)
    request = make_envelope(
        proposal,
        "propose_match_v1",
        proposal.model_dump(mode="json"),
        sequence=1,
    )
    first = _send(_sdk(tmp_path, shared_config_bytes), request)
    assert first.ok
    repository = AtomicFileRepository(tmp_path)
    key = IdempotencyKey(proposal.game_uid, GROUP_A, request.message_id)
    IdempotencyRepository(repository).persist_intent(key, request.digest())

    recovered = _send(_sdk(tmp_path, shared_config_bytes), request)

    assert recovered == first
    record = IdempotencyRepository(repository).inspect(key, request.digest())
    assert record is not None
    assert record.response == first


@pytest.mark.parametrize(
    ("sequence", "message"),
    [
        (1, "old or duplicate"),
        (3, "out-of-order"),
        (9, "future sequence"),
    ],
)
def test_old_gap_and_far_future_sequences_are_rejected_without_buffering(
    tmp_path: Path,
    shared_config: SharedConfig,
    shared_config_bytes: bytes,
    sequence: int,
    message: str,
) -> None:
    sdk = _sdk(tmp_path, shared_config_bytes)
    proposal = make_proposal(shared_config, shared_config_bytes)
    _send(
        sdk,
        make_envelope(
            proposal,
            "propose_match_v1",
            proposal.model_dump(mode="json"),
            sequence=1,
        ),
    )
    response = _send(
        sdk,
        make_envelope(
            proposal,
            "accept_match_v1",
            make_acceptance(proposal).model_dump(mode="json"),
            sequence=sequence,
        ),
    )
    assert response.code == "SEQUENCE_VIOLATION"
    assert message in response.message


def test_unknown_session_identity_role_and_phase_fail_safely(
    tmp_path: Path,
    shared_config: SharedConfig,
    shared_config_bytes: bytes,
) -> None:
    sdk = _sdk(tmp_path, shared_config_bytes)
    proposal = make_proposal(shared_config, shared_config_bytes)
    unknown = make_envelope(proposal, "commit_step_v1", {}, sequence=1).model_copy(
        update={"game_uid": "22222222-2222-4222-8222-222222222222"}
    )
    assert _send(sdk, unknown).code == "UNKNOWN_SESSION"

    proposed = make_envelope(
        proposal,
        "propose_match_v1",
        proposal.model_dump(mode="json"),
        sequence=1,
    )
    wrong_role = proposed.model_copy(
        update={"sender": SenderIdentity(group_id=GROUP_A, role=Role.THIEF)}
    )
    assert _send(_sdk(tmp_path / "role", shared_config_bytes), wrong_role).code == (
        "IDENTITY_MISMATCH"
    )

    assert _send(sdk, proposed).ok
    phase_error = _send(
        sdk,
        make_envelope(proposal, "commit_step_v1", {}, sequence=2),
    )
    assert phase_error.code == "PHASE_VIOLATION"


def test_unexpected_storage_failure_is_correlation_safe(
    tmp_path: Path,
    shared_config: SharedConfig,
    shared_config_bytes: bytes,
) -> None:
    sdk = _sdk(tmp_path, shared_config_bytes)
    proposal = make_proposal(shared_config, shared_config_bytes)
    request = make_envelope(
        proposal,
        "propose_match_v1",
        proposal.model_dump(mode="json"),
        sequence=1,
    )
    assert _send(sdk, request).ok
    key = IdempotencyKey(proposal.game_uid, GROUP_A, request.message_id)
    AtomicFileRepository(tmp_path).save(key.storage_key(), b"{")
    response = _send(_sdk(tmp_path, shared_config_bytes), request)
    assert response.code == "INTERNAL_FAILURE"
    assert response.correlation_id == request.correlation_id
    assert "traceback" not in response.message.lower()
    assert str(tmp_path) not in response.message


def test_unconfigured_sdk_protocol_boundary_fails_explicitly() -> None:
    with pytest.raises(RuntimeError, match="not configured"):
        SimulationSdk().protocol_health()

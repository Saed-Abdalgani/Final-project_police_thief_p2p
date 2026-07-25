from pathlib import Path

import pytest

from police_thief_p2p.adapters.persistence import AtomicFileRepository
from police_thief_p2p.sdk import SimulationSdk, create_protocol_runtime
from police_thief_p2p.services.protocol.envelope import ProtocolResponse
from police_thief_p2p.services.protocol.errors import ProtocolFailure
from police_thief_p2p.services.protocol.idempotency import (
    IdempotencyKey,
    IdempotencyRecord,
    IdempotencyRepository,
    RecordState,
)
from police_thief_p2p.services.protocol.negotiation import NegotiationService
from police_thief_p2p.services.protocol.negotiation_context import NegotiationContext
from police_thief_p2p.services.protocol.negotiation_models import CountedLedger
from police_thief_p2p.services.protocol.phases import ProtocolPhase, next_phase
from police_thief_p2p.services.protocol.session import ProtocolSession, SessionRegistry
from police_thief_p2p.shared.config_models import SharedConfig
from tests.helpers.protocol import (
    GROUP_A,
    GROUP_B,
    make_envelope,
    make_proposal,
)


def _sdk(root: Path, shared: bytes, local: str = GROUP_B) -> SimulationSdk:
    return SimulationSdk(
        create_protocol_runtime(
            local_group=local,
            shared_document=shared,
            storage_root=root,
        )
    )


def test_parser_tool_version_and_payload_edges_fail_safely(
    tmp_path: Path,
    shared_config: SharedConfig,
    shared_config_bytes: bytes,
) -> None:
    proposal = make_proposal(shared_config, shared_config_bytes)
    valid = make_envelope(
        proposal,
        "propose_match_v1",
        proposal.model_dump(mode="json"),
        sequence=1,
    )
    sdk = _sdk(tmp_path, shared_config_bytes)
    assert sdk.receive_protocol_request("unknown_v1", valid.canonical_bytes()).code == (
        "PROTOCOL_VALIDATION"
    )
    assert (
        sdk.receive_protocol_request("commit_step_v1", valid.canonical_bytes()).code
        == "PROTOCOL_VALIDATION"
    )
    incompatible = valid.model_copy(update={"protocol_version": "9.0.0"})
    assert (
        sdk.receive_protocol_request("propose_match_v1", incompatible.canonical_bytes()).code
        == "PROTOCOL_VALIDATION"
    )
    invalid_payload = valid.model_copy(update={"payload": {}})
    assert (
        _sdk(tmp_path / "invalid", shared_config_bytes)
        .receive_protocol_request("propose_match_v1", invalid_payload.canonical_bytes())
        .code
        == "PROTOCOL_VALIDATION"
    )


def test_bootstrap_sender_identity_subgame_and_acceptance_edges(
    tmp_path: Path,
    shared_config: SharedConfig,
    shared_config_bytes: bytes,
) -> None:
    proposal = make_proposal(shared_config, shared_config_bytes)
    from_local = make_envelope(
        proposal,
        "propose_match_v1",
        proposal.model_dump(mode="json"),
        sequence=1,
        sender=GROUP_A,
    )
    assert (
        _sdk(tmp_path / "self", shared_config_bytes, GROUP_A)
        .receive_protocol_request("propose_match_v1", from_local.canonical_bytes())
        .code
        == "IDENTITY_MISMATCH"
    )

    sdk = _sdk(tmp_path / "session", shared_config_bytes)
    assert sdk.receive_protocol_request("propose_match_v1", from_local.canonical_bytes()).ok
    wrong_sender = make_envelope(
        proposal,
        "accept_match_v1",
        {},
        sequence=2,
        sender=GROUP_B,
    )
    assert (
        sdk.receive_protocol_request("accept_match_v1", wrong_sender.canonical_bytes()).code
        == "IDENTITY_MISMATCH"
    )
    outside_schedule = make_envelope(proposal, "accept_match_v1", {}, sequence=2).model_copy(
        update={"sub_game_number": 7}
    )
    assert (
        sdk.receive_protocol_request("accept_match_v1", outside_schedule.canonical_bytes()).code
        == "IDENTITY_MISMATCH"
    )
    invalid_acceptance = make_envelope(
        proposal,
        "accept_match_v1",
        {},
        sequence=2,
    )
    assert (
        sdk.receive_protocol_request("accept_match_v1", invalid_acceptance.canonical_bytes()).code
        == "PROTOCOL_VALIDATION"
    )


def test_session_and_idempotency_private_record_edges(
    tmp_path: Path,
    shared_config: SharedConfig,
    shared_config_bytes: bytes,
) -> None:
    proposal = make_proposal(shared_config, shared_config_bytes)
    records = AtomicFileRepository(tmp_path)
    registry = SessionRegistry(GROUP_B, records)
    session = registry.create(proposal, GROUP_A)
    assert registry.get(proposal.game_uid) is session
    with pytest.raises(ProtocolFailure, match="already exists"):
        registry.create(proposal, GROUP_A)
    with pytest.raises(ProtocolFailure, match="unknown"):
        registry.get("22222222-2222-4222-8222-222222222222")
    with pytest.raises(ValueError, match="object"):
        ProtocolSession.from_bytes(b"[]")

    key = IdempotencyKey(proposal.game_uid, GROUP_A, "message")
    repository = IdempotencyRepository(records)
    repository.persist_intent(key, "a" * 64)
    with pytest.raises(ProtocolFailure, match="different request"):
        repository.inspect(key, "b" * 64)
    with pytest.raises(ValueError, match="object"):
        IdempotencyRecord.from_bytes(b"[]")
    response = ProtocolResponse(
        ok=True,
        code="OK",
        message="done",
        correlation_id=None,
    )
    record = IdempotencyRecord("a" * 64, RecordState.COMPLETED, response)
    assert IdempotencyRecord.from_bytes(record.to_bytes()) == record
    assert (
        response.canonical_bytes()
        == b'{"code":"OK","correlation_id":null,"message":"done","ok":true,"payload":{}}'
    )


def test_negotiation_absent_group_shared_group_and_base64_edges(
    shared_config: SharedConfig,
    shared_config_bytes: bytes,
) -> None:
    proposal = make_proposal(shared_config, shared_config_bytes)
    service = NegotiationService(
        NegotiationContext(
            "OTHER001",
            shared_config,
            shared_config_bytes,
            CountedLedger(),
            {},
        )
    )
    with pytest.raises(ProtocolFailure, match="absent"):
        service.validate_proposal(proposal)
    context = NegotiationContext(
        GROUP_A,
        shared_config,
        shared_config_bytes,
        CountedLedger(),
        {},
    )
    bad_group = proposal.participants[1].model_copy(update={"group_id": "OTHER001"})
    with pytest.raises(ProtocolFailure, match="shared configuration"):
        NegotiationService(context).validate_proposal(
            proposal.model_copy(update={"participants": (proposal.participants[0], bad_group)})
        )
    with pytest.raises(ProtocolFailure, match="base64"):
        NegotiationService(context).validate_proposal(
            proposal.model_copy(update={"config_raw_b64": "***"})
        )


def test_phase_remaining_paths_and_unknown_mutation() -> None:
    assert next_phase("capture_claim_v1", {}) is ProtocolPhase.VERIFYING
    assert next_phase("capture_response_v1", {"accepted": False}) is ProtocolPhase.WAITING
    assert next_phase("capture_response_v1", {"accepted": True}) is ProtocolPhase.AUDITING
    with pytest.raises(ProtocolFailure, match="unknown"):
        next_phase("not_a_tool", {})

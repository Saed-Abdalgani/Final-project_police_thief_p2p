import inspect

import pytest

from police_thief_p2p.domain import Action, Role
from police_thief_p2p.services.crypto.nonce import MIN_NONCE_BYTES, SecretNonce
from police_thief_p2p.services.crypto.payload import (
    CommitmentBody,
    CommitmentPayload,
    CommittedAction,
    verify_commitment,
)
from police_thief_p2p.services.crypto.store import (
    CommitmentIdentity,
    SealedStepStore,
)
from police_thief_p2p.services.protocol.errors import ProtocolFailure
from police_thief_p2p.services.protocol.phases import ProtocolPhase

GAME_UID = "12345678-1234-4234-8234-123456789abc"
DIGEST = "a" * 64


def body(**changes: object) -> CommitmentBody:
    values: dict[str, object] = {
        "game_uid": GAME_UID,
        "sub_game_number": 1,
        "step_number": 1,
        "actor": Role.POLICE,
        "pre_action_state_digest": DIGEST,
        "action": CommittedAction.from_domain(Action.stay()),
        "hint": "still",
        "verdict": "truth",
        "hint_semantic_intent": "neutral",
        "token_count": 0,
        "model_provider": "template",
        "model_name": "fixed",
        "config_sha256": DIGEST,
        "protocol_version": "0.7.0",
        "scent_model_sha256": DIGEST,
        "scent_frame_sha256": DIGEST,
    }
    values.update(changes)
    return CommitmentBody.model_validate(values)


def test_nonce_entropy_redaction_format_and_csprng_source() -> None:
    nonce = SecretNonce.generate()
    assert len(bytes.fromhex(nonce.reveal_hex())) >= MIN_NONCE_BYTES
    assert repr(nonce) == "SecretNonce(<redacted>)"
    assert str(nonce) == "<redacted>"
    with pytest.raises(ValueError, match="128 bits"):
        SecretNonce(b"x" * 15)
    source = inspect.getsource(__import__("police_thief_p2p.services.crypto.nonce", fromlist=["*"]))
    assert "secrets.token_bytes" in source
    assert "random" not in source


def test_commitment_has_stable_golden_bytes_and_constant_time_verification() -> None:
    payload = CommitmentPayload(body(), SecretNonce(bytes(range(32))))
    expected = (
        b'{"action":{"action_type":"STAY","direction":null,"target":null},'
        b'"actor":"police","commitment_version":"1.1.0","config_sha256":"'
        + DIGEST.encode()
        + b'","game_uid":"12345678-1234-4234-8234-123456789abc","hint":"still",'
        b'"hint_semantic_intent":"neutral",'
        b'"model_name":"fixed","model_provider":"template","nonce":"'
        b"000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"
        b'","pre_action_state_digest":"'
        + DIGEST.encode()
        + b'","protocol_version":"0.7.0","public_effects":[],"scent_frame_sha256":"'
        + DIGEST.encode()
        + b'","scent_model_sha256":"'
        + DIGEST.encode()
        + b'","step_number":1,"sub_game_number":1,"token_count":0,"verdict":"truth"}'
    )
    assert payload.canonical_bytes() == expected
    assert payload.digest() == "496d8de1b8c1fb0def5a781b296932cb46bb17588236e139b7a67bfad25f6e05"
    assert verify_commitment(payload, payload.digest())
    assert "compare_digest" in inspect.getsource(verify_commitment)


def test_sealed_store_enforces_lifecycle_and_never_live_reveals_nonce() -> None:
    payload = CommitmentPayload(body(), SecretNonce(b"N" * 32))
    store = SealedStepStore()
    public = store.seal(payload)
    identity = CommitmentIdentity(GAME_UID, 1, 1, Role.POLICE)
    assert "nonce" not in public.model_dump()
    with pytest.raises(ProtocolFailure):
        store.reveal(identity)
    with pytest.raises(ProtocolFailure):
        store.final_manifest(GAME_UID, 1, ProtocolPhase.WAITING)
    store.acknowledge(identity, public.commitment_sha256)
    with pytest.raises(ProtocolFailure, match="immutable"):
        store.replace_before_ack(
            identity,
            CommitmentPayload(body(hint="changed"), SecretNonce(b"M" * 32)),
        )
    reveal = store.reveal(identity)
    assert "nonce" not in reveal.model_dump()
    manifest = store.final_manifest(GAME_UID, 1, ProtocolPhase.AUDITING)
    assert manifest.entries[0].nonce_hex == (b"N" * 32).hex()


def test_nonce_reuse_and_identity_reuse_fail_closed() -> None:
    store = SealedStepStore()
    nonce = SecretNonce(b"R" * 32)
    store.seal(CommitmentPayload(body(), nonce))
    with pytest.raises(ProtocolFailure, match="identity"):
        store.seal(CommitmentPayload(body(), SecretNonce(b"S" * 32)))
    with pytest.raises(ProtocolFailure, match="nonce reuse"):
        store.seal(CommitmentPayload(body(step_number=2), nonce))
    with pytest.raises(ProtocolFailure, match="nonce reuse"):
        store.seal(CommitmentPayload(body(sub_game_number=2), nonce))


@pytest.mark.parametrize(
    "operation",
    ["unknown_ack", "unknown_reveal", "wrong_ack", "early_reveal", "early_final"],
)
def test_illegal_commit_reveal_order_matrix(operation: str) -> None:
    store = SealedStepStore()
    identity = CommitmentIdentity(GAME_UID, 1, 1, Role.POLICE)
    if operation == "unknown_ack":
        with pytest.raises(ProtocolFailure):
            store.acknowledge(identity, DIGEST)
        return
    if operation == "unknown_reveal":
        with pytest.raises(ProtocolFailure):
            store.reveal(identity)
        return
    public = store.seal(CommitmentPayload(body(), SecretNonce(f"{operation:0<32}".encode())))
    if operation == "wrong_ack":
        with pytest.raises(ProtocolFailure, match="digest differs"):
            store.acknowledge(identity, "f" * 64)
    elif operation == "early_reveal":
        with pytest.raises(ProtocolFailure, match="acknowledgement"):
            store.reveal(identity)
    else:
        store.acknowledge(identity, public.commitment_sha256)
        with pytest.raises(ProtocolFailure, match="live-revealed"):
            store.final_manifest(GAME_UID, 1, ProtocolPhase.AUDITING)

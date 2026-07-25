import io
from dataclasses import replace

import pytest

from police_thief_p2p.services.crypto.capture import (
    CaptureExchange,
    CaptureStatement,
    SealedCapture,
)
from police_thief_p2p.services.crypto.declaration import (
    SignedStepZero,
    StepZeroBody,
    load_signing_key,
)
from police_thief_p2p.services.crypto.journal import EventJournal, verify_journal
from police_thief_p2p.services.crypto.nonce import SecretNonce
from police_thief_p2p.services.ports.git_info import GitState
from police_thief_p2p.services.ports.system_info import SystemInfo
from police_thief_p2p.shared.redaction import redact_value

DIGEST = "a" * 64


def declaration(**changes: object) -> StepZeroBody:
    values: dict[str, object] = {
        "system": SystemInfo("Linux", "3.13", "CPU", 8, 1024),
        "git": GitState("b" * 40, False),
        "group_id": "GRP00001",
        "counted": True,
        "template_mode": True,
        "model_provider": "template",
        "model_name": "fixed",
        "estimated_tokens": 0,
        "config_sha256": DIGEST,
        "scent_model_sha256": DIGEST,
        "role_schedule_sha256": DIGEST,
        "protocol_version": "0.5.0",
        "schema_version": "0.2.0",
    }
    values.update(changes)
    return StepZeroBody.compose(**values)  # type: ignore[arg-type]


def test_step_zero_key_loading_signing_tamper_and_redaction() -> None:
    key = load_signing_key(env_name="COURSE_KEY", environ={"COURSE_KEY": "K" * 32})
    file_key = load_signing_key(file_handle=io.BytesIO(b"F" * 32))
    assert "<redacted>" in repr(key)
    signed = SignedStepZero.create(declaration(), key)
    assert signed.verify(key)
    assert not signed.model_copy(update={"signature_sha256": "0" * 64}).verify(key)
    assert SignedStepZero.create(declaration(), file_key).verify(file_key)
    with pytest.raises(ValueError, match="exactly one"):
        load_signing_key()
    safe = redact_value({"nested": {"signing_key": "raw", "hmac-key": "raw"}})
    assert "raw" not in repr(safe)


def test_step_zero_rejects_dirty_unknown_and_nonzero_template_tokens() -> None:
    with pytest.raises(ValueError, match="clean exact Git"):
        declaration(git=GitState("b" * 40, True))
    with pytest.raises(ValueError, match="clean exact Git"):
        declaration(git=GitState(None, None))
    with pytest.raises(ValueError, match="zero operational"):
        declaration(estimated_tokens=1)
    warmup = declaration(counted=False, git=GitState(None, None))
    assert warmup.git.commit is None


def test_system_info_rejects_impossible_capacity_and_allows_unknown_gpu() -> None:
    system = SystemInfo("Linux", "3.13", None, None, None)
    assert system.gpu_model is None
    assert system.vram_bytes is None
    with pytest.raises(ValueError, match="positive"):
        SystemInfo("Linux", "3.13", "CPU", -1, 1024)
    with pytest.raises(ValueError, match="VRAM"):
        SystemInfo("Linux", "3.13", "CPU", 1, 1024, vram_bytes=-1)


def test_journal_detects_removal_reorder_and_modification() -> None:
    journal = EventJournal()
    first = journal.append("commit", {"digest": "a"})
    second = journal.append("reveal", {"action": "STAY"})
    assert verify_journal(journal.entries)
    assert not verify_journal((second,))
    assert not verify_journal((second, first))
    altered = replace(second, payload_sha256="f" * 64)
    assert not verify_journal((first, altered))


def test_capture_exchange_binds_context_without_positions() -> None:
    common = {
        "game_uid": "game",
        "sub_game_number": 1,
        "step_number": 2,
        "action_commitment_sha256": DIGEST,
        "captured": True,
    }
    claim = SealedCapture(
        CaptureStatement.model_validate({"kind": "claim", **common}),
        SecretNonce(b"C" * 32),
    )
    response = SealedCapture(
        CaptureStatement.model_validate({"kind": "response", **common}),
        SecretNonce(b"D" * 32),
    )
    assert claim.verify(claim.digest())
    assert "position" not in repr(claim.statement.model_dump())
    assert CaptureExchange(claim, response).response.statement.captured
    wrong = SealedCapture(
        CaptureStatement.model_validate({"kind": "response", **common, "step_number": 3}),
        SecretNonce(b"E" * 32),
    )
    with pytest.raises(ValueError, match="context"):
        CaptureExchange(claim, wrong)

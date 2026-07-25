import ast
import hashlib
import inspect
import json
from pathlib import Path

import pytest

from police_thief_p2p.services.audit import AuditService
from police_thief_p2p.services.crypto.declaration import SignedStepZero, SigningKey, StepZeroBody
from police_thief_p2p.services.crypto.nonce import SecretNonce
from police_thief_p2p.services.crypto.payload import CommitmentBody, CommitmentPayload
from police_thief_p2p.shared.config_errors import ConfigError
from police_thief_p2p.shared.config_models import SharedConfig
from police_thief_p2p.shared.schema_registry import validate_schema
from tests.helpers.audit import build_valid_audit_bundle

ROOT = Path(__file__).parents[2]
VECTOR = ROOT / "data/conformance/crypto/commitment.v1.json"
STEP_ZERO_VECTOR = ROOT / "data/conformance/crypto/step_zero.v1.json"


def test_cross_repository_commitment_vector_is_exact() -> None:
    vector = json.loads(VECTOR.read_text(encoding="utf-8"))
    police_body = CommitmentBody.model_validate(vector["body"])
    thief_body = CommitmentBody.model_validate(json.loads(json.dumps(vector["body"])))
    police = CommitmentPayload(police_body, SecretNonce.from_hex(vector["nonce_hex"]))
    thief = CommitmentPayload(thief_body, SecretNonce.from_hex(vector["nonce_hex"]))
    assert police.canonical_bytes() == thief.canonical_bytes()
    assert hashlib.sha256(police.canonical_bytes()).hexdigest() == vector["commitment_sha256"]
    validate_schema(vector["body"], "commitment_body.schema.json", source=str(VECTOR))


def test_full_step_zero_golden_bytes_digest_and_hmac_are_exact() -> None:
    vector = json.loads(STEP_ZERO_VECTOR.read_text(encoding="utf-8"))
    body = StepZeroBody.model_validate(vector["body"])
    assert hashlib.sha256(body.canonical_bytes()).hexdigest() == vector["canonical_sha256"]
    signed = SignedStepZero.create(body, SigningKey(b"A" * 32))
    assert signed.signature_sha256 == vector["test_hmac_sha256"]


def test_live_reveal_schema_forbids_nonce_at_every_live_boundary(
    shared_config: SharedConfig,
) -> None:
    bundle = build_valid_audit_bundle(shared_config)
    reveal = bundle.steps[0].reveal.model_dump(mode="json")
    validate_schema(reveal, "live_reveal.schema.json", source="live-reveal")
    for location in ("root", "body"):
        altered = json.loads(json.dumps(reveal))
        target = altered if location == "root" else altered["body"]
        target["nonce"] = "00" * 32
        with pytest.raises(ConfigError):
            validate_schema(altered, "live_reveal.schema.json", source=location)


def test_final_manifest_capture_and_report_are_schema_valid(
    shared_config: SharedConfig,
) -> None:
    bundle = build_valid_audit_bundle(shared_config)
    manifest = {
        "game_uid": bundle.final_manifest.game_uid,
        "sub_game_number": bundle.final_manifest.sub_game_number,
        "entries": [entry.as_dict() for entry in bundle.final_manifest.entries],
        "manifest_sha256": bundle.final_manifest.manifest_sha256,
    }
    validate_schema(manifest, "final_reveal.schema.json", source="final")
    assert bundle.capture_exchange is not None
    validate_schema(
        bundle.capture_exchange.claim.statement.model_dump(mode="json"),
        "capture_statement.schema.json",
        source="capture",
    )
    report = AuditService().verify(bundle)
    validate_schema(report.as_dict(), "audit_report.schema.json", source="report")


def test_audit_service_has_no_adapter_gui_or_network_dependency() -> None:
    module = inspect.getmodule(AuditService)
    assert module is not None
    tree = ast.parse(inspect.getsource(module))
    imports = {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)} | {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert all(
        forbidden not in imported
        for imported in imports
        for forbidden in ("adapters", ".gui", "network")
    )

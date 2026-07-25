"""Deterministic constitution, declaration, journal, and manifest checks."""

import secrets

from police_thief_p2p.services.audit.models import AuditBundle, AuditFinding
from police_thief_p2p.services.crypto.journal import verify_journal
from police_thief_p2p.services.crypto.scent_evidence import scent_model_digest
from police_thief_p2p.shared.canonical_json import sha256_digest


def preflight_findings(bundle: AuditBundle) -> tuple[AuditFinding, ...]:
    """Return ordered failures that make physical replay unsafe."""
    failures: list[tuple[str, str, str]] = []
    if not secrets.compare_digest(bundle.config.digest(), bundle.config_sha256):
        failures.append(("CONFIG_DIGEST", "config", "shared configuration digest differs"))
    if not secrets.compare_digest(
        scent_model_digest(bundle.scent_policy),
        bundle.scent_model_sha256,
    ):
        failures.append(("SCENT_MODEL", "scent-model", "signed scent model differs"))
    if not secrets.compare_digest(
        bundle.role_schedule_sha256,
        bundle.expected_role_schedule_sha256,
    ):
        failures.append(("ROLE_SCHEDULE", "schedule", "role schedule digest differs"))
    failures.extend(_step_zero_failures(bundle))
    if not verify_journal(bundle.journal):
        failures.append(("JOURNAL_CHAIN", "journal", "event journal chain is invalid"))
    elif not _journal_matches_steps(bundle):
        failures.append(
            ("JOURNAL_EVIDENCE", "journal", "journal does not cover exact step reveals")
        )
    if not _manifest_matches(bundle):
        failures.append(("FINAL_MANIFEST", "final-reveal", "nonce manifest linkage differs"))
    return tuple(
        AuditFinding(order, code, evidence, detail)
        for order, (code, evidence, detail) in enumerate(failures, start=1)
    )


def _step_zero_failures(bundle: AuditBundle) -> list[tuple[str, str, str]]:
    failures = []
    if len(bundle.step_zero) != 2:
        failures.append(
            ("STEP_ZERO_COMPLETENESS", "step-zero", "exactly two declarations are required")
        )
    for index, (declaration, key) in enumerate(bundle.step_zero, start=1):
        body = declaration.body
        evidence = f"step-zero:{index}"
        if not declaration.verify(key):
            failures.append(("STEP_ZERO_SIGNATURE", evidence, "Step-0 signature is invalid"))
        binding = (
            body.config_sha256 == bundle.config_sha256
            and body.scent_model_sha256 == bundle.scent_model_sha256
            and body.role_schedule_sha256 == bundle.role_schedule_sha256
        )
        if not binding:
            failures.append(("STEP_ZERO_BINDING", evidence, "Step-0 artifact binding differs"))
    declared_groups = {item[0].body.group_id for item in bundle.step_zero}
    if declared_groups != set(bundle.config.agreed_between):
        failures.append(
            ("STEP_ZERO_IDENTITY", "step-zero", "declared groups differ from constitution")
        )
    return failures


def _manifest_matches(bundle: AuditBundle) -> bool:
    manifest = bundle.final_manifest
    if manifest.game_uid != bundle.game_uid or manifest.sub_game_number != bundle.sub_game_number:
        return False
    if len(manifest.entries) != len(bundle.steps):
        return False
    expected = sha256_digest([entry.as_dict() for entry in manifest.entries])
    if not secrets.compare_digest(expected, manifest.manifest_sha256):
        return False
    reveal_entries = {
        (
            step.reveal.body.step_number,
            step.reveal.body.actor,
            step.reveal.commitment_sha256,
            step.nonce_hex,
        )
        for step in bundle.steps
    }
    manifest_entries = {
        (
            entry.identity.step_number,
            entry.identity.actor,
            entry.commitment_sha256,
            entry.nonce_hex,
        )
        for entry in manifest.entries
    }
    return (
        len(reveal_entries) == len(bundle.steps)
        and len(manifest_entries) == len(manifest.entries)
        and reveal_entries == manifest_entries
    )


def _journal_matches_steps(bundle: AuditBundle) -> bool:
    if len(bundle.journal) != len(bundle.steps):
        return False
    for entry, step in zip(bundle.journal, bundle.steps, strict=True):
        if entry.event_type != "step-reveal":
            return False
        expected = sha256_digest(step.reveal.model_dump(mode="json"))
        if not secrets.compare_digest(entry.payload_sha256, expected):
            return False
    return True

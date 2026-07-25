from dataclasses import replace

import pytest

from police_thief_p2p.domain import Action, Direction, Role, TerminalReason
from police_thief_p2p.services.audit import (
    AuditService,
    AuditStatus,
    agree_audits,
    recompute_series,
)
from police_thief_p2p.services.crypto.capture import CaptureExchange, SealedCapture
from police_thief_p2p.services.crypto.payload import CommittedAction, PublicEffect
from police_thief_p2p.shared.config_models import SharedConfig
from tests.helpers.audit import (
    build_valid_audit_bundle,
    replace_step_body,
    reseal_step_body,
)


def test_complete_final_reveal_and_two_independent_audits_are_verified(
    shared_config: SharedConfig,
) -> None:
    bundle = build_valid_audit_bundle(shared_config)
    left = AuditService().verify(bundle)
    right = AuditService().verify(bundle)
    assert left.status is AuditStatus.VERIFIED_OK
    assert right.status is AuditStatus.VERIFIED_OK
    assert left.verified_steps == 11
    assert left.terminal_reason == TerminalReason.CAPTURE.value
    agreement = agree_audits(
        bundle.final_manifest.manifest_sha256,
        bundle.final_manifest.manifest_sha256,
        left,
        right,
    )
    assert agreement.status is AuditStatus.VERIFIED_OK


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("commitment_version", "1.0.1"),
        ("game_uid", "22345678-1234-4234-8234-123456789abc"),
        ("sub_game_number", 2),
        ("step_number", 2),
        ("actor", Role.THIEF),
        ("pre_action_state_digest", "b" * 64),
        ("action", CommittedAction.from_domain(Action.move(Direction.EAST))),
        ("hint", "mutated"),
        ("verdict", "lie"),
        ("public_effects", ()),
        ("token_count", 1),
        ("model_provider", "other"),
        ("model_name", "other"),
        ("config_sha256", "b" * 64),
        ("protocol_version", "9.9.9"),
        ("scent_model_sha256", "b" * 64),
        ("scent_frame_sha256", "b" * 64),
    ],
)
def test_every_commitment_field_mutation_is_detected(
    shared_config: SharedConfig,
    field: str,
    value: object,
) -> None:
    bundle = build_valid_audit_bundle(shared_config)
    if field == "public_effects":
        value = (PublicEffect(effect_type="barrier_placed", target=(0, 0)),)
    altered = replace_step_body(bundle, 0, **{field: value})
    report = AuditService().verify(altered)
    assert report.status is AuditStatus.TAMPERED
    assert report.police_points == report.thief_points == 0


def test_missing_duplicate_reordered_truncated_and_foreign_steps_fail(
    shared_config: SharedConfig,
) -> None:
    bundle = build_valid_audit_bundle(shared_config)
    variants = (
        replace(bundle, steps=bundle.steps[1:]),
        replace(bundle, steps=(bundle.steps[0], *bundle.steps)),
        replace(bundle, steps=(bundle.steps[1], bundle.steps[0], *bundle.steps[2:])),
        replace(bundle, steps=bundle.steps[:-1]),
        replace_step_body(bundle, 0, game_uid="22345678-1234-4234-8234-123456789abc"),
    )
    assert all(AuditService().verify(item).status is AuditStatus.TAMPERED for item in variants)


def test_valid_hash_with_illegal_action_and_false_capture_fail(
    shared_config: SharedConfig,
) -> None:
    bundle = build_valid_audit_bundle(shared_config)
    illegal = reseal_step_body(
        bundle,
        0,
        action=CommittedAction.from_domain(Action.move(Direction.NORTH)),
    )
    illegal_report = AuditService().verify(illegal)
    assert illegal_report.status is AuditStatus.TAMPERED
    assert illegal_report.first_failure is not None
    assert illegal_report.first_failure.code == "ILLEGAL_ACTION"
    forged_scent = reseal_step_body(bundle, 0, scent_frame_sha256="f" * 64)
    scent_report = AuditService().verify(forged_scent)
    assert scent_report.first_failure is not None
    assert scent_report.first_failure.code == "SCENT_FRAME"
    assert bundle.capture_exchange is not None
    false_response = bundle.capture_exchange.response
    false_statement = false_response.statement.model_copy(update={"captured": False})
    exchange = CaptureExchange(
        bundle.capture_exchange.claim,
        SealedCapture(false_statement, false_response.nonce),
    )
    report = AuditService().verify(replace(bundle, capture_exchange=exchange))
    assert report.first_failure is not None
    assert report.first_failure.code == "FALSE_CAPTURE"


def test_manifest_or_independent_result_disagreement_blocks_reporting(
    shared_config: SharedConfig,
) -> None:
    bundle = build_valid_audit_bundle(shared_config)
    report = AuditService().verify(bundle)
    with pytest.raises(ValueError, match="manifest disagreement"):
        agree_audits("a" * 64, "b" * 64, report, report)
    altered = replace(report, evidence_sha256="f" * 64)
    with pytest.raises(ValueError, match="result disagreement"):
        agree_audits("a" * 64, "a" * 64, report, altered)


def test_finding_order_is_deterministic_and_capture_digest_tamper_fails(
    shared_config: SharedConfig,
) -> None:
    bundle = build_valid_audit_bundle(shared_config)
    broken = replace(
        bundle,
        config_sha256="f" * 64,
        scent_model_sha256="e" * 64,
        role_schedule_sha256="d" * 64,
    )
    first = AuditService().verify(broken)
    second = AuditService().verify(broken)
    assert first.findings == second.findings
    assert [item.order for item in first.findings] == list(range(1, len(first.findings) + 1))
    assert bundle.capture_exchange is not None
    altered_capture = replace(
        bundle.capture_exchange,
        response_commitment_sha256="f" * 64,
    )
    capture_report = AuditService().verify(replace(bundle, capture_exchange=altered_capture))
    assert capture_report.first_failure is not None
    assert capture_report.first_failure.code == "CAPTURE_COMMITMENT"


def test_series_totals_and_tie_awards_are_recomputed_by_group(
    shared_config: SharedConfig,
) -> None:
    report = AuditService().verify(build_valid_audit_bundle(shared_config))
    games = tuple(
        ("GRP00001", "GRP00002", report) if number % 2 else ("GRP00002", "GRP00001", report)
        for number in range(1, 7)
    )
    series = recompute_series(games, shared_config, "GRP00001", "GRP00002")
    assert series.total_for("GRP00001") == 75
    assert series.total_for("GRP00002") == 75
    assert series.tie_award_for("GRP00001") == 2
    assert series.winner is None

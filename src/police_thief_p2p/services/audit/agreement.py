"""Mutual audit-manifest and final-result agreement."""

import secrets
from dataclasses import dataclass

from police_thief_p2p.domain.scoring import (
    SeriesScore,
    SubGameOutcome,
    aggregate_series,
)
from police_thief_p2p.domain.values import TerminalReason
from police_thief_p2p.services.audit.models import AuditReport, AuditStatus
from police_thief_p2p.shared.canonical_json import sha256_digest
from police_thief_p2p.shared.config_models import SharedConfig


@dataclass(frozen=True, slots=True)
class FinalAgreement:
    """Digest proving two peers agreed on evidence and independent outcomes."""

    audit_manifest_sha256: str
    result_agreement_sha256: str
    status: AuditStatus


def agree_audits(
    left_manifest_sha256: str,
    right_manifest_sha256: str,
    left_report: AuditReport,
    right_report: AuditReport,
) -> FinalAgreement:
    """Block reporting unless both manifest and result digests agree."""
    if not secrets.compare_digest(left_manifest_sha256, right_manifest_sha256):
        raise ValueError("audit manifest disagreement blocks reporting")
    left_digest = left_report.digest()
    right_digest = right_report.digest()
    if not secrets.compare_digest(left_digest, right_digest):
        raise ValueError("independent audit result disagreement blocks reporting")
    return FinalAgreement(
        left_manifest_sha256,
        sha256_digest(
            {
                "audit_manifest_sha256": left_manifest_sha256,
                "left_report_sha256": left_digest,
                "right_report_sha256": right_digest,
            }
        ),
        left_report.status,
    )


def recompute_series(
    reports: tuple[tuple[str, str, AuditReport], ...],
    config: SharedConfig,
    group_a: str,
    group_b: str,
) -> SeriesScore:
    """Recompute six role-swapped totals and tie awards from verified reports."""
    if any(report.status is not AuditStatus.VERIFIED_OK for _, _, report in reports):
        raise ValueError("tampered sub-game cannot enter series scoring")
    outcomes = tuple(
        SubGameOutcome.from_terminal(
            index,
            police_group,
            thief_group,
            TerminalReason(report.terminal_reason),
            config.scoring,
        )
        for index, (police_group, thief_group, report) in enumerate(reports, start=1)
    )
    return aggregate_series(outcomes, group_a, group_b)

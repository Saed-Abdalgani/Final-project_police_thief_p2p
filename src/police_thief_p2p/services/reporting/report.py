"""Build a standard JSON report only from verified manifest evidence."""

import base64
import copy
import secrets
from dataclasses import dataclass

from police_thief_p2p.services.artifacts.accounting import (
    verify_result_totals,
    verify_token_accounting,
)
from police_thief_p2p.services.artifacts.linkage import VerifiedManifest
from police_thief_p2p.services.artifacts.result import FinalResultArtifact
from police_thief_p2p.services.reporting.models import OutboxItem
from police_thief_p2p.services.reporting.policy import ReportingPolicy
from police_thief_p2p.shared.canonical_json import (
    canonical_json_bytes,
    digest_bytes,
    sha256_digest,
)


@dataclass(frozen=True, slots=True)
class PreparedReport:
    """Verified JSON attachment and durable outbox snapshot."""

    attachment: bytes
    item: OutboxItem


def result_payload_digest(document: dict[str, object]) -> str:
    """Digest result content excluding its self-referential confirmation value."""
    unsigned = copy.deepcopy(document)
    agreement = unsigned.get("agreement")
    if not isinstance(agreement, dict):
        raise ValueError("result agreement is missing")
    agreement.pop("agreed_digest", None)
    return sha256_digest(unsigned)


def build_report(
    verified: VerifiedManifest,
    policy: ReportingPolicy,
    *,
    recipient: str,
) -> PreparedReport:
    """Build and identify the sole authoritative JSON report attachment."""
    destination = policy.validate_recipient(recipient)
    document = verified.result_document()
    result = FinalResultArtifact.model_validate(document)
    verify_token_accounting(result)
    verify_result_totals(result)
    expected = result_payload_digest(document)
    if not secrets.compare_digest(expected, result.agreement.agreed_digest):
        raise ValueError("mutual result digest confirmation is invalid")
    if set(result.agreement.signers) != {group.group_id for group in result.groups}:
        raise ValueError("mutual result signers do not match participants")
    attachment = canonical_json_bytes(document)
    attachment_sha256 = digest_bytes(attachment)
    logical_id = sha256_digest(
        {"game_uid": result.game_uid, "sender_group_id": result.sender_group_id}
    )
    name = f"result_{result.game_id}.json"
    return PreparedReport(
        attachment,
        OutboxItem(
            logical_report_id=logical_id,
            game_uid=result.game_uid,
            sender_group_id=result.sender_group_id,
            attachment_name=name,
            attachment_sha256=attachment_sha256,
            attachment_b64=base64.b64encode(attachment).decode("ascii"),
            recipient=destination,
        ),
    )

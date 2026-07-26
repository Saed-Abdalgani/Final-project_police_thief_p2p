"""Verified report construction and durable idempotent dispatch."""

from police_thief_p2p.services.reporting.dispatcher import (
    DispatchOutcome,
    OutboxDispatcher,
)
from police_thief_p2p.services.reporting.mime import build_report_mime
from police_thief_p2p.services.reporting.models import (
    OutboxItem,
    OutboxState,
)
from police_thief_p2p.services.reporting.outbox import DurableOutbox
from police_thief_p2p.services.reporting.policy import (
    GMAIL_SEND_SCOPE,
    REQUIRED_RECIPIENT,
    ReportingPolicy,
)
from police_thief_p2p.services.reporting.report import (
    PreparedReport,
    build_report,
    result_payload_digest,
)

__all__ = [
    "GMAIL_SEND_SCOPE",
    "REQUIRED_RECIPIENT",
    "DispatchOutcome",
    "DurableOutbox",
    "OutboxDispatcher",
    "OutboxItem",
    "OutboxState",
    "PreparedReport",
    "ReportingPolicy",
    "build_report",
    "build_report_mime",
    "result_payload_digest",
]

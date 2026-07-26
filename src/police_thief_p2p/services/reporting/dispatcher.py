"""Durable outbox dispatch through the central Gatekeeper only."""

import base64
from dataclasses import dataclass
from enum import StrEnum

from police_thief_p2p.services.ports.clock import ClockPort
from police_thief_p2p.services.reporting.mime import build_report_mime
from police_thief_p2p.services.reporting.models import OutboxItem, OutboxState
from police_thief_p2p.services.reporting.outbox import DurableOutbox
from police_thief_p2p.services.reporting.report import PreparedReport
from police_thief_p2p.shared.gatekeeper import ExternalCall, GatekeeperPort


class DispatchOutcome(StrEnum):
    """Stable visible dispatcher outcomes."""

    SENT = "sent"
    ALREADY_SENT = "already-sent"
    RETRY_WAIT = "retry-wait"
    FAILED_PERMANENT = "failed-permanent"
    VALIDATED_DRY_RUN = "validated-dry-run"


@dataclass(frozen=True, slots=True)
class DispatchReceipt:
    """Redacted report status without attachment/provider details."""

    outcome: DispatchOutcome
    logical_report_id: str
    attempts: int
    provider_id: str | None = None
    error_code: str | None = None


class OutboxDispatcher:
    """Perform exactly-once logical report dispatch through a Gatekeeper."""

    __slots__ = ("_clock", "_gatekeeper", "_outbox", "_sender")

    def __init__(
        self,
        outbox: DurableOutbox,
        gatekeeper: GatekeeperPort,
        clock: ClockPort,
        *,
        sender: str,
    ) -> None:
        """Bind durable state, protected execution, and public sender identity."""
        self._outbox = outbox
        self._gatekeeper = gatekeeper
        self._clock = clock
        self._sender = sender

    def enqueue(self, report: PreparedReport) -> OutboxItem:
        """Durably admit one verified logical report."""
        return self._outbox.enqueue(report.item)

    def validate(self, report: PreparedReport) -> DispatchReceipt:
        """Build and validate MIME without an outbox or provider state change."""
        build_report_mime(report.item, sender=self._sender)
        return DispatchReceipt(
            DispatchOutcome.VALIDATED_DRY_RUN,
            report.item.logical_report_id,
            0,
        )

    async def dispatch(self, logical_report_id: str) -> DispatchReceipt:
        """Recover, validate, send, and durably record one report outcome."""
        item = self._outbox.get(logical_report_id)
        if item.state is OutboxState.SENT:
            return _receipt(DispatchOutcome.ALREADY_SENT, item)
        if item.state is OutboxState.FAILED_PERMANENT:
            return _receipt(DispatchOutcome.FAILED_PERMANENT, item)
        if item.state is OutboxState.RETRY_WAIT:
            if item.retry_not_before is not None and self._clock.monotonic() < float(
                item.retry_not_before
            ):
                return _receipt(DispatchOutcome.RETRY_WAIT, item)
            item = self._outbox.transition(logical_report_id, OutboxState.VALIDATED)
        elif item.state is OutboxState.PENDING:
            item = self._outbox.transition(logical_report_id, OutboxState.VALIDATED)
        raw_mime = build_report_mime(item, sender=self._sender)
        item = self._outbox.transition(logical_report_id, OutboxState.SENDING)
        result = await self._gatekeeper.execute(
            ExternalCall(
                service="gmail",
                operation="send_report",
                payload={
                    "logical_report_id": item.logical_report_id,
                    "raw_mime_b64": base64.urlsafe_b64encode(raw_mime).decode("ascii"),
                    "priority": 2,
                },
            )
        )
        if result.outcome == "success" and isinstance(result.payload.get("provider_id"), str):
            sent = self._outbox.transition(
                logical_report_id,
                OutboxState.SENT,
                provider_id=result.payload["provider_id"],
                last_error_code=None,
                retry_not_before=None,
            )
            return _receipt(DispatchOutcome.SENT, sent)
        code = result.payload.get("code")
        safe_code = code if isinstance(code, str) else "MALFORMED_PROVIDER_RESPONSE"
        if result.outcome in {"auth_error", "permanent", "malformed"}:
            failed = self._outbox.transition(
                logical_report_id,
                OutboxState.FAILED_PERMANENT,
                last_error_code=safe_code,
            )
            return _receipt(DispatchOutcome.FAILED_PERMANENT, failed)
        retry_after = result.payload.get("retry_after_sec", 1)
        delay = float(retry_after) if isinstance(retry_after, (int, float)) else 1.0
        retry_at = self._clock.monotonic() + max(1.0, delay)
        waiting = self._outbox.transition(
            logical_report_id,
            OutboxState.RETRY_WAIT,
            last_error_code=safe_code,
            retry_not_before=format(retry_at, ".9f").rstrip("0").rstrip("."),
        )
        return _receipt(DispatchOutcome.RETRY_WAIT, waiting)


def _receipt(outcome: DispatchOutcome, item: OutboxItem) -> DispatchReceipt:
    return DispatchReceipt(
        outcome,
        item.logical_report_id,
        item.attempts,
        provider_id=item.provider_id,
        error_code=item.last_error_code,
    )

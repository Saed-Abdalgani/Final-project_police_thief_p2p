"""Deterministic MCP-series and outbox-outage measurements for M11."""

from police_thief_p2p.adapters.system.clocks import FakeClock
from police_thief_p2p.domain import Role
from police_thief_p2p.services.protocol.envelope import ProtocolEnvelope, SenderIdentity
from police_thief_p2p.services.protocol.inventory import MUTATING_TOOLS
from police_thief_p2p.services.reporting.models import OutboxItem, OutboxState
from police_thief_p2p.services.reporting.outbox import DurableOutbox
from police_thief_p2p.shared.version import PROTOCOL_VERSION
from scripts.m11_benchmark_support import measure
from scripts.m11_soak_support import MemoryRepository

_GAME_UID = "11111111-1111-4111-8111-111111111111"


def protocol_series_metrics() -> dict[str, object]:
    """Measure canonical transport bytes for a six-game, one-step series."""
    envelopes = tuple(
        ProtocolEnvelope(
            protocol_version=PROTOCOL_VERSION,
            message_type=tool,
            message_id=f"00000000-0000-4000-8000-{sequence:012d}",
            correlation_id="00000000-0000-4000-8000-000000000001",
            game_uid=_GAME_UID,
            sub_game_number=sub_game,
            step_number=1,
            sender=SenderIdentity(group_id="GRP00001", role=Role.POLICE),
            sequence=sequence,
            payload={"fixture": "m11-one-step-series"},
        )
        for sequence, (sub_game, tool) in enumerate(
            ((sub_game, tool) for sub_game in range(1, 7) for tool in sorted(MUTATING_TOOLS)),
            start=1,
        )
    )
    sizes = tuple(len(item.canonical_bytes()) for item in envelopes)
    latency = measure(
        lambda: sum(len(item.canonical_bytes()) for item in envelopes),
        warmups=2,
        samples=20,
    )
    return {
        "workload": "six sub-games, one step, every mutating MCP tool",
        "request_count": len(envelopes),
        "request_bytes": sum(sizes),
        "retry_count_baseline": 0,
        "response_loss_campaign_retries": len(envelopes),
        "encoding_latency": latency.as_dict(),
    }


def outbox_outage_metrics() -> dict[str, object]:
    """Measure queue recovery and age across one deterministic provider outage."""
    repository = MemoryRepository()
    clock = FakeClock()
    outbox = DurableOutbox(repository)
    item = outbox.enqueue(
        OutboxItem(
            logical_report_id="a" * 64,
            game_uid=_GAME_UID,
            sender_group_id="GRP00001",
            attachment_name="official-report.json",
            attachment_sha256="b" * 64,
            attachment_b64="e30=",
            recipient="israelz@ariel.ac.il",
        )
    )
    maximum_depth = len(outbox.items())
    outbox.transition(item.logical_report_id, OutboxState.VALIDATED)
    outbox.transition(item.logical_report_id, OutboxState.SENDING)
    outbox.transition(
        item.logical_report_id,
        OutboxState.RETRY_WAIT,
        last_error_code="SIMULATED_GMAIL_503",
        retry_not_before="30",
    )
    clock.advance(30)
    recovered = DurableOutbox(repository)
    recovered.transition(item.logical_report_id, OutboxState.VALIDATED)
    recovered.transition(item.logical_report_id, OutboxState.SENDING)
    sent = recovered.transition(
        item.logical_report_id,
        OutboxState.SENT,
        provider_id="redacted-provider-id",
        last_error_code=None,
        retry_not_before=None,
    )
    return {
        "simulated_outage_seconds": 30,
        "outbox_age_seconds": clock.monotonic(),
        "dispatch_attempts": sent.attempts,
        "maximum_queue_depth": maximum_depth,
        "recovered_queue_depth": len(recovered.items()),
        "final_state": sent.state.value,
    }

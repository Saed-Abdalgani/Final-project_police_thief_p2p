"""SDK-owned composition root for one isolated protocol peer."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path

from police_thief_p2p.adapters.persistence import AtomicFileRepository
from police_thief_p2p.services.protocol.idempotency import IdempotencyRepository
from police_thief_p2p.services.protocol.limits import ProtocolLimits
from police_thief_p2p.services.protocol.negotiation import NegotiationService
from police_thief_p2p.services.protocol.negotiation_context import NegotiationContext
from police_thief_p2p.services.protocol.negotiation_models import CountedLedger
from police_thief_p2p.services.protocol.runtime import ProtocolRuntime
from police_thief_p2p.services.protocol.session import SessionRegistry
from police_thief_p2p.shared.config_loader import load_shared_bytes


def create_protocol_runtime(
    *,
    local_group: str,
    shared_document: bytes,
    storage_root: Path,
    counted_opponents: frozenset[str] = frozenset(),
    optional_capabilities: dict[str, object] | None = None,
    limits: ProtocolLimits | None = None,
    health_provider: Callable[[], Mapping[str, object]] | None = None,
) -> ProtocolRuntime:
    """Compose one protocol runtime using only its private durable root."""
    shared = load_shared_bytes(shared_document)
    records = AtomicFileRepository(storage_root)
    context = NegotiationContext(
        local_group=local_group,
        shared_config=shared,
        shared_raw_bytes=shared_document,
        ledger=CountedLedger(counted_opponents),
        optional_capabilities=optional_capabilities or {},
    )
    return ProtocolRuntime(
        local_group=local_group,
        negotiation=NegotiationService(context),
        sessions=SessionRegistry(local_group, records),
        idempotency=IdempotencyRepository(records),
        limits=limits or ProtocolLimits(),
        health_provider=health_provider,
    )

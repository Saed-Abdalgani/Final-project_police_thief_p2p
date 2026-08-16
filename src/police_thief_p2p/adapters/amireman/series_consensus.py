"""Final consensus exchange for an amireman compatibility series."""

from __future__ import annotations

import time
from typing import Any

from police_thief_p2p.adapters.amireman.wire import (
    CONSENSUS_TAG,
    AuditPayload,
    is_series_consensus,
)


def exchange_consensus(
    transport: Any,
    our_role: str,
    our_sha: str,
    turn_timeout: float,
    deferred: dict[str, Any] | None = None,
) -> str | None:
    """Exchange canonical result digests after the final audited game."""
    ours = AuditPayload(our_role, [], CONSENSUS_TAG, consensus_sha=our_sha).to_wire()
    transport.send_audit(ours)
    candidates = [deferred] if deferred is not None else []
    deadline = time.monotonic() + min(turn_timeout, 8.0)
    while True:
        for msg in candidates:
            peer = AuditPayload.from_wire(msg)
            if is_series_consensus(peer) and peer.consensus_sha:
                return peer.consensus_sha
        candidates = []
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        msg = transport.poll_audit(remaining)
        if msg is None:
            return None
        candidates.append(msg)

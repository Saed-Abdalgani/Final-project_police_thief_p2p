"""Local authoritative context for fail-closed negotiation."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from police_thief_p2p.services.protocol.negotiation_models import CountedLedger
from police_thief_p2p.shared.canonical_json import sha256_digest
from police_thief_p2p.shared.config_models import SharedConfig
from police_thief_p2p.shared.identifiers import GroupId


def deterministic_game_id(group_a: str, group_b: str, config_digest: str) -> str:
    """Derive a stable safe game slug independent of peer ordering."""
    groups = "-".join(sorted((str(GroupId(group_a)), str(GroupId(group_b)))))
    seed = f"{groups}:{config_digest}".encode()
    return f"match-{hashlib.sha256(seed).hexdigest()[:24]}"


@dataclass(frozen=True, slots=True)
class NegotiationContext:
    """Local authoritative terms used to validate remote proposals."""

    local_group: str
    shared_config: SharedConfig
    shared_raw_bytes: bytes
    ledger: CountedLedger
    optional_capabilities: dict[str, object]

    def __post_init__(self) -> None:
        """Validate the local identity and immutable byte input."""
        GroupId(self.local_group)

    @property
    def scent_digest(self) -> str:
        """Return the signed scent-model digest."""
        return sha256_digest(self.shared_config.pheromones.model_dump(mode="json"))

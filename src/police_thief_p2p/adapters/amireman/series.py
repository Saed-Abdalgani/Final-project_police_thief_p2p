"""Identity helpers and series orchestration for the amireman wire."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from police_thief_p2p.adapters.amireman.canonical import consensus_sha, settlement_sha
from police_thief_p2p.adapters.amireman.negotiate import Negotiator
from police_thief_p2p.adapters.amireman.runtime import SubGameRuntime
from police_thief_p2p.adapters.amireman.scoring import aggregate, canonical_rows, role_for
from police_thief_p2p.adapters.amireman.scent import MULTIPLICATIVE_KERNEL_V1
from police_thief_p2p.adapters.amireman.wire import (
    CONSENSUS_TAG,
    AuditPayload,
    is_series_consensus,
)

DEFAULT_REPOS = {
    "cop": "https://github.com/JCS1029/GRP00001-police-p2p",
    "thief": "https://github.com/JCS1029/GRP00001-thief-p2p",
}
BOOK_V1_CONFIG_SHA256 = "3835f6a137620d8d98ab3925b2d1ed397d2d20d23bb9ba857bcd104284aac443"
BOOK_V1_SCENT_SHA256 = "ea7225f5d71989add99a0057287342b7c5b86ab4efffd1608da25d0e368c0a28"
WIRE_CODE_VERSION = "1.00"


def mcp_servers_for(public_mcp_url: str | None) -> dict[str, str]:
    if not public_mcp_url:
        return {}
    return {"cop": public_mcp_url, "thief": public_mcp_url}


def identity_for(
    group: str,
    *,
    members: list[str],
    github_commit: str,
    public_mcp_url: str | None = None,
    repos: dict[str, str] | None = None,
    llm_model: str = "template",
    scent_model: str = MULTIPLICATIVE_KERNEL_V1,
) -> dict[str, Any]:
    identity: dict[str, Any] = {
        "group_id": group,
        "group_name": group,
        "git_commit_hash": github_commit,
        "github_commit": github_commit,
        "members": list(members),
        "repos": repos or dict(DEFAULT_REPOS),
        "mcp_servers": mcp_servers_for(public_mcp_url),
        "llm_model": llm_model,
        "code_version": WIRE_CODE_VERSION,
        "first_mover": "thief",
    }
    if scent_model == MULTIPLICATIVE_KERNEL_V1:
        identity["config_sha256"] = BOOK_V1_CONFIG_SHA256
        identity["scent_model_sha256"] = BOOK_V1_SCENT_SHA256
    return identity


@dataclass
class SeriesResult:
    summaries: list = field(default_factory=list)
    own_identity: dict = field(default_factory=dict)
    peer_identity: dict = field(default_factory=dict)
    game_id: str | None = None
    game_uid: str | None = None
    consensus_sha: str | None = None
    peer_consensus_sha: str | None = None
    settlement_sha: str | None = None
    sha_match: bool = False
    results_agreed: bool = False


def _exchange_consensus(
    transport, our_role, our_sha, turn_timeout, deferred: dict | None = None
) -> str | None:
    ours = AuditPayload(our_role, [], CONSENSUS_TAG, consensus_sha=our_sha).to_wire()
    transport.send_audit(ours)
    candidates = []
    if deferred is not None:
        candidates.append(deferred)
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


def run_series(
    terms: dict[str, Any],
    natural_role: str,
    transport: Any,
    group: str,
    github_commit: str,
    own_identity: dict[str, Any],
    *,
    num_games: int = 6,
    seed: int = 1234,
    listener: Callable[[dict], None] | None = None,
    turn_timeout: float = 180.0,
    game_id: str | None = None,
    scent_model: str = MULTIPLICATIVE_KERNEL_V1,
) -> SeriesResult:
    result = SeriesResult(own_identity=own_identity)
    known_opponent: str | None = None
    deferred_consensus: dict | None = None
    for n in range(1, num_games + 1):
        role = role_for(natural_role, n)
        negotiator = Negotiator(terms, own_identity, group)
        peer_msg = transport.exchange_agreement(
            negotiator.signed(role, n, opponent_group=known_opponent).to_wire()
        )
        agreed = negotiator.verify_peer(peer_msg)
        result.game_id = game_id or agreed.game_id
        result.game_uid = agreed.game_uid
        known_opponent = agreed.opponent_group
        result.peer_identity = agreed.opponent_identity or result.peer_identity
        if listener is not None:
            listener({"type": "negotiated", "sub_game": n, "role": role, "game_id": result.game_id})
        runtime = SubGameRuntime(
            role, terms, transport, group, github_commit, n, seed, listener, scent_model=scent_model
        )
        result.summaries.append(runtime.run(turn_timeout=turn_timeout))
        if runtime.deferred_consensus is not None:
            deferred_consensus = runtime.deferred_consensus
    theirs = result.peer_identity.get("group_id", "")
    rows = canonical_rows(result.summaries, group, theirs)
    result.consensus_sha = consensus_sha(result.game_id or "", result.game_uid or "", rows)
    result.settlement_sha = settlement_sha(result.game_id or "", aggregate(rows), rows)
    result.results_agreed = bool(result.summaries) and all(
        s["audit"].get("result_agreed", False) for s in result.summaries
    )
    result.peer_consensus_sha = _exchange_consensus(
        transport, natural_role, result.consensus_sha, turn_timeout, deferred_consensus
    )
    result.sha_match = (
        result.peer_consensus_sha is not None and result.peer_consensus_sha == result.consensus_sha
    )
    return result

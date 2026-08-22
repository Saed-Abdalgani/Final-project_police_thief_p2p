"""Identity helpers and series orchestration for the amireman wire."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from police_thief_p2p.adapters.amireman.canonical import consensus_sha, settlement_sha
from police_thief_p2p.adapters.amireman.negotiate import Negotiator
from police_thief_p2p.adapters.amireman.runtime import SubGameRuntime
from police_thief_p2p.adapters.amireman.scent import MULTIPLICATIVE_KERNEL_V1
from police_thief_p2p.adapters.amireman.scoring import aggregate, canonical_rows, role_for
from police_thief_p2p.adapters.amireman.series_consensus import exchange_consensus
from police_thief_p2p.adapters.amireman.series_identity import (
    BOOK_V1_CONFIG_SHA256 as BOOK_V1_CONFIG_SHA256,
)
from police_thief_p2p.adapters.amireman.series_identity import (
    BOOK_V1_SCENT_SHA256 as BOOK_V1_SCENT_SHA256,
)
from police_thief_p2p.adapters.amireman.series_identity import (
    DEFAULT_REPOS as DEFAULT_REPOS,
)
from police_thief_p2p.adapters.amireman.series_identity import (
    WIRE_CODE_VERSION as WIRE_CODE_VERSION,
)
from police_thief_p2p.adapters.amireman.series_identity import (
    attest_role as attest_role,
)
from police_thief_p2p.adapters.amireman.series_identity import (
    identity_for as identity_for,
)
from police_thief_p2p.adapters.amireman.series_identity import (
    mcp_servers_for as mcp_servers_for,
)

if TYPE_CHECKING:
    from police_thief_p2p.sdk import CompatibilityStrategySession


@dataclass
class SeriesResult:
    """Six-game summaries, consensus, and private audited training records."""

    summaries: list[dict[str, Any]] = field(default_factory=list)
    own_identity: dict[str, Any] = field(default_factory=dict)
    peer_identity: dict[str, Any] = field(default_factory=dict)
    game_id: str | None = None
    game_uid: str | None = None
    consensus_sha: str | None = None
    peer_consensus_sha: str | None = None
    settlement_sha: str | None = None
    sha_match: bool = False
    results_agreed: bool = False
    training_records: list[dict[str, Any]] = field(default_factory=list)


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
    listener: Callable[[dict[str, Any]], None] | None = None,
    turn_timeout: float = 180.0,
    game_id: str | None = None,
    game_uid: str | None = None,
    scent_model: str = MULTIPLICATIVE_KERNEL_V1,
    strategy_session: CompatibilityStrategySession | None = None,
    police_commit: str | None = None,
    thief_commit: str | None = None,
    canonical_commit: str | None = None,
) -> SeriesResult:
    """Negotiate and play a role-alternating compatibility series."""
    result = SeriesResult(own_identity=own_identity)
    known_opponent: str | None = None
    deferred_consensus: dict[str, Any] | None = None
    police_sha = police_commit or github_commit
    thief_sha = thief_commit or github_commit
    for n in range(1, num_games + 1):
        role = role_for(natural_role, n)
        identity, role_sha = attest_role(
            own_identity,
            role,
            police_commit=police_sha,
            thief_commit=thief_sha,
            canonical_commit=canonical_commit,
        )
        negotiator = Negotiator(terms, identity, group, game_id=game_id, game_uid=game_uid)
        peer_msg = transport.exchange_agreement(
            negotiator.signed(role, n, opponent_group=known_opponent).to_wire()
        )
        agreed = negotiator.verify_peer(peer_msg)
        result.game_id = game_id or agreed.game_id
        result.game_uid = game_uid or agreed.game_uid
        result.own_identity = identity
        known_opponent = agreed.opponent_group
        result.peer_identity = agreed.opponent_identity or result.peer_identity
        if strategy_session is not None:
            strategy_session.start_subgame(
                role,
                n,
                opponent_id=known_opponent,
                scent_model=scent_model,
            )
        if listener is not None:
            listener({"type": "negotiated", "sub_game": n, "role": role, "game_id": result.game_id})
        runtime = SubGameRuntime(
            role,
            terms,
            transport,
            group,
            role_sha,
            n,
            seed,
            listener,
            scent_model=scent_model,
            strategy_session=strategy_session,
        )
        summary = runtime.run(turn_timeout=turn_timeout)
        result.summaries.append(summary)
        audit_passed = bool(summary["audit"].get("passed"))
        if strategy_session is not None:
            strategy_session.complete_audited_subgame(
                runtime.peer_records,
                audit_passed=audit_passed,
            )
        if audit_passed:
            result.training_records.append(
                {
                    "sub_game_number": n,
                    "role": role,
                    "own_records": runtime.engine.records,
                    "peer_records": runtime.peer_records,
                }
            )
        if runtime.deferred_consensus is not None:
            deferred_consensus = runtime.deferred_consensus
    theirs = result.peer_identity.get("group_id", "")
    rows = canonical_rows(result.summaries, group, theirs)
    result.consensus_sha = consensus_sha(result.game_id or "", result.game_uid or "", rows)
    result.settlement_sha = settlement_sha(result.game_id or "", aggregate(rows), rows)
    result.results_agreed = bool(result.summaries) and all(
        s["audit"].get("result_agreed", False) for s in result.summaries
    )
    result.peer_consensus_sha = exchange_consensus(
        transport, natural_role, result.consensus_sha, turn_timeout, deferred_consensus
    )
    result.sha_match = (
        result.peer_consensus_sha is not None and result.peer_consensus_sha == result.consensus_sha
    )
    return result

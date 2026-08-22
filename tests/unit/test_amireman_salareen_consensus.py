"""Salareen official_reference_v1 consensus digest (wired settlement_sha)."""

from __future__ import annotations

from police_thief_p2p.adapters.amireman.canonical import consensus_sha, settlement_sha
from police_thief_p2p.adapters.amireman.scoring import aggregate
from police_thief_p2p.adapters.amireman.series_consensus import exchange_consensus
from police_thief_p2p.adapters.amireman.wire import AuditPayload

SALAREEN_VECTOR_SHA = "a2c55e1b164a19177b8f2aa5c5211ce78b013724c43c9e91134838533e780d9b"
GAME_ID = "GRP00001-vs-salareen"
GAME_UID = "4c32e6bd-a04b-f490-c6c1-a684a9d8903d"


def _salareen_rows() -> list[dict]:
    rows = []
    for n in range(1, 7):
        odd = n % 2 == 1
        rows.append(
            {
                "sub_game_number": n,
                "result": "capture" if odd else "survival",
                "roles": {
                    "salareen": "police" if odd else "thief",
                    "GRP00001": "thief" if odd else "police",
                },
                "score": {
                    "salareen": 20 if odd else 10,
                    "GRP00001": 5,
                },
                "winner_group": "salareen",
            }
        )
    return rows


def test_shared_salareen_vector_reproduces_a2c55e1b() -> None:
    rows = _salareen_rows()
    totals = aggregate(rows)
    assert totals == {
        "total_score": {"GRP00001": 30, "salareen": 90},
        "sub_games_won": {"GRP00001": 0, "salareen": 6},
        "ties": 0,
        "winner_group": "salareen",
        "series_tie": False,
    }
    digest = settlement_sha(GAME_ID, totals, rows)
    assert digest == SALAREEN_VECTOR_SHA
    shuffled = list(reversed(rows))
    assert settlement_sha(GAME_ID, aggregate(shuffled), shuffled) == SALAREEN_VECTOR_SHA


def test_wired_digest_equals_local_settlement_not_compact_consensus() -> None:
    rows = _salareen_rows()
    local = settlement_sha(GAME_ID, aggregate(rows), rows)
    compact = consensus_sha(GAME_ID, GAME_UID, rows)
    assert local == SALAREEN_VECTOR_SHA
    assert compact != local

    sent: dict = {}

    class _Transport:
        def send_audit(self, payload: dict) -> None:
            sent.update(payload)

        def poll_audit(self, timeout: float) -> dict | None:
            del timeout
            return AuditPayload("police", [], "series_consensus", consensus_sha=local).to_wire()

    peer = exchange_consensus(_Transport(), "thief", local, 1.0)
    assert sent["consensus_sha"] == local
    assert peer == local
    assert sent["consensus_sha"] == settlement_sha(GAME_ID, aggregate(rows), rows)

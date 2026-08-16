"""ahk-yosi reference-family landmines: scent serve, audit envelope, capture."""

from __future__ import annotations

from police_thief_p2p.adapters.amireman.half import PeerHalf
from police_thief_p2p.adapters.amireman.runtime import SubGameRuntime
from police_thief_p2p.adapters.amireman.scent import decay_only, grid_out, step_update
from police_thief_p2p.adapters.amireman.terms import default_terms
from police_thief_p2p.adapters.amireman.wire import AuditPayload, TurnMessage, is_series_consensus


class _FakeTransport:
    def __init__(self, audits: list[dict]) -> None:
        self._audits = list(audits)
        self.sent: dict | None = None
        self.last_turn: dict | None = None

    def send_audit(self, payload: dict) -> None:
        self.sent = payload

    def poll_audit(self, timeout: float) -> dict | None:
        return self._audits.pop(0) if self._audits else None

    def send_turn(self, message: dict) -> None:
        self.last_turn = message

    def poll_turn(self, timeout: float) -> dict | None:
        return None


def test_tau0_serves_0_81_not_0_9() -> None:
    field = step_update({}, (3, 3), 7, 0.1)
    served = grid_out(decay_only(field, 0.1))
    assert served["3,3"] == 0.81
    assert served["3,3"] != 0.9


def test_first_thief_turn_serves_decayed_center() -> None:
    half = PeerHalf("thief", default_terms(setting="New York"), "saedshki", "c" * 40, 1, 7)
    out = half.act()
    assert out["scent"]["3,3"] == 0.81
    assert half.records[-1]["payload"]["sub_game"] == 1
    assert half.records[-1]["payload"]["sub_game_number"] == 1
    assert half.records[0]["payload"]["sub_game"] == 1


def test_police_capture_claim_is_unsuppressable() -> None:
    half = PeerHalf("police", default_terms(), "saedshki", "c" * 40, 2, 3)
    out = half.act()
    assert out["claim"] == list(half.pos)
    assert half.records[-1]["payload"]["capture_claim"] == list(half.pos)


def test_thief_enclosure_win_claim_is_not_scored_as_survival() -> None:
    transport = _FakeTransport([])
    runtime = SubGameRuntime("thief", default_terms(), transport, "saedshki", "c" * 40, 1)
    runtime.engine.half.pos = (0, 0)
    runtime.engine.half.barriers = {(0, 1), (1, 0)}
    runtime._process(TurnMessage(step=2, sender="police", commit="b" * 64, hint=""))
    assert runtime.result == ("capture", "police")
    assert transport.last_turn is not None
    assert transport.last_turn.get("win_claim") == {"type": "capture"}


def test_audit_envelope_names_sub_game_and_skips_consensus() -> None:
    consensus = {
        "sender": "thief",
        "records": [],
        "result_claim": "series_consensus",
        "consensus_sha": "a" * 64,
    }
    reveal = {
        "sender": "thief",
        "sub_game": 3,
        "sub_game_number": 3,
        "records": [],
        "result_claim": "capture",
    }
    transport = _FakeTransport([consensus, reveal])
    runtime = SubGameRuntime("police", default_terms(), transport, "saedshki", "c" * 40, 3)
    audit = runtime._exchange_audit("capture", 2.0)
    assert is_series_consensus(consensus) is True
    assert runtime.deferred_consensus == consensus
    assert audit["peer_result_claim"] == "capture"
    assert audit["result_agreed"] is True
    assert transport.sent is not None
    assert transport.sent["sub_game"] == 3
    assert transport.sent["sub_game_number"] == 3
    parsed = AuditPayload.from_wire(transport.sent)
    assert parsed.sub_game == 3
    assert parsed.sub_game_number == 3


def test_police_last_move_sets_survival_result() -> None:
    transport = _FakeTransport([])
    runtime = SubGameRuntime("police", default_terms(), transport, "saedshki", "c" * 40, 1)
    runtime.engine.half.step = 34
    runtime._take_turn()
    assert runtime.result == ("survival", "thief")
    assert transport.last_turn is not None
    assert transport.last_turn.get("win_claim") == {"type": "survival"}


def test_inbound_audit_ends_wait_without_timeout() -> None:
    reveal = {
        "sender": "thief",
        "sub_game": 1,
        "sub_game_number": 1,
        "records": [],
        "result_claim": "survival",
    }
    transport = _FakeTransport([reveal])
    runtime = SubGameRuntime("police", default_terms(), transport, "saedshki", "c" * 40, 1)
    summary = runtime.run(turn_timeout=30.0)
    assert summary["result"] == "survival"
    assert summary["duration_seconds"] < 2.0
    assert summary["audit"]["peer_result_claim"] == "survival"
    assert summary["audit"]["skipped"] is False


def test_stale_audit_from_other_subgame_is_ignored() -> None:
    stale = {
        "sender": "thief",
        "sub_game": 1,
        "sub_game_number": 1,
        "records": [],
        "result_claim": "survival",
    }
    transport = _FakeTransport([stale])
    runtime = SubGameRuntime("thief", default_terms(), transport, "saedshki", "c" * 40, 2)
    summary = runtime.run(turn_timeout=0.2)
    assert summary["result"] == "timeout"
    assert transport.last_turn is not None
    assert transport.last_turn.get("step") == 1


def test_thief_closes_immediately_on_peer_capture_audit() -> None:
    reveal = {
        "sender": "police",
        "sub_game": 2,
        "sub_game_number": 2,
        "records": [],
        "result_claim": "capture",
    }
    transport = _FakeTransport([reveal])
    runtime = SubGameRuntime("thief", default_terms(), transport, "saedshki", "c" * 40, 2)
    summary = runtime.run(turn_timeout=30.0)
    assert summary["result"] == "capture"
    assert summary["winner"] == "police"
    assert summary["duration_seconds"] < 2.0
    assert summary["audit"]["peer_result_claim"] == "capture"

"""SMNGRP05 / reference-v3 contract: hashes, thief-first, Chebyshev scent, 10-key turns."""

from __future__ import annotations

from pathlib import Path

import pytest

from police_thief_p2p.adapters.amireman.canonical import derive_game_ids, seal, terms_digest
from police_thief_p2p.adapters.amireman.config_map import load_terms
from police_thief_p2p.adapters.amireman.engine import SubEngine
from police_thief_p2p.adapters.amireman.half import PeerHalf
from police_thief_p2p.adapters.amireman.negotiate import NegotiationRefusedError, Negotiator
from police_thief_p2p.adapters.amireman.runtime import SubGameRuntime
from police_thief_p2p.adapters.amireman.scent import (
    SUBTRACTIVE_CHEBYSHEV_V1,
    decay_only,
    grid_out,
    step_update,
)
from police_thief_p2p.adapters.amireman.self_mail import _assert_policy
from police_thief_p2p.adapters.amireman.terms import default_terms
from police_thief_p2p.adapters.amireman.wire import TURN_KEYS, TurnMessage
from police_thief_p2p.constants import REQUIRED_REPORT_RECIPIENT

NY_HASH = "a284082dfb1572236f1b614d29295a99625539c7d33a096f7f8921bafbc3d08d"
HAIFA_HASH = "ad9e1bfd724e9debcde523833381cb7982a5d619d693d3738b59e0da61f4d81a"


def test_smngrp05_published_contract_hashes() -> None:
    assert terms_digest(default_terms(setting="New York")) == NY_HASH
    assert terms_digest(default_terms(setting="Haifa")) == HAIFA_HASH


def test_smngrp05_terms_file_matches_new_york_hash() -> None:
    from pathlib import Path

    path = Path(__file__).resolve().parents[2] / "config" / "shared" / "smngrp05.terms.json"
    assert terms_digest(load_terms(path)) == NY_HASH


def test_subtractive_chebyshev_serves_0_80() -> None:
    field = step_update({}, (3, 3), 7, 0.1, SUBTRACTIVE_CHEBYSHEV_V1)
    served = grid_out(decay_only(field, 0.1, SUBTRACTIVE_CHEBYSHEV_V1))
    assert served["3,3"] == 0.8
    assert served["3,3"] != 0.81
    assert served["3,4"] == 0.5
    assert served["3,5"] == 0.2


def test_first_thief_turn_subtractive_center_is_0_80() -> None:
    half = PeerHalf(
        "thief",
        default_terms(setting="New York"),
        "saedshki",
        "c" * 40,
        1,
        7,
        scent_model=SUBTRACTIVE_CHEBYSHEV_V1,
    )
    out = half.act()
    assert out["scent"]["3,3"] == 0.8


def test_turn_wire_is_exactly_ten_keys_with_explicit_nulls() -> None:
    engine = SubEngine("police", default_terms(), "saedshki", "c" * 40, 1)
    message = engine.take_turn()
    wire = message.to_wire()
    assert tuple(wire) == TURN_KEYS
    assert set(wire) == set(TURN_KEYS)
    assert len(wire) == 10
    assert wire["win_claim"] is None
    extra = TurnMessage.from_wire({**wire, "unknown_field": "nope"})
    assert "unknown_field" not in extra.to_wire()


def test_terms_mismatch_names_key_and_both_values() -> None:
    ours = default_terms(setting="New York")
    theirs = default_terms(setting="Haifa")
    negotiator = Negotiator(ours, {"group_id": "saedshki"}, "saedshki")
    greeting = {
        "terms": theirs,
        "nonce": "a" * 32,
        "signature": "b" * 64,
        "group_id": "SMNGRP05",
    }
    with pytest.raises(NegotiationRefusedError, match="setting: ours='New York' theirs='Haifa'"):
        negotiator.verify_peer(greeting)


def test_mail_policy_allows_opponent_blocks_lecturer_unless_allowlisted() -> None:
    me = "lovely.lololagain@gmail.com"
    them = "afafgharra000@gmail.com"
    _assert_policy(me, me, (me, them))
    _assert_policy(me, them, (me, them))
    with pytest.raises(ValueError, match="allowlist"):
        _assert_policy(me, REQUIRED_REPORT_RECIPIENT, (me, them))
    _assert_policy(me, REQUIRED_REPORT_RECIPIENT, (me, REQUIRED_REPORT_RECIPIENT))


class _SilentTransport:
    def send_audit(self, payload: dict) -> None:
        return None

    def poll_audit(self, timeout: float) -> dict | None:
        return None

    def send_turn(self, message: dict) -> None:
        return None

    def poll_turn(self, timeout: float) -> dict | None:
        return None


def test_smngrp05_game_uid_matches_their_fourth_friendly() -> None:
    path = Path(__file__).resolve().parents[2] / "config" / "shared" / "smngrp05.terms.json"
    assert derive_game_ids(load_terms(path), "SMNGRP05", "saedshki") == (
        "SMNGRP05-vs-saedshki",
        "bbf29792-ddb5-74ac-dab5-dfbaf532ec61",
    )


def test_reference_v3_step0_tag_does_not_drop_live_steps() -> None:
    runtime = SubGameRuntime(
        "police", default_terms(setting="New York"), _SilentTransport(), "saedshki", "c" * 40, 1
    )
    spec = {"step": 0, "type": "system_spec", "sub_game_number": 1}
    live = {"step": 1, "role": "thief", "hint": "moving carefully", "move": "N"}
    sealed_live = seal(live)
    records = [{"payload": spec, **seal(spec)}, {"payload": live, **sealed_live}]
    runtime.inbox.played = {1: sealed_live["commit"]}
    scoped = runtime._records_for_this_game(records)
    assert len(scoped) == 2
    audit = runtime._verify_theirs(records)
    assert audit["tampered"] is False
    assert audit["log_verified"] is True
    assert audit["failed_steps"] == []
    assert audit["verified_steps"] == 2
    assert audit["example"] is None

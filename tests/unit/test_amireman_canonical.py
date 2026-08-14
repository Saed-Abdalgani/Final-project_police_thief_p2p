"""Golden tests for amireman canonical crypto and ids."""

from __future__ import annotations

from police_thief_p2p.adapters.amireman.canonical import (
    audit_records,
    canonical,
    commit_of,
    consensus_sha,
    derive_game_ids,
    seal,
    verify,
)
from police_thief_p2p.adapters.amireman.config_map import load_terms, terms_from_nested_game
from police_thief_p2p.adapters.amireman.terms import DEFAULTS, default_terms, validate_terms


def test_canonical_is_compact_sorted() -> None:
    assert canonical({"b": 1, "a": 2}) == '{"a":2,"b":1}'


def test_commit_of_matches_appendix_b() -> None:
    terms = default_terms()
    nonce = "a" * 32
    digest = commit_of(terms, nonce)
    assert len(digest) == 64
    assert digest == commit_of(dict(terms), nonce)
    assert verify(terms, nonce, digest)


def test_derive_game_ids_order_independent() -> None:
    terms = default_terms()
    a = derive_game_ids(terms, "saedshki", "amireman")
    b = derive_game_ids(terms, "amireman", "saedshki")
    assert a == b
    assert a[0] == "amireman-vs-saedshki"
    assert len(a[1]) == 36


def test_consensus_sha_stable() -> None:
    rows = [
        {
            "sub_game_number": 1,
            "result": "survival",
            "roles": {"saedshki": "police", "amireman": "thief"},
            "score": {"saedshki": 5, "amireman": 10},
            "winner_group": "amireman",
        }
    ]
    left = consensus_sha("DEMO1", "uid", rows)
    right = consensus_sha("DEMO1", "uid", list(reversed(rows)))
    assert left == right
    assert len(left) == 64


def test_audit_records_roundtrip() -> None:
    payload = {"step": 1, "move": "STAY"}
    sealed = seal(payload)
    records = [{"payload": payload, **sealed}]
    assert audit_records(records)["passed"] is True


def test_nested_game_maps_to_flat_terms(tmp_path) -> None:
    nested = {
        "board_and_agents": {
            "grid_size": 7,
            "thief_start": [3, 3],
            "cop_start": [0, 0],
            "axis_origin_corner": "top-left",
            "axis_start_index": 0,
        },
        "world": {"map_area": "Haifa", "hint_max_words": 15},
        "movement_and_barriers": {"max_barriers": 14, "max_moves": 35},
        "pheromones": {
            "pheromone_center_intensity": 0.9,
            "pheromone_decay": 0.1,
            "pheromone_grid_size": 5,
        },
        "network_and_league": {"num_games": 6},
    }
    terms = terms_from_nested_game(nested)
    validate_terms(terms)
    assert terms == DEFAULTS
    path = tmp_path / "game.json"
    path.write_text(
        '{"schema_version":"1.2","board_and_agents":{"grid_size":7,"thief_start":[3,3],'
        '"cop_start":[0,0],"axis_origin_corner":"top-left","axis_start_index":0},'
        '"world":{"map_area":"Haifa","hint_max_words":15},'
        '"movement_and_barriers":{"max_barriers":14,"max_moves":35},'
        '"pheromones":{"pheromone_center_intensity":0.9,"pheromone_decay":0.1,'
        '"pheromone_grid_size":5},"network_and_league":{"num_games":6}}',
        encoding="utf-8",
    )
    assert load_terms(path)["setting"] == "Haifa"


AHK_YOSI_TERMS = {
    "axis_origin_corner": "top-left",
    "axis_start_index": 0,
    "barriers_max": 14,
    "board_size": 7,
    "cop_start": [0, 0],
    "decay_per_step": 0.1,
    "emit_intensity": 0.9,
    "hint_max_words": 15,
    "max_steps": 35,
    "min_center_intensity": 0.5,
    "num_games": 6,
    "setting": "New York",
    "smell_grid_size": 5,
    "thief_start": [3, 3],
}


def test_ahk_yosi_commit_golden_vectors() -> None:
    assert (
        commit_of({"a": 1}, "abababababababababababababababab")
        == "2d5faf71c42626d681a5727c2e7940af4c8e21e7f59f3acd6e063ae654bcee0a"
    )
    step = {
        "barrier": None,
        "hint": "north side",
        "intent": "lie",
        "kind": "step",
        "move": "E",
        "pos_after": [3, 4],
        "pos_before": [3, 3],
        "role": "thief",
        "scent": [[0.0, 0.0], [0.0, 0.81]],
        "step": 1,
        "sub_game": 1,
        "sub_game_number": 1,
    }
    assert (
        commit_of(step, "abababababababababababababababab")
        == "a963512dd17cb3b86f6fe1d9027d1b03de14cdbd791f4c809d98e8b4ff9836a0"
    )


def test_ahk_yosi_game_uid_golden_vectors() -> None:
    assert derive_game_ids(AHK_YOSI_TERMS, "ahk-yosi", "amireman") == (
        "ahk-yosi-vs-amireman",
        "4cada35c-bba4-72c7-0838-d6fd723e13b8",
    )
    assert derive_game_ids(AHK_YOSI_TERMS, "ahk-yosi", "saedshki") == (
        "ahk-yosi-vs-saedshki",
        "749e57f6-03b8-5f91-7323-ec193385c9a1",
    )


def test_ahk_yosi_consensus_golden_vector() -> None:
    rows = [
        {
            "sub_game_number": 1,
            "result": "survival",
            "roles": {"ahk-yosi": "police", "them": "thief"},
            "score": {"ahk-yosi": 5, "them": 10},
            "winner_group": "them",
        },
        {
            "sub_game_number": 2,
            "result": "capture",
            "roles": {"ahk-yosi": "thief", "them": "police"},
            "score": {"ahk-yosi": 5, "them": 20},
            "winner_group": "them",
        },
    ]
    assert (
        consensus_sha("a-vs-b", "uid-1234", rows)
        == "3d2eddb4692b0a42fa3b01a37ad9241f40734687730be4f74724c5b115443764"
    )


def test_ahk_yosi_terms_file_loads() -> None:
    from pathlib import Path

    path = Path(__file__).resolve().parents[2] / "config" / "shared" / "ahk-yosi.terms.json"
    terms = load_terms(path)
    assert terms["setting"] == "New York"
    assert terms["board_size"] == 7
    assert terms["cop_start"] == [0, 0]

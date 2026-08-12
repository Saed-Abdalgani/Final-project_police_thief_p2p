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

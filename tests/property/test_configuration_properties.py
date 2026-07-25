import json
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from police_thief_p2p.shared.canonical_json import canonical_json_bytes
from police_thief_p2p.shared.config_loader import load_shared_bytes
from police_thief_p2p.shared.coordinates import CoordinateTransform, OriginCorner, Position

ROOT = Path(__file__).parents[2]
BASE = json.loads((ROOT / "config/shared/game.example.json").read_text(encoding="utf-8"))

safe_text = st.text(
    alphabet=st.characters(
        codec="utf-8",
        blacklist_characters=("\x00",),
    ),
    max_size=20,
)
json_scalars = st.none() | st.booleans() | st.integers(-1_000_000, 1_000_000) | safe_text
json_values = st.recursive(
    json_scalars,
    lambda children: st.lists(children, max_size=5)
    | st.dictionaries(safe_text.filter(bool), children, max_size=5),
    max_leaves=20,
)


@given(json_values)
def test_canonicalization_is_idempotent(value: object) -> None:
    first = canonical_json_bytes(value)
    decoded = json.loads(first)
    assert canonical_json_bytes(decoded) == first


@given(
    grid_size=st.integers(7, 100),
    token_budget=st.integers(1, 1_000_000),
    response_timeout=st.integers(1, 300),
    extra_watchdog=st.integers(0, 300),
)
def test_shared_config_round_trip_is_canonical(
    grid_size: int,
    token_budget: int,
    response_timeout: int,
    extra_watchdog: int,
) -> None:
    value = json.loads(json.dumps(BASE))
    value["board_and_agents"]["grid_size"] = grid_size
    value["network_and_league"]["token_budget_per_series"] = token_budget
    value["network_and_league"]["response_timeout_sec"] = response_timeout
    value["network_and_league"]["watchdog_timeout_sec"] = response_timeout + extra_watchdog
    model = load_shared_bytes(json.dumps(value).encode())
    reloaded = load_shared_bytes(model.canonical_bytes())
    assert reloaded == model
    assert reloaded.canonical_bytes() == model.canonical_bytes()


@given(
    grid_size=st.integers(1, 1000),
    row=st.integers(0, 999),
    col=st.integers(0, 999),
    origin=st.sampled_from(list(OriginCorner)),
    start_index=st.sampled_from([0, 1]),
)
def test_coordinate_round_trip_property(
    grid_size: int,
    row: int,
    col: int,
    origin: OriginCorner,
    start_index: int,
) -> None:
    row %= grid_size
    col %= grid_size
    transform = CoordinateTransform(grid_size, origin, start_index)
    position = Position(row, col)
    assert transform.to_canonical(transform.from_canonical(position)) == position

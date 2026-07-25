import json
from decimal import Decimal
from pathlib import Path

import pytest

from police_thief_p2p.shared.coordinates import (
    CoordinateTransform,
    OriginCorner,
    Position,
)
from police_thief_p2p.shared.scent import ScentPolicy

ROOT = Path(__file__).parents[2]


@pytest.mark.parametrize("origin", list(OriginCorner))
@pytest.mark.parametrize("start_index", [0, 1])
def test_all_coordinate_conventions_round_trip(
    origin: OriginCorner,
    start_index: int,
) -> None:
    transform = CoordinateTransform(7, origin, start_index)
    external = (start_index + 1, start_index + 5)
    assert transform.from_canonical(transform.to_canonical(external)) == external


def test_coordinate_transform_rejects_invalid_conventions_and_cells() -> None:
    with pytest.raises(ValueError, match="positive"):
        CoordinateTransform(0, OriginCorner.TOP_LEFT, 0)
    with pytest.raises(ValueError, match="0 or 1"):
        CoordinateTransform(7, OriginCorner.TOP_LEFT, 2)
    transform = CoordinateTransform(7, OriginCorner.TOP_LEFT, 0)
    with pytest.raises(ValueError, match="outside"):
        transform.to_canonical((-1, 0))
    with pytest.raises(ValueError, match="outside"):
        transform.from_canonical(Position(7, 0))


def test_scent_policy_matches_signed_golden_vector() -> None:
    vector = json.loads(
        (ROOT / "data/conformance/scent/emission_decay.json").read_text(encoding="utf-8")
    )
    policy = ScentPolicy()
    actual = [[policy.serialize(value) for value in row] for row in policy.emission()]
    assert actual == vector["expected_emission"]
    assert policy.serialize(policy.after_full_turn(Decimal("0.900000"))) == "0.810000"
    assert policy.serialize(policy.after_full_turn(Decimal("0.056250"))) == "0.050625"


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"center_intensity": Decimal("-0.1")}, "center_intensity"),
        ({"decay": Decimal("1.1")}, "decay"),
        ({"decimal_places": 13}, "decimal_places"),
    ],
)
def test_scent_policy_rejects_invalid_values(
    kwargs: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        ScentPolicy(**kwargs)  # type: ignore[arg-type]


def test_scent_policy_rejects_non_finite_quantization() -> None:
    with pytest.raises(ValueError, match="finite"):
        ScentPolicy().quantize(Decimal("NaN"))

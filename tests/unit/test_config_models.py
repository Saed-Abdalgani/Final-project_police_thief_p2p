import copy
import json

import pytest
from pydantic import ValidationError

from police_thief_p2p.shared.config_loader import load_shared_bytes
from police_thief_p2p.shared.config_models import SharedConfig
from police_thief_p2p.shared.config_rules import (
    FIXED_PARAMETERS,
    MINIMUM_PARAMETERS,
    NEGOTIABLE_DEFAULTS,
    MinimumDirection,
)
from police_thief_p2p.shared.coordinates import OriginCorner


def _document(shared_config_bytes: bytes) -> dict[str, object]:
    value = json.loads(shared_config_bytes)
    assert isinstance(value, dict)
    return value


def _set_path(document: dict[str, object], path: str, value: object) -> None:
    section_name, field_name = path.split(".")
    section = document[section_name]
    assert isinstance(section, dict)
    section[field_name] = value


def _bytes(document: dict[str, object]) -> bytes:
    return json.dumps(document).encode()


def _fixed_mutation(value: object) -> object:
    if isinstance(value, tuple):
        return list(value[:-1])
    if isinstance(value, str):
        return "0.8"
    assert isinstance(value, int)
    return value + 1


@pytest.mark.parametrize(("path", "fixed"), FIXED_PARAMETERS.items())
def test_every_fixed_appendix_parameter_rejects_mutation(
    shared_config_bytes: bytes,
    path: str,
    fixed: object,
) -> None:
    document = _document(shared_config_bytes)
    _set_path(document, path, _fixed_mutation(fixed))
    with pytest.raises(ValueError, match=r"CFG_|must"):
        load_shared_bytes(_bytes(document))


@pytest.mark.parametrize(("path", "rule"), MINIMUM_PARAMETERS.items())
def test_every_minimum_rejects_weakening_and_accepts_stricter(
    shared_config_bytes: bytes,
    path: str,
    rule: object,
) -> None:
    direction = rule.direction  # type: ignore[attr-defined]
    threshold = rule.threshold  # type: ignore[attr-defined]
    weak = threshold - 1 if direction is MinimumDirection.AT_LEAST else threshold + 1
    strict = threshold + 1 if direction is MinimumDirection.AT_LEAST else threshold - 1
    weak_document = _document(shared_config_bytes)
    _set_path(weak_document, path, weak)
    with pytest.raises(ValueError, match=r"CFG_|must"):
        load_shared_bytes(_bytes(weak_document))
    strict_document = _document(shared_config_bytes)
    _set_path(strict_document, path, strict)
    assert load_shared_bytes(_bytes(strict_document))


def test_rule_tables_cover_all_appendix_status_groups() -> None:
    assert len(FIXED_PARAMETERS) == 14
    assert len(MINIMUM_PARAMETERS) == 9
    assert len(NEGOTIABLE_DEFAULTS) == 9
    assert all(rule.accepts(rule.threshold) for rule in MINIMUM_PARAMETERS.values())
    assert MINIMUM_PARAMETERS["board_and_agents.grid_size"].accepts(8)
    assert not MINIMUM_PARAMETERS["rate_limiter_gatekeeper.requests_per_minute"].accepts(31)


def test_typed_models_apply_all_negotiable_defaults(shared_config_bytes: bytes) -> None:
    document = _document(shared_config_bytes)
    for path in NEGOTIABLE_DEFAULTS:
        section_name, field_name = path.split(".")
        section = document[section_name]
        assert isinstance(section, dict)
        section.pop(field_name)
    config = SharedConfig.model_validate(document)
    assert config.board_and_agents.axis_origin_corner is OriginCorner.TOP_LEFT
    assert config.board_and_agents.axis_start_index == 0
    assert config.board_and_agents.thief_start == (3, 3)
    assert config.board_and_agents.cop_start == (0, 0)
    assert config.world.map_area == ""
    assert config.world.hint_max_words == 15
    assert config.network_and_league.token_budget_per_series == 200_000
    assert config.network_and_league.response_timeout_sec == 30
    assert config.network_and_league.watchdog_timeout_sec == 60


def test_cross_field_start_and_timeout_validation(shared_config_bytes: bytes) -> None:
    same = _document(shared_config_bytes)
    board = same["board_and_agents"]
    assert isinstance(board, dict)
    board["thief_start"] = [0, 0]
    with pytest.raises(ValueError, match="distinct"):
        load_shared_bytes(_bytes(same))

    outside = _document(shared_config_bytes)
    board = outside["board_and_agents"]
    assert isinstance(board, dict)
    board["cop_start"] = [7, 0]
    with pytest.raises(ValueError, match="outside"):
        load_shared_bytes(_bytes(outside))

    deadline = _document(shared_config_bytes)
    league = deadline["network_and_league"]
    assert isinstance(league, dict)
    league["response_timeout_sec"] = 61
    with pytest.raises(ValueError, match="watchdog"):
        load_shared_bytes(_bytes(deadline))


def test_extensions_are_namespaced_and_canonical(shared_config_bytes: bytes) -> None:
    valid = _document(shared_config_bytes)
    valid["extensions"] = {"example.policy": {"mode": "strict"}}
    assert load_shared_bytes(_bytes(valid)).extensions["example.policy"] == {"mode": "strict"}

    invalid_name = copy.deepcopy(valid)
    invalid_name["extensions"] = {"unsafe": {}}
    with pytest.raises(ValueError, match=r"CFG_|namespaced"):
        load_shared_bytes(_bytes(invalid_name))

    invalid_number = copy.deepcopy(valid)
    invalid_number["extensions"] = {"example.policy": {"weight": 0.5}}
    with pytest.raises(ValueError, match="decimal strings"):
        load_shared_bytes(_bytes(invalid_number))


def test_model_rejects_wrong_version_groups_kernel_and_decimal_type(
    shared_config_bytes: bytes,
) -> None:
    for path, value in (
        ("schema_version", "9.0.0"),
        ("agreed_between", ["same", "same"]),
    ):
        document = _document(shared_config_bytes)
        document[path] = value
        with pytest.raises(ValueError, match=r"must|distinct"):
            SharedConfig.model_validate(document)

    document = _document(shared_config_bytes)
    scent = document["pheromones"]
    assert isinstance(scent, dict)
    scent["pheromone_center_intensity"] = 0.9
    with pytest.raises(ValidationError, match="decimal string"):
        SharedConfig.model_validate(document)

    document = _document(shared_config_bytes)
    scent = document["pheromones"]
    assert isinstance(scent, dict)
    scent["kernel"] = [["1"] * 5] * 5
    with pytest.raises(ValidationError, match="kernel"):
        SharedConfig.model_validate(document)


@pytest.mark.parametrize(
    ("section", "field", "value", "message"),
    [
        (
            "movement_and_barriers",
            "move_set",
            ["N", "S", "E", "W"],
            "must equal",
        ),
        (
            "pheromones",
            "pheromone_center_intensity",
            "0.8",
            "center_intensity",
        ),
        ("pheromones", "pheromone_decay", "0.11", "decay"),
    ],
)
def test_model_level_fixed_guards_are_independent_of_json_schema(
    shared_config_bytes: bytes,
    section: str,
    field: str,
    value: object,
    message: str,
) -> None:
    document = _document(shared_config_bytes)
    section_value = document[section]
    assert isinstance(section_value, dict)
    section_value[field] = value
    with pytest.raises(ValidationError, match=message):
        SharedConfig.model_validate(document)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("center_emission", "0.8"),
        ("center_after_one_full_turn", "0.8"),
    ],
)
def test_model_level_scent_example_guards(
    shared_config_bytes: bytes,
    field: str,
    value: str,
) -> None:
    document = _document(shared_config_bytes)
    scent = document["pheromones"]
    assert isinstance(scent, dict)
    example = scent["numeric_example"]
    assert isinstance(example, dict)
    example[field] = value
    with pytest.raises(ValidationError, match=field):
        SharedConfig.model_validate(document)


def test_model_level_extension_namespace_guard(shared_config_bytes: bytes) -> None:
    document = _document(shared_config_bytes)
    document["extensions"] = {"unsafe": {}}
    with pytest.raises(ValidationError, match="not namespaced"):
        SharedConfig.model_validate(document)


def test_shared_model_is_immutable_and_digest_is_repeatable(
    shared_config_bytes: bytes,
) -> None:
    config = load_shared_bytes(shared_config_bytes)
    assert config.digest() == config.digest()
    assert config.canonical_bytes() == config.canonical_bytes()
    with pytest.raises(ValidationError):
        config.schema_version = "9.0.0"

import base64
import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from police_thief_p2p.shared.canonical_json import canonical_json_bytes
from police_thief_p2p.shared.config_errors import ConfigError
from police_thief_p2p.shared.config_loader import load_shared_path
from police_thief_p2p.shared.schema_registry import (
    SCHEMA_NAMES,
    contracts_are_compatible,
    load_schema,
    validate_schema,
)

ROOT = Path(__file__).parents[2]
CONFORMANCE = ROOT / "data/conformance"


def test_all_packaged_schemas_are_valid_draft_2020_12() -> None:
    for name in SCHEMA_NAMES:
        schema = load_schema(name)
        Draft202012Validator.check_schema(schema)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


def test_game_schema_requires_every_appendix_f_key() -> None:
    schema = load_schema("game.schema.json")
    properties = schema["properties"]
    assert isinstance(properties, dict)
    expected = {
        "board_and_agents": {
            "grid_size",
            "num_agents",
            "axis_origin_corner",
            "axis_start_index",
            "thief_start",
            "cop_start",
        },
        "world": {"map_area", "hint_max_words"},
        "movement_and_barriers": {
            "move_set",
            "max_barriers",
            "max_moves",
            "survival_threshold",
        },
        "pheromones": {
            "pheromone_center_intensity",
            "pheromone_decay",
            "pheromone_grid_size",
            "kernel",
            "rounding",
            "numeric_example",
        },
        "scoring": {
            "capture_cop",
            "capture_thief",
            "survival_cop",
            "survival_thief",
            "tie_score",
        },
        "network_and_league": {
            "num_games",
            "diversity_reward",
            "min_games_to_pass",
            "token_budget_per_series",
            "max_games_per_team",
            "response_timeout_sec",
            "watchdog_timeout_sec",
        },
        "rate_limiter_gatekeeper": {
            "requests_per_minute",
            "concurrent_requests",
            "retry_backoff_sec",
            "max_retries",
            "queue_depth",
        },
    }
    for section, fields in expected.items():
        section_schema = properties[section]
        assert isinstance(section_schema, dict)
        assert set(section_schema["required"]) == fields
        assert section_schema["additionalProperties"] is False
    assert schema["additionalProperties"] is False


def test_manifest_canonical_and_config_vectors_are_exact() -> None:
    manifest = json.loads((CONFORMANCE / "manifest.json").read_text(encoding="utf-8"))
    canonical = manifest["canonical_json"]
    value = json.loads((CONFORMANCE / canonical["input"]).read_text(encoding="utf-8"))
    actual = canonical_json_bytes(value)
    expected = base64.b64decode(
        (CONFORMANCE / canonical["expected_base64"]).read_text(encoding="ascii")
    )
    assert actual == expected
    assert hashlib.sha256(actual).hexdigest() == canonical["sha256"]
    shared = manifest["shared_config"]
    config = load_shared_path((CONFORMANCE / shared["input"]).resolve())
    assert config.digest() == shared["canonical_sha256"]


def test_every_artifact_schema_has_passing_and_failing_fixture() -> None:
    manifest = json.loads((CONFORMANCE / "manifest.json").read_text(encoding="utf-8"))
    for vector in manifest["artifact_schemas"]:
        valid = json.loads((CONFORMANCE / vector["valid"]).read_text(encoding="utf-8"))
        invalid = json.loads((CONFORMANCE / vector["invalid"]).read_text(encoding="utf-8"))
        validate_schema(valid, vector["schema"], source=vector["valid"])
        with pytest.raises(ConfigError):
            validate_schema(invalid, vector["schema"], source=vector["invalid"])


def test_rate_limit_profiles_are_schema_driven() -> None:
    value = json.loads((ROOT / "config/rate_limits.example.json").read_text(encoding="utf-8"))
    validate_schema(value, "rate_limits.schema.json", source="rate_limits.example.json")
    value["services"]["gmail"]["requests_per_minute"] = 31
    with pytest.raises(ConfigError) as captured:
        validate_schema(value, "rate_limits.schema.json", source="rate_limits.example.json")
    assert captured.value.path == "$.services.gmail.requests_per_minute"


def test_schema_registry_allowlist_and_compatibility() -> None:
    assert contracts_are_compatible("0.2.0", "0.7.0")
    assert not contracts_are_compatible("9.9.9", "0.7.0")
    assert not contracts_are_compatible("0.2.0", "9.9.9")
    with pytest.raises(ValueError, match="unknown schema"):
        load_schema("../secret.json")

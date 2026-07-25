import json
from pathlib import Path

import pytest

from police_thief_p2p.shared import config as config_api
from police_thief_p2p.shared.config_errors import ConfigError, ConfigErrorCode
from police_thief_p2p.shared.config_loader import (
    MAX_JSON_DEPTH,
    MAX_PRIVATE_BYTES,
    MAX_SHARED_BYTES,
    load_private_bytes,
    load_private_path,
    load_shared_bytes,
    load_shared_path,
)
from police_thief_p2p.shared.configuration_service import (
    compare_shared_documents,
    load_effective_paths,
)
from police_thief_p2p.shared.effective_config import ConfigSource, merge_effective_config
from police_thief_p2p.shared.private_config import resolve_secret_environment

ROOT = Path(__file__).parents[2]


def test_shared_loader_rejects_hostile_bytes_and_syntax(
    shared_config_bytes: bytes,
) -> None:
    cases = (
        (b"x" * (MAX_SHARED_BYTES + 1), ConfigErrorCode.FILE_TOO_LARGE),
        (b"\xff", ConfigErrorCode.INVALID_UTF8),
        (b'{"a":1,"a":2}', ConfigErrorCode.DUPLICATE_KEY),
        (b'{"value":NaN}', ConfigErrorCode.NON_FINITE_NUMBER),
        (b'{"broken":', ConfigErrorCode.INVALID_JSON),
    )
    for document, code in cases:
        with pytest.raises(ConfigError) as captured:
            load_shared_bytes(document, source="hostile.json")
        assert captured.value.code is code
        assert captured.value.source == "hostile.json"
        assert "hostile.json" in repr(captured.value)
        assert shared_config_bytes not in str(captured.value).encode()


def test_shared_loader_rejects_excessive_depth() -> None:
    document = ("[" * MAX_JSON_DEPTH + "0" + "]" * MAX_JSON_DEPTH).encode()
    with pytest.raises(ConfigError) as captured:
        load_shared_bytes(document)
    assert captured.value.code is ConfigErrorCode.TOO_DEEP


def test_shared_schema_rejects_unknown_missing_and_submission_ids(
    shared_config_bytes: bytes,
) -> None:
    value = json.loads(shared_config_bytes)
    value["unknown"] = True
    with pytest.raises(ConfigError) as captured:
        load_shared_bytes(json.dumps(value).encode())
    assert captured.value.code is ConfigErrorCode.SCHEMA_ERROR
    assert captured.value.path == "$"

    value = json.loads(shared_config_bytes)
    del value["world"]["hint_max_words"]
    with pytest.raises(ConfigError):
        load_shared_bytes(json.dumps(value).encode())

    value = json.loads(shared_config_bytes)
    value["agreed_between"] = ["team-one", "team-two"]
    with pytest.raises(ValueError, match="eight ASCII"):
        load_shared_bytes(json.dumps(value).encode(), submission_mode=True)


def test_shared_file_loader_reports_io_and_loads_example(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"
    with pytest.raises(ConfigError) as captured:
        load_shared_path(missing)
    assert captured.value.code is ConfigErrorCode.IO_ERROR
    assert captured.value.source == str(missing)
    example = ROOT / "config/shared/game.example.json"
    assert load_shared_path(example, submission_mode=True).schema_version == "0.2.0"


def test_private_loader_accepts_example_and_rejects_shared_rules(
    private_config_bytes: bytes,
) -> None:
    config = load_private_bytes(private_config_bytes, source="safe/game.toml")
    assert config.identity.role == "police"
    assert config.network.listen_port == 8000
    hostile = private_config_bytes + b"\n[scoring]\ncapture_cop = 999\n"
    with pytest.raises(ConfigError) as captured:
        load_private_bytes(hostile, source="private/path/game.toml")
    assert captured.value.code is ConfigErrorCode.MODEL_ERROR
    assert captured.value.source == "private/path/game.toml"
    assert captured.value.path == "$.scoring"


def test_private_loader_rejects_resource_and_parse_failures(tmp_path: Path) -> None:
    for document, code in (
        (b"x" * (MAX_PRIVATE_BYTES + 1), ConfigErrorCode.FILE_TOO_LARGE),
        (b"\xff", ConfigErrorCode.INVALID_UTF8),
        (
            b"[identity\nsecret = 'do-not-leak'",  # pragma: allowlist secret
            ConfigErrorCode.INVALID_TOML,
        ),
    ):
        with pytest.raises(ConfigError) as captured:
            load_private_bytes(document, source="private.toml")
        assert captured.value.code is code
        assert "do-not-leak" not in str(captured.value)

    missing = tmp_path / "missing.toml"
    with pytest.raises(ConfigError) as captured:
        load_private_path(missing)
    assert captured.value.code is ConfigErrorCode.IO_ERROR
    assert load_private_path(ROOT / "config/private/game.example.toml").identity.group_id


def test_only_allowlisted_secret_environment_names_are_resolved(
    private_config_bytes: bytes,
) -> None:
    document = private_config_bytes.replace(
        b'# api_key_env = "POLICE_THIEF_LANGUAGE_API_KEY"',  # pragma: allowlist secret
        b'api_key_env = "POLICE_THIEF_LANGUAGE_API_KEY"',  # pragma: allowlist secret
    )
    config = load_private_bytes(document)
    secrets = resolve_secret_environment(
        config,
        {
            "POLICE_THIEF_LANGUAGE_API_KEY": "top-secret",  # pragma: allowlist secret
            "GRID_SIZE": "1",
        },
    )
    assert len(secrets) == 1
    assert secrets.get("POLICE_THIEF_LANGUAGE_API_KEY") == "top-secret"
    assert "top-secret" not in repr(secrets)
    assert "GRID_SIZE" not in repr(secrets)
    with pytest.raises(ConfigError) as captured:
        resolve_secret_environment(config, {})
    assert captured.value.code is ConfigErrorCode.SECRET_MISSING

    invalid = document.replace(
        b"POLICE_THIEF_LANGUAGE_API_KEY",
        b"lowercase-secret-name",
    )
    invalid_config = load_private_bytes(invalid)
    with pytest.raises(ValueError, match="environment variable name"):
        invalid_config.secret_environment_names()


def test_effective_config_records_provenance_and_unknown_paths(
    shared_config_bytes: bytes,
    private_config_bytes: bytes,
) -> None:
    shared = load_shared_bytes(shared_config_bytes)
    private = load_private_bytes(private_config_bytes)
    effective = merge_effective_config(shared, private)
    assert effective.source_for("$.shared.scoring.capture_cop") is ConfigSource.SHARED
    assert effective.source_for("$.private.strategy.profile") is ConfigSource.PRIVATE
    with pytest.raises(KeyError, match="unknown effective"):
        effective.source_for("$.shared.missing")
    from_paths = load_effective_paths(
        ROOT / "config/shared/game.example.json",
        ROOT / "config/private/game.example.toml",
    )
    assert from_paths.shared.digest() == shared.digest()


def test_raw_and_semantic_comparison_are_independent(shared_config_bytes: bytes) -> None:
    compact = json.dumps(json.loads(shared_config_bytes), separators=(",", ":")).encode()
    comparison = compare_shared_documents(shared_config_bytes, compact)
    assert not comparison.byte_identical
    assert comparison.semantic_digest_equal
    assert comparison.left_raw_digest != comparison.right_raw_digest
    assert comparison.left_semantic_digest == comparison.right_semantic_digest


def test_stable_config_module_exports_the_supported_boundary() -> None:
    assert config_api.load_shared_bytes is load_shared_bytes
    assert config_api.load_private_bytes is load_private_bytes
    assert config_api.compare_shared_documents is compare_shared_documents

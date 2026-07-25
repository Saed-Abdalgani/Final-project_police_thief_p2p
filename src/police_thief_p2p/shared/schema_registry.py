"""Packaged JSON Schema loading and safe validation."""

import json
from functools import lru_cache
from importlib.resources import files

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError

from police_thief_p2p.shared.config_errors import ConfigError, ConfigErrorCode

SCHEMA_NAMES = frozenset(
    {
        "game.schema.json",
        "rate_limits.schema.json",
        "declaration.schema.json",
        "sub_game_config.schema.json",
        "log.schema.json",
        "final_result.schema.json",
        "protocol_envelope.schema.json",
    }
)


def load_schema(name: str) -> dict[str, object]:
    """Load one allowlisted package schema."""
    if name not in SCHEMA_NAMES:
        raise ValueError(f"unknown schema: {name}")
    resource = files("police_thief_p2p.schemas").joinpath(name)
    value = json.loads(resource.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"packaged schema {name} is not an object")
    return value


def _json_path(error: ValidationError) -> str:
    path = "$"
    for part in error.absolute_path:
        path += f"[{part}]" if isinstance(part, int) else f".{part}"
    return path


def validate_schema(instance: object, name: str, *, source: str) -> None:
    """Validate an instance and raise the first deterministic safe error."""
    validator = Draft202012Validator(load_schema(name), format_checker=FormatChecker())
    errors = sorted(
        validator.iter_errors(instance),
        key=lambda item: (tuple(str(part) for part in item.absolute_path), item.validator or ""),
    )
    if errors:
        error = errors[0]
        raise ConfigError(
            ConfigErrorCode.SCHEMA_ERROR,
            source=source,
            path=_json_path(error),
            detail=f"violates schema rule {error.validator}",
        )


@lru_cache(maxsize=8)
def contracts_are_compatible(schema_version: str, protocol_version: str) -> bool:
    """Return whether every packaged schema advertises supported versions."""
    for name in SCHEMA_NAMES:
        schema = load_schema(name)
        identifier = schema.get("$id")
        if not isinstance(identifier, str) or f"/{schema_version}/" not in identifier:
            return False
        text = json.dumps(schema, sort_keys=True)
        if (
            name in {"declaration.schema.json", "protocol_envelope.schema.json"}
            and protocol_version not in text
        ):
            return False
    return True

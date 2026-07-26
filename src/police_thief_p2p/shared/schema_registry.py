"""Packaged JSON Schema loading and safe validation."""

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError

from police_thief_p2p.shared.config_errors import ConfigError, ConfigErrorCode
from police_thief_p2p.shared.schema_catalog import (
    SCHEMA_NAMES as SCHEMA_NAMES,
)
from police_thief_p2p.shared.schema_catalog import (
    contracts_are_compatible as contracts_are_compatible,
)
from police_thief_p2p.shared.schema_catalog import load_schema as load_schema


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

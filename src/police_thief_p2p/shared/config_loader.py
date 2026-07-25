"""Resource-bounded shared JSON and private TOML loading."""

import json
import tomllib
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path
from typing import NoReturn

from pydantic import ValidationError

from police_thief_p2p.shared.config_errors import ConfigError, ConfigErrorCode
from police_thief_p2p.shared.config_models import SharedConfig
from police_thief_p2p.shared.identifiers import GroupId
from police_thief_p2p.shared.private_config import PrivateConfig
from police_thief_p2p.shared.schema_registry import validate_schema

MAX_SHARED_BYTES = 262_144
MAX_PRIVATE_BYTES = 131_072
MAX_JSON_DEPTH = 32


class _DuplicateKey(ValueError):
    pass


class _NonFinite(ValueError):
    pass


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKey(key)
        result[key] = value
    return result


def _non_finite(value: str) -> NoReturn:
    raise _NonFinite(value)


def _depth(value: object, current: int = 1) -> int:
    if isinstance(value, Mapping):
        return max((_depth(item, current + 1) for item in value.values()), default=current)
    if isinstance(value, list):
        return max((_depth(item, current + 1) for item in value), default=current)
    return current


def _safe_model_error(error: ValidationError, source: str) -> ConfigError:
    first = error.errors(include_input=False, include_url=False)[0]
    path = "$"
    for part in first["loc"]:
        path += f"[{part}]" if isinstance(part, int) else f".{part}"
    return ConfigError(
        ConfigErrorCode.MODEL_ERROR,
        source=source,
        path=path,
        detail=str(first["msg"]),
    )


def load_shared_bytes(
    document: bytes,
    *,
    source: str = "game.json",
    submission_mode: bool = False,
) -> SharedConfig:
    """Parse and validate one hostile shared JSON document."""
    if len(document) > MAX_SHARED_BYTES:
        raise ConfigError(
            ConfigErrorCode.FILE_TOO_LARGE,
            source=source,
            detail=f"document exceeds {MAX_SHARED_BYTES} bytes",
        )
    try:
        text = document.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ConfigError(
            ConfigErrorCode.INVALID_UTF8, source=source, detail="document is not UTF-8"
        ) from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_float=Decimal,
            parse_constant=_non_finite,
        )
    except _DuplicateKey as exc:
        raise ConfigError(
            ConfigErrorCode.DUPLICATE_KEY, source=source, detail="duplicate object key"
        ) from exc
    except _NonFinite as exc:
        raise ConfigError(
            ConfigErrorCode.NON_FINITE_NUMBER,
            source=source,
            detail="non-finite number is forbidden",
        ) from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(
            ConfigErrorCode.INVALID_JSON,
            source=source,
            path=f"$[line={exc.lineno},column={exc.colno}]",
            detail="malformed JSON",
        ) from exc
    if _depth(value) > MAX_JSON_DEPTH:
        raise ConfigError(
            ConfigErrorCode.TOO_DEEP,
            source=source,
            detail=f"document exceeds depth {MAX_JSON_DEPTH}",
        )
    validate_schema(value, "game.schema.json", source=source)
    try:
        config = SharedConfig.model_validate(value)
    except ValidationError as exc:
        raise _safe_model_error(exc, source) from exc
    if submission_mode:
        for group_id in config.agreed_between:
            GroupId(group_id, submission_mode=True)
    return config


def load_shared_path(path: Path, *, submission_mode: bool = False) -> SharedConfig:
    """Read and validate a shared JSON file with a safe source location."""
    try:
        document = path.read_bytes()
    except OSError as exc:
        raise ConfigError(
            ConfigErrorCode.IO_ERROR, source=str(path), detail="cannot read document"
        ) from exc
    return load_shared_bytes(document, source=str(path), submission_mode=submission_mode)


def load_private_bytes(document: bytes, *, source: str = "game.toml") -> PrivateConfig:
    """Parse and validate one private TOML document without exposing values."""
    if len(document) > MAX_PRIVATE_BYTES:
        raise ConfigError(
            ConfigErrorCode.FILE_TOO_LARGE,
            source=source,
            detail=f"document exceeds {MAX_PRIVATE_BYTES} bytes",
        )
    try:
        text = document.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ConfigError(
            ConfigErrorCode.INVALID_UTF8, source=source, detail="document is not UTF-8"
        ) from exc
    try:
        value = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(
            ConfigErrorCode.INVALID_TOML, source=source, detail="malformed TOML"
        ) from exc
    try:
        return PrivateConfig.model_validate(value)
    except ValidationError as exc:
        raise _safe_model_error(exc, source) from exc


def load_private_path(path: Path) -> PrivateConfig:
    """Read and validate a private TOML file with source-aware failures."""
    try:
        document = path.read_bytes()
    except OSError as exc:
        raise ConfigError(
            ConfigErrorCode.IO_ERROR, source=str(path), detail="cannot read document"
        ) from exc
    return load_private_bytes(document, source=str(path))

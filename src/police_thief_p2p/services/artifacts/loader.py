"""Resource-bounded official artifact JSON loading."""

import json
from collections.abc import Mapping
from typing import NoReturn


class _DuplicateKey(ValueError):
    pass


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKey
        result[key] = value
    return result


def _nonfinite(_: str) -> NoReturn:
    raise ValueError("non-finite artifact number is forbidden")


def _depth(value: object, current: int = 1) -> int:
    if isinstance(value, Mapping):
        return max((_depth(item, current + 1) for item in value.values()), default=current)
    if isinstance(value, list):
        return max((_depth(item, current + 1) for item in value), default=current)
    return current


def load_artifact_json(data: bytes, *, max_bytes: int = 16_777_216) -> dict[str, object]:
    """Parse a bounded UTF-8 object with no duplicates, non-finite numbers, or deep trees."""
    if len(data) > max_bytes:
        raise ValueError("artifact exceeds size limit")
    try:
        value = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_pairs,
            parse_constant=_nonfinite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, _DuplicateKey, RecursionError) as exc:
        raise ValueError("artifact JSON is invalid") from exc
    if not isinstance(value, dict):
        raise ValueError("artifact must contain a JSON object")
    if _depth(value) > 64:
        raise ValueError("artifact exceeds depth limit")
    return value

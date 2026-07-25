"""Canonical JSON and digest primitives for signed protocol records."""

import hashlib
import hmac
import json
import math
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal

type JsonScalar = str | int | bool | None
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]


class CanonicalJsonError(ValueError):
    """A value cannot be represented by the project's canonical JSON profile."""


def _normalize(value: object, path: str = "$") -> JsonValue:
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, (float, Decimal)):
        if isinstance(value, float) and not math.isfinite(value):
            raise CanonicalJsonError(f"{path}: non-finite numbers are forbidden")
        raise CanonicalJsonError(f"{path}: non-integer numbers must be decimal strings")
    if isinstance(value, Mapping):
        normalized: dict[str, JsonValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonicalJsonError(f"{path}: object keys must be strings")
            normalized_key = unicodedata.normalize("NFC", key)
            if normalized_key in normalized:
                raise CanonicalJsonError(f"{path}: keys collide after NFC normalization")
            normalized[normalized_key] = _normalize(item, f"{path}.{normalized_key}")
        return normalized
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_normalize(item, f"{path}[{index}]") for index, item in enumerate(value)]
    raise CanonicalJsonError(f"{path}: unsupported type {type(value).__name__}")


def canonical_json_bytes(value: object) -> bytes:
    """Serialize a JSON-compatible value to deterministic NFC UTF-8 bytes."""
    normalized = _normalize(value)
    return json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256_digest(value: object) -> str:
    """Return a lowercase SHA-256 digest of canonical JSON bytes."""
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def digest_bytes(value: bytes) -> str:
    """Return a lowercase SHA-256 digest of exact raw bytes."""
    return hashlib.sha256(value).hexdigest()


def digests_equal(left: str, right: str) -> bool:
    """Compare lowercase hexadecimal digests in constant time."""
    return hmac.compare_digest(left, right)


@dataclass(frozen=True, slots=True)
class DocumentComparison:
    """Raw and semantic equality evidence for two configuration documents."""

    byte_identical: bool
    semantic_digest_equal: bool
    left_raw_digest: str
    right_raw_digest: str
    left_semantic_digest: str
    right_semantic_digest: str

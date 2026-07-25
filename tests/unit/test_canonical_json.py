import hashlib
from decimal import Decimal

import pytest

from police_thief_p2p.shared.canonical_json import (
    CanonicalJsonError,
    canonical_json_bytes,
    digest_bytes,
    digests_equal,
    sha256_digest,
)


def test_canonical_json_sorts_compacts_and_normalizes_unicode() -> None:
    value = {"z": 1, "text": "Cafe\u0301", "a": {"b": True, "a": None}}
    expected = '{"a":{"a":null,"b":true},"text":"Café","z":1}'.encode()
    assert canonical_json_bytes(value) == expected
    assert sha256_digest(value) == hashlib.sha256(expected).hexdigest()
    assert digest_bytes(expected) == hashlib.sha256(expected).hexdigest()


@pytest.mark.parametrize("value", [1.5, Decimal("1.5"), float("inf"), float("nan")])
def test_canonical_json_requires_decimal_strings(value: object) -> None:
    with pytest.raises(CanonicalJsonError):
        canonical_json_bytes({"value": value})


def test_canonical_json_rejects_unsafe_object_shapes() -> None:
    with pytest.raises(CanonicalJsonError, match="keys must be strings"):
        canonical_json_bytes({1: "value"})
    with pytest.raises(CanonicalJsonError, match="collide"):
        canonical_json_bytes({"é": 1, "e\u0301": 2})
    with pytest.raises(CanonicalJsonError, match="unsupported"):
        canonical_json_bytes({"value": {1, 2}})


def test_digest_comparison_is_exact() -> None:
    left = "a" * 64
    assert digests_equal(left, left)
    assert not digests_equal(left, "b" * 64)

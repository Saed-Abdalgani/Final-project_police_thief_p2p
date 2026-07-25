"""Opaque production nonce with an explicit final-audit reveal."""

from __future__ import annotations

import hashlib
import secrets

MIN_NONCE_BYTES = 16
DEFAULT_NONCE_BYTES = 32


class SecretNonce:
    """At least 128 bits of secret entropy with permanently redacted display."""

    __slots__ = ("__value",)

    def __init__(self, value: bytes) -> None:
        """Copy and validate secret bytes without exposing them in errors."""
        if not isinstance(value, bytes):
            raise TypeError("nonce material must be bytes")
        if len(value) < MIN_NONCE_BYTES:
            raise ValueError("nonce must provide at least 128 bits of entropy")
        self.__value = bytes(value)

    @classmethod
    def generate(cls, length: int = DEFAULT_NONCE_BYTES) -> SecretNonce:
        """Generate a fresh nonce directly from the operating-system CSPRNG."""
        if type(length) is not int or length < MIN_NONCE_BYTES:
            raise ValueError("nonce length must provide at least 128 bits")
        return cls(secrets.token_bytes(length))

    @classmethod
    def from_hex(cls, value: str) -> SecretNonce:
        """Restore final-audit nonce material from strict lowercase hex."""
        if not isinstance(value, str) or value != value.lower():
            raise ValueError("final nonce must be lowercase hexadecimal")
        try:
            return cls(bytes.fromhex(value))
        except ValueError as exc:
            raise ValueError("final nonce must be lowercase hexadecimal") from exc

    def reveal_hex(self) -> str:
        """Explicitly reveal the nonce only for a final-audit manifest."""
        return self.__value.hex()

    def fingerprint(self) -> str:
        """Return a non-reversible reuse-detection fingerprint."""
        return hashlib.sha256(self.__value).hexdigest()

    def __repr__(self) -> str:
        """Never expose nonce length or bytes."""
        return "SecretNonce(<redacted>)"

    def __str__(self) -> str:
        """Never expose nonce material through string conversion."""
        return "<redacted>"

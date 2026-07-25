"""Central recursive redaction for logs, errors, and diagnostics."""

import re
from collections.abc import Mapping
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from police_thief_p2p.constants import REDACTED

_SENSITIVE_KEY_PARTS = (
    "api_key",
    "authorization",
    "credential",
    "nonce",
    "password",
    "private_key",
    "secret",
    "signing_key",
    "hmac_key",
    "token",
)
_EMAIL_PATTERN = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
_BEARER_PATTERN = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+")
_URL_PATTERN = re.compile(r"https?://[^\s\"'<>]+")


def is_sensitive_key(key: str) -> bool:
    """Return whether a field name represents secret material."""
    normalized = key.casefold().replace("-", "_")
    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)


def _redact_url(url: str) -> str:
    """Remove URL user information and sensitive query values."""
    try:
        parts = urlsplit(url)
        hostname = parts.hostname or ""
        netloc = hostname
        if parts.port is not None:
            netloc = f"{hostname}:{parts.port}"
        query = urlencode(
            [
                (key, REDACTED if is_sensitive_key(key) else value)
                for key, value in parse_qsl(parts.query, keep_blank_values=True)
            ],
            safe="[]",
        )
        return urlunsplit((parts.scheme, netloc, parts.path, query, parts.fragment))
    except ValueError:
        return REDACTED


def redact_text(value: str) -> str:
    """Redact emails, bearer credentials, and sensitive URL components."""
    redacted = _URL_PATTERN.sub(lambda match: _redact_url(match.group(0)), value)
    redacted = _BEARER_PATTERN.sub(f"Bearer {REDACTED}", redacted)
    redacted = _EMAIL_PATTERN.sub(REDACTED, redacted)
    return redacted


def redact_value(value: object, *, key: str | None = None) -> object:
    """Recursively return a log-safe copy of a supported value."""
    if key is not None and is_sensitive_key(key):
        return REDACTED
    if isinstance(value, bytes):
        return REDACTED
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, Mapping):
        return {
            str(item_key): redact_value(item_value, key=str(item_key))
            for item_key, item_value in value.items()
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        return [redact_value(item) for item in value]
    return value

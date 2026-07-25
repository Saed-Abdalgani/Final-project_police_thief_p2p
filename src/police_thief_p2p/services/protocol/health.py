"""Redacted protocol health payload composition."""

from collections.abc import Callable, Mapping

from police_thief_p2p.shared.version import (
    PACKAGE_VERSION,
    PROTOCOL_VERSION,
    SCHEMA_VERSION,
)


def health_payload(
    provider: Callable[[], Mapping[str, object]] | None,
) -> dict[str, object]:
    """Return allowed status plus public compatibility versions."""
    status = {"status": "alive"} if provider is None else dict(provider())
    if status.get("status") not in {"alive", "ready", "degraded", "failed"}:
        status = {"status": "failed"}
    return {
        **status,
        "package_version": PACKAGE_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "schema_version": SCHEMA_VERSION,
    }

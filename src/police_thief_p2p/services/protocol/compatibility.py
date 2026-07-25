"""Protocol and optional-capability compatibility rules."""

from __future__ import annotations

import re
from collections.abc import Mapping

from police_thief_p2p.services.protocol.errors import ProtocolErrorCode, ProtocolFailure

_NAMESPACE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)+$")


def protocol_is_compatible(local: str, remote: str) -> bool:
    """Accept the same major when the remote minor is not newer than local."""
    try:
        local_parts = tuple(int(item) for item in local.split("-", 1)[0].split("."))
        remote_parts = tuple(int(item) for item in remote.split("-", 1)[0].split("."))
    except ValueError:
        return False
    return (
        len(local_parts) == 3
        and len(remote_parts) == 3
        and local_parts[0] == remote_parts[0]
        and remote_parts[1] <= local_parts[1]
    )


def negotiate_extensions(
    local: Mapping[str, object],
    remote: Mapping[str, object],
) -> dict[str, object]:
    """Retain mutually named optional extensions without affecting core rules."""
    for namespace in (*local, *remote):
        if _NAMESPACE.fullmatch(namespace) is None:
            raise ProtocolFailure(
                ProtocolErrorCode.VALIDATION,
                "optional capability namespace is invalid",
            )
    return {name: local[name] for name in sorted(local.keys() & remote.keys())}

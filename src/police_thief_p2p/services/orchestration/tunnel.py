"""Strict public-tunnel URL validation and bounded bidirectional preflight."""

import ipaddress
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlsplit, urlunsplit

from police_thief_p2p.services.orchestration.deadlines import DeadlineTracker


def validate_tunnel_url(url: str, *, competition_mode: bool) -> str:
    """Normalize HTTP(S), reject credentials/fragments, and require public HTTPS."""
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("tunnel URL scheme or host is invalid")
    if parsed.username is not None or parsed.password is not None or parsed.fragment:
        raise ValueError("tunnel URL credentials and fragments are forbidden")
    host = parsed.hostname.casefold()
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if competition_mode and (
        parsed.scheme != "https"
        or host == "localhost"
        or (address is not None and not address.is_global)
        or bool(parsed.query)
    ):
        raise ValueError("competition tunnel must be a public HTTPS endpoint")
    netloc = host if parsed.port is None else f"{host}:{parsed.port}"
    path = parsed.path.rstrip("/") or "/mcp"
    return urlunsplit((parsed.scheme, netloc, path, parsed.query, ""))


def validate_tunnel_redirect(
    origin: str,
    target: str,
    *,
    competition_mode: bool,
) -> str:
    """Allow only a validated same-origin redirect target."""
    safe_origin = urlsplit(validate_tunnel_url(origin, competition_mode=competition_mode))
    safe_target = validate_tunnel_url(target, competition_mode=competition_mode)
    parsed_target = urlsplit(safe_target)
    if (safe_origin.scheme, safe_origin.netloc) != (
        parsed_target.scheme,
        parsed_target.netloc,
    ):
        raise ValueError("tunnel redirect must remain on the validated origin")
    return safe_target


class TunnelProbePort(Protocol):
    """Semantic preflight probes implemented by an external adapter."""

    def health(self, url: str, timeout: float) -> bool:
        """Check remote liveness."""
        ...

    def capabilities(self, url: str, timeout: float) -> bool:
        """Check protocol capabilities."""
        ...

    def round_trip(self, url: str, timeout: float) -> bool:
        """Check one safe echo round trip."""
        ...

    def payload_limit(self, url: str, timeout: float) -> bool:
        """Check negotiated maximum payload."""
        ...

    def bidirectional(self, url: str, timeout: float) -> bool:
        """Check both peers can initiate calls."""
        ...


@dataclass(frozen=True, slots=True)
class TunnelPreflight:
    """Run every tunnel capability check under one monotonic deadline."""

    probe: TunnelProbePort

    def run(self, url: str, deadline: DeadlineTracker) -> dict[str, bool]:
        """Return named results and fail closed when the deadline expires."""
        checks = (
            ("health", self.probe.health),
            ("capabilities", self.probe.capabilities),
            ("round_trip", self.probe.round_trip),
            ("payload_limit", self.probe.payload_limit),
            ("bidirectional", self.probe.bidirectional),
        )
        results: dict[str, bool] = {}
        for name, operation in checks:
            remaining = deadline.remaining()
            results[name] = remaining > 0 and operation(url, remaining)
        return results

"""Raw FastMCP call executor reachable only through the Gatekeeper."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from fastmcp import Client

from police_thief_p2p.shared.gatekeeper import ExternalCall, ExternalResult


class FastMcpBackend:
    """Execute one raw remote call for the central Gatekeeper."""

    __slots__ = ("_endpoint", "_timeout_sec")

    def __init__(self, endpoint: Any, *, timeout_sec: float) -> None:
        """Bind a validated endpoint and client-side hard timeout."""
        self._endpoint = endpoint
        self._timeout_sec = timeout_sec

    async def execute_once(self, call: ExternalCall) -> ExternalResult:
        """Perform exactly one transport attempt."""
        async with Client(self._endpoint, timeout=self._timeout_sec) as client:
            result = await client.call_tool(call.operation, dict(call.payload))
        data = result.data
        if not isinstance(data, Mapping):
            return ExternalResult("invalid_response", {"code": "INVALID_RESPONSE"})
        return ExternalResult("success", dict(data))

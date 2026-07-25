"""Thin FastMCP server adapter calling only the public SDK."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from fastmcp import FastMCP

from police_thief_p2p.sdk import SimulationSdk


def build_mcp_server(
    sdk: SimulationSdk,
    *,
    max_request_bytes: int,
    concurrent_requests: int,
) -> FastMCP:
    """Build the versioned server with configured body and concurrency ceilings."""
    if max_request_bytes < 1 or concurrent_requests < 1:
        raise ValueError("server ceilings must be positive")
    server = FastMCP(
        "police-thief-peer",
        mask_error_details=True,
        strict_input_validation=True,
    )
    semaphore = asyncio.Semaphore(concurrent_requests)

    async def health_v1() -> dict[str, Any]:
        """Return state-free peer liveness."""
        return sdk.protocol_health().model_dump(mode="json")

    async def capabilities_v1() -> dict[str, Any]:
        """Return versioned peer readiness and tool capabilities."""
        return sdk.protocol_capabilities().model_dump(mode="json")

    server.tool(name="health_v1", version="1.0.0")(health_v1)
    server.tool(name="capabilities_v1", version="1.0.0")(capabilities_v1)
    tools = sdk.protocol_capabilities().payload["tools"]
    if not isinstance(tools, dict):
        raise RuntimeError("SDK capabilities tools are invalid")
    for name, version in tools.items():
        if name in {"health_v1", "capabilities_v1"}:
            continue
        tool = _tool_handler(
            sdk,
            str(name),
            max_request_bytes=max_request_bytes,
            semaphore=semaphore,
        )
        server.tool(name=str(name), version=str(version))(tool)
    return server


def _tool_handler(
    sdk: SimulationSdk,
    tool_name: str,
    *,
    max_request_bytes: int,
    semaphore: asyncio.Semaphore,
) -> Callable[[str], Any]:
    async def dispatch(envelope_json: str) -> dict[str, Any]:
        """Dispatch one already-framed request through the SDK."""
        document = envelope_json.encode("utf-8")
        if len(document) > max_request_bytes:
            return _adapter_error("PROTOCOL_VALIDATION", "request exceeds byte limit")
        if semaphore.locked():
            return _adapter_error("SERVER_OVERLOADED", "server concurrency limit reached")
        async with semaphore:
            response = sdk.receive_protocol_request(tool_name, document)
        return response.model_dump(mode="json")

    dispatch.__name__ = f"dispatch_{tool_name}"
    return dispatch


def _adapter_error(code: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "code": code,
        "message": message,
        "correlation_id": None,
        "payload": {},
    }

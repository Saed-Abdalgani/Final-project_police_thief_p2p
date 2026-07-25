"""Gatekeeper-only outbound MCP client adapter."""

from __future__ import annotations

from police_thief_p2p.sdk import ProtocolEnvelope, ProtocolResponse
from police_thief_p2p.shared.gatekeeper import ExternalCall, GatekeeperPort


class McpClientAdapter:
    """Send exact canonical request bytes only through the central Gatekeeper."""

    __slots__ = ("_gatekeeper",)

    def __init__(self, gatekeeper: GatekeeperPort) -> None:
        """Bind the mandatory external-call boundary."""
        self._gatekeeper = gatekeeper

    async def send(self, envelope: ProtocolEnvelope) -> ProtocolResponse:
        """Send one envelope and parse the typed safe response."""
        call = ExternalCall(
            service="mcp",
            operation=envelope.message_type,
            payload={"envelope_json": envelope.canonical_bytes().decode("utf-8")},
        )
        result = await self._gatekeeper.execute(call)
        if result.outcome != "success":
            return ProtocolResponse(
                ok=False,
                code=str(result.payload.get("code", "DEPENDENCY_UNAVAILABLE")),
                message="remote peer call did not complete",
                correlation_id=envelope.correlation_id,
            )
        return ProtocolResponse.model_validate(result.payload)

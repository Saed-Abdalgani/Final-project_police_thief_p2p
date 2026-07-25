import asyncio
from collections.abc import Mapping
from pathlib import Path

import pytest
from fastmcp import Client

from police_thief_p2p.adapters.mcp import (
    FastMcpBackend,
    McpClientAdapter,
    build_mcp_server,
)
from police_thief_p2p.adapters.system.clocks import FakeClock
from police_thief_p2p.sdk import SimulationSdk, create_protocol_runtime
from police_thief_p2p.shared.config_models import SharedConfig
from police_thief_p2p.shared.gatekeeper import (
    ExternalCall,
    ExternalResult,
    InitialGatekeeper,
)
from tests.helpers.protocol import make_envelope, make_proposal


class FakeGateway:
    def __init__(self, result: ExternalResult) -> None:
        self.result = result
        self.calls: list[ExternalCall] = []

    async def execute(self, call: ExternalCall) -> ExternalResult:
        self.calls.append(call)
        return self.result


def test_gatekeeper_retries_identical_call_and_maps_timeout_without_sleep() -> None:
    clock = FakeClock()
    seen: list[ExternalCall] = []

    async def retry_once(call: ExternalCall) -> ExternalResult:
        seen.append(call)
        return ExternalResult("retryable" if len(seen) == 1 else "success", {"ok": True})

    async def no_sleep(_: float) -> None:
        return None

    gatekeeper = InitialGatekeeper(
        retry_once,
        clock=clock,
        timeout_sec=2,
        max_retries=2,
        concurrent_requests=1,
        sleep=no_sleep,
    )
    call = ExternalCall("mcp", "health_v1", {})
    result = asyncio.run(gatekeeper.execute(call))
    assert result.outcome == "success"
    assert seen == [call, call]
    assert seen[0] is seen[1]

    async def late(call: ExternalCall) -> ExternalResult:
        clock.advance(3)
        return ExternalResult("success", {"ignored": call.operation})

    timeout = InitialGatekeeper(
        late,
        clock=clock,
        timeout_sec=2,
        max_retries=0,
        concurrent_requests=1,
    )
    assert asyncio.run(timeout.execute(call)).payload["code"] == "REQUEST_TIMEOUT"


def test_gatekeeper_validates_limits_and_maps_dependency_failure() -> None:
    clock = FakeClock()

    async def broken(_: ExternalCall) -> ExternalResult:
        raise OSError("private dependency detail")

    with pytest.raises(ValueError, match="limits"):
        InitialGatekeeper(
            broken,
            clock=clock,
            timeout_sec=0,
            max_retries=0,
            concurrent_requests=1,
        )
    gatekeeper = InitialGatekeeper(
        broken,
        clock=clock,
        timeout_sec=1,
        max_retries=0,
        concurrent_requests=1,
    )
    result = asyncio.run(gatekeeper.execute(ExternalCall("mcp", "tool", {})))
    assert result == ExternalResult("unavailable", {"code": "DEPENDENCY_UNAVAILABLE"})


def test_client_adapter_uses_only_gatekeeper_and_preserves_request_bytes(
    shared_config: SharedConfig,
    shared_config_bytes: bytes,
) -> None:
    proposal = make_proposal(shared_config, shared_config_bytes)
    envelope = make_envelope(
        proposal,
        "propose_match_v1",
        proposal.model_dump(mode="json"),
        sequence=1,
    )
    gateway = FakeGateway(
        ExternalResult(
            "success",
            {
                "ok": True,
                "code": "OK",
                "message": "done",
                "correlation_id": envelope.correlation_id,
                "payload": {},
            },
        )
    )
    response = asyncio.run(McpClientAdapter(gateway).send(envelope))
    assert response.ok
    assert gateway.calls[0].payload["envelope_json"] == (envelope.canonical_bytes().decode())

    unavailable = McpClientAdapter(
        FakeGateway(ExternalResult("timeout", {"code": "REQUEST_TIMEOUT"}))
    )
    assert asyncio.run(unavailable.send(envelope)).code == "REQUEST_TIMEOUT"


def test_real_fastmcp_server_backend_and_health_are_interoperable(
    tmp_path: Path,
    shared_config: SharedConfig,
    shared_config_bytes: bytes,
) -> None:
    sdk = SimulationSdk(
        create_protocol_runtime(
            local_group="GRP00002",
            shared_document=shared_config_bytes,
            storage_root=tmp_path,
        )
    )
    server = build_mcp_server(
        sdk,
        max_request_bytes=65_536,
        concurrent_requests=2,
    )

    async def scenario() -> None:
        async with Client(server) as client:
            health = await client.call_tool("health_v1")
            assert health.data["payload"]["status"] == "alive"
            capabilities = await client.call_tool("capabilities_v1")
            assert "propose_match_v1" in capabilities.data["payload"]["tools"]
        backend = FastMcpBackend(server, timeout_sec=5)
        result = await backend.execute_once(ExternalCall("mcp", "health_v1", {}))
        health_payload = result.payload["payload"]
        assert isinstance(health_payload, Mapping)
        assert health_payload["status"] == "alive"

        proposal = make_proposal(shared_config, shared_config_bytes)
        envelope = make_envelope(
            proposal,
            "propose_match_v1",
            proposal.model_dump(mode="json"),
            sequence=1,
        )
        gateway = InitialGatekeeper(
            backend.execute_once,
            clock=FakeClock(),
            timeout_sec=5,
            max_retries=0,
            concurrent_requests=1,
        )
        assert (await McpClientAdapter(gateway).send(envelope)).ok

    asyncio.run(scenario())


def test_server_rejects_invalid_ceilings() -> None:
    with pytest.raises(ValueError, match="ceilings"):
        build_mcp_server(
            SimulationSdk(),
            max_request_bytes=0,
            concurrent_requests=1,
        )

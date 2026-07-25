import asyncio
from datetime import UTC, datetime

import pytest

from police_thief_p2p.services.ports import (
    ClockPort,
    EmailMessage,
    EmailPort,
    EmailReceipt,
    EntropySource,
    LanguagePort,
    LanguageRequest,
    LanguageResponse,
    RandomSource,
    RepositoryPort,
    SystemInfo,
    SystemInfoPort,
    TransportPort,
    TransportRequest,
    TransportResponse,
)
from police_thief_p2p.shared.gatekeeper import (
    ExternalCall,
    ExternalResult,
    GatekeeperPort,
)

pytestmark = pytest.mark.contract


class CompleteFake:
    def monotonic(self) -> float:
        return 1.0

    def utc_now(self) -> datetime:
        return datetime(2026, 7, 25, tzinfo=UTC)

    def token_bytes(self, length: int) -> bytes:
        return bytes(length)

    def random(self) -> float:
        return 0.5

    def randbelow(self, upper_bound: int) -> int:
        return upper_bound - 1

    def load(self, key: str) -> bytes | None:
        return key.encode()

    def save(self, key: str, data: bytes) -> None:
        _ = (key, data)

    def collect(self) -> SystemInfo:
        return SystemInfo("test-os", "3.13", None, 1, 1024)

    async def request(self, request: TransportRequest) -> TransportResponse:
        return TransportResponse(200, {"operation": request.operation})

    async def generate(self, request: LanguageRequest) -> LanguageResponse:
        return LanguageResponse(request.prompt, 0)

    async def send(self, message: EmailMessage) -> EmailReceipt:
        return EmailReceipt(message.attachment_name)

    async def execute(self, call: ExternalCall) -> ExternalResult:
        return ExternalResult("ok", {"service": call.service})


def test_fake_structurally_conforms_to_all_foundation_ports() -> None:
    fake = CompleteFake()
    assert isinstance(fake, ClockPort)
    assert isinstance(fake, EntropySource)
    assert isinstance(fake, RandomSource)
    assert isinstance(fake, RepositoryPort)
    assert isinstance(fake, SystemInfoPort)
    assert isinstance(fake, TransportPort)
    assert isinstance(fake, LanguagePort)
    assert isinstance(fake, EmailPort)
    assert isinstance(fake, GatekeeperPort)


def test_async_port_contracts_return_typed_results() -> None:
    fake = CompleteFake()
    transport = asyncio.run(fake.request(TransportRequest("health", {})))
    language = asyncio.run(fake.generate(LanguageRequest("hello", 15)))
    email = asyncio.run(fake.send(EmailMessage("recipient", "subject", "result.json", b"{}")))
    external = asyncio.run(fake.execute(ExternalCall("mcp", "health", {})))
    assert transport.status_code == 200
    assert language.token_count == 0
    assert email.message_id == "result.json"
    assert external.outcome == "ok"

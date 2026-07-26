import asyncio
import base64
import json
from pathlib import Path

import pytest

from police_thief_p2p.adapters.email import GmailOAuth, GmailSender
from police_thief_p2p.adapters.email.http import HttpResponse
from police_thief_p2p.adapters.email.oauth_callback import AuthorizationCode
from police_thief_p2p.adapters.persistence import AtomicFileRepository
from police_thief_p2p.adapters.system.clocks import FakeClock
from police_thief_p2p.services.artifacts import ArtifactPaths, verify_manifest
from police_thief_p2p.services.reporting import (
    REQUIRED_RECIPIENT,
    DurableOutbox,
    OutboxDispatcher,
    OutboxState,
    PreparedReport,
    ReportingPolicy,
    build_report,
)
from police_thief_p2p.services.reporting.dispatcher import DispatchOutcome
from police_thief_p2p.shared.gatekeeper import ExternalCall, ExternalResult
from tests.helpers.reporting import build_artifact_fixture


class FakeGatekeeper:
    def __init__(self, result: ExternalResult) -> None:
        self.result = result
        self.calls: list[ExternalCall] = []

    async def execute(self, call: ExternalCall) -> ExternalResult:
        self.calls.append(call)
        return self.result


def _prepared(tmp_path: Path) -> PreparedReport:
    fixture = build_artifact_fixture(tmp_path / "artifacts")
    verified = verify_manifest(fixture.manifest, ArtifactPaths(tmp_path / "artifacts"))
    return build_report(
        verified,
        ReportingPolicy(tmp_path / "artifacts"),
        recipient=REQUIRED_RECIPIENT,
    )


def test_outbox_dispatch_is_durable_and_logically_exactly_once(tmp_path: Path) -> None:
    report = _prepared(tmp_path)
    repository = AtomicFileRepository(tmp_path / "outbox", max_bytes=4_000_000)
    outbox = DurableOutbox(repository)
    gatekeeper = FakeGatekeeper(ExternalResult("success", {"provider_id": "gmail-1"}))
    dispatcher = OutboxDispatcher(
        outbox,
        gatekeeper,
        FakeClock(),
        sender="team@example.com",
    )
    item = dispatcher.enqueue(report)
    first = asyncio.run(dispatcher.dispatch(item.logical_report_id))
    second = asyncio.run(dispatcher.dispatch(item.logical_report_id))
    assert first.outcome is DispatchOutcome.SENT
    assert second.outcome is DispatchOutcome.ALREADY_SENT
    assert len(gatekeeper.calls) == 1
    assert DurableOutbox(repository).get(item.logical_report_id).provider_id == "gmail-1"
    assert outbox.enqueue(report.item).state is OutboxState.SENT
    conflict = report.item.model_copy(update={"attachment_sha256": "f" * 64})
    with pytest.raises(ValueError, match="conflicts"):
        outbox.enqueue(conflict)
    with pytest.raises(ValueError, match="immutable-field"):
        item.transitioned(OutboxState.VALIDATED, recipient="other@example.com")


def test_outbox_recovers_interrupted_send_and_records_failures(tmp_path: Path) -> None:
    report = _prepared(tmp_path)
    repository = AtomicFileRepository(tmp_path / "outbox", max_bytes=4_000_000)
    outbox = DurableOutbox(repository)
    item = outbox.enqueue(report.item)
    outbox.transition(item.logical_report_id, OutboxState.VALIDATED)
    outbox.transition(item.logical_report_id, OutboxState.SENDING)
    recovered = DurableOutbox(repository).get(item.logical_report_id)
    assert recovered.state is OutboxState.RETRY_WAIT
    clock = FakeClock()
    auth = OutboxDispatcher(
        DurableOutbox(repository),
        FakeGatekeeper(ExternalResult("auth_error", {"code": "GMAIL_AUTH_ERROR"})),
        clock,
        sender="team@example.com",
    )
    failed = asyncio.run(auth.dispatch(item.logical_report_id))
    assert failed.outcome is DispatchOutcome.FAILED_PERMANENT
    assert failed.error_code == "GMAIL_AUTH_ERROR"


def test_retry_deadline_is_canonical_and_survives_restart(tmp_path: Path) -> None:
    report = _prepared(tmp_path)
    repository = AtomicFileRepository(tmp_path / "outbox", max_bytes=4_000_000)
    clock = FakeClock()
    gatekeeper = FakeGatekeeper(
        ExternalResult("retryable", {"code": "GMAIL_503", "retry_after_sec": 2.5})
    )
    dispatcher = OutboxDispatcher(
        DurableOutbox(repository),
        gatekeeper,
        clock,
        sender="team@example.com",
    )
    item = dispatcher.enqueue(report)
    waiting = asyncio.run(dispatcher.dispatch(item.logical_report_id))
    assert waiting.outcome is DispatchOutcome.RETRY_WAIT
    assert str(DurableOutbox(repository).get(item.logical_report_id).retry_not_before) == "2.5"
    assert asyncio.run(dispatcher.dispatch(item.logical_report_id)).outcome is (
        DispatchOutcome.RETRY_WAIT
    )
    assert len(gatekeeper.calls) == 1
    clock.advance(2.5)
    gatekeeper.result = ExternalResult("success", {"provider_id": "gmail-recovered"})
    sent = asyncio.run(dispatcher.dispatch(item.logical_report_id))
    assert sent.outcome is DispatchOutcome.SENT
    assert sent.attempts == 2


class Token:
    def access_token(self) -> str:
        return "private-token"


@pytest.mark.parametrize(
    ("response", "outcome"),
    [
        (HttpResponse(200, {}, b'{"id":"provider-1"}'), "success"),
        (HttpResponse(401, {}, b"{}"), "auth_error"),
        (HttpResponse(429, {"Retry-After": "7"}, b"{}"), "rate_limited"),
        (HttpResponse(503, {}, b"{}"), "retryable"),
        (HttpResponse(200, {}, b'{"wrong":"shape"}'), "malformed"),
    ],
)
def test_gmail_adapter_classifies_provider_results(
    response: HttpResponse,
    outcome: str,
) -> None:
    seen: list[tuple[str, bytes]] = []

    def request(url: str, body: bytes, headers: object, timeout: float) -> HttpResponse:
        _ = (headers, timeout)
        seen.append((url, body))
        return response

    sender = GmailSender(
        Token(),
        sender="team@example.com",
        post_request=request,
    )
    call = ExternalCall(
        "gmail",
        "send_report",
        {"raw_mime_b64": base64.urlsafe_b64encode(b"MIME").decode(), "priority": 2},
    )
    result = asyncio.run(sender.execute(call))
    assert result.outcome == outcome
    assert seen
    assert b"private-token" not in seen[0][1]


def test_gmail_adapter_maps_timeout_and_rejects_malformed_call() -> None:
    def timeout(*args: object) -> HttpResponse:
        raise TimeoutError

    sender = GmailSender(Token(), sender="team@example.com", post_request=timeout)
    result = asyncio.run(
        sender.execute(ExternalCall("gmail", "send_report", {"raw_mime_b64": "%%"}))
    )
    assert result.outcome == "malformed"
    valid = base64.urlsafe_b64encode(b"MIME").decode()
    result = asyncio.run(
        sender.execute(ExternalCall("gmail", "send_report", {"raw_mime_b64": valid}))
    )
    assert result.outcome == "timeout"


def test_oauth_refresh_and_first_run_keep_send_only_scope(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    credentials = tmp_path / "private" / "credentials.json"
    token_path = tmp_path / "private" / "token.json"
    credentials.parent.mkdir()
    credentials.write_text(
        json.dumps(
            {
                "installed": {
                    "client_id": "client",
                    "client_secret": "secret",  # pragma: allowlist secret
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            }
        ),
        encoding="utf-8",
    )
    responses: list[bytes] = []

    def token_post(url: str, body: bytes, headers: object, timeout: float) -> HttpResponse:
        _ = (url, headers, timeout)
        responses.append(body)
        return HttpResponse(
            200,
            {},
            b'{"access_token":"new","refresh_token":"refresh","expires_in":3600,"scope":"https://www.googleapis.com/auth/gmail.send"}',
        )

    monkeypatch.setattr(
        "police_thief_p2p.adapters.email.oauth.receive_code",
        lambda state, launch: AuthorizationCode("code", "http://127.0.0.1/callback"),
    )
    oauth = GmailOAuth(
        credentials,
        token_path,
        artifact_root=tmp_path / "artifacts",
        opener=lambda _: True,
        post_form=token_post,
    )
    with pytest.raises(ValueError, match="outside artifact"):
        GmailOAuth(
            credentials,
            token_path,
            artifact_root=tmp_path / "private",
        )
    assert oauth.access_token() == "new"
    stored = json.loads(token_path.read_text(encoding="utf-8"))
    assert stored["scopes"] == ["https://www.googleapis.com/auth/gmail.send"]
    assert "new" not in repr(oauth)
    assert "secret" not in repr(oauth)
    stored["expires_at_epoch"] = 0
    token_path.write_text(json.dumps(stored), encoding="utf-8")
    assert oauth.access_token() == "new"
    assert any(b"grant_type=refresh_token" in body for body in responses)

"""Gmail send-only provider adapter with no result-building authority."""

import asyncio
import base64
import json
from collections.abc import Callable, Mapping
from email.message import EmailMessage as MimeMessage
from email.policy import SMTP
from typing import Protocol

from police_thief_p2p.adapters.email.http import HttpResponse, parse_object, post
from police_thief_p2p.sdk.email import EmailMessage, EmailReceipt
from police_thief_p2p.shared.gatekeeper import ExternalCall, ExternalResult

_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
Post = Callable[[str, bytes, Mapping[str, str], float], HttpResponse]


class AccessTokenProvider(Protocol):
    """Return a current private provider token."""

    def access_token(self) -> str:
        """Return an OAuth access token."""
        ...


class GmailSender:
    """Send prebuilt messages through Gmail without retry or report logic."""

    __slots__ = ("_post", "_sender", "_timeout", "_tokens")

    def __init__(
        self,
        token_provider: AccessTokenProvider,
        *,
        sender: str,
        timeout_sec: float = 30,
        post_request: Post = post,
    ) -> None:
        """Configure the least-privilege provider boundary."""
        if "@" not in sender or "\n" in sender or timeout_sec <= 0:
            raise ValueError("Gmail sender configuration is invalid")
        self._tokens = token_provider
        self._sender = sender
        self._timeout = timeout_sec
        self._post = post_request

    async def send(self, message: EmailMessage) -> EmailReceipt:
        """Implement the send-only email port for a JSON attachment."""
        raw = _mime_for_port(message, self._sender)
        result = await asyncio.to_thread(self._send_raw, raw)
        if result.outcome != "success":
            raise RuntimeError(str(result.payload.get("code", "GMAIL_SEND_FAILED")))
        return EmailReceipt(str(result.payload["provider_id"]))

    async def execute(self, call: ExternalCall) -> ExternalResult:
        """Execute one Gatekeeper-admitted raw MIME send."""
        if call.service != "gmail" or call.operation != "send_report":
            return ExternalResult("permanent", {"code": "UNSUPPORTED_EMAIL_OPERATION"})
        encoded = call.payload.get("raw_mime_b64")
        if not isinstance(encoded, str) or len(encoded) > 22_369_624:
            return ExternalResult("malformed", {"code": "INVALID_MIME_PAYLOAD"})
        try:
            raw = base64.b64decode(encoded.encode("ascii"), altchars=b"-_", validate=True)
        except (ValueError, UnicodeEncodeError):
            return ExternalResult("malformed", {"code": "INVALID_MIME_PAYLOAD"})
        return await asyncio.to_thread(self._send_raw, raw)

    def _send_raw(self, raw: bytes) -> ExternalResult:
        try:
            token = self._tokens.access_token()
            body = json.dumps(
                {"raw": base64.urlsafe_b64encode(raw).decode("ascii")},
                separators=(",", ":"),
            ).encode()
            response = self._post(
                _SEND_URL,
                body,
                {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                self._timeout,
            )
        except PermissionError:
            return ExternalResult("auth_error", {"code": "GMAIL_AUTH_ERROR"})
        except TimeoutError:
            return ExternalResult("timeout", {"code": "GMAIL_TIMEOUT"})
        except OSError:
            return ExternalResult("retryable", {"code": "GMAIL_NETWORK_ERROR"})
        return _classify(response)


def _classify(response: HttpResponse) -> ExternalResult:
    if response.status == 429:
        retry = response.headers.get("Retry-After", "1")
        try:
            seconds = max(1.0, float(retry))
        except ValueError:
            seconds = 1.0
        return ExternalResult("rate_limited", {"code": "GMAIL_429", "retry_after_sec": seconds})
    if response.status in {401, 403}:
        return ExternalResult("auth_error", {"code": "GMAIL_AUTH_ERROR"})
    if response.status >= 500:
        return ExternalResult("retryable", {"code": f"GMAIL_HTTP_{response.status}"})
    if not 200 <= response.status < 300:
        return ExternalResult("permanent", {"code": f"GMAIL_HTTP_{response.status}"})
    try:
        value = parse_object(response.body)
        provider_id = value["id"]
        if not isinstance(provider_id, str) or not provider_id:
            raise ValueError
    except (KeyError, ValueError, json.JSONDecodeError):
        return ExternalResult("malformed", {"code": "GMAIL_MALFORMED_RESPONSE"})
    return ExternalResult("success", {"provider_id": provider_id})


def _mime_for_port(message: EmailMessage, sender: str) -> bytes:
    mime = MimeMessage(policy=SMTP)
    mime["To"] = message.recipient
    mime["From"] = sender
    mime["Subject"] = message.subject
    mime.set_content("The attached JSON is authoritative; this body is informational only.")
    mime.add_attachment(
        message.attachment,
        maintype="application",
        subtype="json",
        filename=message.attachment_name,
    )
    return mime.as_bytes()

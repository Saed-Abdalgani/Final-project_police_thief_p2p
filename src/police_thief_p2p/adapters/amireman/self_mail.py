"""Post-series Gmail notify for amireman runs (self, opponent, or lecturer)."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from police_thief_p2p.adapters.amireman.canonical import canonical
from police_thief_p2p.adapters.email import GmailOAuth, GmailSender
from police_thief_p2p.constants import REQUIRED_REPORT_RECIPIENT
from police_thief_p2p.sdk.email import EmailMessage


def _is_lecturer(address: str) -> bool:
    return address.strip().lower() == REQUIRED_REPORT_RECIPIENT.strip().lower()


def _assert_policy(
    sender: str,
    recipient: str,
    allowlist: tuple[str, ...] = (),
    *,
    allow_lecturer: bool = False,
) -> None:
    sender_n = sender.strip().lower()
    recipient_n = recipient.strip().lower()
    if "@" not in sender_n or _is_lecturer(sender_n):
        raise ValueError("sender must be your own Gmail account")
    if _is_lecturer(recipient_n) and not allow_lecturer:
        raise ValueError("lecturer mail is blocked on warmup/friendly runs; pass --counted")
    allowed = {sender_n}
    if allow_lecturer:
        allowed.add(REQUIRED_REPORT_RECIPIENT.strip().lower())
    if recipient_n not in allowed:
        raise ValueError("warmup/friendly mail can only go to the sender")


def _stamp_result(path: Path, *, to_lecturer: bool) -> None:
    """Align on-disk result flags with the mail destination before attach."""
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["lecturer_report_sent"] = to_lecturer
    doc["match_mode"] = "counted" if to_lecturer else "friendly"
    path.write_bytes(canonical(doc).encode("utf-8") + b"\n")


async def send_series_mail(
    *,
    result_json: Path,
    credentials: Path,
    token: Path,
    sender: str,
    recipient: str,
    artifact_root: Path,
    game_id: str,
    allowlist: tuple[str, ...] = (),
    allow_lecturer: bool = False,
) -> dict[str, Any]:
    """Send result JSON immediately after the series. Lecturer only with --counted."""
    _assert_policy(sender, recipient, allowlist, allow_lecturer=allow_lecturer)
    if not result_json.is_file():
        raise FileNotFoundError(f"missing result file: {result_json}")
    to_lecturer = _is_lecturer(recipient)
    _stamp_result(result_json, to_lecturer=to_lecturer)
    subject = (
        f"[COUNTED] Police-Thief series {game_id}"
        if to_lecturer
        else f"[DEMO NON-COUNTED] Police-Thief series {game_id}"
    )
    oauth = GmailOAuth(credentials, token, artifact_root=artifact_root, timeout_sec=180)
    oauth.access_token()
    gmail = GmailSender(oauth, sender=sender, timeout_sec=90)
    receipt = await gmail.send(
        EmailMessage(
            recipient=recipient,
            subject=subject,
            attachment_name=result_json.name,
            attachment=result_json.read_bytes(),
        )
    )
    return {
        "mail_sent": True,
        "self_mail_sent": not to_lecturer,
        "lecturer_report_sent": to_lecturer,
        "recipient": recipient,
        "sender": sender,
        "provider_id": receipt.message_id,
        "attachment": str(result_json),
        "sent_at_utc": datetime.now(UTC).isoformat(),
    }


def send_series_mail_sync(**kwargs: Any) -> dict[str, Any]:
    """Sync wrapper for CLI / post-series hooks."""
    return asyncio.run(send_series_mail(**kwargs))


# Back-compat aliases used by older call sites / docs.
send_self_demo_mail = send_series_mail
send_self_demo_mail_sync = send_series_mail_sync

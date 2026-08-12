"""Self-only DEMO Gmail notify for amireman friendly runs (never lecturer)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from police_thief_p2p.adapters.email import GmailOAuth, GmailSender
from police_thief_p2p.constants import REQUIRED_REPORT_RECIPIENT
from police_thief_p2p.sdk.email import EmailMessage


def _assert_self_only(sender: str, recipient: str) -> None:
    sender_n = sender.strip().lower()
    recipient_n = recipient.strip().lower()
    lecturer = REQUIRED_REPORT_RECIPIENT.strip().lower()
    if recipient_n == lecturer or sender_n == lecturer:
        raise ValueError("DEMO self-mail refuses the lecturer address")
    if recipient_n != sender_n:
        raise ValueError("DEMO self-mail requires recipient == sender (self only)")


async def send_self_demo_mail(
    *,
    result_json: Path,
    credentials: Path,
    token: Path,
    sender: str,
    recipient: str,
    artifact_root: Path,
    game_id: str,
) -> dict[str, Any]:
    """Send the DEMO result JSON to the operator's own Gmail. Never lecturer."""
    _assert_self_only(sender, recipient)
    if not result_json.is_file():
        raise FileNotFoundError(f"missing result file: {result_json}")
    attachment = result_json.read_bytes()
    oauth = GmailOAuth(credentials, token, artifact_root=artifact_root, timeout_sec=180)
    oauth.access_token()
    gmail = GmailSender(oauth, sender=sender, timeout_sec=90)
    receipt = await gmail.send(
        EmailMessage(
            recipient=recipient,
            subject=f"[DEMO NON-COUNTED] Police-Thief series {game_id}",
            attachment_name=result_json.name,
            attachment=attachment,
        )
    )
    return {
        "self_mail_sent": True,
        "lecturer_report_sent": False,
        "recipient": recipient,
        "provider_id": receipt.message_id,
        "attachment": str(result_json),
        "sent_at_utc": datetime.now(UTC).isoformat(),
    }


def send_self_demo_mail_sync(**kwargs: Any) -> dict[str, Any]:
    """Sync wrapper for CLI / post-series hooks."""
    return asyncio.run(send_self_demo_mail(**kwargs))

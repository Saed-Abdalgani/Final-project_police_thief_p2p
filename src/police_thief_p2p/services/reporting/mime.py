"""RFC MIME construction for one authoritative JSON attachment."""

import base64
from email.message import EmailMessage as MimeMessage
from email.policy import SMTP

from police_thief_p2p.services.reporting.models import OutboxItem
from police_thief_p2p.shared.canonical_json import digest_bytes


def build_report_mime(item: OutboxItem, *, sender: str) -> bytes:
    """Build a concise non-authoritative body plus the exact JSON attachment."""
    if "\n" in sender or "@" not in sender:
        raise ValueError("email sender is invalid")
    attachment = base64.b64decode(item.attachment_b64, validate=True)
    if digest_bytes(attachment) != item.attachment_sha256:
        raise ValueError("outbox attachment digest mismatch")
    message = MimeMessage(policy=SMTP)
    message["To"] = item.recipient
    message["From"] = sender
    message["Subject"] = f"Police-Thief final result: {item.game_uid}"
    message["X-Logical-Report-ID"] = item.logical_report_id
    message.set_content(
        "The attached JSON is the authoritative mutually agreed result. "
        "This message body is informational only."
    )
    message.add_attachment(
        attachment,
        maintype="application",
        subtype="json",
        filename=item.attachment_name,
    )
    message.set_boundary(f"police-thief-{item.logical_report_id[:32]}")
    return message.as_bytes()

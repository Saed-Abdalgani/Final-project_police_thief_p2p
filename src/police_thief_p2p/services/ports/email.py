"""Send-only email port used behind the Gatekeeper."""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class EmailMessage:
    """Validated report email containing one JSON attachment."""

    recipient: str
    subject: str
    attachment_name: str
    attachment: bytes


@dataclass(frozen=True, slots=True)
class EmailReceipt:
    """Provider-neutral successful send receipt."""

    message_id: str


@runtime_checkable
class EmailPort(Protocol):
    """Send a prevalidated message without owning retry policy."""

    async def send(self, message: EmailMessage) -> EmailReceipt:
        """Send one logical report."""
        ...

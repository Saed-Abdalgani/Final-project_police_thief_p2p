"""Thread-safe inbound mailboxes for the four amireman receive tools."""

from __future__ import annotations

import queue
from dataclasses import dataclass, field


@dataclass
class PeerInboxes:
    """Filled by MCP tool handlers; drained by the series runtime."""

    agreements: queue.Queue = field(default_factory=queue.Queue)
    turns: queue.Queue = field(default_factory=queue.Queue)
    audits: queue.Queue = field(default_factory=queue.Queue)
    controls: queue.Queue = field(default_factory=queue.Queue)

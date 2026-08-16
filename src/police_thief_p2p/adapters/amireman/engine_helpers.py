"""Small wire-value helpers shared by engine and runtime."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def now_iso() -> str:
    """Return the current UTC timestamp in ISO format."""
    return datetime.now(UTC).isoformat()


def win_kind(win_claim: dict[str, Any] | str | None) -> str | None:
    """Normalize legacy and current win claims to a result kind."""
    if isinstance(win_claim, str) and win_claim:
        return win_claim
    if isinstance(win_claim, dict):
        kind = win_claim.get("type") or win_claim.get("result")
        return str(kind) if kind else None
    return None

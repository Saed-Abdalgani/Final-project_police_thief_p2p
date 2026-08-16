"""Detailed failure evidence for compatibility audit verification."""

from __future__ import annotations

from typing import Any

from police_thief_p2p.adapters.amireman.canonical import canonical, commit_of


def worked_example(by_step: dict[int, dict[str, Any]], failed: list[int]) -> dict[str, Any] | None:
    """Return one failed record and its locally calculated digest."""
    for step in failed:
        rec = by_step.get(int(step))
        if not isinstance(rec, dict) or not isinstance(rec.get("payload"), dict):
            continue
        payload, nonce = rec["payload"], str(rec.get("nonce", ""))
        return {
            "step": int(step),
            "payload": payload,
            "nonce": nonce,
            "commit": str(rec.get("commit", "")),
            "computed": commit_of(payload, nonce) if nonce else "",
            "preimage": f"{canonical(payload)}|{nonce}",
            "scheme": (
                "sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, "
                'separators=(",", ":")) + "|" + nonce)'
            ),
        }
    return None

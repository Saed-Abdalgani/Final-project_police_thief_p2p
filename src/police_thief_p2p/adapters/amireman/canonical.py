"""Amireman-wire canonical JSON and commit-reveal primitives."""

from __future__ import annotations

import hashlib
import json
import secrets
import uuid
from typing import Any

NONCE_BYTES = 16


def canonical(obj: Any) -> str:
    """Compact sorted-key JSON used for every hash/signature on this wire."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def fresh_nonce() -> str:
    """Return exactly 32 lowercase hex characters."""
    return secrets.token_hex(NONCE_BYTES)


def commit_of(payload: dict[str, Any], nonce: str) -> str:
    """SHA-256 over canonical(payload) + literal '|' + nonce."""
    material = f"{canonical(payload)}|{nonce}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def seal(payload: dict[str, Any]) -> dict[str, str]:
    """Fresh nonce and matching commit for one payload."""
    nonce = fresh_nonce()
    return {"nonce": nonce, "commit": commit_of(payload, nonce)}


def verify(payload: dict[str, Any], nonce: str, commit: str) -> bool:
    """Return whether commit_of(payload, nonce) matches commit."""
    return secrets.compare_digest(commit_of(payload, nonce), commit)


def derive_game_ids(terms: dict[str, Any], group_a: str, group_b: str) -> tuple[str, str]:
    """Return (game_id, game_uid) identical for both peers, order-independent."""
    pair = sorted([group_a, group_b])
    game_id = "-vs-".join(pair)
    seed = f"{canonical(terms)}|{'|'.join(pair)}"
    game_uid = str(uuid.UUID(bytes=hashlib.sha256(seed.encode("utf-8")).digest()[:16]))
    return game_id, game_uid


def consensus_sha(game_id: str, game_uid: str, rows: list[dict[str, Any]]) -> str:
    """SHA-256 of the agreed consensus object {game_id, game_uid, sub_games}."""
    keys = ("sub_game_number", "result", "roles", "score", "winner_group")
    sub_games = [{k: row[k] for k in keys} for row in sorted(rows, key=lambda r: r["sub_game_number"])]
    obj = {"game_id": game_id, "game_uid": game_uid, "sub_games": sub_games}
    return hashlib.sha256(canonical(obj).encode("utf-8")).hexdigest()


def audit_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Re-verify every {payload, nonce, commit} record."""
    failed: list[int] = []
    for rec in records:
        payload = rec.get("payload")
        if not isinstance(payload, dict) or not verify(payload, str(rec["nonce"]), str(rec["commit"])):
            failed.append(int(payload.get("step", -1)) if isinstance(payload, dict) else -1)
    return {
        "passed": not failed,
        "verified_steps": len(records) - len(failed),
        "failed_steps": failed,
    }

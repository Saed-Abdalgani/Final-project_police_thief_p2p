"""Amireman-wire canonical JSON and commit-reveal primitives."""

from __future__ import annotations

import hashlib
import json
import secrets
from typing import Any

NONCE_BYTES = 16


def canonical(obj: Any) -> str:
    """Compact sorted-key JSON used for every hash/signature on this wire."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def terms_digest(terms: dict[str, Any]) -> str:
    """SHA-256 of canonical 14-key terms (SMNGRP05 / reference-v3 contract hash)."""
    return hashlib.sha256(canonical(terms).encode("utf-8")).hexdigest()


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
    """Return (game_id, game_uid) identical for both peers, order-independent.

    game_uid is the course-reference / SMNGRP05 construction: SHA-256 of
    canonical ``{"game_id", "terms"}``, then the first 32 hex chars grouped
    8-4-4-4-12. A different seed here files two honest reports as two matches.
    """
    pair = sorted([group_a, group_b])
    game_id = "-vs-".join(pair)
    fingerprint = hashlib.sha256(
        canonical({"game_id": game_id, "terms": terms}).encode("utf-8")
    ).hexdigest()
    game_uid = "-".join(
        [
            fingerprint[0:8],
            fingerprint[8:12],
            fingerprint[12:16],
            fingerprint[16:20],
            fingerprint[20:32],
        ]
    )
    return game_id, game_uid


def consensus_sha(game_id: str, game_uid: str, rows: list[dict[str, Any]]) -> str:
    """SHA-256 of the agreed consensus object {game_id, game_uid, sub_games}."""
    keys = ("sub_game_number", "result", "roles", "score", "winner_group")
    sub_games = [
        {k: row[k] for k in keys} for row in sorted(rows, key=lambda r: r["sub_game_number"])
    ]
    obj = {"game_id": game_id, "game_uid": game_uid, "sub_games": sub_games}
    return hashlib.sha256(canonical(obj).encode("utf-8")).hexdigest()


def settlement_sha(game_id: str, aggregate: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    """SHA-256 of the lecturer settlement object (spaced JSON, sorted keys).

    Compact separators are for commits. The course-reference result writer uses
    ``json.dumps(..., sort_keys=True, ensure_ascii=False)`` default spacing.
    Hashing the compact form makes two honest reports disagree under rule 35.
    """
    document = {
        "aggregate": aggregate,
        "game_id": game_id,
        "sub_games": [
            {
                "result": row["result"],
                "roles": row["roles"],
                "score": row["score"],
                "sub_game_number": row["sub_game_number"],
                "winner_group": row["winner_group"],
            }
            for row in rows
        ],
    }
    blob = json.dumps(document, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def audit_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Re-verify every {payload, nonce, commit} record."""
    failed: list[int] = []
    for rec in records:
        payload = rec.get("payload") if isinstance(rec, dict) else None
        step = int(payload.get("step", -1)) if isinstance(payload, dict) else -1
        try:
            if not isinstance(payload, dict) or not verify(
                payload, str(rec["nonce"]), str(rec["commit"])
            ):
                failed.append(step)
        except (KeyError, TypeError):
            failed.append(step)
    return {
        "passed": not failed,
        "verified_steps": len(records) - len(failed),
        "failed_steps": failed,
    }

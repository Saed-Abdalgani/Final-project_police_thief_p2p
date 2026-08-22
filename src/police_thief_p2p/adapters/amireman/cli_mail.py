"""Safe post-series email helpers for the amireman CLI."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from police_thief_p2p.adapters.amireman.self_mail import _is_lecturer, send_series_mail_sync
from police_thief_p2p.constants import REQUIRED_REPORT_RECIPIENT
from police_thief_p2p.shared.config_loader import load_private_bytes

_PLACEHOLDER_SENDERS = {"your-account@gmail.com", "lecturer@example.invalid"}


def _resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else (root / path).resolve()


def _mail_paths(root: Path, private_config: Path | None) -> tuple[Path, Path, str, tuple[str, ...]]:
    if private_config is None:
        private_config = root / "config/private/police.amireman.toml"
        if not private_config.is_file():
            private_config = root / "config/private/police.playtest.toml"
    private = load_private_bytes(private_config.read_bytes())
    return (
        _resolve(root, Path(private.email.credential_path)),
        _resolve(root, Path(private.email.token_path)),
        private.email.sender,
        tuple(private.email.recipient_allowlist),
    )


def _recipient_for(args: argparse.Namespace, sender: str) -> str:
    counted = bool(getattr(args, "counted", False))
    requested = (args.mail_to or sender).strip()
    if _is_lecturer(requested) and not counted:
        raise SystemExit(
            "refusing lecturer mail on a warmup/friendly run; "
            f"this series mails only you ({sender}). "
            "Pass --counted only for an agreed counted match."
        )
    if counted and not args.mail_to:
        raise SystemExit(
            "counted runs must pass --mail-to "
            f"{REQUIRED_REPORT_RECIPIENT} explicitly; default remains self-mail"
        )
    if not counted and requested.lower() != sender.strip().lower():
        raise SystemExit(f"warmup/friendly mail can only go to you ({sender})")
    return requested


def _do_mail(
    args: argparse.Namespace,
    root: Path,
    result_doc: dict[str, Any],
    artifacts: list[str | Path],
) -> dict[str, Any]:
    credentials, token, configured_sender, allowlist = _mail_paths(root, args.private_config)
    sender = args.mail_from or configured_sender
    if sender.lower() in _PLACEHOLDER_SENDERS:
        raise SystemExit("pass --mail-from your@gmail.com (sender is still a placeholder)")
    recipient = _recipient_for(args, sender)
    counted = bool(getattr(args, "counted", False))
    result_path = (
        Path(args.result)
        if args.command == "mail"
        else Path(next(path for path in artifacts if Path(path).name.startswith("result_")))
    )
    game_id = args.game_id or result_doc.get("game_id") or result_path.stem.replace("result_", "")
    print(f"mail: sending {result_path.name} to {recipient} (counted={counted}) …", flush=True)
    info = send_series_mail_sync(
        result_json=result_path.resolve(),
        credentials=credentials,
        token=token,
        sender=sender,
        recipient=recipient,
        artifact_root=(root / "results" / "amireman-demo").resolve(),
        game_id=str(game_id),
        allowlist=allowlist,
        allow_lecturer=counted,
    )
    print(f"mail: accepted provider_id={info['provider_id']} at {info['sent_at_utc']}", flush=True)
    return info

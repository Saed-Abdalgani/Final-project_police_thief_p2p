"""CLI for the amireman compatibility peer."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections.abc import Sequence
from pathlib import Path

from police_thief_p2p.adapters.amireman.config_map import load_terms
from police_thief_p2p.adapters.amireman.friendly import dump_result, run_friendly
from police_thief_p2p.adapters.amireman.self_mail import send_series_mail_sync
from police_thief_p2p.adapters.amireman.terms import validate_terms
from police_thief_p2p.constants import REQUIRED_REPORT_RECIPIENT
from police_thief_p2p.shared.config_loader import load_private_bytes

_PLACEHOLDER_SENDERS = {"your-account@gmail.com", "lecturer@example.invalid"}


def _git_head(root: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip()
    except (OSError, subprocess.CalledProcessError):
        return "0" * 40


def _resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else (root / path).resolve()


def _mail_paths(root: Path, private_config: Path | None) -> tuple[Path, Path, str]:
    if private_config is None:
        private_config = root / "config/private/police.amireman.toml"
        if not private_config.is_file():
            private_config = root / "config/private/police.playtest.toml"
    private = load_private_bytes(private_config.read_bytes())
    return (
        _resolve(root, Path(private.email.credential_path)),
        _resolve(root, Path(private.email.token_path)),
        private.email.sender,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    friendly = sub.add_parser("friendly", help="Series runner; mails result when finished")
    friendly.add_argument("--peer", required=True)
    friendly.add_argument("--role", required=True, choices=("police", "thief"))
    friendly.add_argument("--group", default="saedshki")
    friendly.add_argument("--games", type=int, default=6)
    friendly.add_argument("--host", default="127.0.0.1")
    friendly.add_argument("--port", type=int, default=8901)
    friendly.add_argument("--game-id", default=None)
    friendly.add_argument("--public-mcp-url", default=None)
    friendly.add_argument("--out", type=Path, required=True)
    friendly.add_argument("--terms", type=Path, default=None)
    friendly.add_argument("--member", action="append", default=[])
    friendly.add_argument("--commit", default=None)
    friendly.add_argument("--turn-timeout", type=float, default=180.0)
    friendly.add_argument("--seed", type=int, default=1234)
    friendly.add_argument("--verbose", action="store_true")
    friendly.add_argument("--no-mail", action="store_true", help="Skip post-series Gmail")
    friendly.add_argument(
        "--mail-to",
        default=REQUIRED_REPORT_RECIPIENT,
        help=f"Recipient (default: lecturer {REQUIRED_REPORT_RECIPIENT})",
    )
    friendly.add_argument("--mail-from", default=None, help="Your Gmail From address")
    friendly.add_argument("--private-config", type=Path, default=None)
    mail = sub.add_parser("mail", help="Email an existing result JSON now")
    mail.add_argument("--result", type=Path, required=True)
    mail.add_argument("--mail-to", default=REQUIRED_REPORT_RECIPIENT)
    mail.add_argument("--mail-from", default=None)
    mail.add_argument("--private-config", type=Path, default=None)
    mail.add_argument("--game-id", default=None)
    return parser


def _do_mail(args, root: Path, result_doc: dict, artifacts: list) -> dict:
    credentials, token, configured_sender = _mail_paths(root, args.private_config)
    sender = args.mail_from or configured_sender
    if sender.lower() in _PLACEHOLDER_SENDERS:
        raise SystemExit("pass --mail-from your@gmail.com (sender is still a placeholder)")
    recipient = args.mail_to or REQUIRED_REPORT_RECIPIENT
    result_path = (
        Path(args.result)
        if args.command == "mail"
        else Path(next(path for path in artifacts if Path(path).name.startswith("result_")))
    )
    game_id = args.game_id or result_doc.get("game_id") or result_path.stem.replace("result_", "")
    print(f"mail: sending {result_path.name} to {recipient} …", flush=True)
    info = send_series_mail_sync(
        result_json=result_path.resolve(),
        credentials=credentials,
        token=token,
        sender=sender,
        recipient=recipient,
        artifact_root=(root / "results" / "amireman-demo").resolve(),
        game_id=str(game_id),
    )
    print(
        f"mail: accepted provider_id={info['provider_id']} at {info['sent_at_utc']}",
        flush=True,
    )
    return info


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(__file__).resolve().parents[4]
    if args.command == "mail":
        info = _do_mail(args, root, {}, [])
        print(json.dumps(info, indent=2))
        return 0 if info.get("mail_sent") else 1
    if args.command == "self-mail":
        raise SystemExit("renamed: use `mail` instead of `self-mail`")
    if args.command != "friendly":
        raise SystemExit(f"unknown command {args.command}")
    members = list(args.member) or ["Member One", "Member Two"]
    terms = load_terms(args.terms)
    validate_terms(terms)
    commit = args.commit or _git_head(root)
    listener = (lambda event: print(event, flush=True)) if args.verbose else None
    result = run_friendly(
        args.group,
        args.peer,
        args.role,
        terms,
        args.out,
        host=args.host,
        port=args.port,
        github_commit=commit,
        num_games=args.games,
        seed=args.seed,
        turn_timeout=args.turn_timeout,
        members=members,
        public_mcp_url=args.public_mcp_url,
        listener=listener,
        game_id=args.game_id,
    )
    payload = json.loads(dump_result(result))
    if not args.no_mail:
        payload.update(_do_mail(args, root, result.result_doc, result.artifacts))
    else:
        payload.update({"mail_sent": False, "lecturer_report_sent": False})
    print(json.dumps(payload, indent=2))
    ok = result.clean and result.sha_match
    if not args.no_mail:
        ok = ok and bool(payload.get("mail_sent"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

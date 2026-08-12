"""CLI for the amireman compatibility peer (DEMO / friendly only)."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections.abc import Sequence
from pathlib import Path

from police_thief_p2p.adapters.amireman.config_map import load_terms
from police_thief_p2p.adapters.amireman.friendly import dump_result, run_friendly
from police_thief_p2p.adapters.amireman.self_mail import send_self_demo_mail_sync
from police_thief_p2p.adapters.amireman.terms import validate_terms
from police_thief_p2p.shared.config_loader import load_private_bytes


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
    friendly = sub.add_parser("friendly", help="DEMO / NON-COUNTED series (never emails lecturer)")
    friendly.add_argument("--peer", required=True, help="Opponent public MCP URL ending in /mcp")
    friendly.add_argument("--role", required=True, choices=("police", "thief"))
    friendly.add_argument("--group", default="saedshki")
    friendly.add_argument("--games", type=int, default=6)
    friendly.add_argument("--host", default="127.0.0.1")
    friendly.add_argument("--port", type=int, default=8901)
    friendly.add_argument("--game-id", default=None)
    friendly.add_argument("--public-mcp-url", default=None)
    friendly.add_argument("--out", type=Path, required=True)
    friendly.add_argument("--terms", type=Path, default=None, help="Flat terms or nested game.json")
    friendly.add_argument("--member", action="append", default=[], help="Repeatable member name")
    friendly.add_argument("--commit", default=None, help="40-hex runtime SHA (default: git HEAD)")
    friendly.add_argument("--turn-timeout", type=float, default=180.0)
    friendly.add_argument("--seed", type=int, default=1234)
    friendly.add_argument("--verbose", action="store_true")
    friendly.add_argument("--self-mail", action="store_true", help="Email DEMO result JSON to yourself")
    friendly.add_argument("--mail-to", default=None, help="Self Gmail (defaults to private sender)")
    friendly.add_argument("--private-config", type=Path, default=None)
    mail = sub.add_parser("self-mail", help="Email an existing DEMO result JSON to yourself")
    mail.add_argument("--result", type=Path, required=True)
    mail.add_argument("--mail-to", default=None)
    mail.add_argument("--private-config", type=Path, default=None)
    mail.add_argument("--game-id", default=None)
    return parser


def _maybe_self_mail(args, root: Path, result_doc: dict, artifacts: list) -> dict:
    if not getattr(args, "self_mail", False) and args.command != "self-mail":
        return {"self_mail_sent": False, "lecturer_report_sent": False}
    credentials, token, configured_sender = _mail_paths(root, args.private_config)
    recipient = args.mail_to or configured_sender
    sender = recipient  # DEMO self-mail: From and To are the same operator inbox
    result_path = (
        Path(args.result)
        if args.command == "self-mail"
        else Path(next(path for path in artifacts if Path(path).name.startswith("result_")))
    )
    game_id = args.game_id or result_doc.get("game_id") or result_path.stem.replace("result_", "")
    return send_self_demo_mail_sync(
        result_json=result_path.resolve(),
        credentials=credentials,
        token=token,
        sender=sender,
        recipient=recipient,
        artifact_root=(root / "results" / "amireman-demo").resolve(),
        game_id=str(game_id),
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(__file__).resolve().parents[4]
    if args.command == "self-mail":
        info = _maybe_self_mail(args, root, {}, [])
        print(json.dumps(info, indent=2))
        return 0 if info.get("self_mail_sent") else 1
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
    if args.self_mail:
        payload.update(_maybe_self_mail(args, root, result.result_doc, result.artifacts))
    print(json.dumps(payload, indent=2))
    return 0 if result.clean and result.sha_match else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""CLI for the amireman compatibility peer."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
from pathlib import Path

from police_thief_p2p.adapters.amireman.cli_mail import (
    _do_mail,
    _resolve,
)
from police_thief_p2p.adapters.amireman.cli_mail import (
    _recipient_for as _recipient_for,
)
from police_thief_p2p.adapters.amireman.cli_parser import build_parser as build_parser
from police_thief_p2p.adapters.amireman.client import mcp_url
from police_thief_p2p.adapters.amireman.config_map import load_terms
from police_thief_p2p.adapters.amireman.friendly import dump_result, run_friendly
from police_thief_p2p.adapters.amireman.terms import validate_terms
from police_thief_p2p.shared.config_loader import load_private_bytes


def _git_head(root: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],  # noqa: S607
            cwd=root,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip()
    except (OSError, subprocess.CalledProcessError):
        return "0" * 40


def main(argv: Sequence[str] | None = None) -> int:
    """Run one compatibility command and return a shell status."""
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
    members = list(args.member) or ["Mohamed Shawki", "Saed-Abdalgani"]
    terms = load_terms(args.terms)
    if getattr(args, "setting", None):
        terms["setting"] = args.setting
    validate_terms(terms)
    commit = args.commit or _git_head(root)
    private_path = args.private_config or root / "config/private/police.amireman.toml"
    private = load_private_bytes(_resolve(root, private_path).read_bytes())
    listener = (lambda event: print(event, flush=True)) if args.verbose else None
    result = run_friendly(
        args.group,
        mcp_url(args.peer),
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
        public_mcp_url=mcp_url(args.public_mcp_url) if args.public_mcp_url else None,
        listener=listener,
        game_id=args.game_id,
        scent_model=args.scent_model,
        strategy=private.strategy,
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

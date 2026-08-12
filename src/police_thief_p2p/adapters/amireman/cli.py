"""CLI for the amireman compatibility peer (DEMO / friendly only)."""

from __future__ import annotations

import argparse
import subprocess
from collections.abc import Sequence
from pathlib import Path

from police_thief_p2p.adapters.amireman.config_map import load_terms
from police_thief_p2p.adapters.amireman.friendly import dump_result, run_friendly
from police_thief_p2p.adapters.amireman.terms import validate_terms


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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command != "friendly":
        raise SystemExit(f"unknown command {args.command}")
    members = list(args.member) or ["Member One", "Member Two"]
    terms = load_terms(args.terms)
    validate_terms(terms)
    root = Path(__file__).resolve().parents[4]
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
    print(dump_result(result))
    return 0 if result.clean and result.sha_match else 1


if __name__ == "__main__":
    raise SystemExit(main())

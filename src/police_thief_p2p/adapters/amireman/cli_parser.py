"""Argument parser for the amireman compatibility CLI."""

from __future__ import annotations

import argparse
from pathlib import Path

from police_thief_p2p.adapters.amireman.scent import (
    MULTIPLICATIVE_KERNEL_V1,
    SUBTRACTIVE_CHEBYSHEV_V1,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the compatibility peer command-line parser."""
    parser = argparse.ArgumentParser(description="Amireman compatibility peer")
    sub = parser.add_subparsers(dest="command", required=True)
    friendly = sub.add_parser("friendly", help="Series runner; mails result when finished")
    friendly.add_argument("--peer", required=True)
    friendly.add_argument("--role", required=True, choices=("police", "thief"))
    friendly.add_argument("--group", default="GRP00001")
    friendly.add_argument("--games", type=int, default=6)
    friendly.add_argument("--host", default="127.0.0.1")
    friendly.add_argument("--port", type=int, default=8901)
    friendly.add_argument("--game-id", default=None)
    friendly.add_argument("--game-uid", default=None)
    friendly.add_argument("--public-mcp-url", default=None)
    friendly.add_argument("--out", type=Path, required=True)
    friendly.add_argument("--terms", type=Path, default=None)
    friendly.add_argument(
        "--setting",
        default=None,
        help="Override signed terms 'setting' (must match opponent, e.g. 'New York')",
    )
    friendly.add_argument("--member", action="append", default=[])
    friendly.add_argument("--commit", default=None)
    friendly.add_argument("--police-commit", default=None)
    friendly.add_argument("--thief-commit", default=None)
    friendly.add_argument("--canonical-commit", default=None)
    friendly.add_argument("--turn-timeout", type=float, default=180.0)
    friendly.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Deterministic rehearsal seed; omitted generates a private per-series seed",
    )
    friendly.add_argument("--verbose", action="store_true")
    friendly.add_argument(
        "--scent-model",
        default=MULTIPLICATIVE_KERNEL_V1,
        choices=(MULTIPLICATIVE_KERNEL_V1, SUBTRACTIVE_CHEBYSHEV_V1),
        help="Wire scent physics. SMNGRP05 warmup: subtractive_chebyshev_v1",
    )
    friendly.add_argument("--no-mail", action="store_true", help="Skip post-series Gmail")
    friendly.add_argument(
        "--wait-enter",
        action="store_true",
        help="Listen on /mcp, then wait for ENTER before any negotiate",
    )
    friendly.add_argument(
        "--mail-to",
        default=None,
        help="Recipient; lecturer mail requires --counted",
    )
    friendly.add_argument("--mail-from", default=None, help="Your Gmail From address")
    friendly.add_argument("--counted", action="store_true", help="Permit mailing the lecturer")
    friendly.add_argument("--private-config", type=Path, default=None)
    mail = sub.add_parser("mail", help="Email an existing result JSON now")
    mail.add_argument("--result", type=Path, required=True)
    mail.add_argument("--mail-to", default=None)
    mail.add_argument("--mail-from", default=None)
    mail.add_argument("--private-config", type=Path, default=None)
    mail.add_argument("--game-id", default=None)
    mail.add_argument("--counted", action="store_true", help="Permit mailing the lecturer")
    return parser

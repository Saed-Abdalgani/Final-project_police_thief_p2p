"""Thin command-line adapter over :class:`SimulationSdk`."""

import argparse
import json
from collections.abc import Sequence

from police_thief_p2p.sdk import SimulationSdk


def build_parser() -> argparse.ArgumentParser:
    """Build the foundation command parser."""
    parser = argparse.ArgumentParser(prog="police-thief-p2p")
    subparsers = parser.add_subparsers(dest="command", required=True)
    readiness = subparsers.add_parser("readiness", help="show foundation readiness")
    readiness.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI without bypassing the public SDK."""
    args = build_parser().parse_args(argv)
    if args.command != "readiness":
        build_parser().error("unsupported command")

    report = SimulationSdk().check_readiness()
    if args.as_json:
        print(json.dumps(report.as_dict(), sort_keys=True))
    else:
        print(f"{report.status.value}: package {report.versions.package}")
        for check in report.checks:
            print(f"- {check.name}: {'PASS' if check.passed else 'FAIL'} - {check.detail}")
    return 0 if report.is_ready else 1

"""Thin command-line adapter over :class:`SimulationSdk`."""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from police_thief_p2p.constants import REQUIRED_REPORT_RECIPIENT
from police_thief_p2p.sdk import ReplayIntegrity, SimulationSdk


def build_parser() -> argparse.ArgumentParser:
    """Build the foundation command parser."""
    parser = argparse.ArgumentParser(prog="police-thief-p2p")
    subparsers = parser.add_subparsers(dest="command", required=True)
    readiness = subparsers.add_parser("readiness", help="show foundation readiness")
    readiness.add_argument("--json", action="store_true", dest="as_json")
    report = subparsers.add_parser("report", help="reporting operations")
    report_commands = report.add_subparsers(dest="report_command", required=True)
    validate = report_commands.add_parser(
        "validate",
        help="validate artifacts, report JSON, and MIME without sending",
    )
    validate.add_argument("--manifest", required=True, type=Path)
    validate.add_argument("--artifact-root", required=True, type=Path)
    validate.add_argument("--sender", required=True)
    validate.add_argument("--recipient", default=REQUIRED_REPORT_RECIPIENT)
    replay = subparsers.add_parser("replay", help="offline replay verification")
    replay_commands = replay.add_subparsers(dest="replay_command", required=True)
    verify = replay_commands.add_parser(
        "verify",
        help="verify a linked finalized log and optionally export audit reports",
    )
    verify.add_argument("--manifest", required=True, type=Path)
    verify.add_argument("--artifact-root", required=True, type=Path)
    verify.add_argument("--group", required=True)
    verify.add_argument("--sub-game", required=True, type=int, choices=range(1, 7))
    verify.add_argument("--json-report", type=Path)
    verify.add_argument("--html-report", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI without bypassing the public SDK."""
    args = build_parser().parse_args(argv)
    if args.command == "report":
        return _validate_report(args)
    if args.command == "replay":
        return _verify_replay(args)
    if args.command != "readiness":
        return 2

    report = SimulationSdk().check_readiness()
    if args.as_json:
        print(json.dumps(report.as_dict(), sort_keys=True))
    else:
        print(f"{report.status.value}: package {report.versions.package}")
        for check in report.checks:
            print(f"- {check.name}: {'PASS' if check.passed else 'FAIL'} - {check.detail}")
    return 0 if report.is_ready else 1


def _validate_report(args: argparse.Namespace) -> int:
    """Run the reporting dry-run without outbox or provider state changes."""
    sdk = SimulationSdk()
    try:
        manifest = sdk.load_artifact_manifest(args.manifest.read_bytes())
        report = sdk.prepare_report(
            manifest,
            args.artifact_root,
            recipient=args.recipient,
            allowlist=(args.recipient,),
            competition_mode=args.recipient == REQUIRED_REPORT_RECIPIENT,
        )
        mime = sdk.validate_report_mime(report, sender=args.sender)
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "INVALID", "error": str(exc)}, sort_keys=True))
        return 2
    print(
        json.dumps(
            {
                "status": "VALID",
                "logical_report_id": report.item.logical_report_id,
                "attachment_sha256": report.item.attachment_sha256,
                "mime_bytes": len(mime),
                "external_state_changed": False,
            },
            sort_keys=True,
        )
    )
    return 0


def _verify_replay(args: argparse.Namespace) -> int:
    """Verify one manifest-linked log and export reports without bypassing SDK."""
    sdk = SimulationSdk()
    try:
        result = sdk.verify_manifest_log(
            args.manifest.read_bytes(),
            args.artifact_root,
            sub_game_number=args.sub_game,
            viewer_group=args.group,
        )
        machine, human = sdk.export_replay(result)
        if args.json_report is not None:
            _exclusive_write(args.json_report, machine)
        if args.html_report is not None:
            _exclusive_write(args.html_report, human)
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "INVALID", "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result.as_dict(), sort_keys=True))
    return 0 if result.integrity is ReplayIntegrity.VERIFIED_OK else 3


def _exclusive_write(path: Path, document: bytes) -> None:
    """Create one export without silently replacing existing evidence."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(document)

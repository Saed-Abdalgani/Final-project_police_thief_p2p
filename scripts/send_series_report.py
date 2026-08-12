"""Validate or send one finished-series Gmail JSON report through the outbox."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from police_thief_p2p.adapters.email import GmailOAuth, GmailSender
from police_thief_p2p.adapters.persistence import AtomicFileRepository
from police_thief_p2p.adapters.system.clocks import SystemClock
from police_thief_p2p.adapters.system.deterministic_random import DeterministicRandomSource
from police_thief_p2p.constants import REQUIRED_REPORT_RECIPIENT
from police_thief_p2p.sdk import SimulationSdk
from police_thief_p2p.services.gatekeeper import DurableQuotaManager, FullGatekeeper, load_profiles
from police_thief_p2p.services.reporting import DurableOutbox, OutboxDispatcher
from police_thief_p2p.shared.config_loader import load_private_bytes
from scripts.m12_campaign_support import ROOT

DEFAULT_PRIVATE = ROOT / "config/private/police.playtest.toml"
DEFAULT_RATES = ROOT / "config/rate_limits.example.json"


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else (ROOT / path).resolve()


def _email(private_path: Path) -> tuple[Path, Path, str, tuple[str, ...], Path]:
    private = load_private_bytes(private_path.read_bytes())
    root = _resolve(private.paths.artifact_root)
    return (
        _resolve(private.email.credential_path),
        _resolve(private.email.token_path),
        private.email.sender,
        private.email.recipient_allowlist,
        root,
    )


def _prepare(manifest_path: Path, artifact_root: Path, recipient: str, allowlist: tuple[str, ...]):
    sdk = SimulationSdk()
    return sdk.prepare_report(
        sdk.load_artifact_manifest(manifest_path.read_bytes()),
        artifact_root,
        recipient=recipient,
        allowlist=allowlist,
        competition_mode=recipient == REQUIRED_REPORT_RECIPIENT,
    )


async def _send(report, artifact_root: Path, credentials: Path, token: Path, sender: str, rates: Path):
    clock = SystemClock()
    oauth = GmailOAuth(credentials, token, artifact_root=artifact_root, timeout_sec=180)
    oauth.access_token()  # browser login happens here, outside Gatekeeper timeout
    profiles = dict(load_profiles(rates.read_bytes()).services)
    profiles["gmail"] = profiles["gmail"].model_copy(update={"timeout_sec": 120})
    gatekeeper = FullGatekeeper(
        profiles,
        {"gmail": GmailSender(oauth, sender=sender, timeout_sec=90)},
        clock=clock,
        quota=DurableQuotaManager(
            AtomicFileRepository(artifact_root / "diagnostics" / "gmail-quota"),
            clock,
            session_id="report-send",
        ),
        rng=DeterministicRandomSource(11),
    )
    dispatcher = OutboxDispatcher(
        DurableOutbox(AtomicFileRepository(artifact_root / "diagnostics" / "gmail-outbox")),
        gatekeeper,
        clock,
        sender=sender,
    )
    item = dispatcher.enqueue(report)
    return await dispatcher.dispatch(item.logical_report_id)


def _demo_manifest(artifact_root: Path) -> Path:
    from tests.helpers.reporting import build_artifact_fixture

    build_artifact_fixture(artifact_root)
    matches = sorted((artifact_root / "official").glob("manifest_*.json"))
    if not matches:
        raise FileNotFoundError("demo fixture did not write a manifest")
    return matches[0]


def main(argv: list[str] | None = None) -> int:
    """Dry-run by default; use --send for one real Gmail outbox dispatch."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-config", type=Path, default=DEFAULT_PRIVATE)
    parser.add_argument("--rate-limits", type=Path, default=DEFAULT_RATES)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--recipient")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--send", action="store_true")
    args = parser.parse_args(argv)

    credentials, token, sender, allowlist, configured = _email(args.private_config.resolve())
    artifact_root = _resolve(args.artifact_root) if args.artifact_root else configured
    recipient = args.recipient or allowlist[0]
    if recipient not in allowlist:
        raise SystemExit(f"recipient {recipient!r} is not on the private allowlist")
    if args.demo:
        artifact_root = artifact_root / "gmail-demo"
        artifact_root.mkdir(parents=True, exist_ok=True)
        manifest_path = _demo_manifest(artifact_root)
    elif args.manifest is None:
        raise SystemExit("--manifest is required unless --demo is set")
    else:
        manifest_path = args.manifest.resolve()

    report = _prepare(manifest_path, artifact_root, recipient, allowlist)
    mime = SimulationSdk().validate_report_mime(report, sender=sender)
    base = {
        "mode": "send" if args.send else "dry-run",
        "manifest": str(manifest_path),
        "artifact_root": str(artifact_root),
        "sender": sender,
        "recipient": recipient,
        "logical_report_id": report.item.logical_report_id,
        "attachment_sha256": report.item.attachment_sha256,
        "mime_bytes": len(mime),
    }
    if not args.send:
        print(json.dumps({**base, "status": "VALID", "token_exists": token.exists()}, sort_keys=True))
        return 0
    receipt = asyncio.run(
        _send(report, artifact_root, credentials, token, sender, args.rate_limits.resolve())
    )
    print(
        json.dumps(
            {
                **base,
                "status": receipt.outcome.value,
                "attempts": receipt.attempts,
                "provider_id_present": receipt.provider_id is not None,
                "error_code": receipt.error_code,
                "token_exists": token.exists(),
            },
            sort_keys=True,
        )
    )
    return 0 if receipt.outcome.value in {"sent", "already-sent"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

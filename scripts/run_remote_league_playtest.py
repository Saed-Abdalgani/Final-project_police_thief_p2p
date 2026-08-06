"""Drive a counted league playtest against two already-running peer MCP URLs."""

import argparse
import asyncio
import json
from pathlib import Path

from police_thief_p2p.shared.config_loader import load_shared_bytes
from scripts.m12_campaign_support import SHARED_CONFIG
from scripts.playtest_support import (
    drive_series,
    normalize_mcp_url,
    probe_health,
    write_remote_evidence,
)


def _parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--police-url", required=True, help="Police peer MCP URL")
    parser.add_argument("--thief-url", required=True, help="Thief peer MCP URL")
    parser.add_argument(
        "--shared-config",
        default=str(SHARED_CONFIG),
        help="Byte-identical shared game JSON used by both peers",
    )
    return parser.parse_args()


async def _run(police_url: str, thief_url: str, shared_path: Path) -> int:
    police = normalize_mcp_url(police_url)
    thief = normalize_mcp_url(thief_url)
    shared_bytes = shared_path.read_bytes()
    shared = load_shared_bytes(shared_bytes)
    police_ok = await probe_health(police, timeout_sec=5.0)
    thief_ok = await probe_health(thief, timeout_sec=5.0)
    print(json.dumps({"preflight": {"police_ok": police_ok, "thief_ok": thief_ok}}, sort_keys=True))
    if not (police_ok and thief_ok):
        write_remote_evidence(
            police_url=police,
            thief_url=thief,
            series={"warmups": [], "counted": []},
            police_ok=police_ok,
            thief_ok=thief_ok,
        )
        return 1
    series = await drive_series(police, thief, shared, shared_bytes)
    path = write_remote_evidence(
        police_url=police,
        thief_url=thief,
        series=series,
        police_ok=police_ok,
        thief_ok=thief_ok,
    )
    document = json.loads(path.read_text(encoding="utf-8"))
    print(json.dumps({"evidence": str(path), "gates": document["gates"]}, sort_keys=True))
    return 0 if document["gates"]["result"] == "PASS" else 1


def main() -> int:
    """Probe both peers, then run warmups plus six counted sub-games."""
    args = _parse()
    return asyncio.run(_run(args.police_url, args.thief_url, Path(args.shared_config)))


if __name__ == "__main__":
    raise SystemExit(main())

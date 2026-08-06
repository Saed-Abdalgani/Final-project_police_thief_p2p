"""Run the M12 league dress rehearsal between two independently rooted peers."""

import asyncio
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from police_thief_p2p.services.experiments.resources import measure
from police_thief_p2p.shared.config_loader import load_private_path, load_shared_bytes
from police_thief_p2p.shared.config_models import SharedConfig
from scripts.m12_campaign_support import (
    BENCHMARKS,
    PRIVATE_CONFIG,
    SCHEMA_VERSION,
    SHARED_CONFIG,
    commit_sha,
    write_evidence,
)
from scripts.m12_rehearsal_peers import (
    PeerRoot,
    await_health,
    free_port,
    prepare_peer,
    probe_health,
    start_peer,
    stop_peers,
)
from scripts.m12_rehearsal_series import SUB_GAMES, build_plan, client, play_sub_game
from scripts.m12_rehearsal_summary import (
    artifact_families,
    calendar_entries,
    rehearsal_gates,
    tunnel_preflight,
)

WARMUP_GAMES = 2
GROUP_A = "GRP00001"
GROUP_B = "GRP00002"


def _build_roots(rehearsal_root: Path, shared_bytes: bytes) -> dict[str, PeerRoot]:
    ports = {"alpha": free_port(), "beta": free_port()}
    return {
        "alpha": prepare_peer(
            "alpha",
            rehearsal_root / "peer-alpha",
            shared_bytes,
            group=GROUP_A,
            role="police",
            port=ports["alpha"],
            opponent_port=ports["beta"],
        ),
        "beta": prepare_peer(
            "beta",
            rehearsal_root / "peer-beta",
            shared_bytes,
            group=GROUP_B,
            role="thief",
            port=ports["beta"],
            opponent_port=ports["alpha"],
        ),
    }


async def _series(
    peers: dict[str, PeerRoot],
    shared: SharedConfig,
    shared_bytes: bytes,
) -> dict[str, object]:
    warmups = []
    for number in range(1, WARMUP_GAMES + 1):
        plan = build_plan(shared, shared_bytes, number, counted=False)
        warmups.append(await play_sub_game(client(peers["alpha"].endpoint), plan, sender=GROUP_B))
    counted = []
    for number in range(1, SUB_GAMES + 1):
        plan = build_plan(shared, shared_bytes, number, counted=True)
        left, right = await asyncio.gather(
            play_sub_game(client(peers["alpha"].endpoint), plan, sender=GROUP_B),
            play_sub_game(client(peers["beta"].endpoint), plan, sender=GROUP_A),
        )
        counted.append(
            {
                **left,
                "both_peers_agree": left["phases"] == right["phases"],
                "opponent_phases": right["phases"],
            }
        )
    return {"warmups": warmups, "counted": counted}


def main() -> int:
    """Start two isolated peers, warm up, then run the counted six-sub-game series.

    Peer roots live in a fresh directory outside the repository: each peer persists durable
    session snapshots by atomic replacement, and a workspace file watcher holding a handle on
    a snapshot makes that replacement fail on Windows.
    """
    rehearsal_root = Path(tempfile.mkdtemp(prefix="m12-league-rehearsal-"))
    shared_bytes = Path(SHARED_CONFIG).read_bytes()
    shared = load_shared_bytes(shared_bytes)
    private = load_private_path(PRIVATE_CONFIG)
    peers = _build_roots(rehearsal_root, shared_bytes)
    processes: dict[str, subprocess.Popen[bytes]] = {}
    with measure() as ledger:
        try:
            for name, peer in peers.items():
                processes[name] = start_peer(peer)
                asyncio.run(await_health(peer.endpoint, processes[name]))
            preflight = tunnel_preflight(peers, private)
            bidirectional = all(asyncio.run(probe_health(peer.endpoint)) for peer in peers.values())
            series = asyncio.run(_series(peers, shared, shared_bytes))
        finally:
            stop_peers(processes)
    for row in (*series["warmups"], *series["counted"]):  # type: ignore[misc]
        ledger.record_call(len(json.dumps(row).encode("utf-8")), 0.0)
    usage = ledger.usage()
    artifacts = artifact_families(peers)
    gates = rehearsal_gates(series, preflight, artifacts, bidirectional=bidirectional)
    document = {
        "schema_version": SCHEMA_VERSION,
        "commit_sha": commit_sha(),
        "procedure": {
            "peer_roots": {
                name: {
                    "root_leaf": peer.root.name,
                    "group_id": peer.group,
                    "endpoint": peer.endpoint,
                    "artifact_root_leaf": f"{peer.root.name}/{peer.artifact_root.name}",
                    "process_id": processes[name].pid,
                }
                for name, peer in peers.items()
            },
            "separation": (
                "Each peer owns a distinct repository-style root with its own configuration, "
                "artifact root, cache, and temporary directories, and runs as its own operating "
                "system process with an independent port. Both roots live in a fresh "
                "operating-system temporary directory outside the repository, so peer state is "
                "never shared with the workspace or with a previous rehearsal."
            ),
            "transport": "streamable HTTP MCP over the configured tunnel health endpoints",
            "manual_intervention": "none; every move came from the frozen strategy pipeline",
            "wall_time_sec": round(usage.wall_time_sec, 3),
        },
        "resources": usage.as_document(),
        "tunnel_preflight": preflight,
        "league_calendar": calendar_entries(),
        "warmups": series["warmups"],
        "counted_series": series["counted"],
        "artifact_families": artifacts,
        "gates": gates,
    }
    write_evidence(BENCHMARKS / "m12_league_rehearsal.json", document)
    shutil.rmtree(rehearsal_root, ignore_errors=True)
    print(json.dumps(gates, sort_keys=True))
    return 0 if gates["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Shared helpers for local and remote end-to-end playtest campaigns."""

from pathlib import Path
from urllib.parse import urlsplit

from police_thief_p2p.shared.config_models import SharedConfig
from scripts.m12_campaign_support import BENCHMARKS, SCHEMA_VERSION, commit_sha, write_evidence
from scripts.m12_rehearsal_peers import probe_health
from scripts.m12_rehearsal_series import SUB_GAMES, build_plan, client, play_sub_game

GROUP_A = "GRP00001"
GROUP_B = "GRP00002"
WARMUP_GAMES = 2


def normalize_mcp_url(url: str) -> str:
    """Require an absolute MCP endpoint ending with /mcp."""
    parsed = urlsplit(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"invalid peer URL: {url!r}")
    path = parsed.path.rstrip("/") or "/mcp"
    if not path.endswith("/mcp"):
        path = f"{path}/mcp"
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def is_external_https(url: str) -> bool:
    """Return whether the URL looks like a non-loopback public HTTPS endpoint."""
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and host not in {"127.0.0.1", "localhost", "::1"}


async def drive_series(
    police_url: str,
    thief_url: str,
    shared: SharedConfig,
    shared_bytes: bytes,
) -> dict[str, object]:
    """Run warmups against police, then counted games against both peers."""
    police = client(police_url)
    thief = client(thief_url)
    warmups = []
    for number in range(1, WARMUP_GAMES + 1):
        plan = build_plan(shared, shared_bytes, number, counted=False)
        warmups.append(await play_sub_game(police, plan, sender=GROUP_B))
    counted = []
    for number in range(1, SUB_GAMES + 1):
        plan = build_plan(shared, shared_bytes, number, counted=True)
        left = await play_sub_game(police, plan, sender=GROUP_B)
        right = await play_sub_game(thief, plan, sender=GROUP_A)
        counted.append(
            {
                **left,
                "both_peers_agree": left["phases"] == right["phases"],
                "opponent_phases": right["phases"],
            }
        )
    return {"warmups": warmups, "counted": counted}


def write_remote_evidence(
    *,
    police_url: str,
    thief_url: str,
    series: dict[str, object],
    police_ok: bool,
    thief_ok: bool,
) -> Path:
    """Persist remote playtest evidence and return the evidence path."""
    external = is_external_https(police_url) and is_external_https(thief_url)
    counted = list(series["counted"])
    warmups = list(series["warmups"])
    gates = {
        "bidirectional_preflight_ok": police_ok and thief_ok,
        "warmups_completed": bool(warmups) and all(bool(item["completed"]) for item in warmups),
        "six_counted_sub_games": len(counted) == 6,
        "every_counted_sub_game_completed": all(bool(item["completed"]) for item in counted),
        "both_peers_reached_identical_phases": all(
            bool(item["both_peers_agree"]) for item in counted
        ),
        "external_network_tunnels_verified": external,
    }
    gates["result"] = "PASS" if all(gates.values()) else "FAIL"
    path = BENCHMARKS / "two_machine_playtest.json"
    write_evidence(
        path,
        {
            "schema_version": SCHEMA_VERSION,
            "commit_sha": commit_sha(),
            "endpoints": {"police": police_url, "thief": thief_url},
            "preflight": {"police_ok": police_ok, "thief_ok": thief_ok, "external": external},
            "warmups": warmups,
            "counted_series": counted,
            "gates": gates,
        },
    )
    return path


__all__ = [
    "GROUP_A",
    "GROUP_B",
    "drive_series",
    "is_external_https",
    "normalize_mcp_url",
    "probe_health",
    "write_remote_evidence",
]

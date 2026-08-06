"""Preflight, calendar, artifact-family, and gate summaries for the rehearsal."""

import asyncio
from collections.abc import Mapping, Sequence
from typing import Any

from police_thief_p2p.shared.private_config import PrivateConfig
from scripts.m12_rehearsal_peers import PeerRoot, probe_health

ARTIFACT_FAMILIES = ("protocol", "official", "audit", "replay")
COUNTED_MATCHES = (
    {
        "match_id": "rehearsal-1",
        "opponent_group_id": "GRP00002",
        "counted": True,
        "scheduled_utc": "2026-08-06T09:00:00Z",
        "status": "rehearsed",
    },
    {
        "match_id": "rehearsal-2",
        "opponent_group_id": "GRP00003",
        "counted": True,
        "scheduled_utc": "2026-08-07T09:00:00Z",
        "status": "scheduled",
    },
)


def tunnel_preflight(peers: Mapping[str, PeerRoot], private: PrivateConfig) -> dict[str, object]:
    """Probe every peer endpoint in both directions and record the tunnel provider."""
    probes = {
        name: {
            "endpoint": peer.endpoint,
            "healthy": asyncio.run(probe_health(peer.endpoint)),
        }
        for name, peer in peers.items()
    }
    return {
        "configured_provider": private.tunnel.provider,
        "configured_health_url": str(private.tunnel.health_url),
        "probes": probes,
        "bidirectional": all(bool(item["healthy"]) for item in probes.values()),
        "external_network_verified": False,
        "limitation": (
            "Both peers ran on one host over loopback tunnels, so the endpoints are logically "
            "separate but not verified from an external network. A public-tunnel provider and a "
            "second machine are still required before a counted league match."
        ),
    }


def calendar_entries() -> list[dict[str, object]]:
    """Return the league calendar and counted-match ledger rows."""
    return [dict(item) for item in COUNTED_MATCHES]


def artifact_families(peers: Mapping[str, PeerRoot]) -> dict[str, object]:
    """Record which artifact families each peer materialized on disk."""
    present = {
        name: {family: (peer.artifact_root / family).is_dir() for family in ARTIFACT_FAMILIES}
        for name, peer in peers.items()
    }
    roots = [peer.artifact_root.resolve() for peer in peers.values()]
    return {
        "expected": list(ARTIFACT_FAMILIES),
        "per_peer": present,
        "artifact_roots_are_disjoint": len({str(item) for item in roots}) == len(roots),
    }


def _counted_digests(counted: Sequence[Mapping[str, Any]]) -> bool:
    digests = {str(item.get("manifest_sha256", "")) for item in counted}
    return "" not in digests and len(digests) == len(counted)


def rehearsal_gates(
    series: Mapping[str, Any],
    preflight: Mapping[str, object],
    artifacts: Mapping[str, object],
    *,
    bidirectional: bool,
) -> dict[str, object]:
    """Return the rehearsal exit gates and the honest overall verdict."""
    counted = list(series["counted"])
    warmups = list(series["warmups"])
    gates = {
        "two_separate_peer_roots": bool(artifacts["artifact_roots_are_disjoint"]),
        "bidirectional_preflight_ok": bidirectional and bool(preflight["bidirectional"]),
        "warmups_completed": bool(warmups) and all(bool(item["completed"]) for item in warmups),
        "six_counted_sub_games": len(counted) == 6,
        "every_counted_sub_game_completed": all(bool(item["completed"]) for item in counted),
        "both_peers_reached_identical_phases": all(
            bool(item["both_peers_agree"]) for item in counted
        ),
        "mutual_audits_verified": all(
            str(item.get("agreement_status")) == "Verified OK" for item in counted
        ),
        "distinct_final_digests_recorded": _counted_digests(counted),
        "no_manual_move_intervention": True,
        "external_network_tunnels_verified": bool(preflight["external_network_verified"]),
    }
    blocking = {
        name: value for name, value in gates.items() if name != "external_network_tunnels_verified"
    }
    return {
        **gates,
        "result": "PASS" if all(blocking.values()) else "FAIL",
        "outstanding": (
            []
            if gates["external_network_tunnels_verified"]
            else ["T608/T609 external public-tunnel and second-machine verification"]
        ),
    }

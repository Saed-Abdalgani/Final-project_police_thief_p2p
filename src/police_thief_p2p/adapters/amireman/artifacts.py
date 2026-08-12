"""Local DEMO artifact writers for the amireman friendly runner."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from police_thief_p2p.adapters.amireman.canonical import canonical

MATCH_MODE = "friendly"
LECTURER_REPORT_SENT = False


def _write(path: Path, doc: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(doc).encode("utf-8") + b"\n")
    return path


def emit_artifacts(out_dir: Path, series: Any, terms: dict[str, Any]) -> tuple[list[Path], dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    gid, guid = series.game_id, series.game_uid
    ours = series.own_identity["group_id"]
    theirs = series.peer_identity.get("group_id", "opponent")
    paths = [
        _write(
            out_dir / f"declaration_{gid}.json",
            {
                "game_id": gid,
                "game_uid": guid,
                "match_mode": MATCH_MODE,
                "own_identity": series.own_identity,
                "peer_identity": series.peer_identity,
                "num_games": len(series.summaries),
                "terms": terms,
            },
        )
    ]
    for summary in series.summaries:
        n = summary["sub_game_number"]
        paths.append(_write(out_dir / f"config_{gid}_g{n:02d}.json", {"terms": terms, "sub_game": n}))
        slim = {k: v for k, v in summary.items() if k != "records"}
        paths.append(
            _write(
                out_dir / f"log_{gid}_g{n:02d}.json",
                {"game_id": gid, "game_uid": guid, "ours": ours, "theirs": theirs, "summary": slim},
            )
        )
    result_doc = {
        "game_id": gid,
        "game_uid": guid,
        "match_mode": MATCH_MODE,
        "lecturer_report_sent": LECTURER_REPORT_SENT,
        "consensus_sha": series.consensus_sha,
        "peer_consensus_sha": series.peer_consensus_sha,
        "sha_match": series.sha_match,
        "results_agreed": series.results_agreed,
        "summaries": [{k: v for k, v in item.items() if k != "records"} for item in series.summaries],
        "ended_at": datetime.now(UTC).isoformat(),
    }
    paths.append(_write(out_dir / f"result_{gid}.json", result_doc))
    return paths, result_doc

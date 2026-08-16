"""Series runner for amireman-wire; CLI handles optional post-series mail."""

from __future__ import annotations

import json
import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from police_thief_p2p.adapters.amireman.artifacts import (
    LECTURER_REPORT_SENT,
    MATCH_MODE,
    emit_artifacts,
    emit_training_sidecar,
)
from police_thief_p2p.adapters.amireman.client import McpTransport, mcp_url
from police_thief_p2p.adapters.amireman.scent import MULTIPLICATIVE_KERNEL_V1
from police_thief_p2p.adapters.amireman.series import identity_for, run_series
from police_thief_p2p.adapters.amireman.server import start_peer_server
from police_thief_p2p.sdk import SimulationSdk


@dataclass
class FriendlyResult:
    """Local result and artifact paths for one completed friendly series."""

    game_id: str | None = None
    game_uid: str | None = None
    summaries: list = field(default_factory=list)
    artifacts: list = field(default_factory=list)
    result_doc: dict = field(default_factory=dict)
    clean: bool = False
    match_mode: str = MATCH_MODE
    lecturer_report_sent: bool = LECTURER_REPORT_SENT
    sha_match: bool = False
    results_agreed: bool = False
    training_sidecar: Path | None = None


def run_friendly(
    group: str,
    opponent_url: str,
    natural_role: str,
    terms: dict[str, Any],
    out_dir: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 8901,
    github_commit: str = "local",
    num_games: int = 6,
    seed: int | None = None,
    turn_timeout: float = 180.0,
    members: list[str] | None = None,
    public_mcp_url: str | None = None,
    listener: Callable[[dict], None] | None = None,
    game_id: str | None = None,
    scent_model: str = MULTIPLICATIVE_KERNEL_V1,
    strategy: Any = None,
) -> FriendlyResult:
    """Stand up server, play the series, write local artifacts (no mail here)."""
    if not members:
        raise ValueError("members list must be non-empty for amireman identity")
    resolved_seed = secrets.randbits(128) if seed is None else int(seed)
    strategy_session = SimulationSdk().create_compatibility_strategy(
        terms,
        strategy,
        "",
        resolved_seed,
        scent_model=scent_model,
    )
    advertised = mcp_url(public_mcp_url or f"http://{host}:{port}/mcp")
    identity = identity_for(
        group,
        members=members,
        github_commit=github_commit,
        public_mcp_url=advertised,
        scent_model=scent_model,
    )
    server = start_peer_server(f"interop-{group}", host, port)
    print(f"mcp: listening on http://{host}:{port}/mcp (tunnel GET should be 406)", flush=True)
    print(
        "mcp: keep this process up; 502 from the opponent means they are not listening yet",
        flush=True,
    )
    transport = McpTransport(opponent_url, server.inboxes)
    try:
        series = run_series(
            terms,
            natural_role,
            transport,
            group,
            github_commit,
            identity,
            num_games=num_games,
            seed=resolved_seed,
            listener=listener,
            turn_timeout=turn_timeout,
            game_id=game_id,
            scent_model=scent_model,
            strategy_session=strategy_session,
        )
    finally:
        transport.close()
        time.sleep(2.0)
        server.stop(max_linger=12.0, grace=8.0)
    paths, result_doc = emit_artifacts(Path(out_dir), series, terms)
    training_sidecar = emit_training_sidecar(
        Path(out_dir),
        series,
        strategy_session.training_snapshot(),
    )
    clean = len(series.summaries) == num_games and all(
        not s["audit"].get("tampered") and s["result"] != "timeout" for s in series.summaries
    )
    return FriendlyResult(
        game_id=series.game_id,
        game_uid=series.game_uid,
        summaries=series.summaries,
        artifacts=paths,
        result_doc=result_doc,
        clean=clean,
        sha_match=series.sha_match,
        results_agreed=series.results_agreed,
        training_sidecar=training_sidecar,
    )


def dump_result(result: FriendlyResult) -> str:
    """Serialize safe command-line output without private training records."""
    return json.dumps(
        {
            "game_id": result.game_id,
            "game_uid": result.game_uid,
            "match_mode": result.match_mode,
            "lecturer_report_sent": result.lecturer_report_sent,
            "clean": result.clean,
            "sha_match": result.sha_match,
            "results_agreed": result.results_agreed,
            "artifacts": [str(path) for path in result.artifacts],
            "training_sidecar": str(result.training_sidecar) if result.training_sidecar else None,
        },
        indent=2,
    )

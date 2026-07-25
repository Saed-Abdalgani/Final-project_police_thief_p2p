import ast
from pathlib import Path

from police_thief_p2p.services.orchestration.watchdog import RecoverySnapshot

ROOT = Path(__file__).parents[2]
ORCHESTRATOR = ROOT / "src/police_thief_p2p/services/orchestration/orchestrator.py"


def test_orchestrator_contains_no_physics_scoring_hash_or_transport_parsing() -> None:
    source = ORCHESTRATOR.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert all(
        forbidden not in imported
        for imported in imports
        for forbidden in (
            ".domain",
            ".strategy.police",
            ".strategy.thief",
            ".crypto",
            ".protocol.envelope",
            ".adapters",
        )
    )
    assert all(
        token not in source
        for token in ("sha256", "json.loads", "shortest_path", "score =", "socket")
    )


def test_watchdog_recovery_snapshot_has_no_secret_capability() -> None:
    snapshot = RecoverySnapshot(
        "progress-stalled",
        "waiting-ack",
        4,
        9,
        "2026-07-25T20:00:00Z",
    )
    document = snapshot.document()
    assert set(document) == {
        "reason",
        "phase",
        "step_number",
        "progress_token",
        "observed_at",
    }
    text = repr(document).casefold()
    assert all(item not in text for item in ("nonce", "api_key", "password", "token.json"))

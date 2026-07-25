import ast
from pathlib import Path

import pytest

from police_thief_p2p.shared.config_loader import load_shared_bytes

ROOT = Path(__file__).parents[2]
STRATEGY_ROOT = ROOT / "src/police_thief_p2p/services/strategy"


def test_strategy_live_types_contain_no_opponent_truth_or_replay_fields() -> None:
    forbidden = {
        "opponent_true_position",
        "opponent_position",
        "objective_state",
        "replay_truth",
        "nonce",
        "secret",
    }
    for path in STRATEGY_ROOT.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        identifiers = {node.id.casefold() for node in ast.walk(tree) if isinstance(node, ast.Name)}
        arguments = {
            argument.arg.casefold()
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            for argument in (*node.args.args, *node.args.kwonlyargs)
        }
        assert forbidden.isdisjoint(identifiers | arguments), path


def test_strategy_has_no_network_gui_filesystem_or_unbounded_wait_imports() -> None:
    forbidden = ("adapters", "socket", "subprocess", "pathlib", "time.sleep", ".gui")
    for path in STRATEGY_ROOT.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert all(item not in source for item in forbidden), path


def test_shared_config_cannot_select_strategy_class(shared_config_bytes: bytes) -> None:
    altered = shared_config_bytes.replace(
        b'"extensions": {}',
        b'"strategy": {"police_class": "os.system"}, "extensions": {}',
    )
    with pytest.raises(ValueError, match=r"CFG_|schema"):
        load_shared_bytes(altered)

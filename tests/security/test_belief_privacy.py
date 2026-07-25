import ast
import inspect
from pathlib import Path

from police_thief_p2p.sdk import SimulationSdk
from police_thief_p2p.services.belief.models import OpponentScentFrame
from police_thief_p2p.services.belief.service import BeliefService
from police_thief_p2p.services.belief.view import LocalView

ROOT = Path(__file__).parents[2]
LIVE_ROOT = ROOT / "src/police_thief_p2p/services/belief"


def test_live_belief_api_never_accepts_opponent_truth() -> None:
    forbidden = {"opponent_position", "opponent_true_position", "true_position"}
    for path in LIVE_ROOT.glob("*.py"):
        if path.name == "offline.py":
            continue
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        assert forbidden.isdisjoint(source.casefold().split()), path
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                arguments = {argument.arg for argument in node.args.args}
                arguments |= {argument.arg for argument in node.args.kwonlyargs}
                assert arguments.isdisjoint(forbidden), f"{path}:{node.lineno}"
    assert forbidden.isdisjoint(OpponentScentFrame.model_fields)
    assert forbidden.isdisjoint(LocalView.__dataclass_fields__)


def test_sdk_has_reveal_workflow_but_no_manual_belief_injection() -> None:
    methods = set(dir(SimulationSdk))
    assert "update_belief_from_reveal" in methods
    assert not {"set_belief", "inject_scent", "set_opponent_position"}.intersection(methods)
    signature = inspect.signature(SimulationSdk.update_belief_from_reveal)
    assert "reveal" in signature.parameters
    assert "frame" in signature.parameters
    assert "evidence" not in signature.parameters


def test_belief_service_imports_no_network_gui_or_adapter() -> None:
    module = inspect.getmodule(BeliefService)
    assert module is not None
    tree = ast.parse(inspect.getsource(module))
    imports = {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert all(
        forbidden not in imported
        for imported in imports
        for forbidden in ("adapters", "network", ".gui")
    )

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.security

ROOT = Path(__file__).parents[2]
MCP_ADAPTER = ROOT / "src/police_thief_p2p/adapters/mcp"


def _calls(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }


def test_inbound_server_has_no_domain_or_service_imports() -> None:
    tree = ast.parse((MCP_ADAPTER / "server.py").read_text(encoding="utf-8"))
    modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    assert not any(
        module.startswith(("police_thief_p2p.domain", "police_thief_p2p.services"))
        for module in modules
    )
    assert "receive_protocol_request" in _calls(MCP_ADAPTER / "server.py")


def test_outbound_adapter_cannot_call_fastmcp_outside_gatekeeper_backend() -> None:
    assert "call_tool" not in _calls(MCP_ADAPTER / "client.py")
    assert "execute" in _calls(MCP_ADAPTER / "client.py")
    assert "call_tool" in _calls(MCP_ADAPTER / "backend.py")

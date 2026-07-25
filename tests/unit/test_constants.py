import ast
from pathlib import Path

from police_thief_p2p.constants import (
    COMMITMENT_DIGEST_NAME,
    PACKAGE_NAME,
    REDACTED,
    TEXT_ENCODING,
)


def test_true_constants_have_expected_protocol_values() -> None:
    assert PACKAGE_NAME == "police-thief-p2p"
    assert TEXT_ENCODING == "utf-8"
    assert COMMITMENT_DIGEST_NAME == "sha256"
    assert REDACTED == "[REDACTED]"


def test_constants_module_contains_no_runtime_tunable_names() -> None:
    root = Path(__file__).parents[2]
    path = root / "src/police_thief_p2p/constants.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = {
        target.id
        for node in tree.body
        if isinstance(node, ast.AnnAssign) and isinstance((target := node.target), ast.Name)
    }
    forbidden_parts = {"TIMEOUT", "RATE", "URL", "PATH", "MODEL", "FEATURE"}
    assert not any(part in name for name in names for part in forbidden_parts)

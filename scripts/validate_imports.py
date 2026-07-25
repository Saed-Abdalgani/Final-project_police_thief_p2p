"""Enforce that protected application adapters import only the public SDK."""

import ast
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

_FORBIDDEN_PREFIXES = (
    "police_thief_p2p.domain",
    "police_thief_p2p.services",
)
_PROTECTED_ADAPTERS = ("cli", "email", "gui", "mcp")


@dataclass(frozen=True, slots=True)
class ForbiddenImport:
    """One protected adapter importing a forbidden internal module."""

    path: Path
    line: int
    module: str


def _modules(node: ast.Import | ast.ImportFrom) -> Iterable[str]:
    """Yield imported absolute module names from one AST node."""
    if isinstance(node, ast.Import):
        yield from (alias.name for alias in node.names)
    elif node.level == 0 and node.module is not None:
        yield node.module


def find_forbidden_imports(adapter_root: Path) -> list[ForbiddenImport]:
    """Return forbidden service/domain imports from protected adapters."""
    findings: list[ForbiddenImport] = []
    for adapter in _PROTECTED_ADAPTERS:
        for path in (adapter_root / adapter).rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    findings.extend(
                        ForbiddenImport(path, node.lineno, module)
                        for module in _modules(node)
                        if module.startswith(_FORBIDDEN_PREFIXES)
                    )
    return findings


def main(argv: Sequence[str] | None = None) -> int:
    """Validate adapter imports and return a shell-friendly status."""
    root = Path(argv[0]).resolve() if argv else Path("src/police_thief_p2p/adapters").resolve()
    findings = find_forbidden_imports(root)
    for finding in findings:
        print(f"{finding.path}:{finding.line}: forbidden import {finding.module}")
    if findings:
        return 1
    print("Import boundaries OK: protected adapters use no domain/service imports.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

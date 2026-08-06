"""Verify one exported role repository before tagging and lecturer handoff."""

import argparse
import json
import re
import subprocess
from collections.abc import Sequence
from pathlib import Path

SECRET_PATTERN = re.compile(r"(api[_-]?key|client_secret|refresh_token)\s*[:=]\s*['\"][^'\"]+['\"]", re.I)
FORBIDDEN_LINKAGE = ("editable = true", 'path = "', "path = '")


def _run(command: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True, timeout=600)


def verify_export(root: Path) -> list[str]:
    """Return verification errors for one exported role tree."""
    errors: list[str] = []
    export = root / "release/ROLE_EXPORT.json"
    readme = root / "README.md"
    if not export.exists():
        errors.append("missing release/ROLE_EXPORT.json")
        return errors
    record = json.loads(export.read_text(encoding="utf-8"))
    sibling = str(record["sibling_repository"])
    text = readme.read_text(encoding="utf-8")
    if sibling not in text:
        errors.append("README does not link the sibling repository")
    if "v1.0-submission" not in text:
        errors.append("README does not name the submission tag")
    private = (root / "config/private/game.example.toml").read_text(encoding="utf-8")
    role = str(record["role"])
    if f'role = "{role}"' not in private:
        errors.append(f"private example is not defaulted to {role}")
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix in {".svg", ".png", ".jpg", ".lock"}:
            continue
        if path.stat().st_size > 2_000_000:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if SECRET_PATTERN.search(content) and "example" not in path.name:
            errors.append(f"possible secret material in {path.relative_to(root)}")
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    if any(token in pyproject for token in FORBIDDEN_LINKAGE):
        errors.append("pyproject appears to link the canonical workspace at runtime")
    structure = _run(["uv", "run", "python", "scripts/validate_structure.py"], root)
    if structure.returncode != 0:
        errors.append(f"structure validation failed: {structure.stdout.strip()}")
    return errors


def main(argv: Sequence[str] | None = None) -> int:
    """Verify one or more export roots."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", nargs="+", type=Path)
    args = parser.parse_args(argv)
    failed = 0
    for root in args.roots:
        errors = verify_export(root.resolve())
        payload = {"root": str(root), "passed": not errors, "errors": errors}
        print(json.dumps(payload, sort_keys=True))
        failed += int(bool(errors))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

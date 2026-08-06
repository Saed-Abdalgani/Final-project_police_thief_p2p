"""Copy helpers and role specialization for deterministic role exports."""

import json
import shutil
from collections.abc import Iterable, Sequence
from fnmatch import fnmatch
from pathlib import Path

ROOT = Path(__file__).parents[1]
MANIFEST_ROOT = ROOT / "release/export_manifests"
EXPORT_ROOT = ROOT / "release/exports"


def load_manifest(role: str) -> dict[str, object]:
    """Load one role manifest merged with the shared include/exclude lists."""
    role_doc = json.loads((MANIFEST_ROOT / f"{role}.json").read_text(encoding="utf-8"))
    common = json.loads((MANIFEST_ROOT / str(role_doc["inherits"])).read_text(encoding="utf-8"))
    return {**common, **role_doc, "include": common["include"], "exclude": common["exclude"]}


def _excluded(relative: str, patterns: Sequence[str]) -> bool:
    posix = relative.replace("\\", "/")
    return any(fnmatch(posix, pattern.rstrip("/")) or fnmatch(posix, pattern) for pattern in patterns)


def selected_files(manifest: dict[str, object]) -> list[Path]:
    """Return repository-relative paths selected by the export manifest."""
    include = [str(item) for item in manifest["include"]]  # type: ignore[index]
    exclude = [str(item) for item in manifest["exclude"]]  # type: ignore[index]
    chosen: list[Path] = []
    for pattern in include:
        source = ROOT / pattern
        if source.is_file():
            relative = source.relative_to(ROOT)
            if not _excluded(relative.as_posix(), exclude):
                chosen.append(relative)
            continue
        if not source.is_dir():
            raise FileNotFoundError(f"export include path missing: {pattern}")
        for path in source.rglob("*"):
            if path.is_file() and not _excluded(path.relative_to(ROOT).as_posix(), exclude):
                chosen.append(path.relative_to(ROOT))
    return sorted(set(chosen), key=lambda item: item.as_posix())


def copy_selection(files: Iterable[Path], destination: Path) -> int:
    """Copy selected files into the export destination and return the count."""
    count = 0
    for relative in files:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
        count += 1
    return count


def specialize_private_config(destination: Path, *, group_id: str, role: str) -> None:
    """Rewrite the example private config to the exported default role and group."""
    path = destination / "config/private/game.example.toml"
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("group_id"):
            lines.append(f'group_id = "{group_id}"')
        elif line.startswith("role "):
            lines.append(f'role = "{role}"')
        else:
            lines.append(line)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def specialize_pyproject(destination: Path, *, repository: str) -> None:
    """Point package URLs at the exported repository without renaming the installable module."""
    path = destination / "pyproject.toml"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "https://github.com/Saed-Abdalgani/Final-project_police_thief_p2p/tree/main/docs",
        f"{repository}/tree/main/docs",
    )
    text = text.replace(
        "https://github.com/Saed-Abdalgani/Final-project_police_thief_p2p",
        repository,
    )
    path.write_text(text, encoding="utf-8", newline="\n")


def write_role_readme(
    destination: Path,
    *,
    role: str,
    repository: str,
    sibling: str,
    commit_sha: str,
) -> None:
    """Write the role-branded README that cross-links the sibling export."""
    title = "Police" if role == "police" else "Thief"
    opposite = "Thief" if role == "police" else "Police"
    body = f"""# {title} Peer — Police-Thief P2P

Standalone `{title}` export of the canonical Police-Thief P2P workspace.

- This repository: [{repository}]({repository})
- Sibling {opposite} repository: [{sibling}]({sibling})
- Annotated submission tag: `v1.0-submission`
- Frozen from canonical commit `{commit_sha}`

```text
uv python install 3.13
uv sync --frozen --all-groups
uv run police-thief-p2p readiness
```

Full operator guide: `README.canonical.md`. Academic model, protocol, strategy,
experiments, and operations live under `docs/`.

Result JSON examples: `results/benchmarks/m12_tuning.json`,
`results/benchmarks/m12_selection.json`, `results/benchmarks/m12_language.json`,
`results/benchmarks/m12_league_rehearsal.json`.
"""
    (destination / "README.md").write_text(body, encoding="utf-8", newline="\n")

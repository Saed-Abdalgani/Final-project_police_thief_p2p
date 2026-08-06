"""Deterministically export one standalone Police or Thief repository snapshot."""

import argparse
import json
import shutil
import subprocess
from collections.abc import Sequence
from pathlib import Path

from scripts.export_role_support import (
    EXPORT_ROOT,
    ROOT,
    copy_selection,
    load_manifest,
    selected_files,
    specialize_private_config,
    specialize_pyproject,
    write_role_readme,
)


def commit_sha() -> str:
    """Return the frozen HEAD digest used as the export provenance."""
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],  # noqa: S607
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    return completed.stdout.strip()


def export_role(role: str, destination: Path | None = None) -> Path:
    """Materialize one role export directory from the current frozen tree."""
    if role not in {"police", "thief"}:
        raise ValueError("role must be 'police' or 'thief'")
    manifest = load_manifest(role)
    target = destination or (EXPORT_ROOT / f"GRP00001-{role}-p2p")
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    files = selected_files(manifest)
    copied = copy_selection(files, target)
    sha = commit_sha()
    canonical_readme = target / "README.md"
    if canonical_readme.exists():
        canonical_readme.replace(target / "README.canonical.md")
    write_role_readme(
        target,
        role=role,
        repository=str(manifest["repository"]),
        sibling=str(manifest["sibling_repository"]),
        commit_sha=sha,
    )
    specialize_private_config(
        target,
        group_id=str(manifest["default_group_id"]),
        role=str(manifest["default_role"]),
    )
    specialize_pyproject(target, repository=str(manifest["repository"]))
    record = {
        "role": role,
        "canonical_commit": sha,
        "files_copied": copied,
        "repository": manifest["repository"],
        "sibling_repository": manifest["sibling_repository"],
        "package_name": manifest["package_name"],
    }
    (target / "release" / "ROLE_EXPORT.json").parent.mkdir(parents=True, exist_ok=True)
    (target / "release" / "ROLE_EXPORT.json").write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(record, sort_keys=True))
    return target


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("role", choices=("police", "thief", "both"))
    parser.add_argument("--destination", type=Path, default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Export one or both role repositories and return a shell status."""
    args = build_parser().parse_args(argv)
    if args.role == "both":
        export_role("police")
        export_role("thief")
        return 0
    export_role(args.role, args.destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

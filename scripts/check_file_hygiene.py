"""Check tracked text files for portable, reviewable formatting."""

import argparse
import shutil
import subprocess
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

_TEXT_SUFFIXES = {
    "",
    ".cfg",
    ".ini",
    ".json",
    ".lock",
    ".md",
    ".py",
    ".sha256",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}


@dataclass(frozen=True, slots=True)
class HygieneIssue:
    """One portable-text hygiene violation."""

    path: Path
    detail: str


def tracked_files(root: Path) -> list[Path]:
    """Return tracked files using NUL-safe Git output."""
    git = shutil.which("git")
    if git is None:
        msg = "Git executable was not found on PATH"
        raise RuntimeError(msg)
    completed = subprocess.run(  # noqa: S603 - executable is resolved; arguments are fixed.
        [git, "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return [root / item.decode("utf-8") for item in completed.stdout.split(b"\0") if item]


def check_files(paths: Iterable[Path]) -> list[HygieneIssue]:
    """Return encoding, line-ending, tab, whitespace, and EOF issues."""
    issues: list[HygieneIssue] = []
    for path in paths:
        if not path.is_file() or path.suffix.casefold() not in _TEXT_SUFFIXES:
            continue
        raw = path.read_bytes()
        if b"\0" in raw:
            continue
        if raw.startswith(b"\xef\xbb\xbf"):
            issues.append(HygieneIssue(path, "UTF-8 BOM is not allowed"))
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            issues.append(HygieneIssue(path, "not valid UTF-8"))
            continue
        if "\r" in text:
            issues.append(HygieneIssue(path, "CR/CRLF line ending found"))
        if text and not text.endswith("\n"):
            issues.append(HygieneIssue(path, "missing final newline"))
        for number, line in enumerate(text.splitlines(), start=1):
            if "\t" in line:
                issues.append(HygieneIssue(path, f"line {number}: tab character"))
            if line.rstrip(" ") != line:
                issues.append(HygieneIssue(path, f"line {number}: trailing spaces"))
    return issues


def main(argv: Sequence[str] | None = None) -> int:
    """Check selected or tracked files and return a shell-friendly status."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args(argv)
    root = Path.cwd().resolve()
    paths = args.paths or tracked_files(root)
    issues = check_files(paths)
    for issue in issues:
        print(f"{issue.path}: {issue.detail}")
    if issues:
        return 1
    print(f"File hygiene OK: {len(paths)} candidate files checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Fail when Python source exceeds the practical code-line policy."""

import argparse
import io
import tokenize
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

DEFAULT_LIMIT = 150
_IGNORED_TOKEN_TYPES = {
    tokenize.COMMENT,
    tokenize.DEDENT,
    tokenize.ENCODING,
    tokenize.ENDMARKER,
    tokenize.INDENT,
    tokenize.NEWLINE,
    tokenize.NL,
}


@dataclass(frozen=True, slots=True)
class FileSizeFinding:
    """One source file that exceeds the selected limit."""

    path: Path
    code_lines: int
    limit: int


def count_code_lines(path: Path) -> int:
    """Count lines containing non-comment Python tokens."""
    source = path.read_text(encoding="utf-8")
    lines: set[int] = set()
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type not in _IGNORED_TOKEN_TYPES:
            lines.update(range(token.start[0], token.end[0] + 1))
    return len(lines)


def iter_python_files(paths: Iterable[Path]) -> Iterable[Path]:
    """Yield unique Python files under files or directories."""
    seen: set[Path] = set()
    for path in paths:
        candidates = path.rglob("*.py") if path.is_dir() else (path,)
        for candidate in candidates:
            resolved = candidate.resolve()
            if candidate.suffix == ".py" and resolved not in seen:
                seen.add(resolved)
                yield candidate


def find_oversized_files(
    paths: Iterable[Path],
    *,
    limit: int = DEFAULT_LIMIT,
) -> list[FileSizeFinding]:
    """Return findings for Python files over ``limit`` code lines."""
    return [
        FileSizeFinding(path=path, code_lines=count, limit=limit)
        for path in iter_python_files(paths)
        if (count := count_code_lines(path)) > limit
    ]


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, default=[Path("src")])
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Check source sizes and return a shell-friendly status."""
    args = build_parser().parse_args(argv)
    findings = find_oversized_files(args.paths, limit=args.limit)
    for finding in findings:
        print(f"{finding.path}: {finding.code_lines} code lines (limit {finding.limit})")
    if findings:
        return 1
    print(f"Source sizes OK: no file exceeds {args.limit} code lines.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

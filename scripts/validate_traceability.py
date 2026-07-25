"""Validate stable requirement/task IDs and traceability coverage."""

import argparse
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from pathlib import Path

_REQUIREMENT_DECLARATION = re.compile(
    r"^- \*\*((?:FR|NFR)-[A-Z]+-(\d{3}))\*\*:",
    re.MULTILINE,
)
_TASK_DECLARATION = re.compile(r"\*\*T(\d{3}) ")
_TRACE_RANGE = re.compile(
    r"^\| `((?:FR|NFR)-[A-Z]+)-(\d{3})(?:\.\.(\d{3}))?` \|",
    re.MULTILINE,
)
_TEST_REFERENCE = re.compile(r"REQ:\s*((?:FR|NFR)-[A-Z]+-\d{3})")


def extract_requirement_ids(text: str) -> list[str]:
    """Extract requirement declarations in document order."""
    return [match.group(1) for match in _REQUIREMENT_DECLARATION.finditer(text)]


def extract_task_ids(text: str) -> list[int]:
    """Extract numeric TODO task declarations in document order."""
    return [int(match.group(1)) for match in _TASK_DECLARATION.finditer(text)]


def expand_traceability_ranges(text: str) -> list[str]:
    """Expand inclusive requirement ranges from the traceability table."""
    expanded: list[str] = []
    for match in _TRACE_RANGE.finditer(text):
        prefix = match.group(1)
        start = int(match.group(2))
        end = int(match.group(3) or match.group(2))
        expanded.extend(f"{prefix}-{number:03d}" for number in range(start, end + 1))
    return expanded


def duplicate_values(values: Iterable[str | int]) -> list[str]:
    """Return stable string forms of duplicate values."""
    return sorted(str(value) for value, count in Counter(values).items() if count > 1)


def missing_task_ids(task_ids: Sequence[int]) -> list[int]:
    """Return gaps between the minimum and maximum task IDs."""
    if not task_ids:
        return []
    expected = set(range(min(task_ids), max(task_ids) + 1))
    return sorted(expected.difference(task_ids))


def missing_requirement_ids(requirement_ids: Sequence[str]) -> list[str]:
    """Return numeric gaps within each requirement prefix."""
    grouped: dict[str, set[int]] = defaultdict(set)
    for requirement_id in requirement_ids:
        prefix, number = requirement_id.rsplit("-", maxsplit=1)
        grouped[prefix].add(int(number))
    missing: list[str] = []
    for prefix, numbers in grouped.items():
        expected = set(range(1, max(numbers) + 1))
        missing.extend(f"{prefix}-{number:03d}" for number in sorted(expected - numbers))
    return sorted(missing)


def unknown_test_references(test_root: Path, valid_ids: set[str]) -> list[str]:
    """Return unknown requirement references found in Python tests."""
    unknown: list[str] = []
    for path in test_root.rglob("*.py"):
        unknown.extend(
            f"{path}:{requirement_id}"
            for requirement_id in _TEST_REFERENCE.findall(path.read_text(encoding="utf-8"))
            if requirement_id not in valid_ids
        )
    return sorted(unknown)


def validate_repository(root: Path) -> list[str]:
    """Return traceability validation errors for a repository."""
    requirements = extract_requirement_ids((root / "docs/PRD.md").read_text(encoding="utf-8"))
    tasks = extract_task_ids((root / "docs/TODO.md").read_text(encoding="utf-8"))
    mapped = expand_traceability_ranges((root / "docs/TRACEABILITY.md").read_text(encoding="utf-8"))
    errors: list[str] = []
    for label, duplicates in (
        ("requirement", duplicate_values(requirements)),
        ("task", duplicate_values(tasks)),
        ("mapped requirement", duplicate_values(mapped)),
    ):
        if duplicates:
            errors.append(f"duplicate {label} IDs: {', '.join(duplicates)}")
    if requirement_gaps := missing_requirement_ids(requirements):
        errors.append(f"missing requirement IDs: {', '.join(requirement_gaps)}")
    if task_gaps := missing_task_ids(tasks):
        errors.append("missing task IDs: " + ", ".join(f"T{value:03d}" for value in task_gaps))
    if missing := sorted(set(requirements) - set(mapped)):
        errors.append(f"unmapped requirements: {', '.join(missing)}")
    if extra := sorted(set(mapped) - set(requirements)):
        errors.append(f"unknown mapped requirements: {', '.join(extra)}")
    if unknown := unknown_test_references(root / "tests", set(requirements)):
        errors.append(f"unknown test references: {', '.join(unknown)}")
    return errors


def main(argv: Sequence[str] | None = None) -> int:
    """Validate repository IDs and return a shell-friendly status."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    errors = validate_repository(args.root.resolve())
    for error in errors:
        print(error)
    if errors:
        return 1
    print("Traceability OK: requirement/task IDs and mappings are complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

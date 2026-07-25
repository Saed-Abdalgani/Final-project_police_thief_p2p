from pathlib import Path

from scripts.check_file_hygiene import check_files
from scripts.check_file_sizes import find_oversized_files
from scripts.validate_structure import validate_structure
from scripts.validate_traceability import (
    duplicate_values,
    extract_requirement_ids,
    extract_task_ids,
    missing_requirement_ids,
    missing_task_ids,
)


def test_structure_validator_detects_missing_path(tmp_path: Path) -> None:
    assert validate_structure(tmp_path, ["required.txt"]) == ["required.txt"]
    (tmp_path / "required.txt").touch()
    assert validate_structure(tmp_path, ["required.txt"]) == []


def test_source_size_validator_detects_151_code_lines(tmp_path: Path) -> None:
    path = tmp_path / "oversized.py"
    path.write_text("".join(f"value_{number} = {number}\n" for number in range(151)))
    findings = find_oversized_files([path], limit=150)
    assert len(findings) == 1
    assert findings[0].code_lines == 151


def test_id_helpers_detect_duplicates_and_numeric_gaps() -> None:
    requirements = extract_requirement_ids(
        "- **FR-ABC-001**: first\n- **FR-ABC-001**: duplicate\n- **FR-ABC-003**: gap\n"
    )
    tasks = extract_task_ids("**T001 [P0]** first\n**T003 [P0]** gap\n")
    assert duplicate_values(requirements) == ["FR-ABC-001"]
    assert missing_requirement_ids(requirements) == ["FR-ABC-002"]
    assert missing_task_ids(tasks) == [2]


def test_file_hygiene_detects_tabs_trailing_spaces_and_eof(tmp_path: Path) -> None:
    path = tmp_path / "bad.py"
    path.write_bytes(b"value = 1  \n\tvalue = 2")
    details = [issue.detail for issue in check_files([path])]
    assert "missing final newline" in details
    assert "line 1: trailing spaces" in details
    assert "line 2: tab character" in details

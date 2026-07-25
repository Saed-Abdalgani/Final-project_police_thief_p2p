from pathlib import Path

import pytest

from scripts import (
    check_file_hygiene,
    check_file_sizes,
    validate_ci,
    validate_imports,
    validate_structure,
    validate_traceability,
)

pytestmark = pytest.mark.integration


def test_repository_quality_entrypoints_pass() -> None:
    root = Path(__file__).parents[2]

    assert validate_structure.main(["--root", str(root)]) == 0
    assert validate_traceability.main(["--root", str(root)]) == 0
    assert validate_imports.main([str(root / "src/police_thief_p2p/adapters")]) == 0
    assert check_file_sizes.main([str(root / "src"), str(root / "scripts")]) == 0
    assert check_file_hygiene.main([str(root / "README.md")]) == 0
    assert validate_ci.main() == 0


def test_validator_entrypoints_report_failures(tmp_path: Path) -> None:
    oversized = tmp_path / "large.py"
    oversized.write_text("".join(f"value_{number} = {number}\n" for number in range(151)))

    assert validate_structure.main(["--root", str(tmp_path)]) == 1
    assert check_file_sizes.main([str(oversized)]) == 1

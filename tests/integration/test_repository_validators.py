from pathlib import Path

import pytest

from scripts.check_file_sizes import find_oversized_files
from scripts.validate_imports import find_forbidden_imports
from scripts.validate_structure import validate_structure
from scripts.validate_traceability import validate_repository

pytestmark = pytest.mark.integration


def test_repository_contracts_pass_on_current_tree() -> None:
    root = Path(__file__).parents[2]
    assert validate_structure(root) == []
    assert validate_repository(root) == []
    assert find_forbidden_imports(root / "src/police_thief_p2p/adapters") == []
    assert find_oversized_files([root / "src", root / "scripts"]) == []

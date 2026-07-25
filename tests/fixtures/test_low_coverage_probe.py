"""Explicit negative coverage probe; excluded from normal discovery."""

from police_thief_p2p.constants import PACKAGE_NAME


def test_only_one_constant_for_negative_coverage_gate() -> None:
    assert PACKAGE_NAME == "police-thief-p2p"

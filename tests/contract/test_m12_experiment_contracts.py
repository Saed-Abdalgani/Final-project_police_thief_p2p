import inspect
from pathlib import Path

import pytest

from police_thief_p2p.sdk import SimulationSdk
from police_thief_p2p.services.experiments import __all__ as experiment_exports
from police_thief_p2p.services.experiments.fixtures import fixtures_for
from police_thief_p2p.services.experiments.spec import SPEC_VERSION, SPLITS
from police_thief_p2p.services.experiments.splits import SPLIT_VERSION
from police_thief_p2p.services.experiments.studies import ABLATIONS, ROBUSTNESS_CASES
from police_thief_p2p.shared.config_models import SharedConfig
from police_thief_p2p.shared.strategy_config import StrategyConfig
from tests.helpers.strategy import strategy_config

pytestmark = pytest.mark.contract

ROOT = Path(__file__).parents[2]
EXPERIMENT_PACKAGE = ROOT / "src/police_thief_p2p/services/experiments"


def test_sdk_exposes_the_offline_tournament_entry_point() -> None:
    sdk = SimulationSdk()
    assert callable(sdk.run_tournament)
    signature = inspect.signature(sdk.run_tournament)
    assert list(signature.parameters)[:3] == ["spec", "shared", "strategy"]
    assert set(sdk.search_space_document()) == {"police", "thief", "belief", "hint"}
    document = sdk.split_manifest_document("train")
    assert document["split"] == "train"
    assert len(str(document["split_sha256"])) == 64


def test_experiment_package_never_imports_adapters_or_the_sdk() -> None:
    for path in sorted(EXPERIMENT_PACKAGE.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        assert "police_thief_p2p.adapters" not in source, path.name
        assert "police_thief_p2p.sdk" not in source, path.name


def test_every_declared_export_resolves() -> None:
    import police_thief_p2p.services.experiments as package

    for name in experiment_exports:
        assert hasattr(package, name), name


def test_versioned_declarations_are_semantic_and_split_names_agree() -> None:
    assert SPEC_VERSION.count(".") == 2
    assert SPLIT_VERSION.count(".") == 2
    assert set(SPLITS) == {"train", "validation", "holdout", "rehearsal"}
    for split in SPLITS:
        assert fixtures_for(split)


def test_ablation_and_robustness_catalogues_are_documented_and_unique() -> None:
    assert ABLATIONS[0].study_id == "ABL-FULL"
    assert not ABLATIONS[0].point
    identifiers = [item.study_id for item in ABLATIONS]
    assert len(identifiers) == len(set(identifiers))
    for study in ABLATIONS:
        assert study.description.endswith(".")
        assert study.component
    cases = [item.case_id for item in ROBUSTNESS_CASES]
    assert len(cases) == len(set(cases))
    for case in ROBUSTNESS_CASES:
        assert case.as_document()["case_id"] == case.case_id
        assert 20 <= case.decision_budget_ms <= 5_000


def test_ablation_points_only_name_real_strategy_fields() -> None:
    base: StrategyConfig = strategy_config()
    from police_thief_p2p.services.experiments.profiles import derive_profile

    for study in ABLATIONS:
        derived = derive_profile(base, dict(study.point))
        assert isinstance(derived, StrategyConfig)


def test_shared_configuration_fixture_supports_every_declared_fixture(
    shared_config: SharedConfig,
) -> None:
    for split in SPLITS:
        for fixture in fixtures_for(split):
            applied = fixture.apply(shared_config)
            assert applied.board_and_agents.grid_size == fixture.grid_size
            assert applied.movement_and_barriers.max_moves == fixture.max_moves

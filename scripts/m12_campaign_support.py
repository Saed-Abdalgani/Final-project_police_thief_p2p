"""Shared loading, spec building, and evidence writing for M12 campaigns."""

import json
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from police_thief_p2p.adapters.system.clocks import SystemClock
from police_thief_p2p.adapters.system.deterministic_random import DeterministicRandomSource
from police_thief_p2p.services.experiments.belief_track import DEFAULT_BELIEF_PROFILE, BeliefProfile
from police_thief_p2p.services.experiments.fixtures import fixtures_for
from police_thief_p2p.services.experiments.report import TournamentReport
from police_thief_p2p.services.experiments.roster import CANDIDATE_ID
from police_thief_p2p.services.experiments.runner import ExperimentRunner
from police_thief_p2p.services.experiments.spec import BoardFixture, TournamentSpec
from police_thief_p2p.services.experiments.splits import split_manifest
from police_thief_p2p.shared.config_loader import load_private_path, load_shared_path
from police_thief_p2p.shared.config_models import SharedConfig
from police_thief_p2p.shared.strategy_config import StrategyConfig

ROOT = Path(__file__).parents[1]
SHARED_CONFIG = ROOT / "config/shared/game.example.json"
PRIVATE_CONFIG = ROOT / "config/private/game.example.toml"
BENCHMARKS = ROOT / "results/benchmarks"
TOURNAMENTS = ROOT / "results/tournaments"
SCHEMA_VERSION = "1.0.0"


def commit_sha() -> str:
    """Return the current commit digest, or a marker when git is unavailable."""
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],  # noqa: S607 - resolved from PATH by design.
            cwd=ROOT,
            check=True,
            capture_output=True,
            timeout=15,
            text=True,
        )
    except (OSError, subprocess.SubprocessError):
        return "unavailable"
    return completed.stdout.strip()


def load_configs() -> tuple[SharedConfig, StrategyConfig]:
    """Load the shared constitution and the private strategy profile."""
    shared = load_shared_path(SHARED_CONFIG)
    private = load_private_path(PRIVATE_CONFIG)
    return shared, private.strategy


def build_runner(
    shared: SharedConfig,
    strategy: StrategyConfig,
    belief: BeliefProfile = DEFAULT_BELIEF_PROFILE,
) -> ExperimentRunner:
    """Build a deterministic offline runner bound to one profile pair."""
    return ExperimentRunner(
        base_config=shared,
        strategy=strategy,
        clock=SystemClock(),
        random_factory=DeterministicRandomSource,
        belief=belief,
    )


@dataclass(frozen=True, slots=True)
class SplitPlan:
    """The frozen opponents, fixtures, and seeds available to one split."""

    split: str
    opponent_ids: tuple[str, ...]
    fixtures: tuple[BoardFixture, ...]
    seeds: tuple[int, ...]

    @classmethod
    def load(cls, split: str) -> "SplitPlan":
        """Load one split's frozen manifest into a usable plan."""
        manifest = split_manifest(split)
        return cls(
            split=split,
            opponent_ids=manifest.opponent_ids,
            fixtures=fixtures_for(split),
            seeds=manifest.seeds,
        )

    def spec(
        self,
        campaign_id: str,
        *,
        opponents: Sequence[str] | None = None,
        fixtures: Sequence[BoardFixture] | None = None,
        seeds: Sequence[int] | None = None,
        decision_budget_ms: int = 250,
        observation_delay: int = 0,
        scent_dropout: float = 0.0,
        repetitions: int = 1,
    ) -> TournamentSpec:
        """Build one tournament spec restricted to this split's frozen assets."""
        chosen_opponents = tuple(self.opponent_ids if opponents is None else opponents)
        chosen_fixtures = tuple(self.fixtures if fixtures is None else fixtures)
        chosen_seeds = tuple(self.seeds if seeds is None else seeds)
        unknown = set(chosen_seeds) - set(self.seeds)
        if unknown:
            raise ValueError(f"seeds {sorted(unknown)} are not frozen into {self.split!r}")
        return TournamentSpec(
            campaign_id=campaign_id,
            split=self.split,
            candidate_id=CANDIDATE_ID,
            opponent_ids=chosen_opponents,
            fixtures=chosen_fixtures,
            seeds=chosen_seeds,
            repetitions=repetitions,
            decision_budget_ms=decision_budget_ms,
            observation_delay=observation_delay,
            scent_dropout=scent_dropout,
        )


def load_freeze() -> dict[str, float | int]:
    """Return the tuned search point recorded by the tuning campaign."""
    path = BENCHMARKS / "m12_tuning.json"
    if not path.exists():
        raise FileNotFoundError("run scripts.run_m12_tuning before dependent campaigns")
    document = json.loads(path.read_text(encoding="utf-8"))
    trials = [
        item
        for outcome in ("random_search", "surrogate_search")
        for item in document[outcome]["trials"]
    ]
    best_id = document["manifest"]["candidate"]["trial_id"]
    for item in trials:
        if item["trial_id"] == best_id:
            return {name: value for name, value in item["point"].items()}
    raise ValueError(f"tuning evidence has no trial {best_id}")


def write_evidence(path: Path, document: Mapping[str, object]) -> None:
    """Write one campaign evidence document with stable formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(document, indent=2, sort_keys=False) + "\n"
    path.write_text(payload, encoding="utf-8", newline="\n")


def report_summary(report: TournamentReport) -> dict[str, object]:
    """Return the compact headline view of one campaign report."""
    document = report.as_document()
    return {
        "campaign_id": report.spec.campaign_id,
        "match_count": document["match_count"],
        "score_share_percent": document["score_share_percent"],
        "score_interval": document["score_interval"],
        "police_capture_rate": document["police_capture_rate"],
        "thief_survival_rate": document["thief_survival_rate"],
        "latency_p95_ms": document["latency_p95_ms"],
        "reliability": document["reliability"],
    }

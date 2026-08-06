"""Offline experiment, tuning, and league-rehearsal services for milestone M12."""

from police_thief_p2p.services.experiments.arena import MatchArena
from police_thief_p2p.services.experiments.gate_result import GateReport, GateResult
from police_thief_p2p.services.experiments.gates import promotion_report
from police_thief_p2p.services.experiments.generalization import (
    overfitting_gate,
    robustness_gate,
)
from police_thief_p2p.services.experiments.manifest import (
    CandidateFreeze,
    ReproducibilityManifest,
)
from police_thief_p2p.services.experiments.metrics import (
    PairedMatch,
    ReliabilityReport,
    role_summary,
)
from police_thief_p2p.services.experiments.opponents import OpponentEntry
from police_thief_p2p.services.experiments.outcome import MatchOutcome
from police_thief_p2p.services.experiments.pairing import MatchBrains
from police_thief_p2p.services.experiments.report import TournamentReport, build_report
from police_thief_p2p.services.experiments.resources import (
    ResourceLedger,
    ResourceUsage,
    measure,
)
from police_thief_p2p.services.experiments.roster import ROSTER, opponent
from police_thief_p2p.services.experiments.runner import ExperimentRunner
from police_thief_p2p.services.experiments.spec import BoardFixture, TournamentSpec
from police_thief_p2p.services.experiments.splits import (
    SealedHoldout,
    SplitManifest,
    split_manifest,
)
from police_thief_p2p.services.experiments.studies import ABLATIONS, ROBUSTNESS_CASES

__all__ = [
    "ABLATIONS",
    "ROBUSTNESS_CASES",
    "ROSTER",
    "BoardFixture",
    "CandidateFreeze",
    "ExperimentRunner",
    "GateReport",
    "GateResult",
    "MatchArena",
    "MatchBrains",
    "MatchOutcome",
    "OpponentEntry",
    "PairedMatch",
    "ReliabilityReport",
    "ReproducibilityManifest",
    "ResourceLedger",
    "ResourceUsage",
    "SealedHoldout",
    "SplitManifest",
    "TournamentReport",
    "TournamentSpec",
    "build_report",
    "measure",
    "opponent",
    "overfitting_gate",
    "promotion_report",
    "robustness_gate",
    "role_summary",
    "split_manifest",
]

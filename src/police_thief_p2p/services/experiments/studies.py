"""Declared ablation variants and robustness cases for M12 studies."""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from police_thief_p2p.services.strategy.hint_profiles import HintProfile

_EMPTY: Final[Mapping[str, float | int]] = MappingProxyType({})


@dataclass(frozen=True, slots=True)
class Ablation:
    """One named component removal measured against the intact candidate."""

    study_id: str
    component: str
    description: str
    point: Mapping[str, float | int] = _EMPTY

    def __post_init__(self) -> None:
        """Require a documented component and identifier."""
        if not self.study_id or not self.component or not self.description:
            raise ValueError("an ablation must name its component and rationale")


ABLATIONS: Final = (
    Ablation("ABL-FULL", "intact", "Full tuned candidate with no component removed."),
    Ablation(
        "ABL-DEPTH",
        "lookahead",
        "Collapse iterative deepening to a single-ply greedy evaluation.",
        MappingProxyType({"search_horizon": 1}),
    ),
    Ablation(
        "ABL-SAMPLES",
        "posterior-sampling",
        "Reduce stratified posterior sampling to a single representative cell.",
        MappingProxyType({"posterior_samples": 1}),
    ),
    Ablation(
        "ABL-CUT",
        "police-graph-cut",
        "Remove the Police connectivity-reduction (barrier cut) term.",
        MappingProxyType({"police.cut": 0.0, "police.budget": 0.0}),
    ),
    Ablation(
        "ABL-INFO",
        "police-information-gain",
        "Remove the Police information-gain exploration term.",
        MappingProxyType({"police.information": 0.0}),
    ),
    Ablation(
        "ABL-ROUTES",
        "thief-escape-routes",
        "Remove the Thief vertex-disjoint escape-route term.",
        MappingProxyType({"thief.routes": 0.0, "thief.corner": 0.0}),
    ),
    Ablation(
        "ABL-SCENT",
        "thief-scent-awareness",
        "Remove the Thief self-scent leakage penalty.",
        MappingProxyType({"thief.scent": 0.0}),
    ),
    Ablation(
        "ABL-RISK",
        "downside-risk-aversion",
        "Replace risk-sensitive scoring with risk-neutral expectation.",
        MappingProxyType({"police.risk": 0.0, "thief.risk": 0.0}),
    ),
    Ablation(
        "ABL-DECEPTION",
        "hint-deception",
        "Force fully honest hints by raising the deception trust threshold.",
        MappingProxyType({"hints.trust_threshold": 1.0}),
    ),
)


@dataclass(frozen=True, slots=True)
class RobustnessCase:
    """One degraded-environment or adversarial condition under test."""

    case_id: str
    description: str
    observation_delay: int = 0
    scent_dropout: float = 0.0
    decision_budget_ms: int = 250
    opponent_ids: tuple[str, ...] = ()
    hint_profile: HintProfile | None = None

    def __post_init__(self) -> None:
        """Validate declared degradation bounds."""
        if self.observation_delay < 0 or not 0.0 <= self.scent_dropout <= 1.0:
            raise ValueError("robustness degradation is outside supported bounds")
        if not 20 <= self.decision_budget_ms <= 5_000:
            raise ValueError("robustness decision budget is outside supported bounds")

    def as_document(self) -> dict[str, object]:
        """Return the serializable declaration of this case."""
        return {
            "case_id": self.case_id,
            "description": self.description,
            "observation_delay": self.observation_delay,
            "scent_dropout": self.scent_dropout,
            "decision_budget_ms": self.decision_budget_ms,
            "opponent_ids": list(self.opponent_ids),
            "hint_profile": None if self.hint_profile is None else self.hint_profile.value,
        }


ROBUSTNESS_CASES: Final = (
    RobustnessCase("ROB-CLEAN", "Nominal observation channel and release budget."),
    RobustnessCase("ROB-DELAY-1", "One-turn delayed opponent scent delivery.", observation_delay=1),
    RobustnessCase("ROB-DELAY-2", "Two-turn delayed opponent scent delivery.", observation_delay=2),
    RobustnessCase("ROB-DROP-30", "Thirty percent scent-frame loss.", scent_dropout=0.3),
    RobustnessCase("ROB-DROP-60", "Sixty percent scent-frame loss.", scent_dropout=0.6),
    RobustnessCase(
        "ROB-DEGRADED",
        "Combined delay, heavy loss, and a halved decision budget.",
        observation_delay=2,
        scent_dropout=0.5,
        decision_budget_ms=120,
    ),
    RobustnessCase(
        "ROB-LIAR",
        "Adversarial always-lying hint opponents.",
        opponent_ids=("BL-ADV-LIAR",),
        hint_profile=HintProfile.ALWAYS_LIE,
    ),
    RobustnessCase(
        "ROB-TRUST-SWITCH",
        "Opponents that build trust before switching to deception.",
        opponent_ids=("BL-ADV-TRUST",),
        hint_profile=HintProfile.TRUST_SWITCH,
    ),
)

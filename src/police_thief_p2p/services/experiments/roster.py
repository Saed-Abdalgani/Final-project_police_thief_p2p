"""Immutable registry of candidate, baseline, and adversary experiment policies."""

from collections.abc import Mapping
from types import MappingProxyType

from police_thief_p2p.services.experiments.hint_adversaries import HINT_ADVERSARIES
from police_thief_p2p.services.experiments.opponents import OpponentEntry, entry
from police_thief_p2p.services.strategy import evaders, pursuers, random_policy, scripted
from police_thief_p2p.services.strategy import reference as reference_module
from police_thief_p2p.services.strategy.baseline import PoliceBaselineBrain, ThiefBaselineBrain
from police_thief_p2p.services.strategy.police import AdvancedPoliceBrain
from police_thief_p2p.services.strategy.thief import AdvancedThiefBrain

CANDIDATE_ID = "candidate-advanced"
REFERENCE_ID = "BL-REF"

_ENTRIES: tuple[OpponentEntry, ...] = (
    entry(
        CANDIDATE_ID,
        "candidate",
        AdvancedPoliceBrain,
        AdvancedThiefBrain,
        "frozen advanced search candidate",
    ),
    entry(
        REFERENCE_ID,
        "baseline",
        reference_module.ReferenceGreedyPoliceBrain,
        reference_module.ReferenceGreedyThiefBrain,
        "documented argmax-Manhattan greedy with random barriers",
    ),
    entry(
        "BL-RND",
        "baseline",
        random_policy.RandomLegalPoliceBrain,
        random_policy.RandomLegalThiefBrain,
        "seeded uniformly random legal policy",
    ),
    entry(
        "BL-SCR",
        "baseline",
        scripted.ShortestPathPoliceBrain,
        scripted.MaximumDistanceThiefBrain,
        "scripted shortest-path Police and maximum-distance Thief",
    ),
    entry(
        "BL-POST",
        "baseline",
        PoliceBaselineBrain,
        ThiefBaselineBrain,
        "posterior-aware deterministic fallback baseline",
    ),
    entry(
        "BL-ADV-CORNER",
        "adversary",
        pursuers.AggressiveBarrierPoliceBrain,
        evaders.CornerHuggingThiefBrain,
        "aggressive barrier Police and corner-hugging Thief",
    ),
    entry(
        "BL-ADV-BOUNDARY",
        "adversary",
        pursuers.GraphCutPoliceBrain,
        evaders.BoundaryFollowingThiefBrain,
        "graph-cut Police and boundary-following Thief",
    ),
    entry(
        "BL-ADV-CYCLE",
        "adversary",
        pursuers.GraphCutPoliceBrain,
        evaders.CycleThiefBrain,
        "graph-cut Police and oscillating Thief",
    ),
    entry(
        "BL-ADV-SWITCH",
        "adversary",
        pursuers.AggressiveBarrierPoliceBrain,
        evaders.SwitchingThiefBrain,
        "aggressive Police and sudden-strategy-switch Thief",
    ),
    *HINT_ADVERSARIES,
    entry(
        "BL-PREV",
        "regression",
        PoliceBaselineBrain,
        ThiefBaselineBrain,
        "previous frozen candidate checkpoint 0.10.0 posterior profile",
        version="0.10.0",
    ),
)
ROSTER: Mapping[str, OpponentEntry] = MappingProxyType(
    {item.opponent_id: item for item in _ENTRIES}
)


def opponent(opponent_id: str) -> OpponentEntry:
    """Return one registered opponent or fail closed on an unknown identifier."""
    try:
        return ROSTER[opponent_id]
    except KeyError as exc:
        raise KeyError(f"unknown experiment opponent: {opponent_id!r}") from exc


def opponents_by_classification(classification: str) -> tuple[str, ...]:
    """Return sorted identifiers for one opponent classification."""
    return tuple(
        sorted(item.opponent_id for item in _ENTRIES if item.classification == classification)
    )

"""Exact mapping from guarded strategy output into commitment fields."""

from dataclasses import dataclass

from police_thief_p2p.services.crypto.payload import CommittedAction
from police_thief_p2p.services.strategy.contracts import Decision


@dataclass(frozen=True, slots=True)
class StrategyCommitmentFields:
    """Outcome-relevant decision fields bound by Commit-Reveal."""

    action: CommittedAction
    hint: str
    verdict: str
    hint_semantic_intent: str


def commitment_fields(decision: Decision) -> StrategyCommitmentFields:
    """Bind action, realized hint, truth verdict, and semantic intent."""
    return StrategyCommitmentFields(
        action=CommittedAction.from_domain(decision.action),
        hint=decision.hint,
        verdict=decision.hint_intent.verdict.value,
        hint_semantic_intent=decision.hint_intent.region.value,
    )

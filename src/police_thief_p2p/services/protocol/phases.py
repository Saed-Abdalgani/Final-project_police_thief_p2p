"""Formal M4 protocol phases and per-tool preconditions."""

from __future__ import annotations

from enum import StrEnum

from police_thief_p2p.services.protocol.errors import ProtocolErrorCode, ProtocolFailure


class ProtocolPhase(StrEnum):
    """Negotiation, play, audit, reporting, and immutable terminal phases."""

    NEGOTIATING = "negotiating"
    READY = "ready"
    WAITING = "waiting"
    AWAITING_ACK = "awaiting_ack"
    REVEALING = "revealing"
    VERIFYING = "verifying"
    AUDITING = "auditing"
    AGREEING_RESULT = "agreeing_result"
    REPORTING = "reporting"
    COMPLETED = "completed"
    TECHNICAL = "technical"
    TAMPER = "tamper"
    STOPPED = "stopped"

    @property
    def terminal(self) -> bool:
        """Return whether this phase can never transition again."""
        return self in {
            ProtocolPhase.COMPLETED,
            ProtocolPhase.TECHNICAL,
            ProtocolPhase.TAMPER,
            ProtocolPhase.STOPPED,
        }


_ALLOWED: dict[str, frozenset[ProtocolPhase]] = {
    "propose_match_v1": frozenset({ProtocolPhase.NEGOTIATING}),
    "accept_match_v1": frozenset({ProtocolPhase.NEGOTIATING}),
    "commit_step_v1": frozenset({ProtocolPhase.READY, ProtocolPhase.WAITING}),
    "acknowledge_step_v1": frozenset({ProtocolPhase.AWAITING_ACK}),
    "reveal_step_v1": frozenset({ProtocolPhase.REVEALING}),
    "capture_claim_v1": frozenset({ProtocolPhase.WAITING}),
    "capture_response_v1": frozenset({ProtocolPhase.VERIFYING}),
    "final_reveal_v1": frozenset({ProtocolPhase.AUDITING}),
    "audit_result_v1": frozenset({ProtocolPhase.AGREEING_RESULT}),
    "agree_result_v1": frozenset({ProtocolPhase.REPORTING}),
}


def require_phase(tool: str, phase: ProtocolPhase) -> None:
    """Reject unknown tools, terminal mutation, and illegal phase/tool pairs."""
    allowed = _ALLOWED.get(tool)
    if allowed is None or phase not in allowed:
        raise ProtocolFailure(
            ProtocolErrorCode.PHASE,
            f"{tool} is not allowed during phase {phase.value}",
        )


def next_phase(tool: str, payload: dict[str, object]) -> ProtocolPhase:
    """Return the deterministic phase after one successful mutation."""
    if tool == "propose_match_v1":
        return ProtocolPhase.NEGOTIATING
    if tool == "accept_match_v1":
        return ProtocolPhase.READY
    if tool == "commit_step_v1":
        return ProtocolPhase.AWAITING_ACK
    if tool == "acknowledge_step_v1":
        return ProtocolPhase.REVEALING
    if tool == "reveal_step_v1":
        return ProtocolPhase.AUDITING if "terminal_reason" in payload else ProtocolPhase.WAITING
    if tool == "capture_claim_v1":
        return ProtocolPhase.VERIFYING
    if tool == "capture_response_v1":
        return ProtocolPhase.AUDITING if payload.get("accepted") is True else ProtocolPhase.WAITING
    if tool == "final_reveal_v1":
        return ProtocolPhase.AGREEING_RESULT
    if tool == "audit_result_v1":
        return ProtocolPhase.REPORTING
    if tool == "agree_result_v1":
        return ProtocolPhase.COMPLETED
    raise ProtocolFailure(ProtocolErrorCode.PHASE, "unknown mutating tool")

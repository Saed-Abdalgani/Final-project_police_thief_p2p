"""Replay frame construction and single-log belief validation."""

from decimal import Decimal, InvalidOperation

from police_thief_p2p.domain import LocalGameState, Role
from police_thief_p2p.services.artifacts.records import SealedLogEntry
from police_thief_p2p.services.crypto.payload import CommitmentBody
from police_thief_p2p.services.replay.models import ReplayFinding, ReplayFrame, ReplayMode


def validate_heatmap(
    heatmap: tuple[str, ...],
    size: int,
    mode: ReplayMode,
    sequence: int,
) -> ReplayFinding | None:
    """Require a normalized local belief in single-log mode."""
    if mode is ReplayMode.OBJECTIVE and not heatmap:
        return None
    try:
        values = tuple(Decimal(item) for item in heatmap)
    except InvalidOperation:
        values = ()
    if len(values) != size * size or sum(values) != Decimal(1):
        return ReplayFinding(
            1,
            "BELIEF",
            f"step:{sequence}",
            "belief is missing or not normalized",
        )
    return None


def build_frame(
    states: dict[Role, LocalGameState],
    viewer_role: Role,
    mode: ReplayMode,
    entry: SealedLogEntry,
    body: CommitmentBody,
    heatmap: tuple[str, ...],
    terminal: str | None,
) -> ReplayFrame:
    """Create one immutable mode-gated navigation frame."""
    police = states[Role.POLICE].position
    thief = states[Role.THIEF].position
    own = states[viewer_role].position
    barriers = states[Role.POLICE].public_barriers.cells
    objective = mode is ReplayMode.OBJECTIVE
    action_text = body.action.direction or body.action.action_type.value
    return ReplayFrame(
        sequence=entry.sequence,
        actor=entry.actor,
        actor_step=entry.step_number,
        action=str(action_text),
        own_position=(own.row, own.col),
        police_position=(police.row, police.col) if objective else None,
        thief_position=(thief.row, thief.col) if objective else None,
        public_barriers=tuple(sorted((item.row, item.col) for item in barriers)),
        belief_heatmap=heatmap if not objective else (),
        commitment_status="Verified OK",
        terminal_reason=terminal,
    )

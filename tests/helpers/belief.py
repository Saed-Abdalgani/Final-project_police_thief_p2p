from police_thief_p2p.domain import Action, Role
from police_thief_p2p.services.belief.models import OpponentScentFrame
from police_thief_p2p.services.crypto.payload import (
    CommitmentBody,
    CommittedAction,
    LiveReveal,
)

GAME_UID = "87654321-4321-4321-8321-cba987654321"
DIGEST = "a" * 64


def make_scent_frame(
    size: int,
    cells: tuple[tuple[int, int, str], ...],
    *,
    step_number: int = 1,
    actor: Role = Role.THIEF,
) -> OpponentScentFrame:
    """Build one valid sparse scent frame."""
    return OpponentScentFrame.create(
        game_uid=GAME_UID,
        sub_game_number=1,
        step_number=step_number,
        actor=actor,
        rows=size,
        cols=size,
        scent_model_sha256=DIGEST,
        cells=[{"row": row, "col": col, "value": value} for row, col, value in cells],
    )


def make_scent_reveal(frame: OpponentScentFrame) -> LiveReveal:
    """Build the exact nonce-free reveal binding one frame digest."""
    body = CommitmentBody(
        game_uid=frame.game_uid,
        sub_game_number=frame.sub_game_number,
        step_number=frame.step_number,
        actor=frame.actor,
        pre_action_state_digest=DIGEST,
        action=CommittedAction.from_domain(Action.stay()),
        hint="quiet center",
        verdict="truth",
        hint_semantic_intent="center",
        token_count=0,
        model_provider="template",
        model_name="deterministic",
        config_sha256=DIGEST,
        protocol_version="0.7.0",
        scent_model_sha256=frame.scent_model_sha256,
        scent_frame_sha256=frame.frame_sha256,
    )
    return LiveReveal(body=body, commitment_sha256="b" * 64)

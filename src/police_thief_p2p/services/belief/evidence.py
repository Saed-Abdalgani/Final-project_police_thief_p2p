"""Commitment-reveal gate for received scent evidence."""

import secrets

from police_thief_p2p.services.belief.models import (
    OpponentScentFrame,
    VerifiedScentEvidence,
)
from police_thief_p2p.services.crypto.payload import LiveReveal


def verify_scent_reveal(
    frame: OpponentScentFrame,
    reveal: LiveReveal,
) -> VerifiedScentEvidence:
    """Accept a frame only when exact identity/model/digest match its reveal."""
    body = reveal.body
    identity_matches = (
        frame.game_uid == body.game_uid
        and frame.sub_game_number == body.sub_game_number
        and frame.step_number == body.step_number
        and frame.actor is body.actor
        and frame.scent_model_sha256 == body.scent_model_sha256
    )
    if not identity_matches:
        raise ValueError("scent frame context differs from commitment reveal")
    if not secrets.compare_digest(frame.frame_sha256, body.scent_frame_sha256):
        raise ValueError("scent frame is not bound to the commitment")
    return VerifiedScentEvidence(frame, reveal.commitment_sha256)

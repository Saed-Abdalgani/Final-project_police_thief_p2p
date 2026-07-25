"""Local sealed-step lifecycle and phase-gated final nonce manifest."""

from __future__ import annotations

import secrets
from dataclasses import replace

from police_thief_p2p.services.crypto.payload import (
    CommitmentPayload,
    LiveReveal,
    PublicCommitment,
)
from police_thief_p2p.services.crypto.store_models import (
    CommitmentIdentity,
    FinalRevealEntry,
    FinalRevealManifest,
    SealedStep,
)
from police_thief_p2p.services.protocol.errors import ProtocolErrorCode, ProtocolFailure
from police_thief_p2p.services.protocol.phases import ProtocolPhase
from police_thief_p2p.shared.canonical_json import sha256_digest

__all__ = [
    "CommitmentIdentity",
    "FinalRevealEntry",
    "FinalRevealManifest",
    "SealedStepStore",
]


class SealedStepStore:
    """Enforce commit, acknowledgement, live reveal, and final reveal order."""

    __slots__ = ("_nonces", "_steps")

    def __init__(self) -> None:
        """Create an empty private sealed store."""
        self._steps: dict[CommitmentIdentity, SealedStep] = {}
        self._nonces: set[str] = set()

    def seal(self, payload: CommitmentPayload) -> PublicCommitment:
        """Persist one unique payload and return only its public digest."""
        identity = self._identity(payload)
        if identity in self._steps:
            raise ProtocolFailure(ProtocolErrorCode.CONFLICT, "commitment identity already exists")
        fingerprint = payload.nonce.fingerprint()
        if fingerprint in self._nonces:
            raise ProtocolFailure(ProtocolErrorCode.CONFLICT, "nonce reuse is prohibited")
        digest = payload.digest()
        self._steps[identity] = SealedStep(payload, digest)
        self._nonces.add(fingerprint)
        return PublicCommitment(
            game_uid=identity.game_uid,
            sub_game_number=identity.sub_game_number,
            step_number=identity.step_number,
            actor=identity.actor,
            commitment_sha256=digest,
        )

    def replace_before_ack(
        self,
        identity: CommitmentIdentity,
        payload: CommitmentPayload,
    ) -> PublicCommitment:
        """Replace an unlocked local decision; never permit post-ack mutation."""
        step = self._get(identity)
        if step.acknowledged:
            raise ProtocolFailure(ProtocolErrorCode.PHASE, "acknowledged payload is immutable")
        if self._identity(payload) != identity:
            raise ProtocolFailure(ProtocolErrorCode.IDENTITY, "replacement identity differs")
        self._nonces.discard(step.payload.nonce.fingerprint())
        del self._steps[identity]
        return self.seal(payload)

    def acknowledge(self, identity: CommitmentIdentity, digest: str) -> None:
        """Lock one exact prior commitment."""
        step = self._get(identity)
        if not secrets.compare_digest(step.commitment_sha256, digest):
            raise ProtocolFailure(ProtocolErrorCode.CONFLICT, "acknowledgement digest differs")
        self._steps[identity] = replace(step, acknowledged=True)

    def reveal(self, identity: CommitmentIdentity) -> LiveReveal:
        """Reveal action/hint/effects only after acknowledgement, never nonce."""
        step = self._get(identity)
        if not step.acknowledged:
            raise ProtocolFailure(ProtocolErrorCode.PHASE, "reveal requires acknowledgement")
        self._steps[identity] = replace(step, revealed=True)
        return LiveReveal(body=step.payload.body, commitment_sha256=step.commitment_sha256)

    def final_manifest(
        self,
        game_uid: str,
        sub_game_number: int,
        phase: ProtocolPhase,
    ) -> FinalRevealManifest:
        """Expose nonces only in terminal audit/result phases."""
        allowed = {
            ProtocolPhase.AUDITING,
            ProtocolPhase.AGREEING_RESULT,
            ProtocolPhase.REPORTING,
            ProtocolPhase.COMPLETED,
        }
        if phase not in allowed:
            raise ProtocolFailure(ProtocolErrorCode.PHASE, "final reveal is not yet allowed")
        selected = tuple(
            (identity, step)
            for identity, step in sorted(self._steps.items())
            if identity.game_uid == game_uid and identity.sub_game_number == sub_game_number
        )
        if not selected or any(not step.revealed for _, step in selected):
            raise ProtocolFailure(ProtocolErrorCode.PHASE, "all steps must be live-revealed first")
        entries = tuple(
            FinalRevealEntry(
                identity,
                step.commitment_sha256,
                step.payload.nonce.reveal_hex(),
            )
            for identity, step in selected
        )
        digest = sha256_digest([entry.as_dict() for entry in entries])
        return FinalRevealManifest(game_uid, sub_game_number, entries, digest)

    def offline_payload(self, identity: CommitmentIdentity) -> CommitmentPayload:
        """Return a payload only to the local offline audit composition root."""
        return self._get(identity).payload

    @staticmethod
    def _identity(payload: CommitmentPayload) -> CommitmentIdentity:
        body = payload.body
        return CommitmentIdentity(
            body.game_uid,
            body.sub_game_number,
            body.step_number,
            body.actor,
        )

    def _get(self, identity: CommitmentIdentity) -> SealedStep:
        try:
            return self._steps[identity]
        except KeyError as exc:
            raise ProtocolFailure(ProtocolErrorCode.UNKNOWN_SESSION, "unknown commitment") from exc

"""Commit-reveal and pure-audit use cases mixed into the public SDK."""

from police_thief_p2p.services.audit.models import AuditBundle, AuditReport
from police_thief_p2p.services.audit.service import AuditService
from police_thief_p2p.services.crypto.declaration import SignedStepZero, SigningKey, StepZeroBody
from police_thief_p2p.services.crypto.nonce import SecretNonce
from police_thief_p2p.services.crypto.payload import (
    CommitmentBody,
    CommitmentPayload,
    LiveReveal,
    PublicCommitment,
)
from police_thief_p2p.services.crypto.store import (
    CommitmentIdentity,
    FinalRevealManifest,
    SealedStepStore,
)
from police_thief_p2p.services.protocol.phases import ProtocolPhase


class CryptoAuditFacade:
    """Expose security use cases without service implementation leakage."""

    __slots__ = ()
    _sealed_steps: SealedStepStore

    def seal_step(
        self,
        body: CommitmentBody,
        nonce: SecretNonce | None = None,
    ) -> PublicCommitment:
        """Seal one immutable decision and expose only its commitment."""
        return self._sealed_steps.seal(
            CommitmentPayload(body, SecretNonce.generate() if nonce is None else nonce)
        )

    def acknowledge_step(self, identity: CommitmentIdentity, digest: str) -> None:
        """Lock an exact prior commitment."""
        self._sealed_steps.acknowledge(identity, digest)

    def reveal_step(self, identity: CommitmentIdentity) -> LiveReveal:
        """Reveal the live body after acknowledgement without its nonce."""
        return self._sealed_steps.reveal(identity)

    def final_reveal(
        self,
        game_uid: str,
        sub_game_number: int,
        phase: ProtocolPhase,
    ) -> FinalRevealManifest:
        """Create the phase-gated final nonce manifest."""
        return self._sealed_steps.final_manifest(game_uid, sub_game_number, phase)

    def sign_step_zero(self, body: StepZeroBody, key: SigningKey) -> SignedStepZero:
        """Sign exact Step-0 canonical bytes without retaining key material."""
        return SignedStepZero.create(body, key)

    def audit_sub_game(self, bundle: AuditBundle) -> AuditReport:
        """Independently verify one immutable offline evidence bundle."""
        return AuditService().verify(bundle)

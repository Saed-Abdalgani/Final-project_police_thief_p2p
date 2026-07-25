"""Immutable sealed-store and final-manifest records."""

from dataclasses import dataclass

from police_thief_p2p.domain.values import Role
from police_thief_p2p.services.crypto.payload import CommitmentPayload


@dataclass(frozen=True, slots=True, order=True)
class CommitmentIdentity:
    """Unique commitment identity within a series."""

    game_uid: str
    sub_game_number: int
    step_number: int
    actor: Role


@dataclass(frozen=True, slots=True)
class SealedStep:
    """Private payload plus public digest and lifecycle locks."""

    payload: CommitmentPayload
    commitment_sha256: str
    acknowledged: bool = False
    revealed: bool = False


@dataclass(frozen=True, slots=True)
class FinalRevealEntry:
    """Final-audit nonce linked to one prior public commitment."""

    identity: CommitmentIdentity
    commitment_sha256: str
    nonce_hex: str

    def as_dict(self) -> dict[str, object]:
        """Return a canonicalizable post-terminal representation."""
        return {
            "game_uid": self.identity.game_uid,
            "sub_game_number": self.identity.sub_game_number,
            "step_number": self.identity.step_number,
            "actor": self.identity.actor.value,
            "commitment_sha256": self.commitment_sha256,
            "nonce_hex": self.nonce_hex,
        }


@dataclass(frozen=True, slots=True)
class FinalRevealManifest:
    """Ordered final reveal entries and their linkage digest."""

    game_uid: str
    sub_game_number: int
    entries: tuple[FinalRevealEntry, ...]
    manifest_sha256: str

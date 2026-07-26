"""Strict finalized reveal input used by replay."""

from pydantic import ConfigDict

from police_thief_p2p.services.crypto.payload import CommitmentBody
from police_thief_p2p.services.protocol.envelope import ProtocolModel


class ReplayReveal(ProtocolModel):
    """Final revealed step material required for independent replay."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    body: CommitmentBody
    nonce_hex: str
    belief_heatmap: tuple[str, ...] = ()

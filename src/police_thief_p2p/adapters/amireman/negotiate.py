"""Per-sub-game negotiation handshake."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from police_thief_p2p.adapters.amireman.canonical import commit_of, derive_game_ids, fresh_nonce, verify
from police_thief_p2p.adapters.amireman.terms import TERMS_KEYS, terms_equal
from police_thief_p2p.adapters.amireman.wire import Negotiation


class NegotiationRefusedError(Exception):
    """Greeting refused: terms, signature, or identity failure."""


@dataclass(frozen=True)
class Agreed:
    game_id: str
    game_uid: str
    opponent_group: str
    opponent_role: str | None
    opponent_identity: dict
    terms: dict


class Negotiator:
    """One peer's side of the agreement handshake for a single sub-game."""

    def __init__(self, terms: dict[str, Any], identity: dict[str, Any], group_id: str) -> None:
        self.terms = terms
        self.identity = identity
        self.group_id = group_id
        self._nonce = fresh_nonce()

    def signed(
        self, role: str, sub_game_number: int, opponent_group: str | None = None
    ) -> Negotiation:
        game_uid = None
        if opponent_group:
            game_uid = derive_game_ids(self.terms, self.group_id, opponent_group)[1]
        return Negotiation(
            terms=self.terms,
            nonce=self._nonce,
            signature=commit_of(self.terms, self._nonce),
            group_id=self.group_id,
            role=role,
            sub_game_number=sub_game_number,
            identity=self.identity,
            game_uid=game_uid,
        )

    def verify_peer(self, raw: dict[str, Any]) -> Agreed:
        if not isinstance(raw, dict) or not isinstance(raw.get("terms"), dict):
            raise NegotiationRefusedError("greeting carries no object terms")
        peer_terms = raw["terms"]
        missing = sorted(set(TERMS_KEYS) - set(peer_terms))
        if missing:
            raise NegotiationRefusedError(f"opponent terms incomplete; missing {missing}")
        if not terms_equal(self.terms, peer_terms):
            raise NegotiationRefusedError("terms mismatch: constitution disagreement")
        nonce, signature = raw.get("nonce"), raw.get("signature")
        if not nonce or not signature:
            raise NegotiationRefusedError("greeting carries no nonce/signature")
        if not verify(peer_terms, str(nonce), str(signature)):
            raise NegotiationRefusedError("terms signature does not verify")
        opponent = raw.get("group_id") or (raw.get("identity") or {}).get("group_id")
        if not opponent:
            raise NegotiationRefusedError("greeting names no group_id")
        game_id, game_uid = derive_game_ids(self.terms, self.group_id, str(opponent))
        declared = raw.get("game_uid")
        if isinstance(declared, str) and declared != game_uid:
            raise NegotiationRefusedError(f"game_uid mismatch: derive {game_uid}, declared {declared}")
        return Agreed(
            game_id,
            game_uid,
            str(opponent),
            raw.get("role"),
            raw.get("identity") or {},
            peer_terms,
        )

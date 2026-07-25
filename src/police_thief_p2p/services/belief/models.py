"""Immutable opponent-facing scent and local belief DTOs."""

from __future__ import annotations

import math
import re
import secrets
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING, Annotated, Literal, Self

from pydantic import Field, StrictInt, StrictStr, model_validator

from police_thief_p2p.domain.values import Role
from police_thief_p2p.services.protocol.envelope import ProtocolModel
from police_thief_p2p.shared.canonical_json import sha256_digest
from police_thief_p2p.shared.identifiers import GameUid

if TYPE_CHECKING:
    from police_thief_p2p.services.belief.grid import BeliefGrid

_DIGEST = re.compile(r"^[a-f0-9]{64}$")
_DECIMAL = re.compile(r"^(?:0|[1-9]\d*)(?:\.\d+)?$")
MAX_SCENT_CELLS = 2_048


class ScentCell(ProtocolModel):
    """One bounded sparse scent cell."""

    row: Annotated[StrictInt, Field(ge=0)]
    col: Annotated[StrictInt, Field(ge=0)]
    value: StrictStr

    def decimal_value(self) -> Decimal:
        """Return a finite probability-range decimal."""
        if _DECIMAL.fullmatch(self.value) is None:
            raise ValueError("scent value must be a plain decimal")
        try:
            value = Decimal(self.value)
        except InvalidOperation as exc:
            raise ValueError("scent value must be a plain decimal") from exc
        if not value.is_finite() or not Decimal(0) <= value <= Decimal(1):
            raise ValueError("scent value must be finite and between zero and one")
        return value


class OpponentScentFrame(ProtocolModel):
    """Commitment-linked sparse observation with no true-position field."""

    frame_version: Literal["1.0.0"] = "1.0.0"
    game_uid: StrictStr
    sub_game_number: Annotated[StrictInt, Field(ge=1, le=6)]
    step_number: Annotated[StrictInt, Field(ge=1)]
    actor: Role
    rows: Annotated[StrictInt, Field(ge=1, le=10_000)]
    cols: Annotated[StrictInt, Field(ge=1, le=10_000)]
    scent_model_sha256: StrictStr
    cells: Annotated[tuple[ScentCell, ...], Field(max_length=MAX_SCENT_CELLS)]
    frame_sha256: StrictStr

    @model_validator(mode="after")
    def validate_frame(self) -> Self:
        """Validate identity, bounds, uniqueness, values, and exact digest."""
        GameUid(self.game_uid)
        if _DIGEST.fullmatch(self.scent_model_sha256) is None:
            raise ValueError("scent model digest is invalid")
        positions = {(cell.row, cell.col) for cell in self.cells}
        if len(positions) != len(self.cells):
            raise ValueError("scent frame contains duplicate cells")
        for cell in self.cells:
            if cell.row >= self.rows or cell.col >= self.cols:
                raise ValueError("scent cell is outside frame dimensions")
            cell.decimal_value()
        expected = sha256_digest(self.digest_document())
        if not secrets.compare_digest(expected, self.frame_sha256):
            raise ValueError("scent frame digest differs")
        return self

    def digest_document(self) -> dict[str, object]:
        """Return the canonical frame fields covered by its digest."""
        return self.model_dump(mode="json", exclude={"frame_sha256"})

    @classmethod
    def create(cls, **values: object) -> Self:
        """Create a frame and derive its canonical digest."""
        document = dict(values)
        document.setdefault("frame_version", "1.0.0")
        document["frame_sha256"] = sha256_digest(document)
        return cls.model_validate(document)


@dataclass(frozen=True, slots=True)
class VerifiedScentEvidence:
    """A frame accepted only through an exact commitment reveal."""

    frame: OpponentScentFrame
    reveal_commitment_sha256: str


@dataclass(frozen=True, slots=True)
class BeliefDiagnostics:
    """Safe local belief quality summary."""

    entropy_bits: float
    peak_probability: float
    credible_region: tuple[tuple[int, int], ...]
    most_likely_cell: tuple[int, int]
    fallback_used: bool
    hint_category: str

    def __post_init__(self) -> None:
        """Validate finite safe diagnostic values."""
        if not all(
            math.isfinite(value) and value >= 0
            for value in (
                self.entropy_bits,
                self.peak_probability,
            )
        ):
            raise ValueError("belief diagnostics must be finite and non-negative")
        if self.peak_probability > 1:
            raise ValueError("belief peak probability cannot exceed one")


@dataclass(frozen=True, slots=True)
class BeliefUpdate:
    """One immutable posterior and its diagnostics."""

    belief: BeliefGrid
    diagnostics: BeliefDiagnostics

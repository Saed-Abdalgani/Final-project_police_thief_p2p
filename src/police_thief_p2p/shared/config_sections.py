"""Immutable typed sections of the shared match constitution."""

import re
from decimal import Decimal
from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    PlainSerializer,
    StrictInt,
    StrictStr,
    field_validator,
    model_validator,
)

from police_thief_p2p.shared.coordinates import OriginCorner
from police_thief_p2p.shared.scent import KERNEL_TEXT, RoundingMode

_DECIMAL_PATTERN = re.compile(r"^(?:0|[1-9]\d*)(?:\.\d+)?$")


def _parse_decimal_text(value: object) -> Decimal:
    if not isinstance(value, str) or _DECIMAL_PATTERN.fullmatch(value) is None:
        raise ValueError("must be a non-negative plain decimal string")
    return Decimal(value)


DecimalText = Annotated[
    Decimal,
    BeforeValidator(_parse_decimal_text),
    PlainSerializer(lambda value: format(value, "f"), return_type=str),
]


class FrozenModel(BaseModel):
    """Strict immutable Pydantic base used by all config sections."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class BoardAndAgents(FrozenModel):
    """Board geometry, coordinate convention, and initial cells."""

    grid_size: Annotated[StrictInt, Field(ge=7, le=10_000)]
    num_agents: Literal[2]
    axis_origin_corner: OriginCorner = OriginCorner.TOP_LEFT
    axis_start_index: Literal[0, 1] = 0
    thief_start: tuple[StrictInt, StrictInt] = (3, 3)
    cop_start: tuple[StrictInt, StrictInt] = (0, 0)


class WorldConfig(FrozenModel):
    """Natural-language world and hint constraints."""

    map_area: Annotated[StrictStr, Field(max_length=200)] = ""
    hint_max_words: Annotated[StrictInt, Field(ge=1, le=100)] = 15


class MovementAndBarriers(FrozenModel):
    """Legal move alphabet and bounded sub-game resources."""

    move_set: tuple[Literal["N", "S", "E", "W", "STAY"], ...]
    max_barriers: Annotated[StrictInt, Field(ge=14, le=1_000_000)]
    max_moves: Annotated[StrictInt, Field(ge=35, le=2_147_483_647)]
    survival_threshold: Annotated[StrictInt, Field(ge=35, le=2_147_483_647)]

    @field_validator("move_set")
    @classmethod
    def exact_move_set(
        cls, value: tuple[Literal["N", "S", "E", "W", "STAY"], ...]
    ) -> tuple[Literal["N", "S", "E", "W", "STAY"], ...]:
        """Enforce the ordered fixed orthogonal move alphabet."""
        if value != ("N", "S", "E", "W", "STAY"):
            raise ValueError("must equal ['N', 'S', 'E', 'W', 'STAY']")
        return value


class ScentRounding(FrozenModel):
    """Signed decimal interoperability policy."""

    decimal_places: Literal[6] = 6
    mode: Literal[RoundingMode.HALF_EVEN] = RoundingMode.HALF_EVEN


class ScentNumericExample(FrozenModel):
    """Signed golden scent example preventing interpretation drift."""

    center_emission: DecimalText
    center_after_one_full_turn: DecimalText

    @model_validator(mode="after")
    def exact_example(self) -> Self:
        """Enforce the reviewed 0.9 then 10% decay vector."""
        if self.center_emission != Decimal("0.900000"):
            raise ValueError("center_emission must equal 0.900000")
        if self.center_after_one_full_turn != Decimal("0.810000"):
            raise ValueError("center_after_one_full_turn must equal 0.810000")
        return self


class PheromoneConfig(FrozenModel):
    """Exact shared scent formula, kernel, and example."""

    pheromone_center_intensity: DecimalText
    pheromone_decay: DecimalText
    pheromone_grid_size: Literal[5]
    kernel: tuple[tuple[DecimalText, ...], ...]
    rounding: ScentRounding
    numeric_example: ScentNumericExample

    @model_validator(mode="after")
    def exact_scent_contract(self) -> Self:
        """Enforce every fixed and selected interoperability value."""
        if self.pheromone_center_intensity != Decimal("0.9"):
            raise ValueError("pheromone_center_intensity must equal 0.9")
        if self.pheromone_decay != Decimal("0.10"):
            raise ValueError("pheromone_decay must equal 0.10")
        expected = tuple(tuple(Decimal(item) for item in row) for row in KERNEL_TEXT)
        if self.kernel != expected:
            raise ValueError("kernel must equal the signed 5x5 conformance kernel")
        return self


class ScoringConfig(FrozenModel):
    """Appendix F fixed scoring table."""

    capture_cop: Literal[20]
    capture_thief: Literal[5]
    survival_cop: Literal[5]
    survival_thief: Literal[10]
    tie_score: Literal[2]

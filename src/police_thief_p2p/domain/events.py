"""Deterministic public events emitted by domain transitions."""

from dataclasses import dataclass
from typing import TypedDict

from police_thief_p2p.domain.values import Position, Role


class BarrierPlacedDict(TypedDict):
    """Serialized public barrier event shape."""

    event_type: str
    actor: str
    step_number: int
    target: list[int]


@dataclass(frozen=True, slots=True)
class BarrierPlaced:
    """Public immutable evidence of one exact Police barrier target."""

    actor: Role
    step_number: int
    target: Position

    def __post_init__(self) -> None:
        """Enforce the only role permitted to place a barrier."""
        if not isinstance(self.actor, Role):
            raise TypeError("barrier actor must be a Role")
        if type(self.step_number) is not int:
            raise TypeError("barrier event step_number must be an integer")
        if not isinstance(self.target, Position):
            raise TypeError("barrier target must be a Position")
        if self.actor is not Role.POLICE:
            raise ValueError("only Police can emit a barrier event")
        if self.step_number < 1:
            raise ValueError("barrier event step_number must be positive")

    def as_dict(self) -> BarrierPlacedDict:
        """Return a deterministic JSON-compatible public representation."""
        return {
            "event_type": "barrier_placed",
            "actor": self.actor.value,
            "step_number": self.step_number,
            "target": [self.target.row, self.target.col],
        }

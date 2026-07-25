"""Immutable primitive values for game physics and outcomes."""

from dataclasses import dataclass
from enum import StrEnum

from police_thief_p2p.shared.coordinates import Position

__all__ = [
    "Action",
    "ActionType",
    "Direction",
    "Position",
    "Role",
    "TerminalReason",
]


class Direction(StrEnum):
    """One legal orthogonal movement direction."""

    NORTH = "N"
    SOUTH = "S"
    EAST = "E"
    WEST = "W"


class ActionType(StrEnum):
    """Mutually exclusive game action categories."""

    MOVE = "MOVE"
    STAY = "STAY"
    BARRIER = "BARRIER"


class Role(StrEnum):
    """A peer's role in one sub-game."""

    POLICE = "police"
    THIEF = "thief"

    @property
    def opponent(self) -> "Role":
        """Return the opposite role."""
        return Role.THIEF if self is Role.POLICE else Role.POLICE


class TerminalReason(StrEnum):
    """Distinct immutable terminal outcome categories."""

    CAPTURE = "capture"
    BARRIER_CAPTURE = "barrier_capture"
    ENCLOSURE = "enclosure"
    SURVIVAL = "survival"
    STEP_CEILING = "step_ceiling"
    TECHNICAL = "technical"
    TAMPER = "tamper"
    STOPPED = "stopped"


@dataclass(frozen=True, slots=True)
class Action:
    """Validated MOVE, STAY, or BARRIER command."""

    action_type: ActionType
    direction: Direction | None = None
    target: Position | None = None

    def __post_init__(self) -> None:
        """Reject ambiguous or combined action fields."""
        if not isinstance(self.action_type, ActionType):
            raise TypeError("action_type must be an ActionType")
        if self.direction is not None and not isinstance(self.direction, Direction):
            raise TypeError("direction must be a Direction")
        if self.target is not None and not isinstance(self.target, Position):
            raise TypeError("target must be a Position")
        valid = {
            ActionType.MOVE: self.direction is not None and self.target is None,
            ActionType.STAY: self.direction is None and self.target is None,
            ActionType.BARRIER: self.direction is None and self.target is not None,
        }
        if not valid[self.action_type]:
            raise ValueError(f"invalid fields for {self.action_type.value} action")

    @classmethod
    def move(cls, direction: Direction) -> "Action":
        """Create one orthogonal move action."""
        return cls(ActionType.MOVE, direction=direction)

    @classmethod
    def stay(cls) -> "Action":
        """Create the no-movement action."""
        return cls(ActionType.STAY)

    @classmethod
    def barrier(cls, target: Position) -> "Action":
        """Create one exact public barrier action."""
        return cls(ActionType.BARRIER, target=target)

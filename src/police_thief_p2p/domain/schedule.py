"""Balanced deterministic role assignment for a six-sub-game series."""

from dataclasses import dataclass

from police_thief_p2p.domain.values import Role
from police_thief_p2p.shared.identifiers import GroupId, SubGameNumber


@dataclass(frozen=True, slots=True)
class RoleAssignment:
    """One sub-game's group-to-role assignment."""

    sub_game_number: SubGameNumber
    police_group: str
    thief_group: str

    def __post_init__(self) -> None:
        """Validate distinct safe group identities."""
        if not isinstance(self.sub_game_number, SubGameNumber):
            raise TypeError("sub_game_number must be a SubGameNumber")
        GroupId(self.police_group)
        GroupId(self.thief_group)
        if self.police_group == self.thief_group:
            raise ValueError("role assignment requires two distinct groups")

    def role_for(self, group_id: str) -> Role:
        """Return a participating group's role."""
        if group_id == self.police_group:
            return Role.POLICE
        if group_id == self.thief_group:
            return Role.THIEF
        raise KeyError(f"group {group_id!r} is not in this assignment")


def balanced_schedule(
    initiating_group: str,
    opponent_group: str,
    *,
    num_games: int = 6,
) -> tuple[RoleAssignment, ...]:
    """Return the signed default P,T,P,T,P,T initiating-group schedule."""
    GroupId(initiating_group)
    GroupId(opponent_group)
    if initiating_group == opponent_group:
        raise ValueError("schedule requires two distinct groups")
    if num_games != 6:
        raise ValueError("balanced M3 schedule requires exactly six sub-games")
    return tuple(
        RoleAssignment(
            sub_game_number=SubGameNumber(number),
            police_group=initiating_group if number % 2 else opponent_group,
            thief_group=opponent_group if number % 2 else initiating_group,
        )
        for number in range(1, num_games + 1)
    )

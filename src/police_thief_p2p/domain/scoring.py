"""Fixed sub-game scoring and group-identity series aggregation."""

from dataclasses import InitVar, dataclass, field
from typing import Final

from police_thief_p2p.domain.values import Role, TerminalReason
from police_thief_p2p.shared.config_sections import ScoringConfig
from police_thief_p2p.shared.identifiers import GroupId, SubGameNumber

_SERIES_TIE_SCORE: Final = 2


@dataclass(frozen=True, slots=True)
class RolePoints:
    """Points awarded to the Police and Thief roles for one outcome."""

    police: int
    thief: int

    def __post_init__(self) -> None:
        """Reject booleans, non-integers, and negative points."""
        if not all(type(value) is int for value in (self.police, self.thief)):
            raise TypeError("role points must be integers")
        if self.police < 0 or self.thief < 0:
            raise ValueError("role points must be non-negative")

    def for_role(self, role: Role) -> int:
        """Return the points awarded to one role."""
        if not isinstance(role, Role):
            raise TypeError("role must be a Role")
        return self.police if role is Role.POLICE else self.thief


def score_terminal(reason: TerminalReason, scoring: ScoringConfig) -> RolePoints:
    """Map one typed terminal reason to the immutable Appendix F score."""
    if not isinstance(reason, TerminalReason):
        raise TypeError("reason must be a TerminalReason")
    if not isinstance(scoring, ScoringConfig):
        raise TypeError("scoring must be a ScoringConfig")
    if reason in {
        TerminalReason.CAPTURE,
        TerminalReason.BARRIER_CAPTURE,
        TerminalReason.ENCLOSURE,
    }:
        return RolePoints(scoring.capture_cop, scoring.capture_thief)
    if reason in {TerminalReason.SURVIVAL, TerminalReason.STEP_CEILING}:
        return RolePoints(scoring.survival_cop, scoring.survival_thief)
    return RolePoints(0, 0)


def series_tie_awards(total_a: int, total_b: int) -> tuple[int, int]:
    """Return fixed equal-series awards, or zero awards for unequal totals."""
    if min(total_a, total_b) < 0:
        raise ValueError("series totals must be non-negative")
    return (_SERIES_TIE_SCORE, _SERIES_TIE_SCORE) if total_a == total_b else (0, 0)


@dataclass(frozen=True, slots=True)
class SubGameOutcome:
    """Verified terminal outcome retaining group identity across role changes."""

    sub_game_number: SubGameNumber
    police_group: str
    thief_group: str
    reason: TerminalReason
    scoring: InitVar[ScoringConfig]
    points: RolePoints = field(init=False)

    def __post_init__(self, scoring: ScoringConfig) -> None:
        """Validate groups and derive unforgeable points from the fixed score."""
        if not isinstance(self.sub_game_number, SubGameNumber):
            raise TypeError("sub_game_number must be a SubGameNumber")
        if not isinstance(self.reason, TerminalReason):
            raise TypeError("reason must be a TerminalReason")
        GroupId(self.police_group)
        GroupId(self.thief_group)
        if self.police_group == self.thief_group:
            raise ValueError("outcome requires two distinct groups")
        object.__setattr__(self, "points", score_terminal(self.reason, scoring))

    @classmethod
    def from_terminal(
        cls,
        sub_game_number: int,
        police_group: str,
        thief_group: str,
        reason: TerminalReason,
        scoring: ScoringConfig,
    ) -> "SubGameOutcome":
        """Create a scored outcome from one verified terminal reason."""
        return cls(
            SubGameNumber(sub_game_number),
            police_group,
            thief_group,
            reason,
            scoring,
        )


@dataclass(frozen=True, slots=True)
class GroupTotal:
    """One immutable group total."""

    group_id: str
    points: int

    def __post_init__(self) -> None:
        """Validate group identity and non-negative integer points."""
        GroupId(self.group_id)
        if isinstance(self.points, bool) or not isinstance(self.points, int):
            raise TypeError("group points must be an integer")
        if self.points < 0:
            raise ValueError("group points must be non-negative")


@dataclass(frozen=True, slots=True)
class SeriesScore:
    """Raw totals, tie awards, and winner for a complete six-game series."""

    totals: tuple[GroupTotal, GroupTotal]
    tie_awards: tuple[GroupTotal, GroupTotal]
    winner: str | None

    def __post_init__(self) -> None:
        """Ensure total/award identities align and winner participates."""
        total_groups = tuple(item.group_id for item in self.totals)
        award_groups = tuple(item.group_id for item in self.tie_awards)
        if len(set(total_groups)) != 2 or award_groups != total_groups:
            raise ValueError("series total and tie-award groups must align")
        if self.winner is not None and self.winner not in total_groups:
            raise ValueError("series winner must be a participating group")

    def total_for(self, group_id: str) -> int:
        """Return one participating group's raw total."""
        for total in self.totals:
            if total.group_id == group_id:
                return total.points
        raise KeyError(f"group {group_id!r} is not in this series")

    def tie_award_for(self, group_id: str) -> int:
        """Return one participating group's fixed tie award."""
        for award in self.tie_awards:
            if award.group_id == group_id:
                return award.points
        raise KeyError(f"group {group_id!r} is not in this series")


def aggregate_series(
    outcomes: tuple[SubGameOutcome, ...],
    group_a: str,
    group_b: str,
) -> SeriesScore:
    """Aggregate exactly six balanced outcomes by group rather than current role."""
    GroupId(group_a)
    GroupId(group_b)
    if group_a == group_b:
        raise ValueError("series requires two distinct groups")
    numbers = {int(outcome.sub_game_number) for outcome in outcomes}
    if len(outcomes) != 6 or numbers != set(range(1, 7)):
        raise ValueError("series requires sub-games 1 through 6 exactly once")
    groups = {group_a, group_b}
    if any({outcome.police_group, outcome.thief_group} != groups for outcome in outcomes):
        raise ValueError("outcome contains a group outside the series")
    police_counts = {
        group: sum(outcome.police_group == group for outcome in outcomes) for group in groups
    }
    if set(police_counts.values()) != {3}:
        raise ValueError("each group must play Police exactly three times")
    totals = {group_a: 0, group_b: 0}
    for outcome in outcomes:
        totals[outcome.police_group] += outcome.points.police
        totals[outcome.thief_group] += outcome.points.thief
    award_a, award_b = series_tie_awards(totals[group_a], totals[group_b])
    winner = None if totals[group_a] == totals[group_b] else max(totals, key=totals.__getitem__)
    return SeriesScore(
        totals=(GroupTotal(group_a, totals[group_a]), GroupTotal(group_b, totals[group_b])),
        tie_awards=(GroupTotal(group_a, award_a), GroupTotal(group_b, award_b)),
        winner=winner,
    )

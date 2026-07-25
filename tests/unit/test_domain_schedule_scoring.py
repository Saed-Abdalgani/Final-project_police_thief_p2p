import pytest

from police_thief_p2p.domain import (
    Role,
    RoleAssignment,
    RolePoints,
    SeriesScore,
    SubGameOutcome,
    TerminalReason,
    aggregate_series,
    balanced_schedule,
    score_terminal,
    series_tie_awards,
)
from police_thief_p2p.domain.scoring import GroupTotal
from police_thief_p2p.shared.config_models import SharedConfig
from police_thief_p2p.shared.identifiers import SubGameNumber

GROUP_A = "ATEAM001"
GROUP_B = "BTEAM002"


def test_balanced_schedule_alternates_and_assigns_three_each() -> None:
    schedule = balanced_schedule(GROUP_A, GROUP_B)
    assert tuple(int(item.sub_game_number) for item in schedule) == tuple(range(1, 7))
    assert tuple(item.role_for(GROUP_A) for item in schedule) == (
        Role.POLICE,
        Role.THIEF,
        Role.POLICE,
        Role.THIEF,
        Role.POLICE,
        Role.THIEF,
    )
    assert sum(item.role_for(GROUP_B) is Role.POLICE for item in schedule) == 3
    with pytest.raises(KeyError, match="not in"):
        schedule[0].role_for("OTHER001")


def test_schedule_and_assignment_reject_invalid_groups_or_count() -> None:
    with pytest.raises(ValueError, match="distinct"):
        balanced_schedule(GROUP_A, GROUP_A)
    with pytest.raises(ValueError, match="six"):
        balanced_schedule(GROUP_A, GROUP_B, num_games=4)
    with pytest.raises(ValueError, match="distinct"):
        RoleAssignment(SubGameNumber(1), GROUP_A, GROUP_A)
    with pytest.raises(ValueError, match="safe ASCII"):
        balanced_schedule("../bad", GROUP_B)
    with pytest.raises(TypeError, match="SubGameNumber"):
        RoleAssignment(1, GROUP_A, GROUP_B)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("reason", "expected"),
    [
        (TerminalReason.CAPTURE, RolePoints(20, 5)),
        (TerminalReason.BARRIER_CAPTURE, RolePoints(20, 5)),
        (TerminalReason.ENCLOSURE, RolePoints(20, 5)),
        (TerminalReason.SURVIVAL, RolePoints(5, 10)),
        (TerminalReason.STEP_CEILING, RolePoints(5, 10)),
        (TerminalReason.TECHNICAL, RolePoints(0, 0)),
        (TerminalReason.TAMPER, RolePoints(0, 0)),
        (TerminalReason.STOPPED, RolePoints(0, 0)),
    ],
)
def test_every_terminal_reason_has_fixed_score(
    shared_config: SharedConfig,
    reason: TerminalReason,
    expected: RolePoints,
) -> None:
    actual = score_terminal(reason, shared_config.scoring)
    assert actual == expected
    assert actual.for_role(Role.POLICE) == expected.police
    assert actual.for_role(Role.THIEF) == expected.thief


def test_technical_and_tamper_remain_distinct_zero_outcomes(
    shared_config: SharedConfig,
) -> None:
    assert {
        TerminalReason.TECHNICAL,
        TerminalReason.TAMPER,
    }.issubset(set(TerminalReason))
    assert score_terminal(TerminalReason.TECHNICAL, shared_config.scoring) == RolePoints(0, 0)
    assert score_terminal(TerminalReason.TAMPER, shared_config.scoring) == RolePoints(0, 0)


def test_role_points_and_tie_awards_validate_boundaries() -> None:
    with pytest.raises(TypeError, match="integers"):
        RolePoints(True, 0)
    with pytest.raises(ValueError, match="non-negative"):
        RolePoints(-1, 0)
    with pytest.raises(TypeError, match="Role"):
        RolePoints(20, 5).for_role("police")  # type: ignore[arg-type]
    assert series_tie_awards(50, 50) == (2, 2)
    assert series_tie_awards(51, 50) == (0, 0)
    with pytest.raises(ValueError, match="non-negative"):
        series_tie_awards(-1, 0)


def test_scoring_and_outcome_runtime_types_fail_closed(
    shared_config: SharedConfig,
) -> None:
    with pytest.raises(TypeError, match="TerminalReason"):
        score_terminal("capture", shared_config.scoring)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="SubGameNumber"):
        SubGameOutcome(
            1,  # type: ignore[arg-type]
            GROUP_A,
            GROUP_B,
            TerminalReason.CAPTURE,
            shared_config.scoring,
        )
    with pytest.raises(TypeError, match="reason"):
        SubGameOutcome(
            SubGameNumber(1),
            GROUP_A,
            GROUP_B,
            "capture",  # type: ignore[arg-type]
            shared_config.scoring,
        )
    with pytest.raises(TypeError, match="ScoringConfig"):
        SubGameOutcome(
            SubGameNumber(1),
            GROUP_A,
            GROUP_B,
            TerminalReason.CAPTURE,
            (20, 5),  # type: ignore[arg-type]
        )


def _outcomes(
    shared_config: SharedConfig,
    reasons: tuple[TerminalReason, ...],
) -> tuple[SubGameOutcome, ...]:
    return tuple(
        SubGameOutcome.from_terminal(
            int(assignment.sub_game_number),
            assignment.police_group,
            assignment.thief_group,
            reason,
            shared_config.scoring,
        )
        for assignment, reason in zip(balanced_schedule(GROUP_A, GROUP_B), reasons, strict=True)
    )


def test_series_aggregation_tracks_group_identity_across_role_changes(
    shared_config: SharedConfig,
) -> None:
    outcomes = _outcomes(
        shared_config,
        (
            TerminalReason.CAPTURE,
            TerminalReason.SURVIVAL,
            TerminalReason.CAPTURE,
            TerminalReason.SURVIVAL,
            TerminalReason.CAPTURE,
            TerminalReason.SURVIVAL,
        ),
    )
    score = aggregate_series(outcomes, GROUP_A, GROUP_B)
    assert score.total_for(GROUP_A) == 90
    assert score.total_for(GROUP_B) == 30
    assert score.tie_award_for(GROUP_A) == 0
    assert score.winner == GROUP_A
    with pytest.raises(KeyError, match="not in"):
        score.total_for("OTHER001")
    with pytest.raises(KeyError, match="not in"):
        score.tie_award_for("OTHER001")


def test_equal_balanced_series_awards_fixed_tie_score(
    shared_config: SharedConfig,
) -> None:
    outcomes = _outcomes(shared_config, (TerminalReason.CAPTURE,) * 6)
    score = aggregate_series(outcomes, GROUP_A, GROUP_B)
    assert score.total_for(GROUP_A) == score.total_for(GROUP_B) == 75
    assert score.tie_award_for(GROUP_A) == score.tie_award_for(GROUP_B) == 2
    assert score.winner is None


def test_outcome_and_series_validation_fail_closed(shared_config: SharedConfig) -> None:
    with pytest.raises(ValueError, match="distinct"):
        SubGameOutcome.from_terminal(
            1,
            GROUP_A,
            GROUP_A,
            TerminalReason.CAPTURE,
            shared_config.scoring,
        )
    good = _outcomes(shared_config, (TerminalReason.CAPTURE,) * 6)
    with pytest.raises(ValueError, match="1 through 6"):
        aggregate_series(good[:-1], GROUP_A, GROUP_B)
    duplicate = (*good[:-1], good[0])
    with pytest.raises(ValueError, match="1 through 6"):
        aggregate_series(duplicate, GROUP_A, GROUP_B)

    outsider = SubGameOutcome.from_terminal(
        1, "OTHER001", GROUP_B, TerminalReason.CAPTURE, shared_config.scoring
    )
    with pytest.raises(ValueError, match="outside"):
        aggregate_series((outsider, *good[1:]), GROUP_A, GROUP_B)

    unbalanced = tuple(
        SubGameOutcome.from_terminal(
            number,
            GROUP_A,
            GROUP_B,
            TerminalReason.CAPTURE,
            shared_config.scoring,
        )
        for number in range(1, 7)
    )
    with pytest.raises(ValueError, match="three times"):
        aggregate_series(unbalanced, GROUP_A, GROUP_B)
    with pytest.raises(ValueError, match="distinct"):
        aggregate_series(good, GROUP_A, GROUP_A)


def test_group_total_and_series_score_validate_public_construction() -> None:
    with pytest.raises(TypeError, match="integer"):
        GroupTotal(GROUP_A, True)
    with pytest.raises(ValueError, match="non-negative"):
        GroupTotal(GROUP_A, -1)
    totals = (GroupTotal(GROUP_A, 10), GroupTotal(GROUP_B, 5))
    with pytest.raises(ValueError, match="align"):
        SeriesScore(totals, (GroupTotal(GROUP_B, 0), GroupTotal(GROUP_A, 0)), GROUP_A)
    with pytest.raises(ValueError, match="winner"):
        SeriesScore(
            totals,
            (GroupTotal(GROUP_A, 0), GroupTotal(GROUP_B, 0)),
            "OTHER001",
        )

import uuid

import pytest

from police_thief_p2p.shared.identifiers import (
    MAX_COUNTER,
    CorrelationId,
    GameId,
    GameUid,
    GroupId,
    MessageId,
    StepNumber,
    SubGameNumber,
)


def test_group_ids_support_development_and_exact_submission_modes() -> None:
    assert str(GroupId("team_alpha-1")) == "team_alpha-1"
    assert str(GroupId("ABC12345", submission_mode=True)) == "ABC12345"
    for value in ("short", "ABC_2345", "123456789"):
        with pytest.raises(ValueError, match="eight ASCII"):
            GroupId(value, submission_mode=True)


@pytest.mark.parametrize("value", ["../team", "team.", "_team", "téam", "", "a" * 65])
def test_group_id_rejects_unsafe_values(value: str) -> None:
    with pytest.raises(ValueError, match="safe ASCII"):
        GroupId(value)


def test_game_id_is_a_bounded_ascii_slug() -> None:
    assert str(GameId("series-2026")) == "series-2026"
    for value in ("../series", "Series", "\u0455eries", "-series", "series-", "a" * 65):
        with pytest.raises(ValueError, match="lowercase ASCII slug"):
            GameId(value)


@pytest.mark.parametrize("identifier_type", [GameUid, MessageId, CorrelationId])
def test_uuid_identifiers_parse_generate_and_render(
    identifier_type: type[GameUid] | type[MessageId] | type[CorrelationId],
) -> None:
    value = "12345678-1234-4234-8234-123456789abc"
    assert str(identifier_type(value)) == value
    assert str(identifier_type(uuid.UUID(value))) == value
    assert identifier_type.generate().value.version == 4
    with pytest.raises(ValueError, match="valid UUID"):
        identifier_type("not-a-uuid")


@pytest.mark.parametrize("counter_type", [SubGameNumber, StepNumber])
def test_positive_protocol_counters_reject_boundaries(
    counter_type: type[SubGameNumber] | type[StepNumber],
) -> None:
    assert int(counter_type(1)) == 1
    assert int(counter_type(MAX_COUNTER)) == MAX_COUNTER
    for value in (0, -1, MAX_COUNTER + 1):
        with pytest.raises(ValueError, match="between"):
            counter_type(value)
    for invalid_value in (True, 1.0):
        with pytest.raises(TypeError, match="integer"):
            counter_type(invalid_value)  # type: ignore[arg-type]

"""Capture A/B/C and delivery contract tests for amireman adapter."""

from __future__ import annotations

import pytest

from police_thief_p2p.adapters.amireman.capture import evaluate_thief_caught
from police_thief_p2p.adapters.amireman.delivery import EquivocationError, Inbox


def test_claim_colocation_captures() -> None:
    assert evaluate_thief_caught(
        thief=(3, 3),
        claim=[3, 3],
        barrier=None,
        barriers=set(),
        size=7,
    )


def test_barrier_on_thief_captures() -> None:
    assert evaluate_thief_caught(
        thief=(2, 2),
        claim=[0, 0],
        barrier=[2, 2],
        barriers={(2, 2)},
        size=7,
    )


def test_enclosure_captures() -> None:
    barriers = {(0, 1), (1, 0), (1, 2), (2, 1)}
    assert evaluate_thief_caught(
        thief=(1, 1),
        claim=[0, 0],
        barrier=[2, 1],
        barriers=barriers,
        size=7,
    )


def test_missed_claim_is_false() -> None:
    assert not evaluate_thief_caught(
        thief=(3, 3),
        claim=[0, 0],
        barrier=None,
        barriers=set(),
        size=7,
    )


def test_enclosed_thief_self_reports_capture_win_claim() -> None:
    from police_thief_p2p.adapters.amireman.engine import SubEngine
    from police_thief_p2p.adapters.amireman.terms import default_terms

    engine = SubEngine("thief", default_terms(), "saedshki", "c" * 40, 1)
    engine.half.pos = (1, 1)
    engine.half.barriers = {(0, 1), (1, 0), (1, 2), (2, 1)}
    assert engine.half.enclosed() is True
    message = engine.report_enclosure()
    assert message.win_claim == {"type": "capture"}
    assert message.capture_claim is None


def test_police_honors_thief_enclosure_win_claim() -> None:
    from police_thief_p2p.adapters.amireman.engine import SubEngine
    from police_thief_p2p.adapters.amireman.terms import default_terms
    from police_thief_p2p.adapters.amireman.wire import TurnMessage

    engine = SubEngine("police", default_terms(), "saedshki", "c" * 40, 1)
    incoming = TurnMessage(
        step=4,
        sender="thief",
        commit="a" * 64,
        hint="",
        win_claim={"type": "enclosure"},
    )
    outcome = engine.receive(incoming)
    assert outcome.i_won is True
    assert outcome.opponent_won is False


def test_police_step_35_announces_survival() -> None:
    from police_thief_p2p.adapters.amireman.engine import SubEngine
    from police_thief_p2p.adapters.amireman.terms import default_terms

    engine = SubEngine("police", default_terms(), "saedshki", "c" * 40, 1)
    engine.half.step = 34
    message = engine.take_turn()
    assert message.step == 35
    assert message.win_claim == {"type": "survival"}


def test_inbox_exactly_once_and_equivocation() -> None:
    inbox = Inbox(window=4)
    first = {"step": 1, "commit": "aaa", "sender": "thief"}
    assert len(inbox.offer(first)) == 1
    assert inbox.offer(first) == []
    with pytest.raises(EquivocationError):
        inbox.offer({"step": 1, "commit": "bbb", "sender": "thief"})

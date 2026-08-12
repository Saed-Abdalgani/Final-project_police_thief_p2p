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


def test_inbox_exactly_once_and_equivocation() -> None:
    inbox = Inbox(window=4)
    first = {"step": 1, "commit": "aaa", "sender": "thief"}
    assert len(inbox.offer(first)) == 1
    assert inbox.offer(first) == []
    with pytest.raises(EquivocationError):
        inbox.offer({"step": 1, "commit": "bbb", "sender": "thief"})

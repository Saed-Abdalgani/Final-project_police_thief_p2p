from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from police_thief_p2p import SimulationSdk
from police_thief_p2p.adapters.amireman.artifacts import emit_training_sidecar
from police_thief_p2p.adapters.amireman.cli import build_parser
from police_thief_p2p.adapters.amireman.scent import decay_only, step_update
from police_thief_p2p.adapters.amireman.strategy import build_payload
from police_thief_p2p.adapters.amireman.terms import default_terms
from police_thief_p2p.sdk import (
    CompatibilityDecision,
    CompatibilityStrategyMetrics,
    CompatibilityStrategySession,
    CompatibilityTurnObservation,
    OpponentFingerprint,
)
from police_thief_p2p.services.experiments.compatibility_arena import CompatibilityArena
from police_thief_p2p.services.strategy.compatibility import CompatibilityStrategyProfile


def _session(
    role: str = "police", seed: int = 7, model: str = "multiplicative_kernel_v1"
) -> CompatibilityStrategySession:
    session = SimulationSdk().create_compatibility_strategy(
        default_terms(), None, "fixture", seed, scent_model=model
    )
    session.start_subgame(role, 1, scent_model=model)
    return session


def test_public_compatibility_dtos_validate_and_normalize() -> None:
    observation = CompatibilityTurnObservation(1, {(0, 0): 0.9})
    assert observation.scent[(0, 0)] == 0.9
    fingerprint = OpponentFingerprint({"cycle": 2.0, "random": 1.0})
    assert sum(fingerprint.probabilities.values()) == pytest.approx(1.0)
    metrics = CompatibilityStrategyMetrics(64, 0.5, 0.4, "cycle", 3, 2.0, "test")
    decision = CompatibilityDecision("N", None, "north district", "lie", metrics)
    assert decision.intent == "lie"
    with pytest.raises(ValueError, match="move"):
        CompatibilityDecision("JUMP", None, "", "truth", metrics)


@pytest.mark.parametrize("model", [("multiplicative_kernel_v1",), ("subtractive_chebyshev_v1",)])
def test_particles_use_pre_emission_scent_timing_and_normalize(model: str) -> None:
    terms = default_terms()
    session = _session(model=model)
    start = (3, 3)
    initial = step_update({}, start, 7, 0.1, model)
    served = decay_only(initial, 0.1, model)
    session.observe(CompatibilityTurnObservation(1, served))
    assert sum(session.particle_weights) == pytest.approx(1.0)
    assert 1 <= len(session.particle_weights) <= 64
    assert terms["thief_start"] == [3, 3]


def test_exact_claim_collapses_posterior_and_barrier_masks_particles() -> None:
    thief = _session(role="thief")
    cop_scent = decay_only(step_update({}, (0, 0), 7, 0.1), 0.1)
    thief.observe(
        CompatibilityTurnObservation(
            1,
            cop_scent,
            capture_claim=(0, 1),
            barrier_placed=(1, 0),
        )
    )
    assert (1, 0) not in thief.particle_positions
    decision = thief.decide(position=(3, 3), barriers={(1, 0)}, step=1)
    assert decision.move in {"N", "S", "E", "W", "STAY"}
    assert decision.barrier is None
    assert decision.metrics.posterior_peak == pytest.approx(1.0)


def test_secret_seed_reproduces_mixed_safe_actions_and_hints() -> None:
    left = _session(role="thief", seed=91)
    right = _session(role="thief", seed=91)
    first = left.decide(position=(3, 3), step=1)
    second = right.decide(position=(3, 3), step=1)
    assert (first.move, first.barrier, first.hint, first.intent) == (
        second.move,
        second.barrier,
        second.hint,
        second.intent,
    )


def test_audited_learning_rejects_unverified_records() -> None:
    session = _session()
    records = [
        {
            "payload": {
                "step": step,
                "state": f"grid=7;self={[3, 3 + (step % 2)]}",
                "move": "E" if step % 2 else "W",
                "hint": "east district",
                "intent": "truth",
                "barrier_placed": [2, 2],
            }
        }
        for step in range(1, 5)
    ]
    before = session.fingerprint
    rejected = session.complete_audited_subgame(records, audit_passed=False)
    assert rejected.audited_subgames == before.audited_subgames == 0
    learned = session.complete_audited_subgame(records, audit_passed=True)
    assert learned.audited_subgames == 1
    assert learned.observed_actions == 3
    assert learned.probabilities["aggressive-barrier"] > before.probabilities["aggressive-barrier"]


def test_deceptive_hint_is_labeled_lie_in_sealed_payload() -> None:
    session = _session()
    decision = session.decide(position=(0, 0), step=1)
    assert len(decision.hint.split()) <= 15
    payload = build_payload(
        1,
        "police",
        "grid=7;self=[1,0]",
        decision.move,
        decision.hint,
        intent=decision.intent,
    )
    assert payload["intent"] == decision.intent
    assert payload["intent"] == "lie"


def test_lie_cadence_forces_a_truthful_hint_and_avoids_coordinates() -> None:
    session = _session()
    decisions = [session.decide(position=(0, index), step=index + 1) for index in range(3)]
    assert [decision.intent for decision in decisions] == ["lie", "lie", "truth"]
    assert all("[" not in decision.hint and "," not in decision.hint for decision in decisions)


def test_cli_omitted_seed_is_private_and_explicit_seed_is_deterministic(tmp_path: Path) -> None:
    parser = build_parser()
    common = ["friendly", "--peer", "http://peer/mcp", "--role", "police", "--out"]
    generated = parser.parse_args([*common, str(tmp_path)])
    explicit = parser.parse_args([*common, str(tmp_path), "--seed", "42"])
    assert generated.seed is None
    assert explicit.seed == 42


@pytest.mark.parametrize("model", [("multiplicative_kernel_v1",), ("subtractive_chebyshev_v1",)])
def test_recovery_arena_has_legal_capture_and_survival_paths(model: str) -> None:
    arena = CompatibilityArena(
        default_terms(), CompatibilityStrategyProfile(particle_count=32), scent_model=model
    )
    police = arena.play("smngrp05", "police", 1)
    thief = arena.play("ahk-yosi", "thief", 1)
    assert police.outcome in {"capture", "survival"}
    assert thief.outcome in {"capture", "survival"}
    assert police.illegal_actions == thief.illegal_actions == 0
    assert police.audit_failures == thief.audit_failures == 0
    assert max((*police.decision_latencies_ms, *thief.decision_latencies_ms)) <= 250.0


def test_training_sidecar_is_separate_from_official_artifacts(tmp_path: Path) -> None:
    series = SimpleNamespace(
        game_id="fixture-vs-team",
        game_uid="uid",
        training_records=[{"sub_game_number": 1, "peer_records": []}],
    )
    path = emit_training_sidecar(tmp_path, series, {"strategy_seed": 123})
    document = json.loads(path.read_text(encoding="utf-8"))
    assert path.name == "training_fixture-vs-team.json"
    assert document["strategy"]["strategy_seed"] == 123
    assert not list(tmp_path.glob("result_*.json"))

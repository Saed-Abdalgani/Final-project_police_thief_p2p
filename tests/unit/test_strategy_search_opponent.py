from dataclasses import dataclass
from pathlib import Path

import pytest

from police_thief_p2p.adapters.persistence.atomic_files import AtomicFileRepository
from police_thief_p2p.adapters.system.clocks import FakeClock
from police_thief_p2p.adapters.system.deterministic_random import DeterministicRandomSource
from police_thief_p2p.domain import Action, ActionType, Direction, Role
from police_thief_p2p.services.strategy.contracts import HintVerdict, ScoreBreakdown
from police_thief_p2p.services.strategy.opponent import (
    ObservationSource,
    OpponentObservation,
    OpponentProfile,
)
from police_thief_p2p.services.strategy.opponent_motion import sample_legal_target
from police_thief_p2p.services.strategy.opponent_store import OpponentProfileStore
from police_thief_p2p.services.strategy.search import (
    BoundedTranspositionCache,
    cvar,
    iterative_search,
    stratified_samples,
)
from police_thief_p2p.services.strategy.search_state import SearchState
from police_thief_p2p.shared.config_models import SharedConfig
from tests.helpers.strategy import request_for


def test_bounded_cache_hits_and_evicts_lru_deterministically() -> None:
    cache: BoundedTranspositionCache[str, int] = BoundedTranspositionCache(2)
    assert cache.get_or_compute("a", lambda: 1) == 1
    cache.get_or_compute("b", lambda: 2)
    assert cache.get_or_compute("a", lambda: 9) == 1
    cache.get_or_compute("c", lambda: 3)
    assert cache.keys() == ("a", "c")
    assert cache.hits == 1
    with pytest.raises(ValueError, match="positive"):
        BoundedTranspositionCache(0)


def test_stratified_sampling_repeatability_distribution_and_cvar(
    shared_config: SharedConfig,
) -> None:
    request = request_for(shared_config, Role.POLICE)
    first = stratified_samples(request.belief, 49, DeterministicRandomSource(11))
    second = stratified_samples(request.belief, 49, DeterministicRandomSource(11))
    assert first == second
    assert len(first) == 49
    assert sum(weight for _, weight in first) == pytest.approx(1)
    assert cvar((10, -4, 2, 8), 0.5) == -1
    with pytest.raises(ValueError, match="CVaR"):
        cvar((), 0.5)


def test_iterative_search_preserves_last_completed_depth(
    shared_config: SharedConfig,
) -> None:
    request = request_for(shared_config, Role.THIEF)
    samples = stratified_samples(request.belief, 4, request.rng)
    state = SearchState(
        request.state.position,
        request.state.public_barriers,
        samples,
        Role.THIEF,
        0,
        3,
        (),
        7,
    )
    clock = FakeClock()

    @dataclass
    class Evaluator:
        def evaluate(
            self,
            _state: SearchState,
            action: Action,
            depth: int,
        ) -> tuple[ScoreBreakdown, tuple[float, ...]]:
            if depth == 2:
                clock.advance(2)
            value = 2.0 if action == Action.stay() else 1.0
            return ScoreBreakdown((("VALUE", value),), value), (value,)

    result = iterative_search(
        state,
        (Action.stay(), Action.move(Direction.NORTH)),
        Evaluator(),
        clock=clock,
        deadline=1,
        cache_entries=4,
        risk_weight=0.5,
    )
    assert result.action == Action.stay()
    assert result.completed_depth == 1


def test_opponent_profile_decay_privacy_and_persistence_isolation(
    tmp_path: Path,
) -> None:
    profile = OpponentProfile("GRP00002", "v1")
    public = OpponentObservation(
        ObservationSource.PUBLIC_REVEAL,
        Direction.NORTH,
        ActionType.MOVE,
        1,
        hint_verdict=HintVerdict.TRUTH,
    )
    updated = profile.update(public, 0.8)
    assert updated.observations == 1
    assert sum(updated.summary().mixture) == pytest.approx(1)
    assert updated.summary().hint_trust > 0.5
    with pytest.raises(ValueError, match="hidden"):
        OpponentObservation(ObservationSource.HIDDEN_REPLAY, Direction.SOUTH, ActionType.MOVE, 2)
    with pytest.raises(ValueError, match="live"):
        OpponentObservation(
            ObservationSource.PUBLIC_REVEAL,
            Direction.SOUTH,
            ActionType.MOVE,
            2,
            on_boundary=True,
        )
    store = OpponentProfileStore(AtomicFileRepository(tmp_path))
    store.save_audited(updated)
    assert store.load("GRP00002", "v1") == updated
    assert store.load("GRP00003", "v1").observations == 0


def test_learned_motion_sampler_enforces_legal_targets(
    shared_config: SharedConfig,
) -> None:
    request = request_for(shared_config, Role.POLICE)
    board = request.state.rules.board
    source = request.state.position
    for seed in range(20):
        target = sample_legal_target(
            board,
            source,
            request.state.public_barriers,
            source,
            request.opponent.mixture,
            DeterministicRandomSource(seed),
        )
        assert target in (*board.neighbors(source), source)
    with pytest.raises(ValueError, match="normalized"):
        sample_legal_target(
            board,
            source,
            request.state.public_barriers,
            source,
            (1, 0, 0, 0, 1),
            DeterministicRandomSource(1),
        )

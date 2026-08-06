import pytest

from police_thief_p2p.adapters.system.clocks import SystemClock
from police_thief_p2p.adapters.system.deterministic_random import DeterministicRandomSource
from police_thief_p2p.domain import (
    Action,
    Position,
    Role,
    TerminalReason,
    initial_local_state,
    transition,
)
from police_thief_p2p.services.belief.models import OpponentScentFrame
from police_thief_p2p.services.experiments.arena import MatchArena
from police_thief_p2p.services.experiments.belief_track import (
    BeliefProfile,
    BeliefTrack,
    MatchScent,
)
from police_thief_p2p.services.experiments.fixtures import fixtures_for
from police_thief_p2p.services.experiments.observation import ObservationChannel
from police_thief_p2p.services.experiments.pairing import MatchBrains, PairResolver
from police_thief_p2p.services.experiments.runner import ExperimentRunner
from police_thief_p2p.services.experiments.spec import TournamentSpec
from police_thief_p2p.services.strategy.contracts import HintIntent, HintVerdict
from police_thief_p2p.services.strategy.hints import (
    opposite_region,
    realize_hint,
    semantic_region,
)
from police_thief_p2p.services.strategy.random_policy import (
    RandomLegalPoliceBrain,
    RandomLegalThiefBrain,
)
from police_thief_p2p.services.strategy.reference import (
    ReferenceGreedyPoliceBrain,
    ReferenceGreedyThiefBrain,
)
from police_thief_p2p.shared.config_models import SharedConfig
from tests.helpers.strategy import strategy_config

pytestmark = pytest.mark.integration

FAST_BUDGET = 60


def _arena(shared: SharedConfig, belief: BeliefProfile | None = None) -> MatchArena:
    board = fixtures_for("train")[0].apply(shared)
    brains = MatchBrains(ReferenceGreedyPoliceBrain(), ReferenceGreedyThiefBrain())
    profile = strategy_config().model_copy(
        update={"decision_budget_ms": FAST_BUDGET, "guard_margin_ms": 10}
    )
    if belief is None:
        return MatchArena(board, profile, brains, SystemClock())
    return MatchArena(board, profile, brains, SystemClock(), None, belief)


def test_arena_reaches_a_verified_terminal_and_records_telemetry(
    shared_config: SharedConfig,
) -> None:
    outcome = _arena(shared_config).play(DeterministicRandomSource(4_242))
    assert outcome.reason in set(TerminalReason)
    assert outcome.completed_turns >= 1
    assert outcome.decisions == len(outcome.latencies_ms)
    assert outcome.invalid_actions == 0
    assert not outcome.failed
    assert outcome.captured or outcome.survived
    assert outcome.max_latency_ms > 0.0


def test_arena_replays_bit_identically_for_one_seed(shared_config: SharedConfig) -> None:
    first = _arena(shared_config).play(DeterministicRandomSource(99))
    second = _arena(shared_config).play(DeterministicRandomSource(99))
    assert (first.reason, first.completed_turns, first.decisions) == (
        second.reason,
        second.completed_turns,
        second.decisions,
    )


def test_seeded_policies_produce_seed_dependent_trajectories(
    shared_config: SharedConfig,
) -> None:
    board = fixtures_for("train")[0].apply(shared_config)
    profile = strategy_config().model_copy(
        update={"decision_budget_ms": FAST_BUDGET, "guard_margin_ms": 10}
    )
    brains = MatchBrains(RandomLegalPoliceBrain(), RandomLegalThiefBrain())
    outcomes = [
        MatchArena(board, profile, brains, SystemClock()).play(DeterministicRandomSource(seed))
        for seed in (1, 2, 3, 4, 5, 6)
    ]
    assert len({(item.reason, item.completed_turns) for item in outcomes}) > 1


def test_degraded_observation_never_breaks_the_referee(shared_config: SharedConfig) -> None:
    outcome = _arena(shared_config).play(
        DeterministicRandomSource(17), observation_delay=2, scent_dropout=0.75
    )
    assert outcome.reason in set(TerminalReason)
    assert outcome.invalid_actions == 0
    assert not outcome.failed


def test_belief_profile_is_threaded_into_the_offline_belief_track(
    shared_config: SharedConfig,
) -> None:
    left = BeliefTrack.create(shared_config, Role.POLICE, BeliefProfile())
    right = BeliefTrack.create(shared_config, Role.POLICE, BeliefProfile(prior_alpha=5.0))
    assert left.reliability.mean("region", 0) < right.reliability.mean("region", 0)
    outcome = _arena(shared_config, BeliefProfile(recency=0.75)).play(DeterministicRandomSource(11))
    assert outcome.decisions > 0


def _frame(shared: SharedConfig) -> OpponentScentFrame:
    state = initial_local_state(shared, Role.THIEF)
    return MatchScent().emit(transition(state, Action.stay()).state, Action.stay())


def test_observation_channel_delays_and_drops_deterministically(
    shared_config: SharedConfig,
) -> None:
    frame = _frame(shared_config)
    channel = ObservationChannel(DeterministicRandomSource(8), 1, 0.0)
    channel.submit(1, frame, "hint one")
    assert channel.due(1) == ()
    assert channel.pending == 1
    assert channel.due(2) == ((frame, "hint one"),)
    dropping = ObservationChannel(DeterministicRandomSource(8), 0, 1.0)
    dropping.submit(1, frame, "hint two")
    assert dropping.due(1) == ()
    with pytest.raises(ValueError, match="observation delay"):
        ObservationChannel(DeterministicRandomSource(1), 9, 0.0)


def test_hint_reliability_learns_from_verified_scent_evidence(
    shared_config: SharedConfig,
) -> None:
    frame = _frame(shared_config)
    track = BeliefTrack.create(shared_config, Role.POLICE)
    state = initial_local_state(shared_config, Role.POLICE)
    honest = semantic_region(
        Position(
            max(frame.cells, key=lambda cell: cell.decimal_value()).row,
            max(frame.cells, key=lambda cell: cell.decimal_value()).col,
        ),
        state.rules.board.size,
    )
    truthful = realize_hint(HintIntent(HintVerdict.TRUTH, honest), "area", 20)
    deceptive = realize_hint(HintIntent(HintVerdict.LIE, opposite_region(honest)), "area", 20)
    liar = BeliefTrack.create(shared_config, Role.POLICE)
    for _ in range(4):
        track.observe(
            frame,
            hint=truthful,
            own_position=state.position,
            barriers=state.public_barriers,
        )
        liar.observe(
            frame,
            hint=deceptive,
            own_position=state.position,
            barriers=state.public_barriers,
        )
    categories = {item.category for item in track.reliability.entries}
    assert categories
    step = frame.step_number
    assert max(track.reliability.mean(name, step) for name in categories) > max(
        liar.reliability.mean(name, step) for name in categories
    )


def test_pair_resolver_seats_each_brain_in_its_declared_role() -> None:
    brains = MatchBrains(RandomLegalPoliceBrain(), RandomLegalThiefBrain())
    resolver = PairResolver(brains)
    config = strategy_config()
    assert resolver.resolve(Role.POLICE, config).role is Role.POLICE
    assert resolver.resolve(Role.THIEF, config).role is Role.THIEF
    with pytest.raises(ValueError, match="matching roles"):
        MatchBrains(RandomLegalThiefBrain(), RandomLegalPoliceBrain())


def test_runner_produces_paired_role_swapped_matches_and_a_full_report(
    shared_config: SharedConfig,
) -> None:
    spec = TournamentSpec(
        campaign_id="test-runner",
        split="train",
        candidate_id="candidate-advanced",
        opponent_ids=("BL-RND",),
        fixtures=fixtures_for("train")[:1],
        seeds=(10_000,),
        decision_budget_ms=FAST_BUDGET,
    )
    runner = ExperimentRunner(
        base_config=shared_config,
        strategy=strategy_config(),
        clock=SystemClock(),
        random_factory=DeterministicRandomSource,
    )
    report = runner.run(spec)
    assert len(report.matches) == spec.match_count == 2
    assert {item.candidate_role for item in report.matches} == {Role.POLICE, Role.THIEF}
    assert 0.0 <= report.score_share <= 100.0
    document = report.as_document()
    ratings = document["ratings"]
    reliability = document["reliability"]
    assert isinstance(ratings, dict)
    assert isinstance(reliability, dict)
    assert set(ratings) == {"candidate-advanced", "BL-RND"}
    assert reliability["invalid_actions"] == 0

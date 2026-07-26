from collections.abc import Callable
from dataclasses import FrozenInstanceError, replace
from threading import Event, current_thread

import pytest

from police_thief_p2p import SimulationSdk
from police_thief_p2p.domain import Action, Role
from police_thief_p2p.sdk import (
    FORBIDDEN_LIVE_FIELDS,
    LifecycleCommand,
    LocalView,
    SnapshotContext,
    ViewMetrics,
    ViewStatus,
)
from police_thief_p2p.sdk.live_view import assert_private_document
from police_thief_p2p.services.belief.models import BeliefDiagnostics, BeliefUpdate
from police_thief_p2p.shared.config_models import SharedConfig


class LifecycleProbe:
    def __init__(self) -> None:
        self.commands: list[LifecycleCommand] = []

    def execute(self, command: LifecycleCommand) -> None:
        self.commands.append(command)


def build_view(config: SharedConfig, status: ViewStatus = ViewStatus.READY) -> LocalView:
    sdk = SimulationSdk()
    state = sdk.create_local_game(config, Role.POLICE)
    state = sdk.apply_action(state, Action.stay()).state
    belief = sdk.initialize_belief(config, Role.POLICE)
    peak = belief.most_likely()
    diagnostics = BeliefDiagnostics(
        entropy_bits=belief.entropy_bits(),
        peak_probability=belief.probability(peak),
        credible_region=tuple((item.row, item.col) for item in belief.credible_region()),
        most_likely_cell=(peak.row, peak.col),
        fallback_used=False,
        hint_category="neutral",
    )
    return sdk.snapshot_local_view(
        state,
        BeliefUpdate(belief, diagnostics),
        config,
        SnapshotContext(
            sub_game_number=2,
            status=status,
            status_detail="Waiting for peer.",
            latest_sent_hint="Near the edge",
            latest_received_hint="Moving carefully",
            own_verdict="truth",
            audit_text="Commitment locked",
            correlation_id="corr-123",
            metrics=ViewMetrics(17, 4, 3, False),
            final=status in {ViewStatus.TERMINAL, ViewStatus.ERROR},
        ),
    )


def test_local_view_is_immutable_complete_and_forbidden_fields_are_unrepresentable(
    shared_config: SharedConfig,
) -> None:
    view = build_view(shared_config)
    assert FORBIDDEN_LIVE_FIELDS.isdisjoint(LocalView.__dataclass_fields__)
    assert view.role == "police"
    assert view.own_position in view.own_visited
    assert len(view.belief_heatmap) == view.board_size**2
    assert sum(float(item) for item in view.belief_heatmap) == pytest.approx(1)
    assert view.latest_received_hint == "Moving carefully"
    with pytest.raises(FrozenInstanceError):
        view.status_detail = "changed"  # type: ignore[misc]


def test_recursive_runtime_privacy_guard_rejects_every_forbidden_key() -> None:
    for field in FORBIDDEN_LIVE_FIELDS:
        with pytest.raises(ValueError, match="forbidden"):
            assert_private_document({"nested": [{field: "hidden"}]})


def test_snapshot_channel_coalesces_visuals_and_preserves_terminal(
    shared_config: SharedConfig,
) -> None:
    sdk = SimulationSdk()
    channel = sdk.new_snapshot_channel(2)
    ready = build_view(shared_config)
    channel.publish(ready)
    channel.publish(replace(ready, step_number=2))
    terminal = build_view(shared_config, ViewStatus.TERMINAL)
    channel.publish(terminal)
    channel.publish(replace(ready, step_number=99))
    assert channel.pending() == 2
    assert channel.drain_latest() is terminal
    assert channel.pending() == 0
    with pytest.raises(TypeError):
        channel.publish("protocol-event")  # type: ignore[arg-type]


def test_lifecycle_and_live_worker_are_routed_through_sdk(
    shared_config: SharedConfig,
) -> None:
    probe = LifecycleProbe()
    sdk = SimulationSdk(lifecycle=probe)
    sdk.lifecycle(LifecycleCommand.START)
    sdk.lifecycle(LifecycleCommand.PAUSE)
    assert probe.commands == [LifecycleCommand.START, LifecycleCommand.PAUSE]
    channel = sdk.new_snapshot_channel()
    caller = current_thread().name
    worker_name: list[str] = []

    def produce(publish: Callable[[LocalView], None], stop: Event) -> None:
        del publish, stop
        worker_name.append(current_thread().name)

    worker = sdk.run_live_async(produce, channel)
    worker.join()
    assert worker_name == ["police-thief-gameplay"]
    assert worker_name[0] != caller


def test_live_observation_cannot_change_headless_domain_evidence(
    shared_config: SharedConfig,
) -> None:
    sdk = SimulationSdk()
    state = sdk.create_local_game(shared_config, Role.THIEF)
    headless = sdk.apply_action(state, Action.stay())
    build_view(shared_config)
    gui_observed = sdk.apply_action(state, Action.stay())
    assert gui_observed == headless

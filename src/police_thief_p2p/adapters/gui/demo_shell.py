"""Deterministic demo feed that opens the Tk local-truth shell."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import replace
from threading import Event, Lock

from police_thief_p2p.adapters.gui.live_app import LiveApp
from police_thief_p2p.sdk import (
    LifecycleCommand,
    LocalView,
    SimulationSdk,
    ViewMetrics,
    ViewStatus,
)
from police_thief_p2p.sdk.live_runtime import LifecyclePort


class DemoLifecycle(LifecyclePort):
    """Drive demo snapshot status from Start/Pause/Resume/Stop/Restart."""

    def __init__(self, base: LocalView) -> None:
        """Create a paused demo controller around one frozen fixture view."""
        self._lock = Lock()
        self._base = base
        self._status = ViewStatus.READY
        self._detail = "Demo ready — press Start."
        self._step = 0
        self._running = False
        self.commands: list[LifecycleCommand] = []

    def execute(self, command: LifecycleCommand) -> None:
        """Apply one operator lifecycle command to the demo feed."""
        with self._lock:
            self.commands.append(command)
            if command is LifecycleCommand.START:
                self._running, self._status = True, ViewStatus.THINKING
                self._detail = "Demo running (local-truth view only; not a live peer)."
            elif command is LifecycleCommand.PAUSE:
                self._running, self._status = False, ViewStatus.PAUSED
                self._detail = "Demo paused."
            elif command is LifecycleCommand.RESUME:
                self._running, self._status = True, ViewStatus.THINKING
                self._detail = "Demo resumed."
            elif command is LifecycleCommand.STOP:
                self._running, self._status = False, ViewStatus.TERMINAL
                self._detail = "Demo stopped."
            elif command is LifecycleCommand.RESTART:
                self._running, self._step = False, 0
                self._status, self._detail = ViewStatus.READY, "Demo restarted — press Start."

    def snapshot(self) -> LocalView:
        """Return the next published view, advancing the step while running."""
        with self._lock:
            if self._running:
                self._step += 1
                self._status = (
                    ViewStatus.WAITING if self._step % 2 == 0 else ViewStatus.THINKING
                )
            return replace(
                self._base,
                status=self._status,
                status_detail=self._detail,
                step_number=self._step,
                audit_text=f"Demo lifecycle: {self._status.value}",
            )


def demo_view() -> LocalView:
    """Return the frozen local-truth fixture used for GUI smoke and screenshots."""
    weights = tuple("0.5" if index == 24 else "0.010416666667" for index in range(49))
    return LocalView(
        role="police",
        own_position=(2, 1),
        own_visited=((0, 0), (1, 0), (2, 0), (2, 1)),
        board_size=7,
        axis_origin_corner="top-left",
        axis_start_index=0,
        public_barriers=((1, 3), (3, 3), (4, 3)),
        belief_heatmap=weights,
        belief_entropy_bits=4.127,
        belief_peak_probability=0.5,
        credible_region=((3, 3), (2, 3), (3, 2), (3, 4), (4, 3)),
        posterior_peak=(3, 3),
        step_number=0,
        sub_game_number=2,
        series_games=6,
        barriers_placed=3,
        max_barriers=14,
        latest_sent_hint="Checking the west corridor",
        latest_received_hint="I prefer open ground",
        own_verdict="uncertain",
        metrics=ViewMetrics(42, 18, 7, False),
        status=ViewStatus.READY,
        status_detail="Demo ready — press Start.",
        audit_text="Demo lifecycle: ready",
        correlation_id=None,
        final=False,
    )


def run_demo(*, auto_close_sec: float | None = None) -> int:
    """Open LiveApp with a lifecycle-driven demo snapshot feed."""
    base = demo_view()
    lifecycle = DemoLifecycle(base)
    sdk = SimulationSdk(lifecycle=lifecycle)
    channel = sdk.new_snapshot_channel()

    def produce(publish: Callable[[LocalView], None], stop: Event) -> None:
        while not stop.is_set():
            publish(lifecycle.snapshot())
            time.sleep(0.2)

    worker = sdk.run_live_async(produce, channel)
    app = LiveApp(sdk, channel)
    if auto_close_sec is not None and auto_close_sec > 0:
        app.root.after(int(auto_close_sec * 1000), app.root.destroy)
    app.run()
    worker.stop()
    worker.join(timeout=2.0)
    return 0

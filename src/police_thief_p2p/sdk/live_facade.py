"""SDK live-view construction, lifecycle, and worker use cases."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from threading import Event

    from police_thief_p2p.domain.state import LocalGameState
    from police_thief_p2p.sdk.live_runtime import (
        LifecycleCommand,
        LifecyclePort,
        LiveWorker,
        SnapshotChannel,
    )
    from police_thief_p2p.sdk.live_view import LocalView, SnapshotContext
    from police_thief_p2p.services.belief.models import BeliefUpdate
    from police_thief_p2p.shared.config_models import SharedConfig


class LiveViewFacade:
    """Expose live monitoring without adapter access to internal services."""

    __slots__ = ()
    _lifecycle: LifecyclePort | None

    def snapshot_local_view(
        self,
        state: LocalGameState,
        update: BeliefUpdate,
        config: SharedConfig,
        context: SnapshotContext,
    ) -> LocalView:
        """Build a complete immutable privacy-safe local view."""
        from police_thief_p2p.sdk.live_view import build_local_view

        return build_local_view(state, update, config, context)

    def lifecycle(self, command: LifecycleCommand) -> None:
        """Route one operator command to the configured lifecycle controller."""
        if self._lifecycle is None:
            raise RuntimeError("lifecycle controller is not configured")
        self._lifecycle.execute(command)

    def new_snapshot_channel(self, max_size: int = 8) -> SnapshotChannel:
        """Create the SDK-approved visual-only bounded channel."""
        from police_thief_p2p.sdk.live_runtime import SnapshotChannel

        return SnapshotChannel(max_size)

    def run_live_async(
        self,
        target: Callable[[Callable[[LocalView], None], Event], None],
        channel: SnapshotChannel,
    ) -> LiveWorker:
        """Start a cooperative gameplay producer outside the UI thread."""
        from police_thief_p2p.sdk.live_runtime import start_live_worker

        return start_live_worker(target, channel)

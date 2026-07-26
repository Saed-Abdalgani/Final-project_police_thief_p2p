"""Live SDK use cases preserving scent and belief privacy boundaries."""

from __future__ import annotations

from typing import TYPE_CHECKING

from police_thief_p2p.domain.board import EMPTY_BARRIERS, BarrierSet

if TYPE_CHECKING:
    from police_thief_p2p.domain.state import LocalGameState
    from police_thief_p2p.domain.values import Action, Position, Role
    from police_thief_p2p.services.belief.grid import BeliefGrid
    from police_thief_p2p.services.belief.models import BeliefUpdate, OpponentScentFrame
    from police_thief_p2p.services.belief.reliability import HintReliability
    from police_thief_p2p.services.belief.scent_engine import OwnScentEngine
    from police_thief_p2p.services.belief.service import BeliefService
    from police_thief_p2p.services.belief.view import LocalView
    from police_thief_p2p.services.crypto.payload import LiveReveal
    from police_thief_p2p.services.ports.repository import RepositoryPort
    from police_thief_p2p.shared.config_models import SharedConfig


class BeliefFacade:
    """Expose reveal-gated belief operations and local-only scent emission."""

    __slots__ = ()
    _scent_engine: OwnScentEngine | None
    _belief_service: BeliefService | None
    _scent_history_repository: RepositoryPort | None

    def _belief_components(self) -> tuple[OwnScentEngine, BeliefService]:
        from police_thief_p2p.services.belief import (
            BeliefService,
            MixtureMotionModel,
            OwnScentEngine,
        )
        from police_thief_p2p.services.belief.history_store import SecretScentStore

        scent_engine = self._scent_engine
        if scent_engine is None:
            store = (
                None
                if self._scent_history_repository is None
                else SecretScentStore(self._scent_history_repository)
            )
            scent_engine = OwnScentEngine(store=store)
            object.__setattr__(self, "_scent_engine", scent_engine)
        belief_service = self._belief_service
        if belief_service is None:
            belief_service = BeliefService(motion_model=MixtureMotionModel())
            object.__setattr__(self, "_belief_service", belief_service)
        return scent_engine, belief_service

    def initialize_belief(
        self,
        config: SharedConfig,
        observer_role: Role,
        barriers: BarrierSet = EMPTY_BARRIERS,
    ) -> BeliefGrid:
        """Initialize uniformly over legal cells reachable from opponent start."""
        from police_thief_p2p.domain.state import initial_local_state
        from police_thief_p2p.services.belief.grid import BeliefGrid, reachable_cells

        opponent_state = initial_local_state(config, observer_role.opponent)
        reachable = reachable_cells(
            opponent_state.rules.board,
            opponent_state.position,
            barriers,
        )
        return BeliefGrid.uniform(opponent_state.rules.board, barriers, reachable)

    def emit_scent_frame(
        self,
        *,
        game_uid: str,
        sub_game_number: int,
        state: LocalGameState,
        action: Action,
        scent_model_sha256: str,
    ) -> OpponentScentFrame:
        """Emit from own post-action state; no remote position can be supplied."""
        scent_engine, _belief_service = self._belief_components()
        return scent_engine.emit_after_action(
            game_uid=game_uid,
            sub_game_number=sub_game_number,
            state=state,
            action=action,
            scent_model_sha256=scent_model_sha256,
        )

    def complete_scent_turn(
        self,
        game_uid: str,
        sub_game_number: int,
        turn_number: int,
    ) -> None:
        """Apply exact decay after both scheduled actors finish one turn."""
        scent_engine, _belief_service = self._belief_components()
        scent_engine.complete_turn(game_uid, sub_game_number, turn_number)

    def update_belief_from_reveal(
        self,
        prior: BeliefGrid,
        frame: OpponentScentFrame,
        reveal: LiveReveal,
        *,
        barriers: BarrierSet,
        hint: str,
        own_position: Position,
        reliability: HintReliability,
        recent_cells: tuple[Position, ...] = (),
    ) -> BeliefUpdate:
        """Validate commitment-linked evidence, then run the single update pipeline."""
        from police_thief_p2p.services.belief.evidence import verify_scent_reveal

        evidence = verify_scent_reveal(frame, reveal)
        _scent_engine, belief_service = self._belief_components()
        return belief_service.update(
            prior,
            evidence,
            barriers=barriers,
            hint=hint,
            observer_position=own_position,
            reliability=reliability,
            recent_cells=recent_cells,
        )

    def create_local_view(
        self,
        state: LocalGameState,
        update: BeliefUpdate,
    ) -> LocalView:
        """Return own truth plus redacted posterior diagnostics."""
        from police_thief_p2p.services.belief.view import create_local_view

        return create_local_view(state, update.belief, update.diagnostics)

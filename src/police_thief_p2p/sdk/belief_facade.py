"""Live SDK use cases preserving scent and belief privacy boundaries."""

from police_thief_p2p.domain.board import EMPTY_BARRIERS, BarrierSet
from police_thief_p2p.domain.state import LocalGameState, initial_local_state
from police_thief_p2p.domain.values import Action, Position, Role
from police_thief_p2p.services.belief.evidence import verify_scent_reveal
from police_thief_p2p.services.belief.grid import BeliefGrid, reachable_cells
from police_thief_p2p.services.belief.models import (
    BeliefUpdate,
    OpponentScentFrame,
)
from police_thief_p2p.services.belief.reliability import HintReliability
from police_thief_p2p.services.belief.scent_engine import OwnScentEngine
from police_thief_p2p.services.belief.service import BeliefService
from police_thief_p2p.services.belief.view import LocalView, create_local_view
from police_thief_p2p.services.crypto.payload import LiveReveal
from police_thief_p2p.shared.config_models import SharedConfig


class BeliefFacade:
    """Expose reveal-gated belief operations and local-only scent emission."""

    __slots__ = ()
    _scent_engine: OwnScentEngine
    _belief_service: BeliefService

    def initialize_belief(
        self,
        config: SharedConfig,
        observer_role: Role,
        barriers: BarrierSet = EMPTY_BARRIERS,
    ) -> BeliefGrid:
        """Initialize uniformly over legal cells reachable from opponent start."""
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
        return self._scent_engine.emit_after_action(
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
        self._scent_engine.complete_turn(game_uid, sub_game_number, turn_number)

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
        evidence = verify_scent_reveal(frame, reveal)
        return self._belief_service.update(
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
        return create_local_view(state, update.belief, update.diagnostics)

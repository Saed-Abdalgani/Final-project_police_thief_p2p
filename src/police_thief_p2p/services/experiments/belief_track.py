"""Per-side offline belief tracking driven only by emitted opponent evidence."""

from collections.abc import Sequence
from dataclasses import dataclass

from police_thief_p2p.domain.board import BarrierSet
from police_thief_p2p.domain.state import LocalGameState, initial_local_state
from police_thief_p2p.domain.values import Action, Position, Role
from police_thief_p2p.services.belief.grid import BeliefGrid, reachable_cells
from police_thief_p2p.services.belief.models import (
    OpponentScentFrame,
    VerifiedScentEvidence,
)
from police_thief_p2p.services.belief.motion import MixtureMotionModel
from police_thief_p2p.services.belief.reliability import HintReliability
from police_thief_p2p.services.belief.scent_engine import OwnScentEngine
from police_thief_p2p.services.belief.service import BeliefService
from police_thief_p2p.services.strategy.contracts import SemanticRegion
from police_thief_p2p.services.strategy.hints import semantic_region
from police_thief_p2p.shared.config_models import SharedConfig

EXPERIMENT_GAME_UID = "00000000-0000-4000-8000-00000000c12a"
EXPERIMENT_SCENT_DIGEST = "c" * 64
_OFFLINE_COMMITMENT = "d" * 64


def claimed_region(likelihoods: Sequence[float], size: int) -> SemanticRegion | None:
    """Return the coarse region a parsed hint most strongly favours."""
    if not likelihoods or max(likelihoods) <= min(likelihoods):
        return None
    index = max(range(len(likelihoods)), key=likelihoods.__getitem__)
    return semantic_region(Position(index // size, index % size), size)


def scent_peak_region(frame: OpponentScentFrame, size: int) -> SemanticRegion | None:
    """Return the coarse region of the strongest verified scent cell."""
    if not frame.cells:
        return None
    peak = max(frame.cells, key=lambda cell: (cell.decimal_value(), -cell.row, -cell.col))
    if peak.decimal_value() <= 0:
        return None
    return semantic_region(Position(peak.row, peak.col), size)


def initial_opponent_belief(config: SharedConfig, observer: Role) -> BeliefGrid:
    """Return the uniform prior over cells reachable from the opponent start."""
    opponent = initial_local_state(config, observer.opponent)
    reachable = reachable_cells(opponent.rules.board, opponent.position)
    return BeliefGrid.uniform(opponent.rules.board, reachable=reachable)


@dataclass(frozen=True, slots=True)
class BeliefProfile:
    """Bounded searchable belief-fusion hyperparameters for experiments."""

    chase: float = 0.2
    evade: float = 0.8
    boundary: float = 0.15
    revisit: float = 0.2
    cycle: float = 0.25
    scent_noise_floor: float = 1e-6
    hint_ratio_cap: float = 3.0
    prior_alpha: float = 2.0
    prior_beta: float = 2.0
    recency: float = 0.95

    def service(self) -> BeliefService:
        """Build the belief service declared by this profile."""
        return BeliefService(
            motion_model=MixtureMotionModel(
                chase=self.chase,
                evade=self.evade,
                boundary=self.boundary,
                revisit=self.revisit,
                cycle=self.cycle,
            ),
            scent_noise_floor=self.scent_noise_floor,
            hint_ratio_cap=self.hint_ratio_cap,
        )

    def reliability(self) -> HintReliability:
        """Build the hint reliability prior declared by this profile."""
        return HintReliability(
            prior_alpha=self.prior_alpha,
            prior_beta=self.prior_beta,
            recency=self.recency,
        )


DEFAULT_BELIEF_PROFILE = BeliefProfile()


@dataclass(slots=True)
class BeliefTrack:
    """One observer's posterior plus its category-isolated hint reliability."""

    belief: BeliefGrid
    reliability: HintReliability
    service: BeliefService

    @classmethod
    def create(
        cls,
        config: SharedConfig,
        observer: Role,
        profile: BeliefProfile = DEFAULT_BELIEF_PROFILE,
    ) -> "BeliefTrack":
        """Create a normalized track before any opponent evidence arrives."""
        return cls(
            belief=initial_opponent_belief(config, observer),
            reliability=profile.reliability(),
            service=profile.service(),
        )

    def observe(
        self,
        frame: OpponentScentFrame,
        *,
        hint: str,
        own_position: Position,
        barriers: BarrierSet,
        recent_cells: tuple[Position, ...] = (),
    ) -> None:
        """Fuse one emitted opponent frame and hint through the live pipeline."""
        evidence = VerifiedScentEvidence(frame, _OFFLINE_COMMITMENT)
        update = self.service.update(
            self.belief,
            evidence,
            barriers=barriers,
            hint=hint,
            observer_position=own_position,
            reliability=self.reliability,
            recent_cells=recent_cells,
        )
        self.belief = update.belief
        self.reliability = self._scored(frame, hint)

    def _scored(self, frame: OpponentScentFrame, hint: str) -> HintReliability:
        """Score the hint against verified scent evidence without opponent truth."""
        cue = self.service.hint_parser.parse(hint, self.belief.size)
        claimed = claimed_region(cue.likelihoods, self.belief.size)
        witnessed = scent_peak_region(frame, self.belief.size)
        if claimed is None or witnessed is None:
            return self.reliability
        return self.reliability.update(
            cue.category,
            consistent=claimed is witnessed,
            step=frame.step_number,
        )


class MatchScent:
    """Own-scent engines for both offline actors in one experiment sub-game."""

    __slots__ = ("_engines",)

    def __init__(self) -> None:
        """Create one independent local engine per actor role."""
        self._engines = {role: OwnScentEngine() for role in Role}

    def emit(self, state: LocalGameState, action: Action) -> OpponentScentFrame:
        """Emit the actor's opponent-safe frame after its own applied action."""
        return self._engines[state.role].emit_after_action(
            game_uid=EXPERIMENT_GAME_UID,
            sub_game_number=1,
            state=state,
            action=action,
            scent_model_sha256=EXPERIMENT_SCENT_DIGEST,
        )

    def complete_turn(self, turn_number: int) -> None:
        """Apply the signed decay exactly once per completed full turn."""
        for engine in self._engines.values():
            engine.complete_turn(EXPERIMENT_GAME_UID, 1, turn_number)

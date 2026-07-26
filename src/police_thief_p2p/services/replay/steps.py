"""Per-step commitment, scent, and domain replay verification."""

from dataclasses import dataclass, field, replace

from police_thief_p2p.domain import LocalGameState, Role, initial_local_state, transition
from police_thief_p2p.domain.events import BarrierPlaced
from police_thief_p2p.services.artifacts.records import SealedLogEntry
from police_thief_p2p.services.audit.replay_support import domain_action, resolved_terminal
from police_thief_p2p.services.belief.scent_field import ScentField
from police_thief_p2p.services.crypto.nonce import SecretNonce
from police_thief_p2p.services.crypto.payload import CommitmentPayload, PublicEffect
from police_thief_p2p.services.crypto.state_digest import local_state_digest
from police_thief_p2p.services.replay.models import ReplayFinding, ReplayFrame, ReplayMode
from police_thief_p2p.services.replay.presentation import build_frame, validate_heatmap
from police_thief_p2p.services.replay.reveal import ReplayReveal
from police_thief_p2p.shared.config_models import SharedConfig
from police_thief_p2p.shared.scent import ScentPolicy
from police_thief_p2p.shared.version import PROTOCOL_VERSION


@dataclass(slots=True)
class ReplayMachine:
    """Private mutable accumulator that never crosses the service boundary."""

    config: SharedConfig
    viewer_role: Role
    mode: ReplayMode
    states: dict[Role, LocalGameState] = field(init=False)
    actor_steps: dict[Role, int] = field(init=False)
    scent_fields: dict[Role, ScentField] = field(init=False)
    nonce_fingerprints: set[str] = field(default_factory=set)
    frames: list[ReplayFrame] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize both audit-only local states."""
        self.states = {role: initial_local_state(self.config, role) for role in Role}
        self.actor_steps = {role: 0 for role in Role}
        self.scent_fields = {
            role: ScentField(self.config.board_and_agents.grid_size) for role in Role
        }

    def verify_step(
        self,
        entry: SealedLogEntry,
        reveal: ReplayReveal,
        expected_game_uid: str,
        expected_sub_game: int,
        config_sha256: str,
        scent_model_sha256: str,
        policy: ScentPolicy,
    ) -> ReplayFinding | None:
        """Verify and apply one revealed step, returning only its first failure."""
        body = reveal.body
        actor = body.actor
        evidence = f"step:{entry.sequence}"
        identity = body.game_uid == expected_game_uid and body.sub_game_number == expected_sub_game
        if not identity or entry.actor != actor.value or body.step_number != entry.step_number:
            return ReplayFinding(1, "STEP_IDENTITY", evidence, "step identity binding differs")
        self.actor_steps[actor] += 1
        if body.step_number != self.actor_steps[actor]:
            return ReplayFinding(1, "STEP_ORDER", evidence, "actor step has a duplicate or gap")
        try:
            nonce = SecretNonce.from_hex(reveal.nonce_hex)
        except ValueError:
            return ReplayFinding(1, "NONCE_FORMAT", evidence, "final nonce is invalid")
        fingerprint = nonce.fingerprint()
        if fingerprint in self.nonce_fingerprints:
            return ReplayFinding(1, "NONCE_REUSE", evidence, "nonce was reused")
        self.nonce_fingerprints.add(fingerprint)
        if entry.commitment_sha256 != CommitmentPayload(body, nonce).digest():
            return ReplayFinding(1, "COMMITMENT", evidence, "recomputed commitment differs")
        if (
            body.config_sha256 != config_sha256
            or body.scent_model_sha256 != scent_model_sha256
            or body.protocol_version != PROTOCOL_VERSION
        ):
            return ReplayFinding(1, "STEP_BINDING", evidence, "constitution binding differs")
        state = self.states[actor]
        if local_state_digest(state) != body.pre_action_state_digest:
            return ReplayFinding(1, "PRE_STATE", evidence, "pre-action state digest differs")
        try:
            result = transition(state, domain_action(body.action))
        except (TypeError, ValueError):
            return ReplayFinding(1, "ILLEGAL_ACTION", evidence, "action is illegal")
        finding = self._verify_scent_and_effects(
            entry, reveal, result.state, result.public_events, scent_model_sha256, policy
        )
        if finding is not None:
            return finding
        self.states[actor] = result.state
        if result.public_events:
            other = self.states[actor.opponent]
            self.states[actor.opponent] = replace(
                other, public_barriers=result.state.public_barriers
            )
        if len(set(self.actor_steps.values())) == 1:
            self.scent_fields = {
                role: value.decay_after_full_turn(policy)
                for role, value in self.scent_fields.items()
            }
        terminal = resolved_terminal(
            self.states, result.public_events[-1].target if result.public_events else None
        )
        self.frames.append(
            build_frame(
                self.states,
                self.viewer_role,
                self.mode,
                entry,
                body,
                reveal.belief_heatmap,
                terminal.value if terminal else None,
            )
        )
        return None

    def _verify_scent_and_effects(
        self,
        entry: SealedLogEntry,
        reveal: ReplayReveal,
        state: LocalGameState,
        events: tuple[BarrierPlaced, ...],
        scent_digest: str,
        policy: ScentPolicy,
    ) -> ReplayFinding | None:
        body = reveal.body
        field = self.scent_fields[body.actor]
        if body.action.action_type.value in {"MOVE", "STAY"}:
            field = field.emit(state.position, policy)
        frame = field.to_frame(
            game_uid=body.game_uid,
            sub_game_number=body.sub_game_number,
            step_number=body.step_number,
            actor=body.actor,
            scent_model_sha256=scent_digest,
            policy=policy,
        )
        self.scent_fields[body.actor] = field
        if frame.frame_sha256 != body.scent_frame_sha256:
            return ReplayFinding(1, "SCENT_FRAME", f"step:{entry.sequence}", "scent differs")
        effects = tuple(
            PublicEffect(effect_type="barrier_placed", target=(event.target.row, event.target.col))
            for event in events
        )
        if effects != body.public_effects:
            return ReplayFinding(1, "PUBLIC_EFFECT", f"step:{entry.sequence}", "effects differ")
        return validate_heatmap(
            reveal.belief_heatmap,
            self.config.board_and_agents.grid_size,
            self.mode,
            entry.sequence,
        )

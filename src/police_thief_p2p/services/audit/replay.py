"""Commitment verification and deterministic domain replay."""

from __future__ import annotations

from dataclasses import replace

from police_thief_p2p.domain import (
    ActionType,
    Role,
    initial_local_state,
    transition,
)
from police_thief_p2p.services.audit.models import AuditBundle
from police_thief_p2p.services.audit.replay_support import (
    ReplayResult,
    domain_action,
    failed_replay,
    resolved_terminal,
    verify_sealed_step,
)
from police_thief_p2p.services.belief.scent_field import ScentField
from police_thief_p2p.services.crypto.payload import PublicEffect
from police_thief_p2p.services.crypto.state_digest import local_state_digest


def replay(bundle: AuditBundle, order_offset: int = 0) -> ReplayResult:
    """Verify identities, commitments, scent, and every physical action."""
    states = {
        Role.POLICE: initial_local_state(bundle.config, Role.POLICE),
        Role.THIEF: initial_local_state(bundle.config, Role.THIEF),
    }
    actor_steps = {Role.POLICE: 0, Role.THIEF: 0}
    scent_fields = {
        Role.POLICE: ScentField(bundle.config.board_and_agents.grid_size),
        Role.THIEF: ScentField(bundle.config.board_and_agents.grid_size),
    }
    nonce_fingerprints: set[str] = set()
    terminal = None
    verified = 0
    for expected_sequence, evidence in enumerate(bundle.steps, start=1):
        body = evidence.reveal.body
        actor_steps[body.actor] += 1
        seal_failure = verify_sealed_step(
            bundle,
            evidence,
            expected_sequence,
            actor_steps[body.actor],
            nonce_fingerprints,
            verified,
            terminal,
            order_offset,
        )
        if seal_failure is not None:
            return seal_failure
        state = states[body.actor]
        if local_state_digest(state) != body.pre_action_state_digest:
            return failed_replay(
                verified,
                terminal,
                order_offset,
                "PRE_STATE",
                f"step:{expected_sequence}",
                "pre-action local-state digest differs",
            )
        try:
            result = transition(state, domain_action(body.action))
        except (TypeError, ValueError):
            return failed_replay(
                verified,
                terminal,
                order_offset,
                "ILLEGAL_ACTION",
                f"step:{expected_sequence}",
                "action is illegal in replayed domain state",
            )
        field = scent_fields[body.actor]
        if body.action.action_type in {ActionType.MOVE, ActionType.STAY}:
            field = field.emit(result.state.position, bundle.scent_policy)
        expected_frame = field.to_frame(
            game_uid=body.game_uid,
            sub_game_number=body.sub_game_number,
            step_number=body.step_number,
            actor=body.actor,
            scent_model_sha256=body.scent_model_sha256,
            policy=bundle.scent_policy,
        )
        if expected_frame.frame_sha256 != body.scent_frame_sha256:
            return failed_replay(
                verified,
                terminal,
                order_offset,
                "SCENT_FRAME",
                f"step:{expected_sequence}",
                "accumulated post-action scent frame differs",
            )
        scent_fields[body.actor] = field
        expected_effects = tuple(
            PublicEffect(
                effect_type="barrier_placed",
                target=(event.target.row, event.target.col),
            )
            for event in result.public_events
        )
        if body.public_effects != expected_effects:
            return failed_replay(
                verified,
                terminal,
                order_offset,
                "PUBLIC_EFFECT",
                f"step:{expected_sequence}",
                "sealed public effects differ from domain events",
            )
        states[body.actor] = result.state
        if len(set(actor_steps.values())) == 1:
            scent_fields = {
                role: scent.decay_after_full_turn(bundle.scent_policy)
                for role, scent in scent_fields.items()
            }
        if result.public_events:
            barriers = result.state.public_barriers
            other = states[body.actor.opponent]
            states[body.actor.opponent] = replace(other, public_barriers=barriers)
        terminal = resolved_terminal(
            states, result.public_events[-1].target if result.public_events else None
        )
        verified += 1
        if terminal is not None and expected_sequence != len(bundle.steps):
            return failed_replay(
                verified,
                terminal,
                order_offset,
                "POST_TERMINAL",
                f"step:{expected_sequence + 1}",
                "records continue after terminal outcome",
            )
    return ReplayResult(verified, terminal, ())

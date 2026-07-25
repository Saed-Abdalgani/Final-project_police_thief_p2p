"""Small deterministic helpers for domain audit replay."""

from dataclasses import dataclass

from police_thief_p2p.domain import (
    Action,
    LocalGameState,
    Position,
    Role,
    TerminalReason,
    resolve_verified_terminal,
)
from police_thief_p2p.services.audit.models import (
    AuditBundle,
    AuditFinding,
    AuditStep,
)
from police_thief_p2p.services.crypto.nonce import SecretNonce
from police_thief_p2p.services.crypto.payload import (
    CommitmentPayload,
    CommittedAction,
    verify_commitment,
)
from police_thief_p2p.shared.version import PROTOCOL_VERSION


@dataclass(frozen=True, slots=True)
class ReplayResult:
    """Replay progress and independently resolved terminal."""

    verified_steps: int
    terminal: TerminalReason | None
    findings: tuple[AuditFinding, ...]


def identity_failure(
    bundle: AuditBundle,
    actual_sequence: int,
    expected_sequence: int,
) -> tuple[str, str, str] | None:
    """Validate global and game identities before reading step content."""
    step = bundle.steps[expected_sequence - 1]
    body = step.reveal.body
    if actual_sequence != expected_sequence:
        return ("STEP_ORDER", f"step:{expected_sequence}", "global sequence is not monotonic")
    if body.game_uid != bundle.game_uid or body.sub_game_number != bundle.sub_game_number:
        return ("FOREIGN_GAME", f"step:{expected_sequence}", "step belongs to another game")
    return None


def verify_sealed_step(
    bundle: AuditBundle,
    evidence: AuditStep,
    expected_sequence: int,
    expected_actor_step: int,
    nonce_fingerprints: set[str],
    verified: int,
    terminal: TerminalReason | None,
    offset: int,
) -> ReplayResult | None:
    """Verify identity, nonce uniqueness, commitment, and signed bindings."""
    failure = identity_failure(bundle, evidence.sequence, expected_sequence)
    if failure is not None:
        return failed_replay(verified, terminal, offset, *failure)
    body = evidence.reveal.body
    if body.step_number != expected_actor_step:
        return failed_replay(
            verified,
            terminal,
            offset,
            "STEP_ORDER",
            f"step:{expected_sequence}",
            "actor step sequence has a duplicate or gap",
        )
    try:
        nonce = SecretNonce.from_hex(evidence.nonce_hex)
    except ValueError:
        return failed_replay(
            verified,
            terminal,
            offset,
            "NONCE_FORMAT",
            f"step:{expected_sequence}",
            "final nonce is invalid",
        )
    if nonce.fingerprint() in nonce_fingerprints:
        return failed_replay(
            verified,
            terminal,
            offset,
            "NONCE_REUSE",
            f"step:{expected_sequence}",
            "nonce was reused",
        )
    nonce_fingerprints.add(nonce.fingerprint())
    if not verify_commitment(CommitmentPayload(body, nonce), evidence.reveal.commitment_sha256):
        return failed_replay(
            verified,
            terminal,
            offset,
            "COMMITMENT",
            f"step:{expected_sequence}",
            "recomputed commitment differs",
        )
    if (
        body.config_sha256 != bundle.config_sha256
        or body.scent_model_sha256 != bundle.scent_model_sha256
        or body.protocol_version != PROTOCOL_VERSION
    ):
        return failed_replay(
            verified,
            terminal,
            offset,
            "STEP_BINDING",
            f"step:{expected_sequence}",
            "step constitution or protocol binding differs",
        )
    return None


def domain_action(action: CommittedAction) -> Action:
    """Convert a wire action into the validated domain value."""
    if action.target is not None:
        return Action.barrier(Position(*action.target))
    if action.direction is not None:
        return Action.move(action.direction)
    return Action.stay()


def resolved_terminal(
    states: dict[Role, LocalGameState],
    placed: Position | None,
) -> TerminalReason | None:
    """Resolve terminal truth from both replayed local states."""
    police = states[Role.POLICE]
    thief = states[Role.THIEF]
    completed = max(police.step_number, thief.step_number)
    return resolve_verified_terminal(
        board=police.rules.board,
        police_position=police.position,
        thief_position=thief.position,
        barriers=police.public_barriers,
        completed_steps=completed,
        survival_threshold=police.rules.survival_threshold,
        max_steps=police.rules.max_steps,
        placed_barrier=placed,
    )


def failed_replay(
    verified: int,
    terminal: TerminalReason | None,
    offset: int,
    code: str,
    evidence: str,
    detail: str,
) -> ReplayResult:
    """Build one deterministic first-failure replay result."""
    return ReplayResult(
        verified,
        terminal,
        (AuditFinding(offset + 1, code, evidence, detail),),
    )

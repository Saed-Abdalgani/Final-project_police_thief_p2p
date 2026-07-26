from dataclasses import replace

from police_thief_p2p.domain import (
    Action,
    Direction,
    Role,
    TerminalReason,
    initial_local_state,
    transition,
)
from police_thief_p2p.services.audit.models import AuditBundle, AuditStep
from police_thief_p2p.services.belief.scent_field import ScentField
from police_thief_p2p.services.crypto.capture import (
    CaptureExchange,
    CaptureStatement,
    SealedCapture,
)
from police_thief_p2p.services.crypto.declaration import (
    SignedStepZero,
    SigningKey,
    StepZeroBody,
)
from police_thief_p2p.services.crypto.journal import EventJournal
from police_thief_p2p.services.crypto.nonce import SecretNonce
from police_thief_p2p.services.crypto.payload import (
    CommitmentBody,
    CommitmentPayload,
    CommittedAction,
)
from police_thief_p2p.services.crypto.scent_evidence import scent_model_digest
from police_thief_p2p.services.crypto.state_digest import local_state_digest
from police_thief_p2p.services.crypto.store import CommitmentIdentity, SealedStepStore
from police_thief_p2p.services.ports.git_info import GitState
from police_thief_p2p.services.ports.system_info import SystemInfo
from police_thief_p2p.services.protocol.phases import ProtocolPhase
from police_thief_p2p.shared.canonical_json import sha256_digest
from police_thief_p2p.shared.config_models import SharedConfig
from police_thief_p2p.shared.scent import ScentPolicy
from police_thief_p2p.shared.version import PROTOCOL_VERSION, SCHEMA_VERSION

GAME_UID = "12345678-1234-4234-8234-123456789abc"
SCHEDULE_DIGEST = sha256_digest({"roles": ["police", "thief"] * 3})
KEY_A = SigningKey(b"A" * 32)
KEY_B = SigningKey(b"B" * 32)


def _step_zero(
    config: SharedConfig,
    group_id: str,
    commit: str,
    key: SigningKey,
    scent_digest: str,
) -> tuple[SignedStepZero, SigningKey]:
    body = StepZeroBody.compose(
        system=SystemInfo("Windows", "3.13.13", "Test CPU", 8, 16_000_000_000),
        git=GitState(commit, False),
        group_id=group_id,
        counted=True,
        template_mode=True,
        model_provider="template",
        model_name="deterministic",
        estimated_tokens=0,
        config_sha256=config.digest(),
        scent_model_sha256=scent_digest,
        role_schedule_sha256=SCHEDULE_DIGEST,
        protocol_version=PROTOCOL_VERSION,
        schema_version=SCHEMA_VERSION,
    )
    return SignedStepZero.create(body, key), key


def build_valid_audit_bundle(
    config: SharedConfig,
    sub_game_number: int = 1,
) -> AuditBundle:
    policy = ScentPolicy()
    scent_digest = scent_model_digest(policy)
    states = {
        Role.POLICE: initial_local_state(config, Role.POLICE),
        Role.THIEF: initial_local_state(config, Role.THIEF),
    }
    moves = (
        (Role.POLICE, Action.move(Direction.SOUTH)),
        (Role.THIEF, Action.stay()),
        (Role.POLICE, Action.move(Direction.SOUTH)),
        (Role.THIEF, Action.stay()),
        (Role.POLICE, Action.move(Direction.SOUTH)),
        (Role.THIEF, Action.stay()),
        (Role.POLICE, Action.move(Direction.EAST)),
        (Role.THIEF, Action.stay()),
        (Role.POLICE, Action.move(Direction.EAST)),
        (Role.THIEF, Action.stay()),
        (Role.POLICE, Action.move(Direction.EAST)),
    )
    store = SealedStepStore()
    journal = EventJournal()
    evidence = []
    actor_steps = {Role.POLICE: 0, Role.THIEF: 0}
    scent_fields = {
        Role.POLICE: ScentField(config.board_and_agents.grid_size),
        Role.THIEF: ScentField(config.board_and_agents.grid_size),
    }
    for sequence, (actor, action) in enumerate(moves, start=1):
        state = states[actor]
        actor_steps[actor] += 1
        result = transition(state, action)
        scent_fields[actor] = scent_fields[actor].emit(result.state.position, policy)
        frame = scent_fields[actor].to_frame(
            game_uid=GAME_UID,
            sub_game_number=sub_game_number,
            step_number=actor_steps[actor],
            actor=actor,
            scent_model_sha256=scent_digest,
            policy=policy,
        )
        body = CommitmentBody(
            game_uid=GAME_UID,
            sub_game_number=sub_game_number,
            step_number=actor_steps[actor],
            actor=actor,
            pre_action_state_digest=local_state_digest(state),
            action=CommittedAction.from_domain(action),
            hint=f"deterministic step {sequence}",
            verdict="truth",
            hint_semantic_intent="neutral",
            token_count=0,
            model_provider="template",
            model_name="deterministic",
            config_sha256=config.digest(),
            protocol_version=PROTOCOL_VERSION,
            scent_model_sha256=scent_digest,
            scent_frame_sha256=frame.frame_sha256,
        )
        nonce = SecretNonce(sequence.to_bytes(32, "big"))
        public = store.seal(CommitmentPayload(body, nonce))
        identity = CommitmentIdentity(GAME_UID, sub_game_number, actor_steps[actor], actor)
        store.acknowledge(identity, public.commitment_sha256)
        reveal = store.reveal(identity)
        journal.append("step-reveal", reveal.model_dump(mode="json"))
        evidence.append(AuditStep(sequence, reveal, nonce.reveal_hex()))
        states[actor] = result.state
        if len(set(actor_steps.values())) == 1:
            scent_fields = {
                role: field.decay_after_full_turn(policy) for role, field in scent_fields.items()
            }
    manifest = store.final_manifest(GAME_UID, sub_game_number, ProtocolPhase.AUDITING)
    last = evidence[-1].reveal.commitment_sha256
    capture = CaptureExchange(
        SealedCapture(
            CaptureStatement(
                game_uid=GAME_UID,
                sub_game_number=sub_game_number,
                step_number=6,
                action_commitment_sha256=last,
                kind="claim",
                captured=True,
            ),
            SecretNonce(b"C" * 32),
        ),
        SealedCapture(
            CaptureStatement(
                game_uid=GAME_UID,
                sub_game_number=sub_game_number,
                step_number=6,
                action_commitment_sha256=last,
                kind="response",
                captured=True,
            ),
            SecretNonce(b"D" * 32),
        ),
    )
    return AuditBundle(
        GAME_UID,
        sub_game_number,
        config,
        config.digest(),
        policy,
        scent_digest,
        SCHEDULE_DIGEST,
        SCHEDULE_DIGEST,
        (
            _step_zero(config, "GRP00001", "a" * 40, KEY_A, scent_digest),
            _step_zero(config, "GRP00002", "b" * 40, KEY_B, scent_digest),
        ),
        tuple(evidence),
        manifest,
        journal.entries,
        TerminalReason.CAPTURE,
        config.scoring.capture_cop,
        config.scoring.capture_thief,
        capture,
    )


def replace_step_body(
    bundle: AuditBundle,
    index: int,
    **changes: object,
) -> AuditBundle:
    step = bundle.steps[index]
    body = step.reveal.body.model_copy(update=changes)
    altered = replace(step, reveal=step.reveal.model_copy(update={"body": body}))
    steps = (*bundle.steps[:index], altered, *bundle.steps[index + 1 :])
    return replace(bundle, steps=steps)


def reseal_step_body(
    bundle: AuditBundle,
    index: int,
    **changes: object,
) -> AuditBundle:
    """Create internally consistent evidence around one changed step body."""
    step = bundle.steps[index]
    body = step.reveal.body.model_copy(update=changes)
    payload = CommitmentPayload(body, SecretNonce.from_hex(step.nonce_hex))
    digest = payload.digest()
    reveal = step.reveal.model_copy(update={"body": body, "commitment_sha256": digest})
    altered = replace(step, reveal=reveal)
    steps = (*bundle.steps[:index], altered, *bundle.steps[index + 1 :])
    entries = tuple(
        replace(entry, commitment_sha256=digest)
        if (entry.identity.actor == body.actor and entry.identity.step_number == body.step_number)
        else entry
        for entry in bundle.final_manifest.entries
    )
    manifest = replace(
        bundle.final_manifest,
        entries=entries,
        manifest_sha256=sha256_digest([entry.as_dict() for entry in entries]),
    )
    journal = EventJournal()
    for item in steps:
        journal.append("step-reveal", item.reveal.model_dump(mode="json"))
    return replace(bundle, steps=steps, final_manifest=manifest, journal=journal.entries)

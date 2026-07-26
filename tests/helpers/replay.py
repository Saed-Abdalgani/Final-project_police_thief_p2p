from dataclasses import dataclass
from pathlib import Path

from police_thief_p2p.services.artifacts import (
    ArtifactKind,
    ArtifactManifest,
    ArtifactWriter,
    SubGameResult,
    TokenUsage,
)
from police_thief_p2p.services.artifacts.records import (
    AgreementRecord,
    PlayedConfigArtifact,
    RoleAssignmentRecord,
    SealedLogEntry,
    SubGameLogArtifact,
)
from police_thief_p2p.shared.canonical_json import canonical_json_bytes
from police_thief_p2p.shared.config_models import SharedConfig
from tests.helpers.audit import build_valid_audit_bundle
from tests.helpers.reporting import (
    AUDIT,
    AUDIT_MANIFEST,
    JOURNAL,
    _declaration,
    _result,
    _roles,
)

GROUPS = ("GRP00001", "GRP00002")
COMMITS = {GROUPS[0]: "1" * 40, GROUPS[1]: "2" * 40}


@dataclass(frozen=True, slots=True)
class ReplayFixture:
    log: SubGameLogArtifact
    config: PlayedConfigArtifact

    @property
    def log_bytes(self) -> bytes:
        return canonical_json_bytes(self.log.model_dump(mode="json"))

    @property
    def config_bytes(self) -> bytes:
        return canonical_json_bytes(self.config.model_dump(mode="json"))


def build_replay_fixture(
    config: SharedConfig,
    sub_game_number: int = 1,
    roles: RoleAssignmentRecord | None = None,
) -> ReplayFixture:
    bundle = build_valid_audit_bundle(config, sub_game_number)
    selected_roles = roles or RoleAssignmentRecord(police=GROUPS[0], thief=GROUPS[1])
    played = PlayedConfigArtifact(
        game_id="m9-series",
        game_uid=bundle.game_uid,
        sub_game_number=bundle.sub_game_number,
        role_assignment=selected_roles,
        config_sha256=config.digest(),
        raw_config_sha256="e" * 64,
        played_commits=COMMITS,
        agreement=AgreementRecord(
            signers=GROUPS,
            agreed_at="2026-07-26T10:00:00Z",
            agreement_sha256="f" * 64,
        ),
        shared_config=config.model_dump(mode="json"),
    )
    probabilities = ("1", *("0" for _ in range(config.board_and_agents.grid_size**2 - 1)))
    entries = tuple(
        SealedLogEntry(
            sequence=step.sequence,
            step_number=step.reveal.body.step_number,
            phase="reveal",
            actor=step.reveal.body.actor.value,
            timestamp=f"2026-07-26T10:00:{step.sequence:02d}Z",
            commitment_sha256=step.reveal.commitment_sha256,
            reveal={
                "body": step.reveal.body.model_dump(mode="json"),
                "nonce_hex": step.nonce_hex,
                "belief_heatmap": probabilities,
            },
            public_effects={},
            metrics={},
            audit_status="verified",
        )
        for step in bundle.steps
    )
    log = SubGameLogArtifact(
        game_id="m9-series",
        game_uid=bundle.game_uid,
        sub_game_number=bundle.sub_game_number,
        role_assignment=selected_roles,
        config_sha256=config.digest(),
        played_commits=COMMITS,
        journal_sha256="b" * 64,
        entries=entries,
        terminal_reason="capture",
        audit_status="verified",
        audit_sha256="c" * 64,
    )
    return ReplayFixture(log, played)


def build_replay_manifest(root: Path, config: SharedConfig) -> ArtifactManifest:
    writer = ArtifactWriter(root)
    declaration = _declaration().model_copy(update={"config_sha256": config.digest()})
    declaration_ref = writer.write(ArtifactKind.DECLARATION, declaration)
    references = [declaration_ref]
    results = []
    base = build_replay_fixture(config)
    for number in range(1, 7):
        roles = _roles(number)
        fixture = build_replay_fixture(config, number, roles)
        played = fixture.config
        config_ref = writer.write(
            ArtifactKind.CONFIG,
            played,
            sub_game_number=number,
            config_sha256=config.digest(),
        )
        log = fixture.log
        log_ref = writer.write(
            ArtifactKind.LOG,
            log,
            sub_game_number=number,
            config_sha256=config.digest(),
            journal_sha256=JOURNAL,
            audit_sha256=AUDIT,
        )
        references.extend((config_ref, log_ref))
        scores = {roles.police: 20, roles.thief: 5}
        results.append(
            SubGameResult(
                sub_game_number=number,
                role_assignment=roles,
                terminal_reason="capture",
                winner=roles.police,
                tie=False,
                scores=scores,
                tokens={
                    GROUPS[0]: TokenUsage(input_tokens=1, output_tokens=2),
                    GROUPS[1]: TokenUsage(input_tokens=3, output_tokens=4),
                },
                config_sha256=config.digest(),
                log_sha256=log_ref.sha256,
                audit_sha256=AUDIT,
                commits=COMMITS,
                config_file=config_ref.filename,
                log_file=log_ref.filename,
                audit_status="verified",
            )
        )
    result = _result(declaration_ref, tuple(results))
    result_ref = writer.write(ArtifactKind.RESULT, result)
    references.append(result_ref)
    manifest = ArtifactManifest(
        game_id="m9-series",
        game_uid=base.log.game_uid,
        config_sha256=config.digest(),
        played_commits=COMMITS,
        journal_sha256=JOURNAL,
        audit_manifest_sha256=AUDIT_MANIFEST,
        entries=tuple(references),
    )
    writer.write(ArtifactKind.MANIFEST, manifest)
    return manifest

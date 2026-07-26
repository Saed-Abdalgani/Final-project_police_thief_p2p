from dataclasses import dataclass
from pathlib import Path

from pydantic import AnyHttpUrl

from police_thief_p2p.services.artifacts import (
    ArtifactKind,
    ArtifactManifest,
    ArtifactReference,
    ArtifactWriter,
    DeclarationGroup,
    FinalResultArtifact,
    GroupResult,
    PlayedConfigArtifact,
    SeriesDeclaration,
    SubGameResult,
    TokenUsage,
)
from police_thief_p2p.services.artifacts.finalize import finalize_log
from police_thief_p2p.services.artifacts.records import (
    AgreementRecord,
    RoleAssignmentRecord,
    SealedLogEntry,
)
from police_thief_p2p.services.artifacts.result import ResultAgreement
from police_thief_p2p.services.reporting.report import result_payload_digest

GAME_ID = "m9-series"
GAME_UID = "12345678-1234-4234-8234-123456789abc"
GROUPS = ("GRP00001", "GRP00002")
CONFIG = "a" * 64
JOURNAL = "b" * 64
AUDIT = "c" * 64
AUDIT_MANIFEST = "d" * 64
COMMITS = {GROUPS[0]: "1" * 40, GROUPS[1]: "2" * 40}


@dataclass(frozen=True, slots=True)
class ArtifactFixture:
    root: Path
    writer: ArtifactWriter
    manifest: ArtifactManifest
    references: tuple[ArtifactReference, ...]


def build_artifact_fixture(root: Path) -> ArtifactFixture:
    writer = ArtifactWriter(root)
    declaration = _declaration()
    references = [
        writer.write(ArtifactKind.DECLARATION, declaration),
    ]
    sub_results: list[SubGameResult] = []
    for number in range(1, 7):
        roles = _roles(number)
        config = PlayedConfigArtifact(
            game_id=GAME_ID,
            game_uid=GAME_UID,
            sub_game_number=number,
            role_assignment=roles,
            config_sha256=CONFIG,
            raw_config_sha256="e" * 64,
            played_commits=COMMITS,
            agreement=AgreementRecord(
                signers=GROUPS,
                agreed_at="2026-07-26T10:00:00Z",
                agreement_sha256="f" * 64,
            ),
            shared_config={"schema_version": "0.2.0", "exact": True},
        )
        config_ref = writer.write(
            ArtifactKind.CONFIG,
            config,
            sub_game_number=number,
            config_sha256=CONFIG,
        )
        log = finalize_log(
            game_id=GAME_ID,
            game_uid=GAME_UID,
            sub_game_number=number,
            role_assignment=roles,
            config_sha256=CONFIG,
            played_commits=COMMITS,
            journal_sha256=JOURNAL,
            entries=(_entry(number),),
            terminal_reason="survival",
            audit_status="verified",
            audit_sha256=AUDIT,
        )
        log_ref = writer.write(
            ArtifactKind.LOG,
            log,
            sub_game_number=number,
            config_sha256=CONFIG,
            journal_sha256=JOURNAL,
            audit_sha256=AUDIT,
        )
        references.extend((config_ref, log_ref))
        scores = {GROUPS[0]: 5 if number % 2 else 10, GROUPS[1]: 10 if number % 2 else 5}
        sub_results.append(
            SubGameResult(
                sub_game_number=number,
                role_assignment=roles,
                terminal_reason="survival",
                winner=GROUPS[1] if number % 2 else GROUPS[0],
                tie=False,
                scores=scores,
                tokens={
                    GROUPS[0]: TokenUsage(input_tokens=1, output_tokens=2),
                    GROUPS[1]: TokenUsage(input_tokens=3, output_tokens=4),
                },
                config_sha256=CONFIG,
                log_sha256=log_ref.sha256,
                audit_sha256=AUDIT,
                commits=COMMITS,
                config_file=config_ref.filename,
                log_file=log_ref.filename,
                audit_status="verified",
            )
        )
    result = _result(references[0], tuple(sub_results))
    result_ref = writer.write(ArtifactKind.RESULT, result)
    references.append(result_ref)
    manifest = ArtifactManifest(
        game_id=GAME_ID,
        game_uid=GAME_UID,
        config_sha256=CONFIG,
        played_commits=COMMITS,
        journal_sha256=JOURNAL,
        audit_manifest_sha256=AUDIT_MANIFEST,
        entries=tuple(references),
    )
    writer.write(ArtifactKind.MANIFEST, manifest)
    return ArtifactFixture(root, writer, manifest, tuple(references))


def _roles(number: int) -> RoleAssignmentRecord:
    police, thief = GROUPS if number % 2 else tuple(reversed(GROUPS))
    return RoleAssignmentRecord(police=police, thief=thief)


def _entry(number: int) -> SealedLogEntry:
    return SealedLogEntry(
        sequence=1,
        step_number=number,
        phase="audit",
        actor="system",
        timestamp="2026-07-26T10:00:00Z",
        public_effects={"terminal": "survival"},
        metrics={
            GROUPS[0]: TokenUsage(input_tokens=1, output_tokens=2),
            GROUPS[1]: TokenUsage(input_tokens=3, output_tokens=4),
        },
        audit_status="verified",
    )


def _declaration() -> SeriesDeclaration:
    group_values = tuple(
        DeclarationGroup(
            group_id=group,
            group_name=group,
            members=("Member",),
            public_mcp_url=AnyHttpUrl(f"https://example.invalid/{group}/mcp"),
            police_repository=AnyHttpUrl(f"https://example.invalid/{group}/police"),
            thief_repository=AnyHttpUrl(f"https://example.invalid/{group}/thief"),
            police_commit=COMMITS[group],
            thief_commit=COMMITS[group],
            step_zero_sha256="1" * 64,
            hardware_sha256="2" * 64,
            model_provider="template",
            model_name="deterministic-template",
            token_budget=200_000,
            counted_total=1,
        )
        for group in GROUPS
    )
    groups = (group_values[0], group_values[1])
    return SeriesDeclaration(
        game_id=GAME_ID,
        game_uid=GAME_UID,
        timezone="UTC",
        counted=True,
        mode="counted",
        groups=groups,
        planned_start="2026-07-26T10:00:00Z",
        planned_end="2026-07-26T11:00:00Z",
        config_sha256=CONFIG,
        scent_model_sha256="3" * 64,
        schedule_sha256="4" * 64,
        acknowledgment_sha256="5" * 64,
    )


def _result(
    declaration: ArtifactReference,
    sub_games: tuple[SubGameResult, ...],
) -> FinalResultArtifact:
    group_values = tuple(
        GroupResult(
            group_id=group,
            score=45,
            wins=3,
            ties=0,
            tokens=TokenUsage(
                input_tokens=6 if group == GROUPS[0] else 18,
                output_tokens=12 if group == GROUPS[0] else 24,
            ),
            police_repository=AnyHttpUrl(f"https://example.invalid/{group}/police"),
            thief_repository=AnyHttpUrl(f"https://example.invalid/{group}/thief"),
            police_commit=COMMITS[group],
            thief_commit=COMMITS[group],
        )
        for group in GROUPS
    )
    groups = (group_values[0], group_values[1])
    agreement = ResultAgreement(
        status="agreed",
        agreed_digest="0" * 64,
        signers=GROUPS,
        audit_manifest_sha256=AUDIT_MANIFEST,
    )
    result = FinalResultArtifact(
        game_id=GAME_ID,
        game_uid=GAME_UID,
        sender_group_id=GROUPS[0],
        sub_games=sub_games,
        groups=groups,
        series_winner=None,
        series_tie=True,
        declaration_file=declaration.filename,
        declaration_sha256=declaration.sha256,
        agreement=agreement,
    )
    digest = result_payload_digest(result.model_dump(mode="json"))
    return result.model_copy(
        update={"agreement": agreement.model_copy(update={"agreed_digest": digest})}
    )

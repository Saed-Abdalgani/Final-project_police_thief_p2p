"""Bounded schema-first replay artifact loading."""

from police_thief_p2p.services.artifacts.loader import load_artifact_json
from police_thief_p2p.services.artifacts.records import (
    PlayedConfigArtifact,
    SubGameLogArtifact,
)
from police_thief_p2p.shared.schema_registry import validate_schema

MAX_REPLAY_BYTES = 16_777_216


def load_replay_documents(
    log_bytes: bytes,
    config_bytes: bytes,
) -> tuple[SubGameLogArtifact, PlayedConfigArtifact]:
    """Validate encoding, size, schema, models, and local linkage."""
    log_document = load_artifact_json(log_bytes, max_bytes=MAX_REPLAY_BYTES)
    config_document = load_artifact_json(config_bytes, max_bytes=MAX_REPLAY_BYTES)
    validate_schema(log_document, "log.schema.json", source="replay-log")
    validate_schema(config_document, "sub_game_config.schema.json", source="replay-config")
    log = SubGameLogArtifact.model_validate(log_document)
    config = PlayedConfigArtifact.model_validate(config_document)
    if (
        log.game_id != config.game_id
        or log.game_uid != config.game_uid
        or log.sub_game_number != config.sub_game_number
        or log.config_sha256 != config.config_sha256
        or log.role_assignment != config.role_assignment
        or log.played_commits != config.played_commits
    ):
        raise ValueError("replay log/config linkage mismatch")
    return log, config

"""Lightweight packaged-schema catalog and compatibility checks."""

import json
from functools import lru_cache
from importlib.resources import files

SCHEMA_NAMES = frozenset(
    {
        "game.schema.json",
        "rate_limits.schema.json",
        "declaration.schema.json",
        "series_declaration.schema.json",
        "sub_game_config.schema.json",
        "log.schema.json",
        "final_result.schema.json",
        "artifact_manifest.schema.json",
        "protocol_envelope.schema.json",
        "match_proposal.schema.json",
        "match_acceptance.schema.json",
        "commitment_body.schema.json",
        "live_reveal.schema.json",
        "final_reveal.schema.json",
        "capture_statement.schema.json",
        "audit_report.schema.json",
        "scent_frame.schema.json",
        "belief_summary.schema.json",
        "replay_audit.schema.json",
    }
)


def load_schema(name: str) -> dict[str, object]:
    """Load one allowlisted package schema."""
    if name not in SCHEMA_NAMES:
        raise ValueError(f"unknown schema: {name}")
    resource = files("police_thief_p2p.schemas").joinpath(name)
    value = json.loads(resource.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"packaged schema {name} is not an object")
    return value


@lru_cache(maxsize=16)
def contracts_are_compatible(schema_version: str, protocol_version: str) -> bool:
    """Return whether every packaged schema advertises supported versions."""
    for name in SCHEMA_NAMES:
        schema = load_schema(name)
        identifier = schema.get("$id")
        if not isinstance(identifier, str) or f"/{schema_version}/" not in identifier:
            return False
        text = json.dumps(schema, sort_keys=True)
        if (
            name in {"declaration.schema.json", "match_proposal.schema.json"}
            and protocol_version not in text
        ):
            return False
    return True

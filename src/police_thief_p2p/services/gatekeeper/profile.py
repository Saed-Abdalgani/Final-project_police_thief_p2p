"""Strict config-loaded per-service Gatekeeper profiles."""

import json
from typing import Annotated

from pydantic import Field, StrictInt, ValidationError

from police_thief_p2p.shared.config_sections import FrozenModel
from police_thief_p2p.shared.schema_registry import validate_schema
from police_thief_p2p.shared.version import SCHEMA_VERSION


class GatekeeperProfile(FrozenModel):
    """Complete protection limits for one external provider."""

    requests_per_minute: Annotated[StrictInt, Field(ge=1, le=30)]
    burst_capacity: Annotated[StrictInt, Field(ge=1, le=30)]
    concurrent_requests: Annotated[StrictInt, Field(ge=1, le=2)]
    retry_backoff_sec: Annotated[StrictInt, Field(ge=5, le=86_400)]
    max_retries: Annotated[StrictInt, Field(ge=3, le=100)]
    queue_depth: Annotated[StrictInt, Field(ge=100, le=1_000_000)]
    timeout_sec: Annotated[StrictInt, Field(ge=1, le=86_400)]
    daily_quota: Annotated[StrictInt, Field(ge=1)]
    session_quota: Annotated[StrictInt, Field(ge=1)]
    circuit_failure_threshold: Annotated[StrictInt, Field(ge=1, le=100)]
    circuit_cooldown_sec: Annotated[StrictInt, Field(ge=1, le=86_400)]
    repeated_call_limit: Annotated[StrictInt, Field(ge=2, le=1_000)]
    sustained_error_limit: Annotated[StrictInt, Field(ge=2, le=1_000)]


class GatekeeperProfiles(FrozenModel):
    """Versioned profile map covering MCP, Gmail, and optional LLM."""

    schema_version: str
    services: dict[str, GatekeeperProfile]

    def model_post_init(self, __context: object) -> None:
        """Require the mandatory provider profiles."""
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError("unsupported rate-limit schema version")
        missing = {"mcp", "gmail", "remote_llm"} - set(self.services)
        if missing:
            raise ValueError(f"missing Gatekeeper profiles: {sorted(missing)}")


def load_profiles(document: bytes) -> GatekeeperProfiles:
    """Load a bounded hostile rate-limit document."""
    if len(document) > 131_072:
        raise ValueError("rate-limit document exceeds size limit")
    try:
        value = json.loads(document)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("rate-limit document is invalid JSON") from exc
    validate_schema(value, "rate_limits.schema.json", source="rate-limits")
    try:
        return GatekeeperProfiles.model_validate(value)
    except ValidationError as exc:
        raise ValueError("rate-limit profile is invalid") from exc

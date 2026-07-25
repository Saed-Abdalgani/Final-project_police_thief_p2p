"""Top-level typed model for the shared signed match constitution."""

import re
from typing import Annotated, Self

from pydantic import Field, StrictInt, StrictStr, field_validator, model_validator

from police_thief_p2p.shared.canonical_json import canonical_json_bytes, sha256_digest
from police_thief_p2p.shared.config_sections import (
    BoardAndAgents,
    FrozenModel,
    MovementAndBarriers,
    PheromoneConfig,
    ScoringConfig,
    WorldConfig,
)
from police_thief_p2p.shared.coordinates import CoordinateTransform
from police_thief_p2p.shared.identifiers import GroupId
from police_thief_p2p.shared.version import SCHEMA_VERSION

_EXTENSION_NAMESPACE = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)+$")


class NetworkAndLeague(FrozenModel):
    """Fixed league limits and negotiated runtime budgets."""

    num_games: int = Field(strict=True, ge=6, le=6)
    diversity_reward: int = Field(strict=True, ge=10, le=10)
    min_games_to_pass: int = Field(strict=True, ge=2, le=2)
    token_budget_per_series: Annotated[StrictInt, Field(ge=1)] = 200_000
    max_games_per_team: int = Field(strict=True, ge=10, le=10)
    response_timeout_sec: Annotated[StrictInt, Field(ge=1, le=86_400)] = 30
    watchdog_timeout_sec: Annotated[StrictInt, Field(ge=1, le=86_400)] = 60

    @model_validator(mode="after")
    def watchdog_covers_response(self) -> Self:
        """Ensure inactivity detection cannot pre-empt one valid response wait."""
        if self.watchdog_timeout_sec < self.response_timeout_sec:
            raise ValueError("watchdog_timeout_sec must be >= response_timeout_sec")
        return self


class GatekeeperConfig(FrozenModel):
    """Shared safety floor for all externally visible calls."""

    requests_per_minute: Annotated[StrictInt, Field(ge=1, le=30)]
    concurrent_requests: Annotated[StrictInt, Field(ge=1, le=2)]
    retry_backoff_sec: Annotated[StrictInt, Field(ge=5, le=86_400)]
    max_retries: Annotated[StrictInt, Field(ge=3, le=100)]
    queue_depth: Annotated[StrictInt, Field(ge=100, le=1_000_000)]


class SharedConfig(FrozenModel):
    """Complete shared configuration, independent of JSON parsing."""

    schema_version: StrictStr
    agreed_between: tuple[StrictStr, StrictStr]
    board_and_agents: BoardAndAgents
    world: WorldConfig
    movement_and_barriers: MovementAndBarriers
    pheromones: PheromoneConfig
    scoring: ScoringConfig
    network_and_league: NetworkAndLeague
    rate_limiter_gatekeeper: GatekeeperConfig
    extensions: dict[str, object] = Field(default_factory=dict)

    @field_validator("schema_version")
    @classmethod
    def compatible_schema_version(cls, value: str) -> str:
        """Reject config versions not implemented by this package."""
        if value != SCHEMA_VERSION:
            raise ValueError(f"must equal supported schema version {SCHEMA_VERSION}")
        return value

    @field_validator("agreed_between")
    @classmethod
    def distinct_group_ids(cls, value: tuple[str, str]) -> tuple[str, str]:
        """Validate two distinct development-safe group identifiers."""
        for item in value:
            GroupId(item)
        if value[0] == value[1]:
            raise ValueError("must contain two distinct group IDs")
        return value

    @field_validator("extensions")
    @classmethod
    def namespaced_extensions(cls, value: dict[str, object]) -> dict[str, object]:
        """Allow only explicitly namespaced, canonicalizable extension keys."""
        for namespace, payload in value.items():
            if _EXTENSION_NAMESPACE.fullmatch(namespace) is None:
                raise ValueError(f"extension key {namespace!r} is not namespaced")
            canonical_json_bytes(payload)
        return value

    @model_validator(mode="after")
    def legal_distinct_starts(self) -> Self:
        """Ensure both configured starts are on-board and not identical."""
        board = self.board_and_agents
        transform = CoordinateTransform(
            grid_size=board.grid_size,
            origin=board.axis_origin_corner,
            start_index=board.axis_start_index,
        )
        thief = transform.to_canonical(board.thief_start)
        cop = transform.to_canonical(board.cop_start)
        if thief == cop:
            raise ValueError("cop_start and thief_start must be distinct")
        return self

    def canonical_bytes(self) -> bytes:
        """Return the signed canonical representation."""
        return canonical_json_bytes(self.model_dump(mode="json"))

    def digest(self) -> str:
        """Return the canonical shared-config SHA-256 digest."""
        return sha256_digest(self.model_dump(mode="json"))

"""Typed private TOML model and allowlisted secret resolution."""

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, HttpUrl, StrictBool, StrictInt, StrictStr, field_validator

from police_thief_p2p.shared.config_errors import ConfigError, ConfigErrorCode
from police_thief_p2p.shared.config_sections import FrozenModel
from police_thief_p2p.shared.identifiers import GroupId
from police_thief_p2p.shared.reliability_config import ReliabilityConfig
from police_thief_p2p.shared.strategy_config import StrategyConfig

_ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]{1,127}$")


class IdentityConfig(FrozenModel):
    """Private peer identity and role metadata."""

    group_id: StrictStr
    role: Literal["police", "thief"]
    member_names: tuple[StrictStr, ...]

    @field_validator("group_id")
    @classmethod
    def valid_group_id(cls, value: str) -> str:
        """Validate a development-safe group identifier."""
        GroupId(value)
        return value


class NetworkConfig(FrozenModel):
    """Private bind and opponent endpoint settings."""

    listen_host: StrictStr = "127.0.0.1"
    listen_port: Annotated[StrictInt, Field(ge=1, le=65_535)]
    opponent_public_url: HttpUrl
    max_request_bytes: Annotated[StrictInt, Field(ge=1_024, le=10_485_760)] = 65_536
    max_json_depth: Annotated[StrictInt, Field(ge=2, le=64)] = 16
    max_string_length: Annotated[StrictInt, Field(ge=64, le=1_048_576)] = 4_096
    max_collection_items: Annotated[StrictInt, Field(ge=8, le=100_000)] = 256
    reorder_window: Annotated[StrictInt, Field(ge=1, le=1_024)] = 8


class PathsConfig(FrozenModel):
    """Private local artifact location."""

    artifact_root: Path


class LanguageConfig(FrozenModel):
    """Private language provider settings and optional secret reference."""

    provider: Literal["template", "ollama", "openai"] = "template"
    model: StrictStr = "deterministic-template"
    deadline_sec: Annotated[StrictInt, Field(ge=1, le=300)] = 10
    api_key_env: StrictStr | None = None


class EmailConfig(FrozenModel):
    """Private Gmail credential path, recipient policy, and secret reference."""

    credential_path: Path
    token_path: Path = Path("token.json")
    sender: StrictStr = "local-sender@example.invalid"
    recipient_allowlist: tuple[StrictStr, ...]
    oauth_client_secret_env: StrictStr | None = None


class GuiConfig(FrozenModel):
    """Private local presentation preferences."""

    enabled: StrictBool = True
    theme: Literal["system", "light", "dark"] = "system"


class TunnelConfig(FrozenModel):
    """Private public-tunnel provider and preflight endpoint."""

    provider: StrictStr
    health_url: HttpUrl


class ObservabilityConfig(FrozenModel):
    """Private logging verbosity."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"


class PrivateConfig(FrozenModel):
    """Complete private peer configuration; shared rule sections are forbidden."""

    identity: IdentityConfig
    network: NetworkConfig
    paths: PathsConfig
    strategy: StrategyConfig
    language: LanguageConfig
    email: EmailConfig
    gui: GuiConfig
    tunnel: TunnelConfig
    observability: ObservabilityConfig
    reliability: ReliabilityConfig = ReliabilityConfig()

    def secret_environment_names(self) -> tuple[str, ...]:
        """Return only explicitly allowlisted secret environment references."""
        candidates = (
            self.language.api_key_env,
            self.email.oauth_client_secret_env,
        )
        names = tuple(name for name in candidates if name is not None)
        for name in names:
            if _ENV_NAME.fullmatch(name) is None:
                raise ValueError(f"invalid secret environment variable name: {name!r}")
        return names


class ResolvedSecrets:
    """Opaque resolved secret values with a permanently redacted representation."""

    __slots__ = ("_values",)

    def __init__(self, values: Mapping[str, str]) -> None:
        """Retain resolved values behind a redacted object boundary."""
        self._values = dict(values)

    def get(self, name: str) -> str:
        """Return one previously allowlisted secret."""
        return self._values[name]

    def __len__(self) -> int:
        """Return the number of resolved secret references."""
        return len(self._values)

    def __repr__(self) -> str:
        """Never include secret names or values in diagnostics."""
        return f"ResolvedSecrets(count={len(self._values)}, values=<redacted>)"


def resolve_secret_environment(
    config: PrivateConfig,
    environ: Mapping[str, str],
) -> ResolvedSecrets:
    """Resolve only secret fields explicitly named by the private model."""
    resolved: dict[str, str] = {}
    for name in config.secret_environment_names():
        value = environ.get(name)
        if not value:
            raise ConfigError(
                ConfigErrorCode.SECRET_MISSING,
                source="environment",
                path=f"$.secrets.{name}",
                detail="required secret is missing",
            )
        resolved[name] = value
    return ResolvedSecrets(resolved)

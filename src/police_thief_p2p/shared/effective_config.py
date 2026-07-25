"""Effective shared/private configuration with field provenance."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType

from police_thief_p2p.shared.config_models import SharedConfig
from police_thief_p2p.shared.private_config import PrivateConfig


class ConfigSource(StrEnum):
    """Authoritative source of an effective field."""

    SHARED = "shared:game.json"
    PRIVATE = "private:game.toml"


def _leaf_paths(value: object, prefix: str = "$") -> set[str]:
    if isinstance(value, Mapping):
        result: set[str] = set()
        for key, item in value.items():
            result.update(_leaf_paths(item, f"{prefix}.{key}"))
        return result
    if isinstance(value, (list, tuple)):
        result = set()
        for index, item in enumerate(value):
            result.update(_leaf_paths(item, f"{prefix}[{index}]"))
        return result
    return {prefix}


@dataclass(frozen=True, slots=True)
class EffectiveConfig:
    """Immutable validated configuration and per-leaf source ledger."""

    shared: SharedConfig
    private: PrivateConfig
    provenance: Mapping[str, ConfigSource]

    def source_for(self, path: str) -> ConfigSource:
        """Return the authoritative source for one exact leaf path."""
        try:
            return self.provenance[path]
        except KeyError as exc:
            raise KeyError(f"unknown effective config path: {path}") from exc


def merge_effective_config(shared: SharedConfig, private: PrivateConfig) -> EffectiveConfig:
    """Merge non-overlapping typed models with shared authority recorded first."""
    shared_paths = _leaf_paths(shared.model_dump(mode="json"), "$.shared")
    private_paths = _leaf_paths(private.model_dump(mode="json"), "$.private")
    provenance = {
        **dict.fromkeys(shared_paths, ConfigSource.SHARED),
        **dict.fromkeys(private_paths, ConfigSource.PRIVATE),
    }
    return EffectiveConfig(
        shared=shared,
        private=private,
        provenance=MappingProxyType(provenance),
    )

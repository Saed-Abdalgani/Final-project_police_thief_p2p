"""Semantic package, protocol, and schema version ownership."""

import re
from dataclasses import dataclass
from typing import Final

PACKAGE_VERSION: Final = "0.11.0"
PROTOCOL_VERSION: Final = "0.7.0"
SCHEMA_VERSION: Final = "0.2.0"
_SEMVER_PATTERN: Final = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


def is_semantic_version(value: str) -> bool:
    """Return whether ``value`` is a valid Semantic Version 2.0 string."""
    return _SEMVER_PATTERN.fullmatch(value) is not None


@dataclass(frozen=True, slots=True)
class VersionInfo:
    """Version tuple exchanged at application boundaries."""

    package: str
    protocol: str
    schema: str

    def __post_init__(self) -> None:
        """Reject invalid version declarations immediately."""
        invalid = [
            name
            for name, value in (
                ("package", self.package),
                ("protocol", self.protocol),
                ("schema", self.schema),
            )
            if not is_semantic_version(value)
        ]
        if invalid:
            msg = f"invalid semantic version fields: {', '.join(invalid)}"
            raise ValueError(msg)


def current_versions() -> VersionInfo:
    """Return the immutable current compatibility versions."""
    return VersionInfo(
        package=PACKAGE_VERSION,
        protocol=PROTOCOL_VERSION,
        schema=SCHEMA_VERSION,
    )

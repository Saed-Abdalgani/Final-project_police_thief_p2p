"""Stable, path-aware, secret-safe configuration errors."""

from enum import StrEnum


class ConfigErrorCode(StrEnum):
    """Machine-readable configuration failure categories."""

    IO_ERROR = "CFG_IO_ERROR"
    FILE_TOO_LARGE = "CFG_FILE_TOO_LARGE"
    INVALID_UTF8 = "CFG_INVALID_UTF8"
    DUPLICATE_KEY = "CFG_DUPLICATE_KEY"
    TOO_DEEP = "CFG_TOO_DEEP"
    NON_FINITE_NUMBER = "CFG_NON_FINITE_NUMBER"
    INVALID_JSON = "CFG_INVALID_JSON"
    SCHEMA_ERROR = "CFG_SCHEMA_ERROR"
    MODEL_ERROR = "CFG_MODEL_ERROR"
    INVALID_TOML = "CFG_INVALID_TOML"
    SECRET_MISSING = "CFG_SECRET_MISSING"  # noqa: S105  # pragma: allowlist secret


class ConfigError(ValueError):
    """Caller-safe configuration failure with an exact document path."""

    def __init__(
        self,
        code: ConfigErrorCode,
        *,
        source: str,
        path: str = "$",
        detail: str,
    ) -> None:
        """Create an error without retaining raw document or secret content."""
        self.code = code
        self.source = source
        self.path = path
        self.detail = detail
        super().__init__(f"[{code.value}] {source}:{path}: {detail}")

    def __repr__(self) -> str:
        """Return only the safe structured fields."""
        return (
            f"ConfigError(code={self.code.value!r}, source={self.source!r}, "
            f"path={self.path!r}, detail={self.detail!r})"
        )

"""Atomic, restart-safe private byte repository."""

from __future__ import annotations

import os
import re
import uuid
from pathlib import Path

_SAFE_KEY = re.compile(r"^[a-z0-9][a-z0-9-]{0,127}$")


class AtomicFileRepository:
    """Persist bounded records with flush-before-atomic-replace semantics."""

    __slots__ = ("_max_bytes", "_root")

    def __init__(self, root: Path, *, max_bytes: int = 1_048_576) -> None:
        """Create a private record root and enforce a per-record size ceiling."""
        if type(max_bytes) is not int or max_bytes < 1:
            raise ValueError("max_bytes must be a positive integer")
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)
        self._max_bytes = max_bytes

    @property
    def root(self) -> Path:
        """Return the isolated absolute repository root."""
        return self._root

    def load(self, key: str) -> bytes | None:
        """Load one safe record, rejecting oversized or non-regular data."""
        path = self._path(key)
        if not path.exists():
            return None
        if not path.is_file():
            raise OSError("repository record is not a regular file")
        data = path.read_bytes()
        if len(data) > self._max_bytes:
            raise OSError("repository record exceeds configured size")
        return data

    def save(self, key: str, data: bytes) -> None:
        """Flush bytes to a sibling temporary file before atomic replacement."""
        if not isinstance(data, bytes):
            raise TypeError("repository data must be bytes")
        if len(data) > self._max_bytes:
            raise ValueError("repository data exceeds configured size")
        target = self._path(key)
        temporary = self._root / f".{key}.{uuid.uuid4().hex}.tmp"
        try:
            with temporary.open("xb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        finally:
            if temporary.exists():
                temporary.unlink()

    def _path(self, key: str) -> Path:
        if _SAFE_KEY.fullmatch(key) is None:
            raise ValueError("repository key is unsafe")
        path = (self._root / f"{key}.json").resolve()
        if path.parent != self._root:
            raise ValueError("repository key escapes root")
        return path

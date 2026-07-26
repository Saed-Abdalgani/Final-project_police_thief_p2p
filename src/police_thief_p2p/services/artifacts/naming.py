"""Appendix F artifact filenames and root-confined paths."""

import os
from enum import StrEnum
from pathlib import Path

from police_thief_p2p.shared.identifiers import GameId, SubGameNumber

_RESERVED = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }
)


class ArtifactKind(StrEnum):
    """Official immutable artifact families."""

    DECLARATION = "declaration"
    CONFIG = "config"
    LOG = "log"
    RESULT = "result"
    MANIFEST = "manifest"


def artifact_filename(
    kind: ArtifactKind,
    game_id: str,
    sub_game_number: int | None = None,
) -> str:
    """Build the exact safe filename for one official artifact."""
    safe_game_id = str(GameId(game_id))
    needs_sub_game = kind in {ArtifactKind.CONFIG, ArtifactKind.LOG}
    if needs_sub_game != (sub_game_number is not None):
        raise ValueError("sub-game number presence does not match artifact kind")
    suffix = "" if sub_game_number is None else f"_g{int(SubGameNumber(sub_game_number)):02d}"
    filename = f"{kind.value}_{safe_game_id}{suffix}.json"
    if len(filename.encode("utf-8")) > 180:
        raise ValueError("artifact filename exceeds safe length")
    if Path(filename).stem.upper() in _RESERVED:
        raise ValueError("artifact filename is reserved")
    return filename


class ArtifactPaths:
    """Separate immutable evidence from rotating operational diagnostics."""

    __slots__ = ("diagnostics", "official", "private", "root")

    def __init__(self, root: Path) -> None:
        """Create and resolve isolated storage roots."""
        self.root = root.resolve()
        self.official = (self.root / "official").resolve()
        self.diagnostics = (self.root / "diagnostics").resolve()
        self.private = (self.root / "private").resolve()
        if any(
            path.parent != self.root for path in (self.official, self.diagnostics, self.private)
        ):
            raise ValueError("classified artifact directory escapes configured root")
        self.official.mkdir(parents=True, exist_ok=True)
        self.diagnostics.mkdir(parents=True, exist_ok=True)
        self.private.mkdir(parents=True, exist_ok=True)

    def resolve_official(self, filename: str) -> Path:
        """Resolve one plain JSON name inside the official root."""
        if Path(filename).name != filename or not filename.endswith(".json"):
            raise ValueError("artifact filename is unsafe")
        if len(filename.encode("utf-8")) > 180 or Path(filename).stem.upper() in _RESERVED:
            raise ValueError("artifact filename is unsafe")
        candidate = (self.official / filename).resolve()
        if candidate.parent != self.official:
            raise ValueError("artifact path escapes configured root")
        return candidate

    @staticmethod
    def apply_permissions(path: Path, *, private: bool) -> None:
        """Apply restrictive private or best-effort read-only final permissions."""
        try:
            os.chmod(path, 0o600 if private else 0o444)
        except OSError:
            return

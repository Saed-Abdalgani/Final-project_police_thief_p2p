"""Write local playtest private configs so operators never hand-edit TOML."""

from pathlib import Path

from scripts.m12_rehearsal_config import private_document

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / "config" / "private"


def main() -> int:
    """Materialize police and thief playtest TOML files with local listen settings."""
    PRIVATE.mkdir(parents=True, exist_ok=True)
    (PRIVATE / "police.playtest.toml").write_text(
        private_document(
            "GRP00001",
            "police",
            8000,
            8001,
            ROOT / "results" / "playtest-police",
        ),
        encoding="utf-8",
    )
    (PRIVATE / "thief.playtest.toml").write_text(
        private_document(
            "GRP00002",
            "thief",
            8000,
            8001,
            ROOT / "results" / "playtest-thief",
        ),
        encoding="utf-8",
    )
    print("wrote config/private/police.playtest.toml")
    print("wrote config/private/thief.playtest.toml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

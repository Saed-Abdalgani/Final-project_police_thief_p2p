from pathlib import Path

import pytest

from police_thief_p2p.adapters.persistence import AtomicFileRepository


def test_atomic_repository_round_trip_and_overwrite(tmp_path: Path) -> None:
    repository = AtomicFileRepository(tmp_path / "records", max_bytes=8)
    assert repository.load("safe-key") is None
    repository.save("safe-key", b"one")
    repository.save("safe-key", b"two")
    assert repository.load("safe-key") == b"two"
    assert list(repository.root.glob("*.tmp")) == []


def test_atomic_repository_rejects_unsafe_keys_types_and_sizes(tmp_path: Path) -> None:
    repository = AtomicFileRepository(tmp_path, max_bytes=3)
    with pytest.raises(ValueError, match="unsafe"):
        repository.load("../escape")
    with pytest.raises(TypeError, match="bytes"):
        repository.save("record", "bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="size"):
        repository.save("record", b"four")
    with pytest.raises(ValueError, match="positive"):
        AtomicFileRepository(tmp_path, max_bytes=0)

import inspect

import pytest

from police_thief_p2p.adapters.system.deterministic_random import (
    DeterministicRandomSource,
)
from police_thief_p2p.adapters.system.secure_random import CryptographicRandomSource
from police_thief_p2p.services.ports import EntropySource, RandomSource


def test_cryptographic_source_satisfies_ports_and_has_no_seed_parameter() -> None:
    source = CryptographicRandomSource()
    assert isinstance(source, EntropySource)
    assert isinstance(source, RandomSource)
    assert "seed" not in inspect.signature(CryptographicRandomSource).parameters
    assert len(source.token_bytes(16)) == 16
    assert 0 <= source.randbelow(7) < 7
    assert 0.0 <= source.random() < 1.0


@pytest.mark.parametrize("length", [0, -1])
def test_cryptographic_source_rejects_invalid_lengths(length: int) -> None:
    with pytest.raises(ValueError, match="positive"):
        CryptographicRandomSource().token_bytes(length)


def test_cryptographic_source_rejects_invalid_upper_bound() -> None:
    with pytest.raises(ValueError, match="positive"):
        CryptographicRandomSource().randbelow(0)


def test_deterministic_source_repeats_seeded_sequence() -> None:
    first = DeterministicRandomSource(seed=42)
    second = DeterministicRandomSource(seed=42)
    assert [first.random(), first.randbelow(10)] == [second.random(), second.randbelow(10)]
    assert isinstance(first, RandomSource)


def test_deterministic_source_rejects_invalid_upper_bound() -> None:
    with pytest.raises(ValueError, match="positive"):
        DeterministicRandomSource(seed=1).randbelow(0)

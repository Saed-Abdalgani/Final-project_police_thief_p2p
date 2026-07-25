"""Explicitly seeded randomness for tests and reproducible simulation only."""

import random


class DeterministicRandomSource:
    """Provide reproducible non-cryptographic values from an explicit seed."""

    __slots__ = ("_random",)

    def __init__(self, seed: int) -> None:
        """Create a deterministic source; never use it for commitments."""
        self._random = random.Random(seed)

    def random(self) -> float:
        """Return the next deterministic value in [0.0, 1.0)."""
        return self._random.random()

    def randbelow(self, upper_bound: int) -> int:
        """Return the next deterministic value in ``range(upper_bound)``."""
        if upper_bound <= 0:
            msg = "upper_bound must be positive"
            raise ValueError(msg)
        return self._random.randrange(upper_bound)

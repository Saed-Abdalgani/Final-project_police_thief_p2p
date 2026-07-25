"""Production randomness backed exclusively by the OS CSPRNG."""

import secrets


class CryptographicRandomSource:
    """Provide entropy without accepting or exposing a deterministic seed."""

    __slots__ = ()

    def token_bytes(self, length: int) -> bytes:
        """Return exactly ``length`` unpredictable bytes."""
        if length <= 0:
            msg = "length must be positive"
            raise ValueError(msg)
        return secrets.token_bytes(length)

    def random(self) -> float:
        """Return a CSPRNG-backed value in [0.0, 1.0)."""
        return secrets.SystemRandom().random()

    def randbelow(self, upper_bound: int) -> int:
        """Return a CSPRNG-backed value in ``range(upper_bound)``."""
        if upper_bound <= 0:
            msg = "upper_bound must be positive"
            raise ValueError(msg)
        return secrets.randbelow(upper_bound)

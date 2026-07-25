"""Optional natural-language provider port."""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class LanguageRequest:
    """Bounded provider-neutral language request."""

    prompt: str
    max_words: int


@dataclass(frozen=True, slots=True)
class LanguageResponse:
    """Parsed provider-neutral language response."""

    text: str
    token_count: int


@runtime_checkable
class LanguagePort(Protocol):
    """Generate bounded language without selecting game actions."""

    async def generate(self, request: LanguageRequest) -> LanguageResponse:
        """Generate or template-render one response."""
        ...

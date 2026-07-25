"""Immutable category-isolated Beta hint reliability."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReliabilityEntry:
    """Beta parameters and most recent update step for one cue."""

    category: str
    alpha: float
    beta: float
    last_step: int

    def __post_init__(self) -> None:
        """Validate positive Beta parameters and non-negative step."""
        if self.alpha <= 0 or self.beta <= 0 or self.last_step < 0:
            raise ValueError("reliability parameters are invalid")


@dataclass(frozen=True, slots=True)
class HintReliability:
    """Independent Beta priors with deterministic recency shrinkage."""

    entries: tuple[ReliabilityEntry, ...] = ()
    prior_alpha: float = 2.0
    prior_beta: float = 2.0
    recency: float = 0.95

    def __post_init__(self) -> None:
        """Validate prior and recency parameters."""
        if self.prior_alpha <= 0 or self.prior_beta <= 0 or not 0 < self.recency <= 1:
            raise ValueError("hint reliability prior is invalid")
        if len({entry.category for entry in self.entries}) != len(self.entries):
            raise ValueError("hint reliability categories must be unique")

    def mean(self, category: str, current_step: int) -> float:
        """Return category reliability shrunk toward neutral with age."""
        entry = next((item for item in self.entries if item.category == category), None)
        if entry is None:
            raw = self.prior_alpha / (self.prior_alpha + self.prior_beta)
            last_step = 0
        else:
            raw = entry.alpha / (entry.alpha + entry.beta)
            last_step = entry.last_step
        age = max(0, current_step - last_step)
        return 0.5 + (raw - 0.5) * (self.recency**age)

    def update(self, category: str, *, consistent: bool, step: int) -> "HintReliability":
        """Return an updated category without affecting other cues."""
        existing = next((item for item in self.entries if item.category == category), None)
        alpha = self.prior_alpha if existing is None else existing.alpha
        beta = self.prior_beta if existing is None else existing.beta
        replacement = ReliabilityEntry(
            category,
            alpha + int(consistent),
            beta + int(not consistent),
            step,
        )
        others = tuple(item for item in self.entries if item.category != category)
        return HintReliability(
            tuple(sorted((*others, replacement), key=lambda item: item.category)),
            self.prior_alpha,
            self.prior_beta,
            self.recency,
        )

"""Versioned offline tournament specification and board fixture families."""

from dataclasses import dataclass, field
from typing import Final

from police_thief_p2p.shared.config_models import SharedConfig

SPEC_VERSION: Final = "1.0.0"
SPLITS: Final = ("train", "validation", "holdout", "rehearsal")


@dataclass(frozen=True, slots=True)
class BoardFixture:
    """One legal negotiated board family used by every comparison."""

    fixture_id: str
    grid_size: int = 7
    thief_start: tuple[int, int] = (3, 3)
    cop_start: tuple[int, int] = (0, 0)
    max_barriers: int = 14
    max_moves: int = 35
    survival_threshold: int = 35
    axis_origin_corner: str = "top-left"
    axis_start_index: int = 0

    def __post_init__(self) -> None:
        """Reject fixtures outside the legal Appendix F negotiation window."""
        if not self.fixture_id:
            raise ValueError("board fixture requires an identifier")
        if self.grid_size < 7 or self.max_barriers < 14:
            raise ValueError("board fixture weakens a minimum parameter")
        if self.max_moves < 35 or self.survival_threshold < 35:
            raise ValueError("board fixture weakens a minimum step parameter")
        low = self.axis_start_index
        for cell in (self.thief_start, self.cop_start):
            if not all(low <= value < self.grid_size + low for value in cell):
                raise ValueError("board fixture start is outside the board")
        if self.thief_start == self.cop_start:
            raise ValueError("board fixture starts must be distinct")

    def apply(self, base: SharedConfig) -> SharedConfig:
        """Return the shared constitution with this fixture's negotiated board."""
        board = base.board_and_agents.model_copy(
            update={
                "grid_size": self.grid_size,
                "thief_start": self.thief_start,
                "cop_start": self.cop_start,
                "axis_origin_corner": self.axis_origin_corner,
                "axis_start_index": self.axis_start_index,
            }
        )
        movement = base.movement_and_barriers.model_copy(
            update={
                "max_barriers": self.max_barriers,
                "max_moves": self.max_moves,
                "survival_threshold": self.survival_threshold,
            }
        )
        return base.model_copy(
            update={"board_and_agents": board, "movement_and_barriers": movement}
        )


@dataclass(frozen=True, slots=True)
class TournamentSpec:
    """Immutable declaration of one reproducible paired tournament campaign."""

    campaign_id: str
    split: str
    candidate_id: str
    opponent_ids: tuple[str, ...]
    fixtures: tuple[BoardFixture, ...]
    seeds: tuple[int, ...]
    spec_version: str = SPEC_VERSION
    repetitions: int = 1
    decision_budget_ms: int = 250
    max_latency_ms: float = 250.0
    primary_metric: str = "official_score_uplift"
    observation_delay: int = 0
    scent_dropout: float = 0.0
    extras: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Validate identities, split membership, and bounded resource limits."""
        if not self.campaign_id or not self.candidate_id:
            raise ValueError("tournament spec requires campaign and candidate identities")
        if self.split not in SPLITS:
            raise ValueError(f"tournament split must be one of {SPLITS}")
        if not self.opponent_ids or len(set(self.opponent_ids)) != len(self.opponent_ids):
            raise ValueError("tournament spec requires unique opponents")
        if not self.fixtures or len({item.fixture_id for item in self.fixtures}) != len(
            self.fixtures
        ):
            raise ValueError("tournament spec requires unique board fixtures")
        if not self.seeds or len(set(self.seeds)) != len(self.seeds):
            raise ValueError("tournament spec requires unique seeds")
        if not 1 <= self.repetitions <= 100:
            raise ValueError("tournament repetitions are outside the bounded range")
        if not 20 <= self.decision_budget_ms <= 5_000 or self.max_latency_ms <= 0:
            raise ValueError("tournament resource limits are invalid")
        if self.observation_delay < 0 or not 0.0 <= self.scent_dropout <= 1.0:
            raise ValueError("tournament observation degradation is invalid")

    @property
    def match_count(self) -> int:
        """Return the exact number of role-swapped matches this spec runs."""
        pairs = len(self.opponent_ids) * len(self.fixtures) * len(self.seeds)
        return pairs * self.repetitions * 2

    def as_document(self) -> dict[str, object]:
        """Return the canonical serializable declaration of this campaign."""
        return {
            "spec_version": self.spec_version,
            "campaign_id": self.campaign_id,
            "split": self.split,
            "candidate_id": self.candidate_id,
            "opponent_ids": list(self.opponent_ids),
            "fixture_ids": [item.fixture_id for item in self.fixtures],
            "seeds": list(self.seeds),
            "repetitions": self.repetitions,
            "decision_budget_ms": self.decision_budget_ms,
            "max_latency_ms": self.max_latency_ms,
            "primary_metric": self.primary_metric,
            "observation_delay": self.observation_delay,
            "scent_dropout": self.scent_dropout,
            "match_count": self.match_count,
            "extras": [list(item) for item in self.extras],
        }

"""Reusable monotonic deadlines and effective operation policy."""

from dataclasses import dataclass
from enum import StrEnum

from police_thief_p2p.services.ports.clock import ClockPort
from police_thief_p2p.shared.effective_config import EffectiveConfig


class Operation(StrEnum):
    """Every bounded external or expensive lifecycle operation."""

    NEGOTIATION = "negotiation"
    MCP = "mcp"
    ACKNOWLEDGEMENT = "acknowledgement"
    REVEAL = "reveal"
    STRATEGY = "strategy"
    LLM = "llm"
    AUDIT = "audit"
    REPORTING = "reporting"


@dataclass(frozen=True, slots=True)
class DeadlineTracker:
    """Absolute monotonic deadline with safe remaining/expired operations."""

    clock: ClockPort
    deadline: float

    @classmethod
    def after(cls, clock: ClockPort, seconds: float) -> "DeadlineTracker":
        """Create a positive relative deadline."""
        if seconds <= 0:
            raise ValueError("deadline duration must be positive")
        return cls(clock, clock.monotonic() + seconds)

    def remaining(self) -> float:
        """Return non-negative remaining seconds."""
        return max(0.0, self.deadline - self.clock.monotonic())

    def expired(self) -> bool:
        """Return whether no time remains."""
        return self.remaining() <= 0


@dataclass(frozen=True, slots=True)
class DeadlinePolicy:
    """Config-derived timeout seconds for every operation."""

    values: dict[Operation, float]
    watchdog_timeout: float

    @classmethod
    def from_effective(cls, config: EffectiveConfig) -> "DeadlinePolicy":
        """Apply shared binding response/watchdog limits plus private local limits."""
        league = config.shared.network_and_league
        private = config.private.reliability
        language = config.private.language
        return cls(
            {
                Operation.NEGOTIATION: private.negotiation_timeout_sec,
                Operation.MCP: league.response_timeout_sec,
                Operation.ACKNOWLEDGEMENT: private.acknowledgement_timeout_sec,
                Operation.REVEAL: private.reveal_timeout_sec,
                Operation.STRATEGY: private.strategy_timeout_sec,
                Operation.LLM: language.deadline_sec,
                Operation.AUDIT: private.audit_timeout_sec,
                Operation.REPORTING: private.reporting_timeout_sec,
            },
            float(league.watchdog_timeout_sec),
        )

    def tracker(self, operation: Operation, clock: ClockPort) -> DeadlineTracker:
        """Create one tracker; no operation can omit a configured timeout."""
        return DeadlineTracker.after(clock, self.values[operation])

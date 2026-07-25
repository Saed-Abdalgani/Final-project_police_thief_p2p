"""Private orchestration deadlines, retry budgets, and queue capacities."""

from typing import Annotated

from pydantic import Field, StrictInt

from police_thief_p2p.shared.config_sections import FrozenModel


class ReliabilityConfig(FrozenModel):
    """Bounded private operational policy; shared response limits still win."""

    negotiation_timeout_sec: Annotated[StrictInt, Field(ge=1, le=600)] = 60
    acknowledgement_timeout_sec: Annotated[StrictInt, Field(ge=1, le=300)] = 30
    reveal_timeout_sec: Annotated[StrictInt, Field(ge=1, le=300)] = 30
    strategy_timeout_sec: Annotated[StrictInt, Field(ge=1, le=30)] = 1
    audit_timeout_sec: Annotated[StrictInt, Field(ge=1, le=3_600)] = 120
    reporting_timeout_sec: Annotated[StrictInt, Field(ge=1, le=3_600)] = 120
    max_attempts: Annotated[StrictInt, Field(ge=1, le=20)] = 4
    max_backoff_ms: Annotated[StrictInt, Field(ge=1, le=60_000)] = 2_000
    gameplay_queue_capacity: Annotated[StrictInt, Field(ge=1, le=10_000)] = 128
    optional_queue_capacity: Annotated[StrictInt, Field(ge=1, le=10_000)] = 32
    circuit_failure_threshold: Annotated[StrictInt, Field(ge=1, le=100)] = 3
    circuit_cooldown_sec: Annotated[StrictInt, Field(ge=1, le=600)] = 10

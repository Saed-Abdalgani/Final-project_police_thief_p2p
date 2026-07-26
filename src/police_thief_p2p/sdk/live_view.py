"""Immutable privacy-safe DTOs for live monitoring."""

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Final

from police_thief_p2p.domain.state import LocalGameState
from police_thief_p2p.domain.values import Position
from police_thief_p2p.services.belief.models import BeliefUpdate
from police_thief_p2p.shared.config_models import SharedConfig
from police_thief_p2p.shared.redaction import redact_text

FORBIDDEN_LIVE_FIELDS: Final = frozenset(
    {
        "opponent_true_position",
        "opponent_track",
        "objective_board",
        "other_peer_private_log",
        "secret_nonce",
        "nonce",
        "future_reveal",
        "private_key",
        "credential",
        "access_token",
        "refresh_token",
    }
)


class ViewStatus(StrEnum):
    """Complete accessible live-status vocabulary."""

    READY = "ready"
    THINKING = "thinking"
    WAITING = "waiting"
    LOCKED = "locked"
    PAUSED = "paused"
    DEGRADED = "degraded"
    TERMINAL = "terminal"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class ViewMetrics:
    """Safe operational metrics shown to the local operator."""

    latency_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    fallback_used: bool = False

    def __post_init__(self) -> None:
        """Reject negative or boolean counters."""
        values = (self.latency_ms, self.input_tokens, self.output_tokens)
        if any(type(value) is not int or value < 0 for value in values):
            raise ValueError("live metrics must be non-negative integers")


@dataclass(frozen=True, slots=True)
class SnapshotContext:
    """Non-secret presentation context accompanying one local state."""

    sub_game_number: int
    series_games: int = 6
    status: ViewStatus = ViewStatus.READY
    status_detail: str = "Ready for local play."
    latest_sent_hint: str = ""
    latest_received_hint: str = ""
    own_verdict: str = "pending"
    audit_text: str = "Audit pending"
    correlation_id: str | None = None
    metrics: ViewMetrics = ViewMetrics()
    final: bool = False


@dataclass(frozen=True, slots=True)
class LocalView:
    """Allowlisted live view that cannot represent opponent objective truth."""

    role: str
    own_position: tuple[int, int]
    own_visited: tuple[tuple[int, int], ...]
    board_size: int
    axis_origin_corner: str
    axis_start_index: int
    public_barriers: tuple[tuple[int, int], ...]
    belief_heatmap: tuple[str, ...]
    belief_entropy_bits: float
    belief_peak_probability: float
    credible_region: tuple[tuple[int, int], ...]
    posterior_peak: tuple[int, int]
    step_number: int
    sub_game_number: int
    series_games: int
    barriers_placed: int
    max_barriers: int
    latest_sent_hint: str
    latest_received_hint: str
    own_verdict: str
    metrics: ViewMetrics
    status: ViewStatus
    status_detail: str
    audit_text: str
    correlation_id: str | None
    final: bool

    def as_dict(self) -> dict[str, object]:
        """Return a recursively privacy-checked presentation document."""
        value = asdict(self)
        assert_private_document(value)
        return value


def build_local_view(
    state: LocalGameState,
    update: BeliefUpdate,
    config: SharedConfig,
    context: SnapshotContext,
) -> LocalView:
    """Build one immutable local snapshot from authoritative SDK inputs."""
    belief = update.belief
    if state.rules.board.size != belief.size or belief.size != config.board_and_agents.grid_size:
        raise ValueError("local state, belief, and configuration dimensions differ")

    def cells(values: Iterable[Position]) -> tuple[tuple[int, int], ...]:
        return tuple(sorted((item.row, item.col) for item in values))

    view = LocalView(
        role=state.role.value,
        own_position=(state.position.row, state.position.col),
        own_visited=cells(state.visited),
        board_size=belief.size,
        axis_origin_corner=config.board_and_agents.axis_origin_corner.value,
        axis_start_index=config.board_and_agents.axis_start_index,
        public_barriers=cells(state.public_barriers.cells),
        belief_heatmap=belief.serialized(),
        belief_entropy_bits=update.diagnostics.entropy_bits,
        belief_peak_probability=update.diagnostics.peak_probability,
        credible_region=update.diagnostics.credible_region,
        posterior_peak=update.diagnostics.most_likely_cell,
        step_number=state.step_number,
        sub_game_number=context.sub_game_number,
        series_games=context.series_games,
        barriers_placed=state.barriers_placed,
        max_barriers=state.rules.max_barriers,
        latest_sent_hint=redact_text(context.latest_sent_hint)[:2_000],
        latest_received_hint=redact_text(context.latest_received_hint)[:2_000],
        own_verdict=context.own_verdict,
        metrics=context.metrics,
        status=context.status,
        status_detail=redact_text(context.status_detail)[:500],
        audit_text=redact_text(context.audit_text)[:500],
        correlation_id=context.correlation_id,
        final=context.final,
    )
    assert_private_document(view.as_dict())
    return view


def assert_private_document(value: object) -> None:
    """Reject forbidden field names anywhere in a live presentation document."""
    if isinstance(value, dict):
        forbidden = {
            key for key in value if any(part in key.casefold() for part in FORBIDDEN_LIVE_FIELDS)
        }
        if forbidden:
            raise ValueError(f"live view contains forbidden fields: {sorted(forbidden)!r}")
        for item in value.values():
            assert_private_document(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_private_document(item)

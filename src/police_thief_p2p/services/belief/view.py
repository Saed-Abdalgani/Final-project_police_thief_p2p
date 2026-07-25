"""Redacted local view containing own truth and belief diagnostics only."""

from dataclasses import dataclass

from police_thief_p2p.domain.state import LocalGameState
from police_thief_p2p.services.belief.grid import BeliefGrid
from police_thief_p2p.services.belief.models import BeliefDiagnostics


@dataclass(frozen=True, slots=True)
class LocalView:
    """Safe GUI/strategy view with no opponent true-position field."""

    role: str
    own_position: tuple[int, int]
    step_number: int
    public_barriers: tuple[tuple[int, int], ...]
    belief_heatmap: tuple[str, ...]
    belief_entropy_bits: float
    belief_peak_probability: float
    credible_region: tuple[tuple[int, int], ...]
    most_likely_cell_diagnostic: tuple[int, int]


def create_local_view(
    state: LocalGameState,
    belief: BeliefGrid,
    diagnostics: BeliefDiagnostics,
) -> LocalView:
    """Compose an immutable redacted view from local state and posterior."""
    if state.rules.board.size != belief.size:
        raise ValueError("local state and belief dimensions differ")
    barriers = tuple(
        (cell.row, cell.col)
        for cell in sorted(state.public_barriers.cells, key=lambda item: (item.row, item.col))
    )
    return LocalView(
        role=state.role.value,
        own_position=(state.position.row, state.position.col),
        step_number=state.step_number,
        public_barriers=barriers,
        belief_heatmap=belief.serialized(),
        belief_entropy_bits=diagnostics.entropy_bits,
        belief_peak_probability=diagnostics.peak_probability,
        credible_region=diagnostics.credible_region,
        most_likely_cell_diagnostic=diagnostics.most_likely_cell,
    )

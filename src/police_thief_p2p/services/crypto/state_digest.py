"""Canonical local-state digest used by commitments and offline replay."""

from police_thief_p2p.domain.state import LocalGameState
from police_thief_p2p.shared.canonical_json import sha256_digest


def local_state_digest(state: LocalGameState) -> str:
    """Bind all outcome-relevant local truth and public state."""
    return sha256_digest(
        {
            "role": state.role.value,
            "position": [state.position.row, state.position.col],
            "board_size": state.rules.board.size,
            "max_barriers": state.rules.max_barriers,
            "max_steps": state.rules.max_steps,
            "survival_threshold": state.rules.survival_threshold,
            "public_barriers": sorted([cell.row, cell.col] for cell in state.public_barriers.cells),
            "barriers_placed": state.barriers_placed,
            "step_number": state.step_number,
            "visited": sorted([cell.row, cell.col] for cell in state.visited),
            "terminal_reason": (
                None if state.terminal_reason is None else state.terminal_reason.value
            ),
        }
    )

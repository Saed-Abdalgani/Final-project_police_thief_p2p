"""Pure verified terminal predicates separated from live local state."""

from police_thief_p2p.domain.board import BarrierSet, Board
from police_thief_p2p.domain.values import Position, TerminalReason


def direct_capture(police_position: Position, thief_position: Position) -> bool:
    """Return whether Police landed on the verified Thief cell."""
    return police_position == thief_position


def barrier_capture(barrier_target: Position, thief_position: Position) -> bool:
    """Return whether a newly placed barrier targets the verified Thief cell."""
    return barrier_target == thief_position


def enclosure_capture(
    board: Board,
    thief_position: Position,
    barriers: BarrierSet,
) -> bool:
    """Return whether Thief has no spatial N/S/E/W escape; STAY is excluded."""
    if not board.contains(thief_position):
        raise ValueError("thief position is outside the board")
    if thief_position in barriers:
        return True
    return not board.neighbors(thief_position, barriers)


def survival_reached(completed_steps: int, threshold: int) -> bool:
    """Return whether the configured survival threshold has been reached."""
    if completed_steps < 0 or threshold < 1:
        raise ValueError("steps must be non-negative and threshold positive")
    return completed_steps >= threshold


def maximum_step_reached(completed_steps: int, ceiling: int) -> bool:
    """Return whether the exact configured step ceiling has been reached."""
    if completed_steps < 0 or ceiling < 1:
        raise ValueError("steps must be non-negative and ceiling positive")
    return completed_steps >= ceiling


def resolve_verified_terminal(
    *,
    board: Board,
    police_position: Position,
    thief_position: Position,
    barriers: BarrierSet,
    completed_steps: int,
    survival_threshold: int,
    max_steps: int,
    placed_barrier: Position | None = None,
    technical: bool = False,
    tamper: bool = False,
    stopped: bool = False,
) -> TerminalReason | None:
    """Resolve a verified offline outcome in deterministic sanction/physics order."""
    if not board.contains(police_position) or not board.contains(thief_position):
        raise ValueError("verified position is outside the board")
    if any(not board.contains(position) for position in barriers.cells):
        raise ValueError("verified barrier is outside the board")
    if placed_barrier is not None and not board.contains(placed_barrier):
        raise ValueError("placed barrier is outside the board")
    survived = survival_reached(completed_steps, survival_threshold)
    ceiling_reached = maximum_step_reached(completed_steps, max_steps)
    if tamper:
        return TerminalReason.TAMPER
    if technical:
        return TerminalReason.TECHNICAL
    if placed_barrier is not None and barrier_capture(placed_barrier, thief_position):
        return TerminalReason.BARRIER_CAPTURE
    if direct_capture(police_position, thief_position):
        return TerminalReason.CAPTURE
    if enclosure_capture(board, thief_position, barriers):
        return TerminalReason.ENCLOSURE
    if survived:
        return TerminalReason.SURVIVAL
    if ceiling_reached:
        return TerminalReason.STEP_CEILING
    if stopped:
        return TerminalReason.STOPPED
    return None

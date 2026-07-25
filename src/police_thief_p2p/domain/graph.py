"""Deterministic graph helpers over the public board and barriers."""

from collections import deque

from police_thief_p2p.domain.board import EMPTY_BARRIERS, BarrierSet, Board
from police_thief_p2p.domain.values import Position


def connected_component(
    board: Board,
    start: Position,
    barriers: BarrierSet = EMPTY_BARRIERS,
) -> frozenset[Position]:
    """Return every passable cell reachable from ``start``."""
    if not board.contains(start) or start in barriers:
        return frozenset()
    reached = {start}
    pending = deque([start])
    while pending:
        current = pending.popleft()
        for neighbor in board.neighbors(current, barriers):
            if neighbor not in reached:
                reached.add(neighbor)
                pending.append(neighbor)
    return frozenset(reached)


def reachable_region(
    board: Board,
    start: Position,
    barriers: BarrierSet = EMPTY_BARRIERS,
) -> frozenset[Position]:
    """Return the current public reachable region for a cell."""
    return connected_component(board, start, barriers)


def connected_components(
    board: Board,
    barriers: BarrierSet = EMPTY_BARRIERS,
) -> tuple[frozenset[Position], ...]:
    """Return all passable components in deterministic row-major order."""
    remaining = {position for position in board.cells() if position not in barriers}
    components: list[frozenset[Position]] = []
    while remaining:
        start = min(remaining, key=lambda item: (item.row, item.col))
        component = connected_component(board, start, barriers)
        components.append(component)
        remaining.difference_update(component)
    return tuple(components)


def shortest_path_length(
    board: Board,
    start: Position,
    goal: Position,
    barriers: BarrierSet = EMPTY_BARRIERS,
) -> int | None:
    """Return BFS distance, or ``None`` when either cell is blocked/unreachable."""
    if not board.contains(start) or not board.contains(goal):
        raise ValueError("path endpoint is outside the board")
    if start in barriers or goal in barriers:
        return None
    pending = deque([(start, 0)])
    reached = {start}
    while pending:
        current, distance = pending.popleft()
        if current == goal:
            return distance
        for neighbor in board.neighbors(current, barriers):
            if neighbor not in reached:
                reached.add(neighbor)
                pending.append((neighbor, distance + 1))
    return None


def articulation_points(
    board: Board,
    barriers: BarrierSet = EMPTY_BARRIERS,
) -> frozenset[Position]:
    """Return vertices whose removal increases public component count."""
    baseline = len(connected_components(board, barriers))
    points = {
        position
        for position in board.cells()
        if position not in barriers
        and len(connected_components(board, barriers.add(position))) > baseline
    }
    return frozenset(points)


def _is_boundary(board: Board, position: Position) -> bool:
    return position.row in (0, board.size - 1) or position.col in (0, board.size - 1)


def _escape_path(
    board: Board,
    start: Position,
    blocked: BarrierSet,
) -> tuple[Position, ...] | None:
    pending = deque([start])
    parents: dict[Position, Position | None] = {start: None}
    destination: Position | None = None
    while pending:
        current = pending.popleft()
        if _is_boundary(board, current):
            destination = current
            break
        for neighbor in board.neighbors(current, blocked):
            if neighbor not in parents:
                parents[neighbor] = current
                pending.append(neighbor)
    if destination is None:
        return None
    reversed_path: list[Position] = []
    cursor: Position | None = destination
    while cursor is not None:
        reversed_path.append(cursor)
        cursor = parents[cursor]
    return tuple(reversed(reversed_path))


def vertex_disjoint_escape_routes(
    board: Board,
    start: Position,
    barriers: BarrierSet = EMPTY_BARRIERS,
) -> tuple[tuple[Position, ...], ...]:
    """Greedily approximate internally vertex-disjoint routes to the boundary."""
    if not board.contains(start):
        raise ValueError("start is outside the board")
    if _is_boundary(board, start):
        return ((start,),)
    base_blocked = BarrierSet(barriers.cells - {start})
    reserved: set[Position] = set()
    routes: list[tuple[Position, ...]] = []
    for neighbor in board.neighbors(start, base_blocked):
        if neighbor in reserved:
            continue
        blocked = BarrierSet(base_blocked.cells | reserved | {start})
        path = _escape_path(board, neighbor, blocked)
        if path is not None:
            route = (start, *path)
            routes.append(route)
            reserved.update(path)
    return tuple(routes)

import pytest

from police_thief_p2p.domain import (
    BarrierSet,
    Board,
    Position,
    articulation_points,
    connected_component,
    connected_components,
    shortest_path_length,
    vertex_disjoint_escape_routes,
)
from police_thief_p2p.domain.graph import reachable_region


def _horizontal_corridor() -> BarrierSet:
    return BarrierSet(frozenset(Position(row, col) for row in (0, 2) for col in range(3)))


def test_shortest_path_golden_boards_and_invalid_endpoints() -> None:
    board = Board(3)
    assert shortest_path_length(board, Position(0, 0), Position(2, 2)) == 4
    assert shortest_path_length(board, Position(1, 1), Position(1, 1)) == 0
    wall = BarrierSet(frozenset(Position(1, col) for col in range(3)))
    assert shortest_path_length(board, Position(0, 0), Position(2, 2), wall) is None
    assert shortest_path_length(board, Position(0, 0), Position(1, 1), wall) is None
    with pytest.raises(ValueError, match="endpoint"):
        shortest_path_length(board, Position(-1, 0), Position(0, 0))


def test_components_and_reachable_regions_match_graph_fixtures() -> None:
    board = Board(3)
    wall = BarrierSet(frozenset(Position(1, col) for col in range(3)))
    components = connected_components(board, wall)
    assert tuple(len(component) for component in components) == (3, 3)
    assert connected_component(board, Position(0, 0), wall) == frozenset(
        Position(0, col) for col in range(3)
    )
    assert reachable_region(board, Position(0, 0), wall) == components[0]
    assert connected_component(board, Position(1, 0), wall) == frozenset()
    assert connected_component(board, Position(-1, 0), wall) == frozenset()


def test_articulation_points_detect_corridor_cut_vertices() -> None:
    board = Board(3)
    assert articulation_points(board) == frozenset()
    assert articulation_points(board, _horizontal_corridor()) == frozenset({Position(1, 1)})


def test_vertex_disjoint_escape_route_approximation() -> None:
    board = Board(5)
    open_routes = vertex_disjoint_escape_routes(board, Position(2, 2))
    assert len(open_routes) == 4
    assert all(route[0] == Position(2, 2) for route in open_routes)
    used = [cell for route in open_routes for cell in route[1:]]
    assert len(used) == len(set(used))

    corridor = BarrierSet(
        frozenset(Position(row, col) for row in range(5) for col in range(5) if row != 2)
    )
    assert len(vertex_disjoint_escape_routes(board, Position(2, 2), corridor)) == 2
    assert vertex_disjoint_escape_routes(board, Position(0, 2)) == ((Position(0, 2),),)
    blocked = BarrierSet(
        frozenset({Position(1, 2), Position(3, 2), Position(2, 1), Position(2, 3)})
    )
    assert vertex_disjoint_escape_routes(board, Position(2, 2), blocked) == ()
    sealed_boundary = BarrierSet(
        frozenset(
            position
            for position in board.cells()
            if position.row in (0, 4) or position.col in (0, 4)
        )
    )
    assert vertex_disjoint_escape_routes(board, Position(2, 2), sealed_boundary) == ()
    with pytest.raises(ValueError, match="outside"):
        vertex_disjoint_escape_routes(board, Position(5, 0))


def test_escape_routes_never_reuse_a_reserved_start_neighbor() -> None:
    board = Board(4)
    barriers = BarrierSet(
        frozenset(
            Position(row, col)
            for row, col in {
                (0, 1),
                (0, 2),
                (0, 3),
                (1, 0),
                (1, 3),
                (2, 3),
                (3, 0),
            }
        )
    )
    routes = vertex_disjoint_escape_routes(board, Position(2, 2), barriers)
    used = [cell for route in routes for cell in route[1:]]
    assert len(routes) == 2
    assert len(used) == len(set(used))

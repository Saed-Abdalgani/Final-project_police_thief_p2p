import inspect

import pytest

import police_thief_p2p.domain as domain

pytestmark = pytest.mark.contract

PUBLIC_API_TASKS = {
    "Action": "T124",
    "ActionType": "T124",
    "BarrierPlaced": "T144",
    "BarrierSet": "T129",
    "Board": "T127",
    "Direction": "T123",
    "GameRules": "T136",
    "GroupTotal": "T155",
    "LocalGameState": "T136",
    "Position": "T122",
    "Role": "T125",
    "RoleAssignment": "T156",
    "RolePoints": "T151",
    "SeriesScore": "T154",
    "SubGameOutcome": "T155",
    "TerminalReason": "T150",
    "TransitionResult": "T157",
    "aggregate_series": "T155",
    "articulation_points": "T134",
    "balanced_schedule": "T156",
    "barrier_capture": "T146",
    "connected_component": "T133",
    "connected_components": "T133",
    "direct_capture": "T145",
    "enclosure_capture": "T147",
    "initial_local_state": "T137/T138",
    "maximum_step_reached": "T149",
    "reachable_region": "T133",
    "resolve_verified_terminal": "T150",
    "score_terminal": "T151/T152/T153",
    "series_tie_awards": "T154",
    "shortest_path_length": "T132",
    "survival_reached": "T148",
    "transition": "T157",
    "vertex_disjoint_escape_routes": "T135",
}


def test_public_domain_inventory_is_complete_documented_and_traceable() -> None:
    assert set(domain.__all__) == set(PUBLIC_API_TASKS)
    assert len(domain.__all__) == len(set(domain.__all__))
    for name in domain.__all__:
        assert inspect.getdoc(getattr(domain, name)), name

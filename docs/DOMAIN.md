# Deterministic Domain Engine

## Boundary

The M3 engine is network-free and deterministic. Application adapters use
`SimulationSdk`; protected CLI, GUI, MCP, and email adapters may not import
`police_thief_p2p.domain`. Internal services and tests can use the pure domain API.

Live state is local truth only:

- own role and true position;
- immutable shared physics limits;
- permanent public barriers;
- own barrier use;
- shared step number;
- own visited cells;
- typed terminal reason.

There is deliberately no opponent true-position field or objective live world.
Capture resolution that needs both revealed positions is a pure offline/audit
predicate and retains neither position.

## Physics

Directions are exactly `N`, `S`, `E`, and `W`. An `Action` is exactly one of:

- MOVE with one direction;
- STAY with no direction or target;
- BARRIER with one exact target and no direction.

Barriers form a persistent `frozenset`. Insertion returns a new set, duplicate
insertion is idempotent, and no removal API exists. Police candidates are the
current cell followed by passable adjacent cells. A barrier consumes the action
instead of movement and is rejected after the signed quota.

The engine permits the book's Police-on-own-cell barrier. Police may subsequently
leave that cell but neither role may enter it. Enclosure examines spatial cardinal
neighbors only; STAY cannot defeat capture.

## Graph helpers

All graph operations use public barriers only:

| Helper | Contract |
|---|---|
| `shortest_path_length` | deterministic BFS length or `None` |
| `connected_component` / `reachable_region` | all passable reachable cells |
| `connected_components` | row-major deterministic component sequence |
| `articulation_points` | cells whose removal increases component count |
| `vertex_disjoint_escape_routes` | greedy deterministic, internally disjoint boundary paths |

## Outcomes and scoring

Terminal reasons remain distinct: capture, barrier capture, enclosure, survival,
step ceiling, technical, tamper, and stopped. Capture-class outcomes score 20/5;
survival/ceiling score 5/10; sanctions/stopped score 0/0. Aggregation retains group
identity across the balanced six-game P,T,P,T,P,T schedule. Equal raw totals receive
the fixed 2/2 tie award.

Golden direct-capture, barrier-capture, enclosure, survival, technical, and tie
fixtures live in `data/conformance/domain/golden_scenarios.json`.

## SDK example

```python
from pathlib import Path

from police_thief_p2p import SimulationSdk
from police_thief_p2p.sdk import Action, Role

sdk = SimulationSdk()
effective = sdk.load_configuration(
    Path("config/shared/game.example.json").read_bytes(),
    Path("config/private/game.example.toml").read_bytes(),
)
state = sdk.create_local_game(effective.shared, Role.POLICE)
result = sdk.apply_action(state, Action.stay())
assert result.state.step_number == 1
```

## Evidence

- 10,000 generated transition cases enforce legal-action closure and state invariants.
- Eight origin/index combinations produce identical normalized transitions.
- The public API inventory maps every exported symbol to T122-T157.
- Every domain source module has 100% branch-aware coverage.
- Performance results are committed at `results/benchmarks/m3_domain.json`.

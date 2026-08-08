"""Open the verified-replay GUI on a deterministic finished-match fixture."""

from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path

from police_thief_p2p.adapters.gui.replay_app import ReplayApp
from police_thief_p2p.sdk import SimulationSdk
from police_thief_p2p.shared.canonical_json import canonical_json_bytes
from scripts.m12_campaign_support import SHARED_CONFIG, load_shared_path
from tests.helpers.replay import GROUPS, build_replay_fixture, build_replay_manifest

ROOT = Path(__file__).resolve().parents[1]
DEMO_ROOT = ROOT / "results" / "replay-demo"


def materialize() -> tuple[Path, Path]:
    """Write a fresh artifact tree (official files are immutable / read-only)."""
    shared = load_shared_path(SHARED_CONFIG)
    run_root = DEMO_ROOT / f"run-{uuid.uuid4().hex[:8]}"
    run_root.mkdir(parents=True, exist_ok=False)
    manifest = build_replay_manifest(run_root, shared)
    manifest_path = run_root / "manifest.json"
    manifest_path.write_bytes(canonical_json_bytes(manifest.model_dump(mode="json")))
    return manifest_path, run_root


def verified_results() -> tuple[object, ...]:
    """Verify finished sub-game fixtures for the Tk navigator."""
    shared = load_shared_path(SHARED_CONFIG)
    sdk = SimulationSdk()
    return tuple(
        sdk.verify_log(
            build_replay_fixture(shared, number).log_bytes,
            build_replay_fixture(shared, number).config_bytes,
            viewer_group=GROUPS[0],
        )
        for number in range(1, 7)
    )


def main() -> int:
    """Materialize artifacts, print CLI verify hint, then open ReplayApp."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-gui", action="store_true", help="only write artifacts + CLI verify")
    parser.add_argument("--seconds", type=float, default=None, help="auto-close GUI after N seconds")
    args = parser.parse_args()
    manifest_path, artifact_root = materialize()
    sdk = SimulationSdk()
    result = sdk.verify_manifest_log(
        manifest_path.read_bytes(),
        artifact_root,
        sub_game_number=1,
        viewer_group=GROUPS[0],
    )
    print(
        json.dumps(
            {
                "integrity": result.integrity.value,
                "frames": len(result.frames),
                "manifest": str(manifest_path),
                "artifact_root": str(artifact_root),
            },
            sort_keys=True,
        )
    )
    print(
        "CLI replay:\n"
        f'  uv run police-thief-p2p replay verify --manifest "{manifest_path}" '
        f'--artifact-root "{artifact_root}" --group {GROUPS[0]} --sub-game 1'
    )
    if args.no_gui:
        return 0 if result.integrity.value == "Verified OK" else 1
    app = ReplayApp(
        sdk,
        verified_results(),
        board_size=int(load_shared_path(SHARED_CONFIG).board_and_agents.grid_size),
    )
    if args.seconds is not None and args.seconds > 0:
        app.root.after(int(args.seconds * 1000), app.root.destroy)
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

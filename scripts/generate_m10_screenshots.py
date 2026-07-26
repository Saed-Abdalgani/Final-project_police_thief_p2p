"""Generate deterministic M10 live and replay SVG evidence."""

from collections.abc import Sequence
from pathlib import Path

from police_thief_p2p.adapters.gui.snapshot_svg import live_view_svg, replay_svg
from police_thief_p2p.sdk import (
    LocalView,
    ReplayFinding,
    ReplayFrame,
    ReplayIntegrity,
    ReplayMode,
    ReplayVerification,
    ViewMetrics,
    ViewStatus,
)


def sample_live_view() -> LocalView:
    """Return the frozen local-truth screenshot fixture."""
    weights = tuple("0.5" if index == 24 else "0.010416666667" for index in range(49))
    return LocalView(
        role="police",
        own_position=(2, 1),
        own_visited=((0, 0), (1, 0), (2, 0), (2, 1)),
        board_size=7,
        axis_origin_corner="top-left",
        axis_start_index=0,
        public_barriers=((1, 3), (3, 3), (4, 3)),
        belief_heatmap=weights,
        belief_entropy_bits=4.127,
        belief_peak_probability=0.5,
        credible_region=((3, 3), (2, 3), (3, 2), (3, 4), (4, 3)),
        posterior_peak=(3, 3),
        step_number=8,
        sub_game_number=2,
        series_games=6,
        barriers_placed=3,
        max_barriers=14,
        latest_sent_hint="Checking the west corridor",
        latest_received_hint="I prefer open ground",
        own_verdict="uncertain",
        metrics=ViewMetrics(42, 18, 7, False),
        status=ViewStatus.WAITING,
        status_detail="Waiting for peer reveal.",
        audit_text="Commitment acknowledged and locked.",
        correlation_id=None,
        final=False,
    )


def sample_replay(tampered: bool = False) -> ReplayVerification:
    """Return a frozen post-audit replay screenshot fixture."""
    frames = (
        ReplayFrame(
            sequence=1,
            actor="police",
            actor_step=1,
            action="S",
            own_position=(1, 0),
            police_position=(1, 0),
            thief_position=(3, 3),
            public_barriers=(),
            belief_heatmap=(),
            commitment_status="Verified OK",
            terminal_reason=None,
        ),
        ReplayFrame(
            sequence=2,
            actor="thief",
            actor_step=1,
            action="STAY",
            own_position=(1, 0),
            police_position=(1, 0),
            thief_position=(3, 3),
            public_barriers=(),
            belief_heatmap=(),
            commitment_status="Verified OK",
            terminal_reason=None,
        ),
    )
    findings = (
        (ReplayFinding(1, "COMMITMENT", "step:3", "recomputed commitment differs"),)
        if tampered
        else ()
    )
    return ReplayVerification(
        game_uid="12345678-1234-4234-8234-123456789abc",
        sub_game_number=1,
        mode=ReplayMode.OBJECTIVE,
        integrity=ReplayIntegrity.TAMPERED if tampered else ReplayIntegrity.VERIFIED_OK,
        verified_steps=2,
        expected_steps=11,
        terminal_reason="tamper" if tampered else "capture",
        police_points=0 if tampered else 20,
        thief_points=0 if tampered else 5,
        frames=frames,
        findings=findings,
        track_banner="Objective tracks verified and linked.",
        evidence_sha256="a" * 64,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Write all deterministic screenshot fixtures."""
    root = Path(argv[0]) if argv else Path("docs/screenshots")
    root.mkdir(parents=True, exist_ok=True)
    documents = {
        "m10_live_local_view.svg": live_view_svg(sample_live_view()),
        "m10_replay_verified.svg": replay_svg(sample_replay()),
        "m10_replay_tampered.svg": replay_svg(sample_replay(tampered=True)),
    }
    for name, document in documents.items():
        (root / name).write_bytes(document)
    print(f"Generated {len(documents)} deterministic M10 screenshots in {root}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

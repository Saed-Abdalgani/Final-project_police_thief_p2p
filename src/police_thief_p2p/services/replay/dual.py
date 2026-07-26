"""Post-audit linkage gate for objective dual-log replay."""

from dataclasses import replace

from police_thief_p2p.services.artifacts.records import (
    PlayedConfigArtifact,
    SubGameLogArtifact,
)
from police_thief_p2p.services.replay.models import (
    ReplayFinding,
    ReplayIntegrity,
    ReplayMode,
    ReplayVerification,
)
from police_thief_p2p.services.replay.outcome import failed_result
from police_thief_p2p.services.replay.verifier import verify_replay_log


def verify_dual_logs(
    primary_log: SubGameLogArtifact,
    primary_config: PlayedConfigArtifact,
    sibling_log: SubGameLogArtifact,
    sibling_config: PlayedConfigArtifact,
    *,
    viewer_group: str,
) -> ReplayVerification:
    """Unlock objective replay only after two independently verified linked logs."""
    primary = verify_replay_log(
        primary_log,
        primary_config,
        mode=ReplayMode.OBJECTIVE,
        viewer_group=viewer_group,
    )
    sibling = verify_replay_log(
        sibling_log,
        sibling_config,
        mode=ReplayMode.OBJECTIVE,
        viewer_group=viewer_group,
    )
    if primary.integrity is ReplayIntegrity.TAMPERED:
        return primary
    if sibling.integrity is ReplayIntegrity.TAMPERED:
        return sibling
    linkage = (
        primary_log.game_uid,
        primary_log.sub_game_number,
        primary_log.config_sha256,
        primary_log.played_commits,
        primary_log.journal_sha256,
        primary_log.audit_sha256,
    )
    sibling_linkage = (
        sibling_log.game_uid,
        sibling_log.sub_game_number,
        sibling_log.config_sha256,
        sibling_log.played_commits,
        sibling_log.journal_sha256,
        sibling_log.audit_sha256,
    )
    if linkage != sibling_linkage:
        finding = ReplayFinding(1, "SIBLING_LINKAGE", "dual-log", "sibling graph differs")
        return failed_result(
            primary_log,
            ReplayMode.OBJECTIVE,
            (),
            0,
            primary.expected_steps,
            finding,
        )
    lengths = (len(primary_log.entries), len(sibling_log.entries))
    banner = (
        "Objective tracks verified and linked."
        if lengths[0] == lengths[1]
        else f"Unequal tracks {lengths[0]}/{lengths[1]}; shorter track is frozen."
    )
    return replace(primary, track_banner=banner)

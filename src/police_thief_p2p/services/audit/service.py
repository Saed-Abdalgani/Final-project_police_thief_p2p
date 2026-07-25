"""Pure fail-closed audit orchestration over an immutable evidence bundle."""

from police_thief_p2p.domain.scoring import score_terminal
from police_thief_p2p.services.audit.models import (
    AuditBundle,
    AuditFinding,
    AuditReport,
    AuditStatus,
)
from police_thief_p2p.services.audit.preflight import preflight_findings
from police_thief_p2p.services.audit.replay import replay
from police_thief_p2p.shared.canonical_json import sha256_digest


class AuditService:
    """Verify evidence without network, GUI, clock, randomness, or storage I/O."""

    def verify(self, bundle: AuditBundle) -> AuditReport:
        """Return Verified OK or the mandatory immutable tamper sanction."""
        preflight = preflight_findings(bundle)
        if preflight:
            return self._tampered(bundle, 0, preflight)
        replayed = replay(bundle)
        if replayed.findings:
            return self._tampered(bundle, replayed.verified_steps, replayed.findings)
        findings: list[AuditFinding] = []
        terminal = replayed.terminal
        if terminal != bundle.expected_terminal:
            findings.append(
                AuditFinding(1, "TERMINAL", "terminal", "reported terminal reason differs")
            )
        points = None if terminal is None else score_terminal(terminal, bundle.config.scoring)
        if points is None or (
            points.police != bundle.expected_police_points
            or points.thief != bundle.expected_thief_points
        ):
            findings.append(AuditFinding(2, "SCORE", "result", "reported sub-game score differs"))
        capture = bundle.capture_exchange
        if capture is not None:
            if not capture.commitments_are_valid():
                findings.append(
                    AuditFinding(
                        3,
                        "CAPTURE_COMMITMENT",
                        "capture-exchange",
                        "capture statement commitment differs",
                    )
                )
            resolved_capture = terminal is not None and terminal.value in {
                "capture",
                "barrier_capture",
                "enclosure",
            }
            claim = capture.claim.statement.captured
            response = capture.response.statement.captured
            if claim != resolved_capture or response != resolved_capture:
                findings.append(
                    AuditFinding(
                        4,
                        "FALSE_CAPTURE",
                        "capture-exchange",
                        "capture claim or response contradicts verified outcome",
                    )
                )
        if findings:
            return self._tampered(bundle, replayed.verified_steps, tuple(findings))
        if points is None or terminal is None:
            internal = (AuditFinding(1, "TERMINAL", "terminal", "terminal evidence is incomplete"),)
            return self._tampered(bundle, replayed.verified_steps, internal)
        evidence_digest = _evidence_digest(bundle)
        return AuditReport(
            AuditStatus.VERIFIED_OK,
            replayed.verified_steps,
            len(bundle.steps),
            terminal.value,
            points.police,
            points.thief,
            (),
            evidence_digest,
        )

    @staticmethod
    def _tampered(
        bundle: AuditBundle,
        verified_steps: int,
        findings: tuple[AuditFinding, ...],
    ) -> AuditReport:
        ordered = tuple(
            AuditFinding(index, item.code, item.evidence, item.detail)
            for index, item in enumerate(findings, start=1)
        )
        return AuditReport(
            AuditStatus.TAMPERED,
            verified_steps,
            len(bundle.steps),
            "tamper",
            0,
            0,
            ordered,
            _evidence_digest(bundle),
        )


def _evidence_digest(bundle: AuditBundle) -> str:
    """Digest public evidence linkage without serializing secret key objects."""
    return sha256_digest(
        {
            "game_uid": bundle.game_uid,
            "sub_game_number": bundle.sub_game_number,
            "config_sha256": bundle.config_sha256,
            "scent_model_sha256": bundle.scent_model_sha256,
            "role_schedule_sha256": bundle.role_schedule_sha256,
            "commitments": [step.reveal.commitment_sha256 for step in bundle.steps],
            "final_manifest_sha256": bundle.final_manifest.manifest_sha256,
            "journal_head": bundle.journal[-1].entry_sha256 if bundle.journal else None,
        }
    )

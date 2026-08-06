"""Six-sub-game protocol exchange driver for the M12 league dress rehearsal."""

import uuid
from dataclasses import dataclass

from police_thief_p2p.adapters.mcp import FastMcpBackend, McpClientAdapter
from police_thief_p2p.adapters.system.clocks import SystemClock
from police_thief_p2p.services.audit import AuditBundle, AuditReport, AuditService, agree_audits
from police_thief_p2p.services.protocol.negotiation_models import MatchProposal
from police_thief_p2p.shared.config_models import SharedConfig
from police_thief_p2p.shared.gatekeeper import InitialGatekeeper
from tests.helpers.audit import build_valid_audit_bundle
from tests.helpers.protocol import make_acceptance, make_envelope, make_proposal

SUB_GAMES = 6


def sub_game_uid(sub_game_number: int, counted: bool) -> str:
    """Return one stable distinct game UID per rehearsal sub-game."""
    marker = 1 if counted else 2
    return str(uuid.UUID(f"0000000{sub_game_number}-000{marker}-4000-8000-000000000000"))


def client(endpoint: str) -> McpClientAdapter:
    """Build one bounded Gatekeeper-wrapped peer client."""
    backend = FastMcpBackend(endpoint, timeout_sec=8)
    gatekeeper = InitialGatekeeper(
        backend.execute_once,
        clock=SystemClock(),
        timeout_sec=15,
        max_retries=2,
        concurrent_requests=1,
    )
    return McpClientAdapter(gatekeeper)


@dataclass(frozen=True, slots=True)
class SubGamePlan:
    """One negotiated sub-game with its own UID, bundle, and verified report."""

    sub_game_number: int
    counted: bool
    proposal: MatchProposal
    bundle: AuditBundle
    report: AuditReport

    @property
    def agreement_status(self) -> str:
        """Return the mutual audit agreement status for this sub-game."""
        digest = self.bundle.final_manifest.manifest_sha256
        return agree_audits(digest, digest, self.report, self.report).status.value


def build_plan(
    shared: SharedConfig,
    shared_bytes: bytes,
    sub_game_number: int,
    *,
    counted: bool,
) -> SubGamePlan:
    """Prepare one sub-game's proposal and independently verified audit report."""
    base = make_proposal(shared, shared_bytes, counted=counted)
    proposal = base.model_copy(update={"game_uid": sub_game_uid(sub_game_number, counted)})
    bundle = build_valid_audit_bundle(shared, sub_game_number)
    return SubGamePlan(
        sub_game_number=sub_game_number,
        counted=counted,
        proposal=proposal,
        bundle=bundle,
        report=AuditService().verify(bundle),
    )


def _manifest_payload(plan: SubGamePlan) -> dict[str, object]:
    manifest = plan.bundle.final_manifest
    return {
        "game_uid": manifest.game_uid,
        "sub_game_number": manifest.sub_game_number,
        "entries": [entry.as_dict() for entry in manifest.entries],
        "manifest_sha256": manifest.manifest_sha256,
    }


def envelope_sequence(plan: SubGamePlan, sender: str) -> tuple[tuple[str, dict[str, object]], ...]:
    """Return the ordered tool and payload sequence for one sub-game."""
    commitments = [entry.commitment_sha256 for entry in plan.bundle.final_manifest.entries]
    return (
        ("propose_match_v1", plan.proposal.model_dump(mode="json")),
        ("accept_match_v1", make_acceptance(plan.proposal).model_dump(mode="json")),
        ("commit_step_v1", {"commitments": commitments}),
        ("acknowledge_step_v1", {"acknowledged": True}),
        (
            "reveal_step_v1",
            {
                "reveals": [step.reveal.model_dump(mode="json") for step in plan.bundle.steps],
                "terminal_reason": plan.report.terminal_reason,
            },
        ),
        ("final_reveal_v1", {"manifest": _manifest_payload(plan)}),
        ("audit_result_v1", {"report": plan.report.as_dict()}),
        ("agree_result_v1", {"result_agreement_sha256": plan.report.digest()}),
    )


async def play_sub_game(
    peer: McpClientAdapter,
    plan: SubGamePlan,
    sender: str,
) -> dict[str, object]:
    """Drive one full sub-game against one peer and record every phase."""
    phases: list[str] = []
    codes: list[str] = []
    for sequence, (tool, payload) in enumerate(envelope_sequence(plan, sender), start=1):
        envelope = make_envelope(
            plan.proposal,
            tool,
            payload,
            sequence=sequence,
            sender=sender,
            sub_game_number=plan.sub_game_number,
        )
        response = await peer.send(envelope)
        codes.append(response.code)
        if not response.ok:
            return {
                "sub_game_number": plan.sub_game_number,
                "counted": plan.counted,
                "completed": False,
                "failed_tool": tool,
                "codes": codes,
                "phases": phases,
            }
        phases.append(str(response.payload.get("phase", "")))
    return {
        "sub_game_number": plan.sub_game_number,
        "counted": plan.counted,
        "completed": phases[-1] == "completed",
        "codes": codes,
        "phases": phases,
        "manifest_sha256": plan.bundle.final_manifest.manifest_sha256,
        "agreement_status": plan.agreement_status,
    }

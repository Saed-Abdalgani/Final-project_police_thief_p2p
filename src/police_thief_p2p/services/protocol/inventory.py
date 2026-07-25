"""Frozen M4 FastMCP tool inventory and semantic versions."""

from typing import Final

TOOL_VERSIONS: Final[dict[str, str]] = {
    "health_v1": "1.0.0",
    "capabilities_v1": "1.0.0",
    "propose_match_v1": "1.0.0",
    "accept_match_v1": "1.0.0",
    "commit_step_v1": "1.0.0",
    "acknowledge_step_v1": "1.0.0",
    "reveal_step_v1": "1.0.0",
    "capture_claim_v1": "1.0.0",
    "capture_response_v1": "1.0.0",
    "final_reveal_v1": "1.0.0",
    "audit_result_v1": "1.0.0",
    "agree_result_v1": "1.0.0",
    "peer_status_v1": "1.0.0",
}

SESSION_TOOLS: Final = frozenset(TOOL_VERSIONS) - {"health_v1", "capabilities_v1"}
MUTATING_TOOLS: Final = SESSION_TOOLS - {"peer_status_v1"}

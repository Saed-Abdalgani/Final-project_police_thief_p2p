"""Public identity construction for amireman compatibility series."""

from __future__ import annotations

from typing import Any

from police_thief_p2p.adapters.amireman.scent import MULTIPLICATIVE_KERNEL_V1

DEFAULT_REPOS = {
    "cop": "https://github.com/JCS1029/GRP00001-police-p2p",
    "thief": "https://github.com/JCS1029/GRP00001-thief-p2p",
}
BOOK_V1_CONFIG_SHA256 = "3835f6a137620d8d98ab3925b2d1ed397d2d20d23bb9ba857bcd104284aac443"
BOOK_V1_SCENT_SHA256 = "ea7225f5d71989add99a0057287342b7c5b86ab4efffd1608da25d0e368c0a28"
WIRE_CODE_VERSION = "1.00"


def mcp_servers_for(public_mcp_url: str | None) -> dict[str, str]:
    """Map one advertised endpoint to both compatibility roles."""
    if not public_mcp_url:
        return {}
    return {"cop": public_mcp_url, "thief": public_mcp_url}


def identity_for(
    group: str,
    *,
    members: list[str],
    github_commit: str,
    public_mcp_url: str | None = None,
    repos: dict[str, str] | None = None,
    llm_model: str = "template",
    scent_model: str = MULTIPLICATIVE_KERNEL_V1,
) -> dict[str, Any]:
    """Build the public compatibility identity advertised at negotiation."""
    identity: dict[str, Any] = {
        "group_id": group,
        "group_name": group,
        "git_commit_hash": github_commit,
        "github_commit": github_commit,
        "members": list(members),
        "repos": repos or dict(DEFAULT_REPOS),
        "mcp_servers": mcp_servers_for(public_mcp_url),
        "llm_model": llm_model,
        "code_version": WIRE_CODE_VERSION,
        "first_mover": "thief",
    }
    if scent_model == MULTIPLICATIVE_KERNEL_V1:
        identity["config_sha256"] = BOOK_V1_CONFIG_SHA256
        identity["scent_model_sha256"] = BOOK_V1_SCENT_SHA256
    return identity

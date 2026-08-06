"""Private configuration template for each independently rooted rehearsal peer."""

from pathlib import Path

TEMPLATE = """
[identity]
group_id = "{group}"
role = "{role}"
member_names = ["League Rehearsal"]
[network]
listen_host = "127.0.0.1"
listen_port = {port}
opponent_public_url = "http://127.0.0.1:{opponent_port}/mcp"
max_request_bytes = 65536
max_json_depth = 16
max_string_length = 4096
max_collection_items = 256
reorder_window = 8
[paths]
artifact_root = "{artifact_root}"
[strategy]
police_class = "police_thief_p2p.services.strategy.police.AdvancedPoliceBrain"
thief_class = "police_thief_p2p.services.strategy.thief.AdvancedThiefBrain"
profile = "m12-rehearsal"
[language]
provider = "template"
model = "deterministic-template"
deadline_sec = 10
[email]
credential_path = "credentials.json"
recipient_allowlist = ["lecturer@example.invalid"]
[gui]
enabled = false
theme = "system"
[tunnel]
provider = "local"
health_url = "http://127.0.0.1:{port}/mcp"
[observability]
level = "ERROR"
"""


def private_document(
    group: str,
    role: str,
    port: int,
    opponent_port: int,
    artifact_root: Path,
) -> str:
    """Render one peer's private TOML with its own artifact root and ports."""
    return TEMPLATE.format(
        group=group,
        role=role,
        port=port,
        opponent_port=opponent_port,
        artifact_root=artifact_root.as_posix(),
    )

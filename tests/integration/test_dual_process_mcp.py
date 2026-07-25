from __future__ import annotations

import asyncio
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

from police_thief_p2p.adapters.mcp import FastMcpBackend, McpClientAdapter
from police_thief_p2p.adapters.system.clocks import SystemClock
from police_thief_p2p.sdk import ProtocolEnvelope
from police_thief_p2p.services.audit import AuditBundle, AuditReport, AuditService, agree_audits
from police_thief_p2p.services.protocol.negotiation_models import MatchProposal
from police_thief_p2p.shared.config_loader import load_shared_bytes
from police_thief_p2p.shared.gatekeeper import ExternalCall, InitialGatekeeper
from tests.helpers.audit import build_valid_audit_bundle
from tests.helpers.protocol import (
    GROUP_A,
    GROUP_B,
    make_acceptance,
    make_envelope,
    make_proposal,
)

pytestmark = pytest.mark.integration


def _free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _private_config(
    group: str,
    role: str,
    port: int,
    opponent_port: int,
    artifact_root: Path,
) -> str:
    root = artifact_root.as_posix()
    return f"""
[identity]
group_id = "{group}"
role = "{role}"
member_names = ["M4 Process"]
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
artifact_root = "{root}"
[strategy]
police_class = "police_thief_p2p.services.strategy.police.AdvancedPoliceBrain"
thief_class = "police_thief_p2p.services.strategy.thief.AdvancedThiefBrain"
profile = "m4"
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


def _prepare_peer(
    root: Path,
    shared: bytes,
    *,
    group: str,
    role: str,
    port: int,
    opponent_port: int,
) -> tuple[Path, Path]:
    config_root = root / "config"
    config_root.mkdir(parents=True)
    shared_path = config_root / "game.json"
    private_path = config_root / "game.toml"
    shared_path.write_bytes(shared)
    private_path.write_text(
        _private_config(group, role, port, opponent_port, root / "artifacts"),
        encoding="utf-8",
    )
    (root / "cache").mkdir()
    (root / "temp").mkdir()
    return shared_path, private_path


def _start_peer(root: Path, shared_path: Path, private_path: Path) -> subprocess.Popen[bytes]:
    environment = os.environ.copy()
    environment["TMP"] = str(root / "temp")
    environment["TEMP"] = str(root / "temp")
    environment["XDG_CACHE_HOME"] = str(root / "cache")
    log = (root / "peer.log").open("wb")
    process = subprocess.Popen(  # noqa: S603 - fixed interpreter and module command
        [
            sys.executable,
            "-m",
            "police_thief_p2p.adapters.mcp.peer_process",
            "--shared-config",
            str(shared_path),
            "--private-config",
            str(private_path),
        ],
        cwd=root,
        env=environment,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    log.close()
    return process


async def _wait_health(endpoint: str, process: subprocess.Popen[bytes]) -> None:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"peer exited early with code {process.returncode}")
        try:
            backend = FastMcpBackend(endpoint, timeout_sec=1)
            gatekeeper = InitialGatekeeper(
                backend.execute_once,
                clock=SystemClock(),
                timeout_sec=1,
                max_retries=0,
                concurrent_requests=1,
            )
            result = await gatekeeper.execute(ExternalCall("mcp", "health_v1", {}))
            if result.outcome == "success" and result.payload["ok"] is True:
                return
        except Exception:
            await asyncio.sleep(0.1)
    raise TimeoutError("peer did not become healthy within bounded startup deadline")


def _client(endpoint: str) -> McpClientAdapter:
    backend = FastMcpBackend(endpoint, timeout_sec=5)
    gatekeeper = InitialGatekeeper(
        backend.execute_once,
        clock=SystemClock(),
        timeout_sec=10,
        max_retries=2,
        concurrent_requests=1,
    )
    return McpClientAdapter(gatekeeper)


async def _run_peer_sequence(
    client: McpClientAdapter,
    proposal: MatchProposal,
    bundle: AuditBundle,
    report: AuditReport,
    *,
    sender: str,
) -> tuple[str, ...]:
    envelopes: list[ProtocolEnvelope] = [
        make_envelope(
            proposal,
            "propose_match_v1",
            proposal.model_dump(mode="json"),
            sequence=1,
            sender=sender,
        ),
        make_envelope(
            proposal,
            "accept_match_v1",
            make_acceptance(proposal).model_dump(mode="json"),
            sequence=2,
            sender=sender,
        ),
    ]
    manifest = {
        "game_uid": bundle.final_manifest.game_uid,
        "sub_game_number": bundle.final_manifest.sub_game_number,
        "entries": [entry.as_dict() for entry in bundle.final_manifest.entries],
        "manifest_sha256": bundle.final_manifest.manifest_sha256,
    }
    events: tuple[tuple[str, dict[str, object]], ...] = (
        (
            "commit_step_v1",
            {"commitments": [entry.commitment_sha256 for entry in bundle.final_manifest.entries]},
        ),
        ("acknowledge_step_v1", {"acknowledged": True}),
        (
            "reveal_step_v1",
            {
                "reveals": [step.reveal.model_dump(mode="json") for step in bundle.steps],
                "terminal_reason": report.terminal_reason,
            },
        ),
        ("final_reveal_v1", {"manifest": manifest}),
        ("audit_result_v1", {"report": report.as_dict()}),
        ("agree_result_v1", {"result_agreement_sha256": report.digest()}),
    )
    envelopes.extend(
        make_envelope(proposal, tool, payload, sequence=sequence, sender=sender)
        for sequence, (tool, payload) in enumerate(events, start=3)
    )
    responses = [await client.send(envelope) for envelope in envelopes]
    assert all(response.ok for response in responses)
    return tuple(str(response.payload["phase"]) for response in responses)


@pytest.mark.parametrize("start_order", [("a", "b"), ("b", "a")])
def test_two_isolated_processes_are_start_order_independent_and_converge(
    tmp_path: Path,
    shared_config_bytes: bytes,
    start_order: tuple[str, str],
) -> None:
    roots = {"a": tmp_path / "peer-a", "b": tmp_path / "peer-b"}
    for root in roots.values():
        root.mkdir()
    ports = {"a": _free_port(), "b": _free_port()}
    configs = {
        "a": _prepare_peer(
            roots["a"],
            shared_config_bytes,
            group=GROUP_A,
            role="police",
            port=ports["a"],
            opponent_port=ports["b"],
        ),
        "b": _prepare_peer(
            roots["b"],
            shared_config_bytes,
            group=GROUP_B,
            role="thief",
            port=ports["b"],
            opponent_port=ports["a"],
        ),
    }
    endpoints = {name: f"http://127.0.0.1:{port}/mcp" for name, port in ports.items()}
    processes: dict[str, subprocess.Popen[bytes]] = {}
    try:
        first, second = start_order
        processes[first] = _start_peer(roots[first], *configs[first])
        asyncio.run(_wait_health(endpoints[first], processes[first]))
        processes[second] = _start_peer(roots[second], *configs[second])
        asyncio.run(_wait_health(endpoints[second], processes[second]))

        shared = load_shared_bytes(shared_config_bytes)
        proposal = make_proposal(shared, shared_config_bytes)
        bundle = build_valid_audit_bundle(shared)
        left_report = AuditService().verify(bundle)
        right_report = AuditService().verify(bundle)
        agreement = agree_audits(
            bundle.final_manifest.manifest_sha256,
            bundle.final_manifest.manifest_sha256,
            left_report,
            right_report,
        )

        async def scenario() -> tuple[tuple[str, ...], tuple[str, ...]]:
            return await asyncio.gather(
                _run_peer_sequence(
                    _client(endpoints["a"]),
                    proposal,
                    bundle,
                    left_report,
                    sender=GROUP_B,
                ),
                _run_peer_sequence(
                    _client(endpoints["b"]),
                    proposal,
                    bundle,
                    right_report,
                    sender=GROUP_A,
                ),
            )

        phases_a, phases_b = asyncio.run(scenario())
        assert phases_a == phases_b
        assert phases_a[-1] == "completed"
        assert agreement.status.value == "Verified OK"
        assert processes["a"].pid != processes["b"].pid
        assert (roots["a"] / "artifacts/protocol").is_dir()
        assert (roots["b"] / "artifacts/protocol").is_dir()
        assert not (roots["a"] / "artifacts/protocol").samefile(roots["b"] / "artifacts/protocol")
    finally:
        for process in processes.values():
            if process.poll() is None:
                process.terminate()
        for process in processes.values():
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

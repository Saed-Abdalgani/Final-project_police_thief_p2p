"""Independently rooted peer processes for the M12 league dress rehearsal."""

import asyncio
import os
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from police_thief_p2p.adapters.mcp import FastMcpBackend
from police_thief_p2p.adapters.system.clocks import SystemClock
from police_thief_p2p.shared.gatekeeper import ExternalCall, InitialGatekeeper
from scripts.m12_rehearsal_config import private_document

STARTUP_DEADLINE_SEC = 30.0
PEER_MODULE = "police_thief_p2p.adapters.mcp.peer_process"


def free_port() -> int:
    """Reserve one ephemeral loopback port."""
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


@dataclass(frozen=True, slots=True)
class PeerRoot:
    """One fully separated peer installation root."""

    name: str
    root: Path
    group: str
    role: str
    port: int
    shared_path: Path
    private_path: Path

    @property
    def endpoint(self) -> str:
        """Return this peer's streamable-HTTP endpoint."""
        return f"http://127.0.0.1:{self.port}/mcp"

    @property
    def artifact_root(self) -> Path:
        """Return this peer's isolated artifact root."""
        return self.root / "artifacts"


def prepare_peer(
    name: str,
    root: Path,
    shared: bytes,
    *,
    group: str,
    role: str,
    port: int,
    opponent_port: int,
) -> PeerRoot:
    """Materialize one peer root with its own config, cache, and temp trees."""
    config_root = root / "config"
    config_root.mkdir(parents=True, exist_ok=True)
    shared_path = config_root / "game.json"
    private_path = config_root / "game.toml"
    shared_path.write_bytes(shared)
    private_path.write_text(
        private_document(group, role, port, opponent_port, root / "artifacts"),
        encoding="utf-8",
    )
    for folder in ("cache", "temp", "artifacts"):
        (root / folder).mkdir(parents=True, exist_ok=True)
    return PeerRoot(name, root, group, role, port, shared_path, private_path)


def start_peer(peer: PeerRoot) -> subprocess.Popen[bytes]:
    """Launch one peer process with isolated cache and temp environments."""
    environment = os.environ.copy()
    environment["TMP"] = str(peer.root / "temp")
    environment["TEMP"] = str(peer.root / "temp")
    environment["XDG_CACHE_HOME"] = str(peer.root / "cache")
    with (peer.root / "peer.log").open("wb") as log:
        return subprocess.Popen(  # noqa: S603 - fixed interpreter and module command.
            [
                sys.executable,
                "-m",
                PEER_MODULE,
                "--shared-config",
                str(peer.shared_path),
                "--private-config",
                str(peer.private_path),
            ],
            cwd=peer.root,
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
        )


async def probe_health(endpoint: str, *, timeout_sec: float = 2.0) -> bool:
    """Return whether one endpoint answers a bounded health call."""
    backend = FastMcpBackend(endpoint, timeout_sec=timeout_sec)
    gatekeeper = InitialGatekeeper(
        backend.execute_once,
        clock=SystemClock(),
        timeout_sec=timeout_sec,
        max_retries=0,
        concurrent_requests=1,
    )
    try:
        result = await gatekeeper.execute(ExternalCall("mcp", "health_v1", {}))
    except Exception:
        return False
    return result.outcome == "success" and result.payload.get("ok") is True


async def await_health(endpoint: str, process: subprocess.Popen[bytes]) -> float:
    """Block until one peer is healthy and return the observed startup seconds."""
    started = time.monotonic()
    deadline = started + STARTUP_DEADLINE_SEC
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"peer exited early with code {process.returncode}")
        if await probe_health(endpoint, timeout_sec=1.0):
            return time.monotonic() - started
        await asyncio.sleep(0.15)
    raise TimeoutError("peer did not become healthy inside the bounded startup deadline")


def stop_peers(processes: dict[str, subprocess.Popen[bytes]]) -> None:
    """Terminate every rehearsal peer, escalating only when needed."""
    for process in processes.values():
        if process.poll() is None:
            process.terminate()
    for process in processes.values():
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

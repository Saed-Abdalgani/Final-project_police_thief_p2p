"""FastMCP server exposing the four amireman receive tools."""

from __future__ import annotations

import socket
import threading
import time

import uvicorn
from fastmcp import FastMCP

from police_thief_p2p.adapters.amireman.queues import PeerInboxes


class PeerServer:
    """Running peer MCP server with drain-aware graceful stop."""

    def __init__(self, inboxes: PeerInboxes, server: uvicorn.Server, thread: threading.Thread) -> None:
        self.inboxes = inboxes
        self._server = server
        self._thread = thread

    def stop(self, max_linger: float = 8.0, settle: float = 0.3, grace: float = 5.0) -> None:
        deadline = time.monotonic() + max_linger
        idle_since: float | None = None
        while time.monotonic() < deadline:
            state = getattr(self._server, "server_state", None)
            active = len(state.connections) if state is not None else None
            if active is None:
                time.sleep(min(max_linger, 3.0))
                break
            now = time.monotonic()
            if active == 0:
                idle_since = idle_since if idle_since is not None else now
                if now - idle_since >= settle:
                    break
            else:
                idle_since = None
            time.sleep(0.05)
        self._server.should_exit = True
        self._thread.join(grace)


def build_peer_server(name: str, inboxes: PeerInboxes) -> FastMCP:
    mcp = FastMCP(name=name)

    @mcp.tool
    def negotiate(message: dict) -> dict:
        inboxes.agreements.put(message)
        return {"ok": True}

    @mcp.tool
    def receive_turn(message: dict) -> dict:
        inboxes.turns.put(message)
        return {"ok": True}

    @mcp.tool
    def submit_audit(payload: dict) -> dict:
        inboxes.audits.put(payload)
        return {"ok": True}

    @mcp.tool
    def receive_control(message: dict) -> dict:
        inboxes.controls.put(message)
        return {"ok": True}

    return mcp


def start_peer_server(name: str, host: str, port: int) -> PeerServer:
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        probe.bind((host, port))
    finally:
        probe.close()
    inboxes = PeerInboxes()
    app = build_peer_server(name, inboxes).http_app()
    config = uvicorn.Config(app, host=host, port=port, log_level="warning", timeout_graceful_shutdown=5)
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True, name=f"mcp-{name}")
    thread.start()
    while not server.started:
        if not thread.is_alive():
            raise RuntimeError(f"peer MCP server failed to start on {host}:{port}")
        time.sleep(0.02)
    return PeerServer(inboxes, server, thread)

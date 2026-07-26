"""Loopback callback receiver for installed-app Gmail OAuth."""

import http.server
import secrets
import urllib.parse
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AuthorizationCode:
    """Validated one-time callback material."""

    code: str
    redirect_uri: str


class _CallbackHandler(http.server.BaseHTTPRequestHandler):
    expected_state = ""
    code: str | None = None

    def do_GET(self) -> None:
        """Accept only the expected state and a non-empty authorization code."""
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
        state = query.get("state", [""])[0]
        code = query.get("code", [""])[0]
        accepted = (
            len(state) <= 256
            and len(code) <= 2_048
            and secrets.compare_digest(state, self.expected_state)
            and bool(code)
        )
        if accepted:
            type(self).code = code
        self.send_response(200 if accepted else 400)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        body = (
            b"Authorization complete. You may close this window."
            if accepted
            else b"Invalid OAuth callback."
        )
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        """Suppress callback URLs because they contain secret codes."""
        _ = (format, args)


def receive_code(
    state: str,
    launch: Callable[[str], bool],
    *,
    timeout_sec: float = 180,
) -> AuthorizationCode:
    """Wait once on loopback without disclosing callback query parameters."""
    handler = type("OAuthCallback", (_CallbackHandler,), {"expected_state": state, "code": None})
    with http.server.HTTPServer(("127.0.0.1", 0), handler) as server:
        server.timeout = timeout_sec
        port = server.server_address[1]
        redirect_uri = f"http://127.0.0.1:{port}/oauth2/callback"
        if not launch(redirect_uri):
            raise RuntimeError("OAuth authorization browser could not be opened")
        return _receive(server, handler, redirect_uri)


def _receive(
    server: http.server.HTTPServer,
    handler: type[_CallbackHandler],
    redirect_uri: str,
) -> AuthorizationCode:
    server.handle_request()
    if handler.code is None:
        raise TimeoutError("OAuth authorization callback was not completed")
    return AuthorizationCode(handler.code, redirect_uri)

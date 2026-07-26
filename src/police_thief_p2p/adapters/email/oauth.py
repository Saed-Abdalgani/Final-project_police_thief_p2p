"""Send-only installed-app OAuth authorization and refresh."""

import base64
import hashlib
import secrets
import time
import urllib.parse
import webbrowser
from collections.abc import Callable, Mapping
from pathlib import Path

from police_thief_p2p.adapters.email.http import HttpResponse, parse_object, post
from police_thief_p2p.adapters.email.oauth_callback import receive_code
from police_thief_p2p.adapters.email.oauth_store import (
    TokenRecord,
    load_client,
    load_token,
    write_token,
)
from police_thief_p2p.constants import GMAIL_SEND_SCOPE

Post = Callable[[str, bytes, Mapping[str, str], float], HttpResponse]


class GmailOAuth:
    """Load private OAuth files and obtain only a Gmail send access token."""

    __slots__ = ("_credentials_path", "_opener", "_post", "_timeout", "_token_path")

    def __init__(
        self,
        credentials_path: Path,
        token_path: Path,
        *,
        artifact_root: Path,
        timeout_sec: float = 30,
        opener: Callable[[str], bool] = webbrowser.open,
        post_form: Post = post,
    ) -> None:
        """Configure private file handles without reading or logging secrets."""
        credentials = credentials_path.resolve()
        token = token_path.resolve()
        artifacts = artifact_root.resolve()
        if timeout_sec <= 0 or credentials == token:
            raise ValueError("OAuth configuration is invalid")
        if any(path == artifacts or artifacts in path.parents for path in (credentials, token)):
            raise ValueError("OAuth files must live outside artifact storage")
        self._credentials_path = credentials
        self._token_path = token
        self._timeout = timeout_sec
        self._opener = opener
        self._post = post_form

    def access_token(self) -> str:
        """Return a current access token, refreshing or authorizing as needed."""
        token = load_token(self._token_path)
        if token is not None and token["expires_at_epoch"] > int(time.time()) + 60:
            return str(token["access_token"])
        client = load_client(self._credentials_path)
        if token is not None and token["refresh_token"] is not None:
            refreshed = self._token_request(
                client,
                {
                    "client_id": client["client_id"],
                    "client_secret": client.get("client_secret", ""),
                    "refresh_token": token["refresh_token"],
                    "grant_type": "refresh_token",
                },
                prior_refresh=token["refresh_token"],
            )
            return str(refreshed["access_token"])
        return self._authorize(client)

    def _authorize(self, client: dict[str, str]) -> str:
        state = secrets.token_urlsafe(32)
        verifier = secrets.token_urlsafe(64)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        challenge_text = challenge.rstrip(b"=").decode("ascii")

        def launch(redirect_uri: str) -> bool:
            query = urllib.parse.urlencode(
                {
                    "client_id": client["client_id"],
                    "redirect_uri": redirect_uri,
                    "response_type": "code",
                    "scope": GMAIL_SEND_SCOPE,
                    "access_type": "offline",
                    "prompt": "consent",
                    "state": state,
                    "code_challenge": challenge_text,
                    "code_challenge_method": "S256",
                }
            )
            return self._opener(f"{client['auth_uri']}?{query}")

        authorization = receive_code(state, launch)
        token = self._token_request(
            client,
            {
                "client_id": client["client_id"],
                "client_secret": client.get("client_secret", ""),
                "code": authorization.code,
                "code_verifier": verifier,
                "grant_type": "authorization_code",
                "redirect_uri": authorization.redirect_uri,
            },
        )
        return str(token["access_token"])

    def _token_request(
        self,
        client: dict[str, str],
        fields: dict[str, str],
        *,
        prior_refresh: str | None = None,
    ) -> TokenRecord:
        body = urllib.parse.urlencode(fields).encode("ascii")
        response = self._post(
            client["token_uri"],
            body,
            {"Content-Type": "application/x-www-form-urlencoded"},
            self._timeout,
        )
        if response.status != 200:
            raise PermissionError("OAuth token request was rejected")
        value = parse_object(response.body)
        access_token = value.get("access_token")
        expires_in = value.get("expires_in")
        scope = value.get("scope", GMAIL_SEND_SCOPE)
        if (
            not isinstance(access_token, str)
            or type(expires_in) is not int
            or set(str(scope).split()) != {GMAIL_SEND_SCOPE}
        ):
            raise ValueError("OAuth token response violates send-only contract")
        refresh = value.get("refresh_token", prior_refresh)
        token = TokenRecord(
            access_token=access_token,
            refresh_token=refresh if isinstance(refresh, str) else None,
            expires_at_epoch=int(time.time()) + expires_in,
            scopes=[GMAIL_SEND_SCOPE],
        )
        write_token(self._token_path, token)
        return token

    def __repr__(self) -> str:
        """Never disclose secret paths or token values."""
        return "GmailOAuth(scope=gmail.send, credentials=<private>, token=<redacted>)"

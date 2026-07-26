"""Private bounded OAuth credential and token persistence."""

import json
import os
import urllib.parse
import uuid
from pathlib import Path
from typing import TypedDict

from police_thief_p2p.constants import GMAIL_SEND_SCOPE


class TokenRecord(TypedDict):
    """Validated private token fields; never safe for logs."""

    access_token: str
    refresh_token: str | None
    expires_at_epoch: int
    scopes: list[str]


def load_client(path: Path) -> dict[str, str]:
    """Load one installed-app OAuth client without returning unknown fields."""
    value = _read_object(path)
    client = value.get("installed")
    if not isinstance(client, dict):
        raise ValueError("OAuth credentials must contain an installed client")
    required = ("client_id", "auth_uri", "token_uri")
    if any(not isinstance(client.get(key), str) for key in required):
        raise ValueError("OAuth installed client is incomplete")
    result = {key: str(item) for key, item in client.items() if isinstance(item, str)}
    for key in ("auth_uri", "token_uri"):
        parsed = urllib.parse.urlsplit(result[key])
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("OAuth provider URLs must be credential-free HTTPS")
    return result


def load_token(path: Path) -> TokenRecord | None:
    """Load and scope-check one private token record."""
    if not path.exists():
        return None
    value = _read_object(path)
    if value.get("scopes") != [GMAIL_SEND_SCOPE]:
        raise ValueError("stored OAuth token does not have exact send-only scope")
    access_token = value.get("access_token")
    expires_at = value.get("expires_at_epoch")
    refresh = value.get("refresh_token")
    if not isinstance(access_token, str) or not isinstance(expires_at, int):
        raise ValueError("stored OAuth token is invalid")
    if refresh is not None and not isinstance(refresh, str):
        raise ValueError("stored OAuth refresh token is invalid")
    return TokenRecord(
        access_token=access_token,
        refresh_token=refresh,
        expires_at_epoch=expires_at,
        scopes=[GMAIL_SEND_SCOPE],
    )


def write_token(path: Path, token: TokenRecord) -> None:
    """Atomically store token bytes with owner-only permissions."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.{uuid.uuid4().hex}.tmp"
    try:
        data = json.dumps(token, sort_keys=True, separators=(",", ":")).encode()
        with temporary.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        if temporary.exists():
            temporary.unlink()


def _read_object(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    if len(data) > 131_072:
        raise ValueError("OAuth private file exceeds size limit")
    value = json.loads(data)
    if not isinstance(value, dict):
        raise ValueError("OAuth private file must contain a JSON object")
    return value

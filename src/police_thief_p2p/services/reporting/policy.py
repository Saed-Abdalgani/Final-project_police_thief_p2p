"""Least-privilege Gmail reporting policy."""

from pathlib import Path
from typing import Final

from police_thief_p2p.constants import (
    GMAIL_SEND_SCOPE as PRODUCT_GMAIL_SEND_SCOPE,
)
from police_thief_p2p.constants import (
    REQUIRED_REPORT_RECIPIENT,
)

GMAIL_SEND_SCOPE: Final = PRODUCT_GMAIL_SEND_SCOPE
REQUIRED_RECIPIENT = REQUIRED_REPORT_RECIPIENT
_FORBIDDEN_SCOPES = frozenset(
    {
        "https://mail.google.com/",
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/gmail.readonly",
    }
)


class ReportingPolicy:
    """Validate recipient, scopes, and private credential locations."""

    __slots__ = ("allowlist", "artifact_root", "competition_mode")

    def __init__(
        self,
        artifact_root: Path,
        *,
        allowlist: tuple[str, ...] = (REQUIRED_RECIPIENT,),
        competition_mode: bool = True,
    ) -> None:
        """Create a closed recipient set with the mandatory default."""
        if not allowlist or any("@" not in item or "\n" in item for item in allowlist):
            raise ValueError("recipient allowlist is invalid")
        if competition_mode and REQUIRED_RECIPIENT not in allowlist:
            raise ValueError("competition allowlist must contain required recipient")
        self.artifact_root = artifact_root.resolve()
        self.allowlist = frozenset(allowlist)
        self.competition_mode = competition_mode

    def validate_recipient(self, recipient: str) -> str:
        """Reject arbitrary destination injection."""
        if recipient not in self.allowlist:
            raise ValueError("report recipient is not allowlisted")
        return recipient

    def validate_scopes(self, scopes: tuple[str, ...]) -> tuple[str, ...]:
        """Require exactly Gmail send-only authority."""
        if frozenset(scopes) & _FORBIDDEN_SCOPES or scopes != (GMAIL_SEND_SCOPE,):
            raise ValueError("OAuth scopes must equal Gmail send-only scope")
        return scopes

    def validate_private_paths(
        self,
        credentials_path: Path,
        token_path: Path,
    ) -> tuple[Path, Path]:
        """Require separate credential files outside official artifact storage."""
        credentials = credentials_path.resolve()
        token = token_path.resolve()
        if credentials == token:
            raise ValueError("credential and token paths must be distinct")
        for path in (credentials, token):
            if path == self.artifact_root or self.artifact_root in path.parents:
                raise ValueError("OAuth files must live outside artifact storage")
        return credentials, token

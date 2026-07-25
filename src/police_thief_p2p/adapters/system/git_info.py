"""Constrained Git revision probe for signed Step-0 declarations."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from police_thief_p2p.services.ports.git_info import GitState

_COMMIT = re.compile(r"^[a-f0-9]{40}$")


class SubprocessGitInfoProbe:
    """Resolve revision identity with fixed, non-shell Git commands."""

    __slots__ = ("_root", "_timeout")

    def __init__(self, root: Path, timeout_seconds: float = 2.0) -> None:
        """Bind the probe to one explicit repository root."""
        self._root = root.resolve()
        self._timeout = timeout_seconds

    def collect(self) -> GitState:
        """Return unknown values when Git is absent or the root is not a repository."""
        commit = self._run("rev-parse", "--verify", "HEAD")
        status = self._run("status", "--porcelain", "--untracked-files=normal")
        if commit is None or _COMMIT.fullmatch(commit) is None or status is None:
            return GitState(None, None)
        return GitState(commit, bool(status))

    def _run(self, *arguments: str) -> str | None:
        try:
            result = subprocess.run(  # noqa: S603 - executable and arguments are fixed
                ("git", "-C", str(self._root), *arguments),
                capture_output=True,
                check=False,
                shell=False,
                text=True,
                timeout=self._timeout,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        return result.stdout.strip() if result.returncode == 0 else None

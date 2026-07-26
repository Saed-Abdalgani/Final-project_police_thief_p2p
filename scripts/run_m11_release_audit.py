"""Scan tracked files, Git history, ignore policy, and release archives."""

import json
import re
import shutil
import subprocess
import tarfile
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).parents[1]
OUTPUT = ROOT / "results/benchmarks/m11_security_audit.json"
_SECRET = re.compile(
    rb"(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|AIza[0-9A-Za-z_-]{35}|"
    rb"gh[pousr]_[A-Za-z0-9]{20,}|ya29\.[0-9A-Za-z_-]{20,}|sk-[A-Za-z0-9]{20,})"
)
_FORBIDDEN_TRACKED = re.compile(
    r"(^|/)(?:\.env(?:\..+)?|credentials\.json|token\.json|[^/]+\.(?:pem|key|p12|pfx))$"
)
_REQUIRED_IGNORES = (
    ".env",
    "credentials.json",
    "token.json",
    "*.pem",
    "*.key",
    "**/secrets/**",
)


def _git(*args: str) -> subprocess.CompletedProcess[bytes]:
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("Git executable is required for the release audit")
    return subprocess.run(  # noqa: S603 - resolved executable and fixed argument boundary.
        [git, *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )


def _tracked_files() -> list[str]:
    result = _git("ls-files", "-z", "--cached", "--others", "--exclude-standard")
    if result.returncode:
        raise RuntimeError("cannot enumerate tracked files")
    return [item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def _working_findings(paths: list[str]) -> list[str]:
    return [
        path for path in paths if _SECRET.search((ROOT / path).read_bytes()[:8_388_608]) is not None
    ]


def _history_findings() -> list[str]:
    commits = _git("rev-list", "--all").stdout.splitlines()
    findings: list[str] = []
    pattern = _SECRET.pattern.decode("ascii")
    for commit in commits:
        result = _git("grep", "-I", "-l", "-E", pattern, commit.decode("ascii"), "--", ".")
        if result.returncode == 0:
            findings.extend(
                f"{commit.decode('ascii')[:12]}:{path}"
                for path in result.stdout.decode("utf-8").splitlines()
            )
    return sorted(set(findings))


def _safe_member(name: str) -> bool:
    path = PurePosixPath(name)
    return not path.is_absolute() and ".." not in path.parts


def _archive_findings() -> list[str]:
    findings: list[str] = []
    for archive_path in sorted((ROOT / "dist").glob("police_thief_p2p-0.10.0*")):
        readers: list[tuple[str, bytes]] = []
        if archive_path.suffix == ".whl":
            with zipfile.ZipFile(archive_path) as archive:
                readers = [
                    (item.filename, archive.read(item))
                    for item in archive.infolist()
                    if not item.is_dir() and item.file_size <= 8_388_608
                ]
        elif archive_path.name.endswith(".tar.gz"):
            with tarfile.open(archive_path, "r:gz") as archive:
                readers = [
                    (item.name, stream.read())
                    for item in archive.getmembers()
                    if item.isfile()
                    and item.size <= 8_388_608
                    and (stream := archive.extractfile(item)) is not None
                ]
        for name, data in readers:
            if not _safe_member(name) or _SECRET.search(data):
                findings.append(f"{archive_path.name}:{name}")
    return findings


def main() -> int:
    """Write a non-secret audit summary and fail on any release finding."""
    tracked = _tracked_files()
    ignore_text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    forbidden = [path for path in tracked if _FORBIDDEN_TRACKED.search(path)]
    missing_ignores = [item for item in _REQUIRED_IGNORES if item not in ignore_text]
    working = _working_findings(tracked)
    history = _history_findings()
    archives = _archive_findings()
    finding_count = sum(
        len(items) for items in (forbidden, missing_ignores, working, history, archives)
    )
    passed = not any((forbidden, missing_ignores, working, history, archives))
    document = {
        "schema_version": "1.0.0",
        "measured_at": "2026-07-26",
        "package_version": "0.10.0",
        "scope": {
            "candidate_files": len(tracked),
            "git_commits_all_refs": len(_git("rev-list", "--all").stdout.splitlines()),
            "role_history": "unified canonical history feeding both M13 role exports",
            "release_archives": 2,
        },
        "findings": {
            "forbidden_tracked_paths": forbidden,
            "missing_ignore_rules": missing_ignores,
            "working_tree_secret_patterns": working,
            "history_secret_patterns": history,
            "archive_secret_or_path_findings": archives,
        },
        "result": "PASS" if passed else "FAIL",
    }
    OUTPUT.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"result": document["result"], "findings": finding_count}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

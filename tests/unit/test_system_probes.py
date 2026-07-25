import ctypes
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from police_thief_p2p.adapters.system import system_info
from police_thief_p2p.adapters.system.git_info import SubprocessGitInfoProbe
from police_thief_p2p.adapters.system.system_info import PlatformSystemInfoProbe


def test_unix_memory_probe_normalizes_pages_to_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_sysconf(name: str) -> int:
        return {"SC_PHYS_PAGES": 2, "SC_PAGE_SIZE": 4096}[name]

    monkeypatch.setattr(os, "sysconf", fake_sysconf, raising=False)
    assert system_info._memory_bytes("linux") == 8192


def test_windows_memory_probe_uses_platform_api(monkeypatch: pytest.MonkeyPatch) -> None:
    class Kernel:
        @staticmethod
        def GlobalMemoryStatusEx(pointer: object) -> int:
            pointer._obj.total_physical = 16_384  # type: ignore[attr-defined]
            return 1

    monkeypatch.setattr(
        ctypes,
        "windll",
        SimpleNamespace(kernel32=Kernel()),
        raising=False,
    )
    assert system_info._memory_bytes("win32") == 16_384


def test_system_probe_degrades_gpu_and_frequencies_to_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("POLICE_THIEF_GPU_MODEL", raising=False)
    monkeypatch.delenv("POLICE_THIEF_VRAM_BYTES", raising=False)
    monkeypatch.delenv("POLICE_THIEF_CPU_FREQUENCY_MHZ", raising=False)
    monkeypatch.setattr(system_info, "_memory_bytes", lambda: None)
    actual = PlatformSystemInfoProbe().collect()
    assert actual.gpu_model is None
    assert actual.vram_bytes is None
    assert actual.cpu_frequency_mhz is None


def test_git_probe_returns_exact_clean_revision_or_unknown(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    responses = iter(
        (
            subprocess.CompletedProcess([], 0, stdout="a" * 40 + "\n", stderr=""),
            subprocess.CompletedProcess([], 0, stdout="", stderr=""),
        )
    )
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: next(responses))
    assert SubprocessGitInfoProbe(tmp_path).collect().commit == "a" * 40
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess([], 1, stdout="", stderr=""),
    )
    unknown = SubprocessGitInfoProbe(tmp_path).collect()
    assert unknown.commit is None
    assert unknown.dirty is None

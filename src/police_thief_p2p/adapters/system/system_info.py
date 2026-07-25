"""Platform-safe best-effort system information probe."""

from __future__ import annotations

import ctypes
import os
import platform
import sys
from ctypes import wintypes

from police_thief_p2p.services.ports.system_info import SystemInfo


class _MemoryStatus(ctypes.Structure):
    _fields_ = [
        ("length", wintypes.DWORD),
        ("memory_load", wintypes.DWORD),
        ("total_physical", ctypes.c_ulonglong),
        ("available_physical", ctypes.c_ulonglong),
        ("total_page_file", ctypes.c_ulonglong),
        ("available_page_file", ctypes.c_ulonglong),
        ("total_virtual", ctypes.c_ulonglong),
        ("available_virtual", ctypes.c_ulonglong),
        ("available_extended_virtual", ctypes.c_ulonglong),
    ]


def _memory_bytes(platform_name: str | None = None) -> int | None:
    """Return physical RAM using the host's standard API."""
    selected_platform = sys.platform if platform_name is None else platform_name
    if selected_platform == "win32":
        status = _MemoryStatus()
        status.length = ctypes.sizeof(status)
        try:
            succeeded = ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
        except (AttributeError, OSError):
            return None
        return int(status.total_physical) if succeeded and status.total_physical > 0 else None
    sysconf = getattr(os, "sysconf", None)
    if not callable(sysconf):
        return None
    try:
        pages = sysconf("SC_PHYS_PAGES")
        page_size = sysconf("SC_PAGE_SIZE")
    except (OSError, ValueError):
        return None
    value = pages * page_size
    return value if type(value) is int and value > 0 else None


def _optional_capacity(name: str, *, allow_zero: bool = False) -> int | None:
    """Read explicitly supplied optional hardware capacity safely."""
    value = os.environ.get(name)
    if value is None:
        return None
    try:
        parsed = int(value)
    except ValueError:
        return None
    minimum = 0 if allow_zero else 1
    return parsed if parsed >= minimum else None


class PlatformSystemInfoProbe:
    """Collect only non-secret, normalized hardware/runtime facts."""

    def collect(self) -> SystemInfo:
        """Return a portable snapshot; unsupported facts remain unknown."""
        cpu_model = platform.processor().strip() or platform.machine().strip() or None
        gpu_model = os.environ.get("POLICE_THIEF_GPU_MODEL") or None
        return SystemInfo(
            operating_system=platform.system() or "unknown",
            python_version=platform.python_version(),
            cpu_model=cpu_model,
            cpu_cores=os.cpu_count(),
            memory_bytes=_memory_bytes(),
            cpu_frequency_mhz=_optional_capacity("POLICE_THIEF_CPU_FREQUENCY_MHZ"),
            gpu_model=gpu_model,
            vram_bytes=_optional_capacity("POLICE_THIEF_VRAM_BYTES", allow_zero=True),
            platform=platform.platform() or "unknown",
        )

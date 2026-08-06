"""Cheap cross-platform peak resident memory probe for experiment evidence."""

import ctypes
import sys
from ctypes import wintypes

BYTES_PER_MB = 1024 * 1024
_KILOBYTE_PLATFORMS = ("linux",)


class _MemoryCounters(ctypes.Structure):
    """Subset of PROCESS_MEMORY_COUNTERS needed for the peak working set."""

    _fields_ = (
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    )


def _windows_peak_bytes() -> int:
    kernel32 = ctypes.WinDLL("kernel32")
    psapi = ctypes.WinDLL("psapi")
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(_MemoryCounters),
        wintypes.DWORD,
    )
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    counters = _MemoryCounters()
    counters.cb = ctypes.sizeof(_MemoryCounters)
    handle = kernel32.GetCurrentProcess()
    if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
        return 0
    return int(counters.PeakWorkingSetSize)


def _posix_peak_bytes() -> int:
    usage = __import__("resource")
    peak = int(usage.getrusage(usage.RUSAGE_SELF).ru_maxrss)
    return peak * 1024 if sys.platform.startswith(_KILOBYTE_PLATFORMS) else peak


def peak_rss_mb() -> float:
    """Return this process's peak resident set size in mebibytes, or zero."""
    try:
        raw = _windows_peak_bytes() if sys.platform == "win32" else _posix_peak_bytes()
    except (AttributeError, ImportError, OSError, ValueError):
        return 0.0
    return raw / BYTES_PER_MB

"""CLI launcher for the Tk local-truth GUI demo."""

import argparse

from police_thief_p2p.adapters.gui.demo_shell import run_demo


def main() -> int:
    """Open the live GUI; pass --seconds for a timed smoke close."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seconds",
        type=float,
        default=None,
        help="auto-close after N seconds; omit for interactive use",
    )
    return run_demo(auto_close_sec=parser.parse_args().seconds)


if __name__ == "__main__":
    raise SystemExit(main())

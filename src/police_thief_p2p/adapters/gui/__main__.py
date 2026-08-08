"""Package entry: ``python -m police_thief_p2p.adapters.gui`` opens the live demo."""

from police_thief_p2p.adapters.gui.demo_shell import run_demo


def main() -> int:
    """Delegate to the timed/interactive demo shell CLI."""
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", type=float, default=None)
    return run_demo(auto_close_sec=parser.parse_args().seconds)


if __name__ == "__main__":
    raise SystemExit(main())

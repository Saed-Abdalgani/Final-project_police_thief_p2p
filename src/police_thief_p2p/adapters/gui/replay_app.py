"""Accessible Tk replay navigator over SDK-verified results."""

from __future__ import annotations

import tkinter as tk
from functools import partial
from tkinter import ttk

from police_thief_p2p.sdk import ReplayVerification, SimulationSdk

from .replay_board import ReplayBoard
from .view_model import safe_ui_error


class ReplayApp:
    """Offline replay shell with immutable SDK navigation."""

    def __init__(
        self,
        sdk: SimulationSdk,
        results: tuple[ReplayVerification, ...],
        board_size: int,
        root: tk.Tk | None = None,
    ) -> None:
        """Build a selectable six-game replay UI."""
        if not results:
            raise ValueError("replay application requires verified results")
        self.sdk = sdk
        self.results = {item.sub_game_number: item for item in results}
        self.root = root or tk.Tk()
        self.root.title("Police-Thief Verified Replay")
        self.root.minsize(760, 560)
        self.selected = tk.IntVar(value=min(self.results))
        self.goto = tk.IntVar(value=0)
        self.status = tk.StringVar()
        self.detail = tk.StringVar()
        self.cursor = sdk.replay_cursor(self.results[self.selected.get()])
        self.board = ReplayBoard(self.root, board_size)
        self._build()
        self._render()
        self._bind_keys()

    def run(self) -> None:
        """Enter the replay event loop."""
        self.root.mainloop()

    def _build(self) -> None:
        header = ttk.Frame(self.root, padding=10)
        header.pack(fill="x")
        ttk.Label(header, textvariable=self.status, font=("TkDefaultFont", 14, "bold")).pack(
            side="left"
        )
        ttk.Label(header, text="Sub-game").pack(side="right")
        selector = ttk.Combobox(
            header,
            textvariable=self.selected,
            values=tuple(str(number) for number in self.results),
            state="readonly",
            width=4,
        )
        selector.pack(side="right", padx=5)
        selector.bind("<<ComboboxSelected>>", self._select)
        self.board.pack(fill="both", expand=True, padx=10)
        ttk.Label(self.root, textvariable=self.detail, wraplength=720).pack(fill="x", padx=10)
        controls = ttk.Frame(self.root, padding=10)
        controls.pack(fill="x")
        for label, command in (
            ("Play", "play"),
            ("Pause", "pause"),
            ("Previous", "previous"),
            ("Next", "next"),
            ("Restart", "restart"),
        ):
            ttk.Button(controls, text=label, command=partial(self._navigate, command)).pack(
                side="left", padx=3
            )
        ttk.Entry(controls, textvariable=self.goto, width=5).pack(side="left", padx=(12, 3))
        ttk.Button(controls, text="Go to step", command=lambda: self._navigate("go-to-step")).pack(
            side="left"
        )

    def _select(self, _event: tk.Event[tk.Misc]) -> None:
        self.cursor = self.sdk.replay_cursor(self.results[self.selected.get()])
        self._render()

    def _navigate(self, command: str) -> None:
        try:
            self.cursor = self.sdk.navigate_replay(
                self.cursor,
                command,
                step=self.goto.get() if command == "go-to-step" else None,
            )
            self._render()
            if command == "play":
                self.root.after(400, self._tick)
        except Exception as error:  # UI exception boundary
            safe = safe_ui_error(error)
            self.status.set(f"⚠ ERROR — {safe.message} Correlation: {safe.correlation_id}")

    def _tick(self) -> None:
        if not self.cursor.playing:
            return
        previous = self.cursor.index
        self.cursor = self.sdk.navigate_replay(self.cursor, "next")
        self._render()
        if self.cursor.index != previous:
            self.root.after(400, self._tick)

    def _render(self) -> None:
        result = self.cursor.verification
        self.status.set(result.accessible_status)
        self.board.render(self.cursor.frame)
        finding = result.first_failure
        finding_text = (
            "No integrity findings."
            if finding is None
            else f"First failure {finding.code}: {finding.detail}"
        )
        self.detail.set(
            f"{result.track_banner} Frame {self.cursor.index + 1}/"
            f"{max(1, len(result.frames))}. {finding_text}"
        )

    def _bind_keys(self) -> None:
        bindings = {
            "<space>": "play",
            "<Escape>": "pause",
            "<Left>": "previous",
            "<Right>": "next",
            "<Home>": "restart",
        }
        for key, command in bindings.items():
            self.root.bind(key, partial(self._key_navigate, command))

    def _key_navigate(self, command: str, _event: tk.Event[tk.Misc]) -> None:
        self._navigate(command)

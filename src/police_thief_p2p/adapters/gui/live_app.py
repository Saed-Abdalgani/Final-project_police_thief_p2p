"""Tk live shell driven exclusively by immutable SDK snapshots."""

from __future__ import annotations

import tkinter as tk
from functools import partial
from tkinter import messagebox, ttk

from police_thief_p2p.sdk import SimulationSdk
from police_thief_p2p.sdk.live_runtime import LifecycleCommand, SnapshotChannel

from .board import BoardCanvas
from .view_model import LiveViewModel, safe_ui_error


class LiveApp:
    """Accessible local-truth application shell with no game decisions."""

    POLL_MS = 50

    def __init__(
        self,
        sdk: SimulationSdk,
        channel: SnapshotChannel,
        root: tk.Tk | None = None,
    ) -> None:
        """Build the dependency-injected Tk shell."""
        self.sdk = sdk
        self.channel = channel
        self.root = root or tk.Tk()
        self.root.title("Police-Thief Local Truth")
        self.root.minsize(760, 560)
        self.root.protocol("WM_DELETE_WINDOW", self._quit)
        self._font_size = tk.IntVar(value=11)
        self._status = tk.StringVar(value="● READY — Ready for local play.")
        self._summary = tk.StringVar(value="Waiting for the first local snapshot.")
        self._details = tk.StringVar(value="")
        self._build()
        self._bind_keys()
        self.root.after(self.POLL_MS, self._poll)

    def run(self) -> None:
        """Enter the Tk event loop."""
        self.root.mainloop()

    def _build(self) -> None:
        container = ttk.Frame(self.root, padding=12)
        container.pack(fill="both", expand=True)
        banner = ttk.Label(
            container,
            textvariable=self._status,
            anchor="center",
            font=("TkDefaultFont", 13, "bold"),
        )
        banner.pack(fill="x", pady=(0, 8))
        body = ttk.Panedwindow(container, orient="horizontal")
        body.pack(fill="both", expand=True)
        self.board = BoardCanvas(body)
        panel = ttk.Frame(body, padding=10)
        body.add(self.board, weight=3)
        body.add(panel, weight=2)
        ttk.Label(panel, textvariable=self._summary, wraplength=300).pack(anchor="w", fill="x")
        ttk.Separator(panel).pack(fill="x", pady=8)
        ttk.Label(panel, textvariable=self._details, wraplength=300).pack(anchor="w", fill="x")
        ttk.Label(panel, text="Text size").pack(anchor="w", pady=(12, 0))
        ttk.Scale(
            panel,
            from_=9,
            to=20,
            variable=self._font_size,
            command=self._scale_text,
        ).pack(fill="x")
        controls = ttk.Frame(container)
        controls.pack(fill="x", pady=(8, 0))
        commands = (
            ("Start", LifecycleCommand.START, False),
            ("Pause", LifecycleCommand.PAUSE, False),
            ("Resume", LifecycleCommand.RESUME, False),
            ("Stop", LifecycleCommand.STOP, True),
            ("Restart", LifecycleCommand.RESTART, True),
            ("Quit", LifecycleCommand.QUIT, True),
        )
        self.buttons: list[ttk.Button] = []
        for label, command, confirm in commands:
            button = ttk.Button(
                controls,
                text=label,
                command=partial(self._action, command, confirm),
            )
            button.pack(side="left", padx=3)
            self.buttons.append(button)
        self.buttons[0].focus_set()

    def _poll(self) -> None:
        snapshot = self.channel.drain_latest()
        if snapshot is not None:
            model = LiveViewModel.from_view(snapshot)
            self.board.render(snapshot)
            self._status.set(f"{model.status.icon} {model.status.label} — {snapshot.status_detail}")
            self._summary.set(
                "\n".join(
                    (
                        model.role_label,
                        model.position_label,
                        model.progress_label,
                        model.belief_summary,
                    )
                )
            )
            self._details.set(
                "\n".join(
                    (
                        f"Sent hint: {snapshot.latest_sent_hint or 'none'}",
                        f"Received hint: {snapshot.latest_received_hint or 'none'}",
                        f"Own verdict: {snapshot.own_verdict}",
                        f"Barriers: {snapshot.barriers_placed}/{snapshot.max_barriers}",
                        model.metrics_label,
                        snapshot.audit_text,
                    )
                )
            )
        if self.root.winfo_exists():
            self.root.after(self.POLL_MS, self._poll)

    def _action(self, command: LifecycleCommand, confirm: bool) -> bool:
        if confirm and not messagebox.askyesno(
            "Confirm lifecycle action",
            f"Safely {command.value} the current session?",
            parent=self.root,
        ):
            return False
        try:
            self.sdk.lifecycle(command)
            if command is LifecycleCommand.QUIT:
                self.root.destroy()
            return True
        except Exception as error:  # UI exception boundary
            safe = safe_ui_error(error)
            self._status.set(f"⚠ ERROR — {safe.message} Correlation: {safe.correlation_id}")
            return False

    def _quit(self) -> None:
        self._action(LifecycleCommand.QUIT, True)

    def _scale_text(self, value: str) -> None:
        self.root.option_add("*Font", ("TkDefaultFont", int(float(value))))

    def _bind_keys(self) -> None:
        bindings = {
            "<Alt-s>": LifecycleCommand.START,
            "<Alt-p>": LifecycleCommand.PAUSE,
            "<Alt-r>": LifecycleCommand.RESUME,
            "<Alt-x>": LifecycleCommand.STOP,
            "<Control-r>": LifecycleCommand.RESTART,
            "<Control-q>": LifecycleCommand.QUIT,
        }
        for key, command in bindings.items():
            self.root.bind(key, partial(self._key_action, command))

    def _key_action(
        self,
        command: LifecycleCommand,
        _event: tk.Event[tk.Misc],
    ) -> None:
        self._action(command, command.value in {"stop", "restart", "quit"})

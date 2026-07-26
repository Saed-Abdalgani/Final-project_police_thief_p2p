"""Resizable Tk board renderer for privacy-safe local snapshots."""

from __future__ import annotations

import tkinter as tk

from police_thief_p2p.sdk import LocalView

from .palette import heat_color


class BoardCanvas(tk.Canvas):
    """Draw local truth, public topology, and normalized belief only."""

    def __init__(self, master: tk.Misc) -> None:
        """Create a keyboard-focusable scalable board."""
        super().__init__(
            master,
            background="#FFFFFF",
            highlightthickness=2,
            highlightbackground="#334155",
            takefocus=True,
        )
        self._view: LocalView | None = None
        self.accessible_summary = "Local board is waiting for a snapshot."
        self.bind("<Configure>", self._redraw)

    def render(self, view: LocalView) -> None:
        """Render one immutable SDK view."""
        self._view = view
        self.accessible_summary = (
            f"Own {view.role} at {view.own_position}; {len(view.public_barriers)} barriers; "
            "heatmap represents uncertain opponent belief."
        )
        self._draw(view)

    def _redraw(self, _event: tk.Event[tk.Misc]) -> None:
        if self._view is not None:
            self._draw(self._view)

    def _draw(self, view: LocalView) -> None:
        self.delete("all")
        margin = 46
        usable = min(max(1, self.winfo_width()), max(1, self.winfo_height())) - 2 * margin
        cell = max(10.0, usable / view.board_size)
        credible = set(view.credible_region)
        visited = set(view.own_visited)
        barriers = set(view.public_barriers)
        for row in range(view.board_size):
            for col in range(view.board_size):
                x0, y0 = margin + col * cell, margin + row * cell
                probability = float(view.belief_heatmap[row * view.board_size + col])
                self.create_rectangle(
                    x0,
                    y0,
                    x0 + cell,
                    y0 + cell,
                    fill=heat_color(probability),
                    outline="#0F172A" if (row, col) in credible else "#CBD5E1",
                    width=2 if (row, col) in credible else 1,
                )
                if (row, col) in visited:
                    self.create_oval(
                        x0 + cell * 0.35,
                        y0 + cell * 0.35,
                        x0 + cell * 0.65,
                        y0 + cell * 0.65,
                        outline="#6D28D9",
                        width=2,
                    )
                if (row, col) in barriers:
                    self.create_text(
                        x0 + cell / 2,
                        y0 + cell / 2,
                        text="▦",
                        fill="#111827",
                        font=("TkDefaultFont", max(8, int(cell * 0.45)), "bold"),
                    )
        self._labels(view, margin, cell)
        row, col = view.own_position
        token = "P" if view.role == "police" else "T"
        self.create_oval(
            margin + col * cell + 2,
            margin + row * cell + 2,
            margin + (col + 1) * cell - 2,
            margin + (row + 1) * cell - 2,
            fill="#7C2D12",
            outline="#431407",
            width=3,
        )
        self.create_text(
            margin + (col + 0.5) * cell,
            margin + (row + 0.5) * cell,
            text=token,
            fill="#FFFFFF",
            font=("TkDefaultFont", max(9, int(cell * 0.45)), "bold"),
            tags=("own-position",),
        )
        self.create_text(
            margin,
            margin + view.board_size * cell + 22,
            anchor="w",
            text="Belief scale: 0.00 ░ 0.25 ▒ 0.50 ▓ 0.75 █ 1.00",
            fill="#0F172A",
        )

    def _labels(self, view: LocalView, margin: int, cell: float) -> None:
        reverse_rows = view.axis_origin_corner.startswith("bottom")
        reverse_cols = view.axis_origin_corner.endswith("right")
        for index in range(view.board_size):
            row = view.board_size - 1 - index if reverse_rows else index
            col = view.board_size - 1 - index if reverse_cols else index
            external = index + view.axis_start_index
            self.create_text(margin - 16, margin + (row + 0.5) * cell, text=str(external))
            self.create_text(margin + (col + 0.5) * cell, margin - 16, text=str(external))

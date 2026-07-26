"""Replay frame canvas with explicit single/objective truth modes."""

from __future__ import annotations

import tkinter as tk

from police_thief_p2p.sdk import ReplayFrame

from .palette import heat_color


class ReplayBoard(tk.Canvas):
    """Render only already-verified replay frames."""

    def __init__(self, master: tk.Misc, board_size: int) -> None:
        """Create a resizable replay board."""
        super().__init__(master, background="#FFFFFF", takefocus=True)
        self.board_size = board_size
        self._frame: ReplayFrame | None = None
        self.bind("<Configure>", self._redraw)

    def render(self, frame: ReplayFrame | None) -> None:
        """Render the selected verified frame."""
        self._frame = frame
        self._draw()

    def _redraw(self, _event: tk.Event[tk.Misc]) -> None:
        self._draw()

    def _draw(self) -> None:
        self.delete("all")
        if self._frame is None:
            self.create_text(20, 20, anchor="nw", text="No verified frame available.")
            return
        frame = self._frame
        margin = 36
        cell = max(
            10.0,
            (min(max(1, self.winfo_width()), max(1, self.winfo_height())) - 2 * margin)
            / self.board_size,
        )
        for row in range(self.board_size):
            for col in range(self.board_size):
                index = row * self.board_size + col
                probability = float(frame.belief_heatmap[index]) if frame.belief_heatmap else 0.0
                x0, y0 = margin + col * cell, margin + row * cell
                self.create_rectangle(
                    x0,
                    y0,
                    x0 + cell,
                    y0 + cell,
                    fill=heat_color(probability),
                    outline="#CBD5E1",
                )
        for row, col in frame.public_barriers:
            self.create_text(
                margin + (col + 0.5) * cell,
                margin + (row + 0.5) * cell,
                text="▦",
                fill="#111827",
            )
        markers = (
            (frame.own_position, "OWN", "#6D28D9"),
            (frame.police_position, "P", "#9A3412"),
            (frame.thief_position, "T", "#065F46"),
        )
        seen: set[tuple[int, int]] = set()
        for position, label, color in markers:
            if position is None or position in seen:
                continue
            seen.add(position)
            row, col = position
            self.create_text(
                margin + (col + 0.5) * cell,
                margin + (row + 0.5) * cell,
                text=label,
                fill=color,
                font=("TkDefaultFont", max(8, int(cell * 0.3)), "bold"),
            )

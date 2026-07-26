"""Deterministic SVG evidence rendering from public SDK DTOs."""

from html import escape

from police_thief_p2p.sdk import LocalView, ReplayVerification
from police_thief_p2p.sdk.live_view import assert_private_document

from .palette import STATUS_STYLES, heat_color


def live_view_svg(view: LocalView, *, width: int = 960, height: int = 640) -> bytes:
    """Render a deterministic accessible local-truth screenshot fixture."""
    assert_private_document(view.as_dict())
    size, x0, y0, board_pixels = view.board_size, 42, 90, 500
    cell = board_pixels / size
    elements = [_svg_header(width, height, "Live local-truth belief view")]
    style = STATUS_STYLES[view.status.value]
    elements.append(
        f'<rect x="0" y="0" width="{width}" height="64" fill="{style.background}"/>'
        f'<text x="30" y="40" class="title" fill="{style.foreground}">'
        f"{escape(style.icon)} {escape(style.label)} - {escape(view.status_detail)}</text>"
    )
    barriers, trail, credible = (
        set(view.public_barriers),
        set(view.own_visited),
        set(view.credible_region),
    )
    for row in range(size):
        for col in range(size):
            x, y = x0 + col * cell, y0 + row * cell
            probability = float(view.belief_heatmap[row * size + col])
            stroke = "#0F172A" if (row, col) in credible else "#CBD5E1"
            width_value = 2 if (row, col) in credible else 1
            elements.append(
                f'<rect x="{x:.2f}" y="{y:.2f}" width="{cell:.2f}" height="{cell:.2f}" '
                f'fill="{heat_color(probability)}" stroke="{stroke}" '
                f'stroke-width="{width_value}"/>'
            )
            if (row, col) in trail:
                elements.append(
                    f'<circle cx="{x + cell / 2:.2f}" cy="{y + cell / 2:.2f}" '
                    f'r="{cell * 0.12:.2f}" fill="none" stroke="#6D28D9" stroke-width="2"/>'
                )
            if (row, col) in barriers:
                elements.append(
                    f'<text x="{x + cell / 2:.2f}" y="{y + cell * 0.62:.2f}" '
                    'class="cell" text-anchor="middle">#</text>'
                )
    elements.extend(_coordinate_labels(view, x0, y0, cell))
    row, col = view.own_position
    cx, cy = x0 + (col + 0.5) * cell, y0 + (row + 0.5) * cell
    role = "P" if view.role == "police" else "T"
    elements.append(
        f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{cell * 0.3:.2f}" fill="#7C2D12"/>'
        f'<text x="{cx:.2f}" y="{cy + cell * 0.12:.2f}" class="marker" '
        f'text-anchor="middle">{role}</text>'
    )
    elements.extend(_live_panel(view, 590, 110))
    elements.append("</svg>")
    return "".join(elements).encode("utf-8")


def replay_svg(
    result: ReplayVerification,
    *,
    width: int = 960,
    height: int = 420,
) -> bytes:
    """Render deterministic verified/tampered replay evidence."""
    verified = not result.findings
    background, foreground = ("#E6FCF5", "#064E3B") if verified else ("#FFF5F5", "#7F1D1D")
    finding = result.first_failure
    finding_text = (
        "No integrity findings."
        if finding is None
        else f"First failure {finding.code}: {finding.detail}"
    )
    frames = "".join(
        f"<tr><td>{item.sequence}</td><td>{escape(item.actor)}</td>"
        f"<td>{escape(item.action)}</td><td>{escape(item.commitment_status)}</td></tr>"
        for item in result.frames[:8]
    )
    return (
        _svg_header(width, height, "Verified offline replay")
        + f'<rect x="0" y="0" width="{width}" height="74" fill="{background}"/>'
        + f'<text x="32" y="46" class="title" fill="{foreground}">'
        + escape(result.accessible_status)
        + "</text>"
        + f'<text x="32" y="112" class="body">Sub-game {result.sub_game_number}; '
        + f"{result.verified_steps}/{result.expected_steps} steps verified.</text>"
        + f'<text x="32" y="148" class="body">{escape(result.track_banner)}</text>'
        + f'<text x="32" y="184" class="body">{escape(finding_text)}</text>'
        + f'<text x="32" y="232" class="mono">Evidence: {result.evidence_sha256}</text>'
        + '<foreignObject x="32" y="260" width="896" height="130">'
        + '<table xmlns="http://www.w3.org/1999/xhtml"><thead><tr><th>Step</th>'
        + f"<th>Actor</th><th>Action</th><th>Commitment</th></tr></thead><tbody>{frames}"
        + "</tbody></table></foreignObject></svg>"
    ).encode("utf-8")


def _svg_header(width: int, height: int, label: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-label="{escape(label)}" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}"><style>'
        ".title{font:700 24px system-ui}.body{font:17px system-ui;fill:#17202A}"
        ".cell{font:700 18px monospace;fill:#111827}.marker{font:700 18px system-ui;fill:white}"
        ".mono{font:13px monospace;fill:#334155}"
        "table{border-collapse:collapse;font:14px system-ui;width:100%}"
        "th,td{border:1px solid #94A3B8;padding:5px;text-align:left}</style>"
    )


def _coordinate_labels(view: LocalView, x0: int, y0: int, cell: float) -> list[str]:
    labels = []
    reverse_rows = view.axis_origin_corner.startswith("bottom")
    reverse_cols = view.axis_origin_corner.endswith("right")
    for index in range(view.board_size):
        row = view.board_size - 1 - index if reverse_rows else index
        col = view.board_size - 1 - index if reverse_cols else index
        external = index + view.axis_start_index
        labels.append(
            f'<text x="{x0 - 18}" y="{y0 + (row + 0.6) * cell:.2f}" '
            f'class="body" text-anchor="middle">{external}</text>'
        )
        labels.append(
            f'<text x="{x0 + (col + 0.5) * cell:.2f}" y="{y0 - 14}" '
            f'class="body" text-anchor="middle">{external}</text>'
        )
    return labels


def _live_panel(view: LocalView, x: int, y: int) -> list[str]:
    lines = (
        f"Own role: {view.role.title()}",
        f"Own position: {view.own_position}",
        f"Sub-game {view.sub_game_number}/{view.series_games}; step {view.step_number}",
        "Opponent belief - not a true position",
        f"Peak: {view.belief_peak_probability:.3f}",
        f"Entropy: {view.belief_entropy_bits:.3f} bits",
        f"90% credible region: {len(view.credible_region)} cells",
        f"Barriers: {view.barriers_placed}/{view.max_barriers}",
        f"Latency: {view.metrics.latency_ms} ms",
        f"Tokens: {view.metrics.input_tokens + view.metrics.output_tokens}",
        f"Fallback: {'yes' if view.metrics.fallback_used else 'no'}",
        f"Audit: {view.audit_text}",
        "Belief scale: 0.00  0.25  0.50  0.75  1.00",
    )
    return [
        f'<text x="{x}" y="{y + index * 34}" class="body">{escape(line)}</text>'
        for index, line in enumerate(lines)
    ]

"""Deterministic machine and human-readable replay report export."""

from html import escape

from police_thief_p2p.services.replay.models import ReplayVerification
from police_thief_p2p.shared.canonical_json import canonical_json_bytes


def replay_json(result: ReplayVerification) -> bytes:
    """Return canonical machine-readable replay audit JSON."""
    return canonical_json_bytes(result.as_dict())


def replay_html(result: ReplayVerification) -> bytes:
    """Return a standalone escaped accessible replay audit report."""
    findings = "".join(
        f"<li><strong>{escape(item.code)}</strong>: {escape(item.detail)}</li>"
        for item in result.findings
    )
    if not findings:
        findings = "<li>No integrity findings.</li>"
    status_class = "verified" if not result.findings else "tampered"
    document = f"""<!doctype html>
<html lang="en"><meta charset="utf-8"><title>Replay audit</title>
<style>
body{{font:18px system-ui;max-width:56rem;margin:2rem auto;padding:0 1rem;color:#17202a}}
.verified{{border-left:.5rem solid #087f5b;background:#e6fcf5;padding:1rem}}
.tampered{{border-left:.5rem solid #c92a2a;background:#fff5f5;padding:1rem}}
code{{word-break:break-all}}
</style>
<main><h1>Police-Thief Replay Audit</h1>
<section class="{status_class}" aria-label="{escape(result.integrity.value)}">
<h2>{escape(result.accessible_status)}</h2>
<p>Sub-game {result.sub_game_number}; {result.verified_steps}/{result.expected_steps}
 steps verified. {escape(result.track_banner)}</p></section>
<h2>Outcome</h2><p>Terminal: {escape(result.terminal_reason)}.
 Police {result.police_points}; Thief {result.thief_points}.</p>
<h2>Findings</h2><ol>{findings}</ol>
<h2>Evidence digest</h2><code>{escape(result.evidence_sha256)}</code>
</main></html>"""
    return document.encode("utf-8")

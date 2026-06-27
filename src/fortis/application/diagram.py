"""Autosegmental tier diagrams as monospace Unicode text.

The classic autosegmental picture, in text: autosegments sit on tier rows above the
segments, joined to their anchors by association lines. One autosegment forking to
several anchors is **spread**; several converging on one anchor is a **contour**; an
unlinked autosegment **floats** at its lexical position with no line. Rendered with
box-drawing characters so it stays readable in any monospace IPA font.
"""
from __future__ import annotations

from src.fortis.application.rendering import render_segment
from src.fortis.general.utils import is_combining
from src.fortis.models.autosegment import AutosegmentalTier
from src.fortis.models.form import Form
from src.fortis.models.project import Project

# Tone scalar (1=extra-low … 5=extra-high) → Chao tone letter.
_TONE = {5: "˥", 4: "˦", 3: "˧", 2: "˨", 1: "˩"}
_STRESS = {2: "ˈ", 1: "ˌ"}
_SEP = 3  # blank display columns between segment slots


def _dwidth(text: str) -> int:
    """Display width — combining marks occupy no column."""
    return sum(0 if is_combining(ch) else 1 for ch in text)


def _label(autoseg, tier_name: str) -> str:
    """A short label for one autosegment (a tone letter, a stress mark, …)."""
    for feature, spec in autoseg.bundle.items():
        value = spec.value
        if feature == "tone":
            if isinstance(value, tuple):
                return "".join(_TONE.get(v, "?") for v in value)
            return _TONE.get(value, str(value))
        if feature == "stress":
            return _STRESS.get(value, str(value))
        return str(value)
    return "?"


def _put(row: list[str], col: int, text: str) -> None:
    for offset, ch in enumerate(text):
        if 0 <= col + offset < len(row):
            row[col + offset] = ch


def render_autosegmental(form: Form, project: Project) -> str:
    """Render *form*'s tiers as a monospace autosegmental diagram."""
    segs = form.segments
    if not segs:
        return "(empty)"
    rendered = [render_segment(s.bundle, project) or "∅" for s in segs]
    slot = max(max((_dwidth(r) for r in rendered), default=1), 3)  # ≥3 leaves room for a contour
    step = slot + _SEP
    margin = 4  # room for a floating autosegment before the first / after the last segment
    total = margin + len(segs) * step - _SEP + margin
    center = {s.id: margin + i * step + slot // 2 for i, s in enumerate(segs)}
    pos = {s.id: i for i, s in enumerate(segs)}

    lines: list[str] = []
    for name, tier in form.tiers.items():
        if tier.autosegs:
            lines.extend(_tier_band(tier, name, center, pos, segs, total))

    seg_row = [" "] * total
    for i, r in enumerate(rendered):
        col = margin + i * step + (slot - _dwidth(r)) // 2
        _put(seg_row, col, r)
    lines.append("".join(seg_row))
    return "\n".join(line.rstrip() for line in lines)


def _tier_band(
    tier: AutosegmentalTier, name: str, center, pos, segs, total: int
) -> list[str]:
    """The label row + connector row for one tier."""
    seg_ids = {s.id for s in segs}
    label_row = [" "] * total
    conn_row = [" "] * total

    spreads, singles, floats = [], {}, []
    for autoseg in tier.autosegs:
        anchors = sorted(
            center[sid] for (a, sid) in tier.links if a == autoseg.id and sid in seg_ids
        )
        if not anchors:
            floats.append(autoseg)
        elif len(anchors) > 1:
            spreads.append((autoseg, anchors))
        else:
            singles.setdefault(anchors[0], []).append(autoseg)

    for autoseg, anchors in spreads:  # one autoseg → many anchors (the fork)
        label = _label(autoseg, name)
        mid = (anchors[0] + anchors[-1]) // 2
        _put(label_row, mid - (_dwidth(label) - 1) // 2, label)
        for x in range(anchors[0], anchors[-1] + 1):
            conn_row[x] = "─"
        for a in anchors:
            conn_row[a] = "┬"
        conn_row[anchors[0]] = "┌"
        conn_row[anchors[-1]] = "┐"
        conn_row[mid] = "┼" if mid in anchors else "┴"

    for col, group in singles.items():
        if len(group) == 1:  # one tone on one anchor
            label = _label(group[0], name)
            _put(label_row, col - (_dwidth(label) - 1) // 2, label)
            conn_row[col] = "│"
        else:  # several tones converging on one anchor — a contour
            labels = [_label(a, name) for a in group]
            _put(label_row, col - 1, labels[0])
            _put(label_row, col + 1, labels[-1])
            conn_row[col - 1], conn_row[col], conn_row[col + 1] = "└", "┬", "┘"

    for autoseg in floats:  # unlinked: shown at its lexical gap, no line
        label = _label(autoseg, name)
        col = _float_col(tier, autoseg.id, center, pos, segs)
        _put(label_row, col - (_dwidth(label) - 1) // 2, label)

    return ["".join(label_row), "".join(conn_row)]


def _float_col(tier, autoseg_id, center, pos, segs) -> int:
    host = tier.float_hosts.get(autoseg_id)
    if host is None or host[0] not in center:
        return center[segs[0].id]
    sid, side = host
    return center[sid] + (2 if side == "after" else -2)

"""Tests for the autosegmental text diagram (application/diagram.py)."""

from src.fortis.application.diagram import render_autosegmental
from src.fortis.application.segmentation import string_to_sequence
from src.fortis.models.autosegment import Autoseg
from src.fortis.models.bundles import FeatureBundle
from src.fortis.models.specs import FeatureSpec


def _tone(value, autoseg_id):
    return Autoseg(FeatureBundle({"tone": FeatureSpec("tone", value)}), autoseg_id)


def test_single_link_is_a_vertical_bar(project):
    form = string_to_sequence("ta", project)  # t a
    h = form.fresh_id()
    form.tiers["tone"].autosegs.append(_tone(4, h))
    form.tiers["tone"].links.add((h, 1))  # high on the vowel
    out = render_autosegmental(form, project)
    assert "˦" in out and "│" in out  # the tone letter + one association line


def test_spread_is_a_fork(project):
    form = string_to_sequence("taka", project)
    h = form.fresh_id()
    form.tiers["tone"].autosegs.append(_tone(4, h))
    form.tiers["tone"].links |= {(h, 1), (h, 3)}  # one tone, two anchors
    out = render_autosegmental(form, project)
    assert "┌" in out and "┐" in out and "┴" in out  # the fork


def test_contour_converges(project):
    form = string_to_sequence("ta", project)
    hi, mid = form.fresh_id(), form.fresh_id()
    form.tiers["tone"].autosegs += [_tone(5, hi), _tone(3, mid)]
    form.tiers["tone"].links |= {(hi, 1), (mid, 1)}  # two tones on one vowel
    out = render_autosegmental(form, project)
    assert "└┬┘" in out and "˥" in out and "˧" in out  # converging contour


def test_floating_tone_has_no_line(project):
    form = string_to_sequence("kata⟨◌́⟩", project)  # a floating high suffix, unanchored
    out = render_autosegmental(form, project)
    assert "˦" in out.split("\n")[0]  # the high appears on the tone row
    assert "│" not in out and "┬" not in out  # ...with no association line — it floats

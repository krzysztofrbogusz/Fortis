"""Tests for the tier maintenance pass (application/tiers.cleanup_tiers)."""

from src.fortis.application.tiers import cleanup_tiers
from src.fortis.models.autosegment import Autoseg, AutosegmentalTier
from src.fortis.models.bundles import FeatureBundle
from src.fortis.models.form import Form
from src.fortis.models.segment import Segment
from src.fortis.models.specs import FeatureSpec


def _b(**features):
    return FeatureBundle({f: FeatureSpec(feature=f, value=v) for f, v in features.items()})


def _tone(value, autoseg_id):
    return Autoseg(_b(tone=value), autoseg_id)


def test_prune_drops_links_to_deleted_segments(project):
    # H was linked to a segment that no longer exists → the link is pruned, H floats.
    form = Form([Segment(_b(syllabic=1), 0)])
    h = _tone(4, 100)
    form.tiers["tone"] = AutosegmentalTier(autosegs=[h], links={(100, 5)})  # segment 5 is gone
    cleanup_tiers(form, project.tiers)
    assert form.tiers["tone"].links == set()  # dangling link pruned
    assert form.tiers["tone"].autosegs == [h]  # the autoseg survives, now floating (stability)


def test_ocp_merges_adjacent_identical_autosegs(project):
    # two H's on adjacent syllables → merge into one H linked to both.
    form = Form([Segment(_b(syllabic=1), 0), Segment(_b(syllabic=1), 1)])
    form.tiers["tone"] = AutosegmentalTier(
        autosegs=[_tone(4, 100), _tone(4, 101)], links={(100, 0), (101, 1)}
    )
    cleanup_tiers(form, project.tiers)
    tier = form.tiers["tone"]
    assert len(tier.autosegs) == 1  # merged
    survivor = tier.autosegs[0].id
    assert tier.links == {(survivor, 0), (survivor, 1)}  # one H, both anchors


def test_distinct_adjacent_autosegs_do_not_merge(project):
    form = Form([Segment(_b(syllabic=1), 0), Segment(_b(syllabic=1), 1)])
    form.tiers["tone"] = AutosegmentalTier(
        autosegs=[_tone(4, 100), _tone(2, 101)], links={(100, 0), (101, 1)}  # H, L
    )
    cleanup_tiers(form, project.tiers)
    assert len(form.tiers["tone"].autosegs) == 2  # H != L: no merge


def test_stray_erase_only_at_the_surface(project):
    form = Form([Segment(_b(syllabic=1), 0)])
    floating = _tone(4, 100)
    form.tiers["tone"] = AutosegmentalTier(autosegs=[floating], links=set())  # no link = floating
    cleanup_tiers(form, project.tiers, surface=False)
    assert form.tiers["tone"].autosegs == [floating]  # persists mid-derivation (can re-dock)
    cleanup_tiers(form, project.tiers, surface=True)
    assert form.tiers["tone"].autosegs == []  # stray-erased at the surface

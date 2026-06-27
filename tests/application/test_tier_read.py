"""Tests for the tier read helper (application/tiers.carried_features)."""

from src.fortis.application.tiers import carried_features
from src.fortis.models.autosegment import Autoseg, AutosegmentalTier
from src.fortis.models.bundles import FeatureBundle
from src.fortis.models.form import Form
from src.fortis.models.segment import Segment
from src.fortis.models.specs import FeatureSpec


def _b(**features):
    return FeatureBundle({f: FeatureSpec(feature=f, value=v) for f, v in features.items()})


def test_reads_the_linked_autoseg_feature(project):
    form = Form([Segment(_b(syllabic=1), 0)])
    form.tiers["stress"] = AutosegmentalTier(
        autosegs=[Autoseg(_b(stress=2), 100)], links={(100, 0)}
    )
    assert carried_features(form, 0)["stress"].value == 2


def test_empty_for_an_unlinked_segment(project):
    form = Form([Segment(_b(syllabic=1), 0), Segment(_b(consonantal=1), 1)])
    form.tiers["stress"] = AutosegmentalTier(
        autosegs=[Autoseg(_b(stress=2), 100)], links={(100, 0)}
    )
    assert carried_features(form, 1) == FeatureBundle()  # segment 1 bears nothing


def test_merges_features_across_tiers(project):
    form = Form([Segment(_b(syllabic=1), 0)])
    form.tiers["stress"] = AutosegmentalTier(
        autosegs=[Autoseg(_b(stress=2), 100)], links={(100, 0)}
    )
    form.tiers["tone"] = AutosegmentalTier(
        autosegs=[Autoseg(_b(tone=4), 200)], links={(200, 0)}
    )
    carried = carried_features(form, 0)
    assert carried["stress"].value == 2 and carried["tone"].value == 4


def test_two_autosegs_on_one_anchor_form_a_contour(project):
    # H then L both linked to one segment → a falling contour, in tier order.
    form = Form([Segment(_b(syllabic=1), 0)])
    form.tiers["tone"] = AutosegmentalTier(
        autosegs=[Autoseg(_b(tone=5), 10), Autoseg(_b(tone=3), 11)], links={(10, 0), (11, 0)}
    )
    assert carried_features(form, 0)["tone"].value == (5, 3)

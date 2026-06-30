"""Tests for the tier read helper (application/tiers.carried_features)."""

from src.fortis.application.tiers import carried_features, lower_tiers
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


def _two_contours() -> Form:
    """Two syllables: a falling contour (5>3) on segment 0, a rising one (2>4) on segment 1."""
    form = Form([Segment(_b(syllabic=1), 0), Segment(_b(syllabic=1), 1)])
    form.tiers["tone"] = AutosegmentalTier(
        autosegs=[
            Autoseg(_b(tone=5), 10),
            Autoseg(_b(tone=3), 11),  # falling on segment 0
            Autoseg(_b(tone=2), 12),
            Autoseg(_b(tone=4), 13),  # rising on segment 1
        ],
        links={(10, 0), (11, 0), (12, 1), (13, 1)},
    )
    return form


def test_contours_on_two_anchors_keep_per_anchor_order(project):
    # Each anchor keeps ITS limbs in tier order — no cross-anchor mixing when many autosegs exist.
    form = _two_contours()
    assert carried_features(form, 0)["tone"].value == (5, 3)  # falling
    assert carried_features(form, 1)["tone"].value == (2, 4)  # rising


def test_lower_tiers_preserves_contour_direction_per_segment(project):
    # The whole-form lower must keep each segment's contour direction (the reindex invariant).
    lowered = lower_tiers(_two_contours())
    assert lowered[0]["tone"].value == (5, 3) and lowered[1]["tone"].value == (2, 4)

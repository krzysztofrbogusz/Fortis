"""Tests for syllabification (application/syllabifying.py).

The ``sonorities`` and ``syllable_parts`` fixtures come from conftest.
"""

from src.fortis.application.syllabifying import syllabify
from src.fortis.models.bundles import FeatureBundle
from src.fortis.models.inventories import SyllablePartsInventory
from src.fortis.models.specs import FeatureSpec


def _fb(**features: object) -> FeatureBundle:
    return FeatureBundle({f: FeatureSpec(feature=f, value=v) for f, v in features.items()})


# Segment builders (rhotic needs nasal/lateral ABSENT to match its "none" predicate).
def _v():
    return _fb(syllabic=1, consonantal=0)


def _stop():
    return _fb(consonantal=1, sonorant=0)


def _lat():
    return _fb(consonantal=1, sonorant=1, lateral=1)


def _rho():
    return _fb(consonantal=1, sonorant=1)


def _nas():
    return _fb(consonantal=1, sonorant=1, nasal=1)


def _syl(segments, sonorities, syllable_parts):
    return sorted(syllabify(segments, sonorities, syllable_parts, time=0))


class TestSyllabify:
    def test_single_nucleus_marks_word_edges(self, sonorities, syllable_parts):
        assert _syl([_v()], sonorities, syllable_parts) == [0, 1]

    def test_no_nucleus_is_unsyllabifiable(self, sonorities, syllable_parts):
        assert _syl([_stop(), _stop()], sonorities, syllable_parts) == []

    def test_hiatus_boundary_between_adjacent_nuclei(self, sonorities, syllable_parts):
        assert _syl([_v(), _v()], sonorities, syllable_parts) == [0, 1, 2]

    def test_single_intervocalic_consonant_is_onset(self, sonorities, syllable_parts):
        # V C V → V.CV (maximal onset).
        assert _syl([_v(), _stop(), _v()], sonorities, syllable_parts) == [0, 1, 3]

    def test_rising_cluster_is_all_onset(self, sonorities, syllable_parts):
        # a t l a → a.tla : stop(1) < lateral(4) rises toward the nucleus.
        assert _syl([_v(), _stop(), _lat(), _v()], sonorities, syllable_parts) == [0, 1, 4]

    def test_falling_cluster_splits_to_coda(self, sonorities, syllable_parts):
        # a l t a → al.ta : lateral(4) > stop(1), so the lateral is a coda.
        assert _syl([_v(), _lat(), _stop(), _v()], sonorities, syllable_parts) == [0, 2, 4]

    def test_nasal_coda_before_stop_onset(self, sonorities, syllable_parts):
        # p l a n t a → plan.ta : nasal(3) > stop(1) splits the nt cluster.
        word = [_stop(), _lat(), _v(), _nas(), _stop(), _v()]
        assert _syl(word, sonorities, syllable_parts) == [0, 4, 6]

    def test_rhotic_maximal_onset(self, sonorities, syllable_parts):
        # a t r a → a.tra : stop(1) < rhotic(5). Confirms the "none" predicate scores
        # the rhotic (nasal/lateral absent), not the least-sonorous fallback.
        assert _syl([_v(), _stop(), _rho(), _v()], sonorities, syllable_parts) == [0, 1, 4]

    def test_no_nucleus_definition_yields_nothing(self, sonorities, features):
        empty_parts = SyllablePartsInventory()
        assert syllabify([_v()], sonorities, empty_parts, time=0) == frozenset()

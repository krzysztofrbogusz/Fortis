"""Tests for derived-side correspondences (src/fortis/induction/correspond.py)."""

from src.fortis.analysis.grading import Grade
from src.fortis.induction.correspond import correspondences


def _grade(derived: str, target: str, distance: int, gloss: str) -> Grade:
    return Grade(gloss=gloss, ipa=derived, derived=derived, target=target, distance=distance)


class TestCorrespondences:
    def test_finds_the_substitution_and_conditions_on_the_derived_side(self, synth):
        # o → u happens before t (change) but o is kept before s (stay): the derived-side
        # right-neighbour t must surface as a positive predictor.
        grades = (
            _grade("kot", "kut", 1, "w1"),
            _grade("pot", "put", 1, "w2"),
            _grade("mot", "mut", 1, "w3"),
            _grade("kosa", "kose", 1, "w4"),  # o kept before s; the a→e error is elsewhere
            _grade("posa", "pose", 1, "w5"),
            _grade("nosa", "nose", 1, "w6"),
        )
        corrs = correspondences(grades, synth, cap=6)
        by_pair = {(c.got, c.expected): c for c in corrs}
        assert ("o", "u") in by_pair
        ou = by_pair[("o", "u")]
        assert ou.kind == "substitution"
        assert ou.delta is not None and ou.delta > 0
        right_ts = [p for p in ou.predictors if p.side == "right" and p.element == "t"]
        assert right_ts and right_ts[0].phi > 0.5

    def test_distance_cap_excludes_unreliable_words(self, synth):
        # A word past the alignment_distance_cap (default 4) must not feed the tally.
        garbage = _grade("xxxxxxxx", "kut", 8, "junk")
        clean = tuple(_grade("kot", "kut", 1, f"w{i}") for i in range(3))
        corrs = correspondences((garbage, *clean), synth, cap=6)
        # the garbage word contributes no (o,u) miscount beyond the clean ones
        ou = next((c for c in corrs if (c.got, c.expected) == ("o", "u")), None)
        assert ou is not None
        assert ou.count == 3  # only the three clean words

    def test_final_deletion_is_a_deletion_correspondence(self, synth):
        # target has a final vowel the derived form dropped → a deletion correspondence.
        grades = tuple(_grade("kan", "kana", 1, f"w{i}") for i in range(4))
        corrs = correspondences(grades, synth, cap=6)
        deletion = next((c for c in corrs if c.kind == "deletion"), None)
        assert deletion is not None
        assert deletion.expected == "a" and deletion.got is None

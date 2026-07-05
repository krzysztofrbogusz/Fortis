"""Tests for the diagnosis layer (src/fortis/analysis/diagnosis.py)."""

from src.fortis.analysis.diagnosis import (
    Confusion,
    ContextAssociation,
    FocusAutopsy,
    confusions,
    diagnose,
    diagnosis_summary_line,
    error_contexts,
    phi_coefficient,
    render_diagnosis,
)
from src.fortis.analysis.grading import AlignOp, Grade, align


def _grade(derived: str, target: str, gloss: str = "") -> Grade:
    """A Grade with a phone distance computed from the two forms (feature distance unused)."""
    from src.fortis.analysis.grading import compare

    return Grade(gloss=gloss, ipa=derived, derived=derived, target=target, distance=compare(derived, target))


class TestAlign:
    def test_all_match(self):
        ops = align(["k", "a"], ["k", "a"])
        assert [o.kind for o in ops] == ["match", "match"]
        assert [o.target_index for o in ops] == [0, 1]

    def test_substitution_on_the_diagonal(self):
        # kata → kada: the t/d mismatch is one substitution, not delete+insert.
        ops = align(["k", "a", "t", "a"], ["k", "a", "d", "a"])
        assert [o.kind for o in ops] == ["match", "match", "sub", "match"]
        sub = ops[2]
        assert (sub.target, sub.derived, sub.target_index) == ("t", "d", 2)

    def test_deletion_carries_target_index_and_no_derived(self):
        # pata → ata: p is deleted; the deletion knows its target position.
        ops = align(["p", "a", "t", "a"], ["a", "t", "a"])
        assert ops[0] == AlignOp("delete", "p", None, 0)

    def test_insertion_has_no_target_index(self):
        ops = align(["a", "t", "a"], ["p", "a", "t", "a"])
        assert ops[0] == AlignOp("insert", None, "p", None)

    def test_metathesis_reads_as_two_substitutions(self):
        # no transposition discount here (unlike edit_distance): ab → ba is two subs.
        ops = align(["a", "b"], ["b", "a"])
        assert [o.kind for o in ops] == ["sub", "sub"]


class TestConfusions:
    def test_tally_and_examples(self):
        # two t→d and one p→b across three inexact words.
        grades = (
            _grade("kada", "kata", "one"),
            _grade("mada", "mata", "two"),
            _grade("taba", "tapa", "three"),
        )
        table = confusions(grades)
        assert table[0] == Confusion("t", "d", 2, ("one", "two"))
        assert Confusion("p", "b", 1, ("three",)) in table

    def test_exact_words_contribute_nothing(self):
        assert confusions((_grade("kata", "kata"),)) == []

    def test_deletion_and_insertion_kinds(self):
        deletion = confusions((_grade("ata", "pata"),))[0]
        assert deletion.expected == "p" and deletion.got is None and deletion.kind == "deletion"
        insertion = confusions((_grade("pata", "ata"),))[0]
        assert insertion.expected is None and insertion.got == "p" and insertion.kind == "insertion"

    def test_examples_capped_at_three(self):
        grades = tuple(_grade("da", "ta", f"w{i}") for i in range(5))
        assert len(confusions(grades)[0].examples) == 3

    def test_limit(self):
        grades = (_grade("da", "ta"), _grade("ba", "pa"), _grade("ga", "ka"))
        assert len(confusions(grades, limit=2)) == 2


class TestPhiCoefficient:
    def test_perfect_positive_association(self):
        # every predictor-present case is an error, every predictor-absent case correct.
        assert phi_coefficient(err_here=2, ok_here=0, err_away=0, ok_away=1) == 1.0

    def test_no_association_is_zero(self):
        assert phi_coefficient(1, 1, 1, 1) == 0.0

    def test_perfect_negative_association(self):
        assert phi_coefficient(err_here=0, ok_here=2, err_away=2, ok_away=0) == -1.0

    def test_zero_margin_is_zero_not_error(self):
        # a predictor present everywhere (no absent cases): coefficient undefined ⇒ 0.
        assert phi_coefficient(5, 5, 0, 0) == 0.0


class TestErrorContexts:
    """A conditioned autopsy fixture with counts known by hand.

    Focus /t/ occurs five times: three after /a/ (all wrong: t→d) and twice after
    /i/ (both right). So among /t/, left=a perfectly predicts the error — phi 1.0,
    support 3 — while left=i perfectly predicts correctness.
    """

    def _grades(self):
        return (
            _grade("ada", "ata", "a1"),
            _grade("ada", "ata", "a2"),
            _grade("ada", "ata", "a3"),
            _grade("ita", "ita", "i1"),
            _grade("ita", "ita", "i2"),
        )

    def test_counts(self, project):
        autopsy = error_contexts(self._grades(), "t", project)
        assert (autopsy.phone, autopsy.errors, autopsy.total) == ("t", 3, 5)

    def test_left_a_perfectly_predicts_error(self, project):
        autopsy = error_contexts(self._grades(), "t", project)
        left_a = next(a for a in autopsy.associations if a.predictor == "left=a")
        assert left_a.phi == 1.0
        assert (left_a.err_here, left_a.ok_here) == (3, 0)
        assert (left_a.err_away, left_a.ok_away) == (0, 2)
        assert left_a.support == 3

    def test_associations_sorted_most_error_associated_first(self, project):
        autopsy = error_contexts(self._grades(), "t", project)
        phis = [a.phi for a in autopsy.associations]
        assert phis == sorted(phis, reverse=True)

    def test_support_floor_drops_thin_predictors(self, project):
        # 'right=#' would mark the two /a/-final... but here focus /t/ never sits word-final;
        # a predictor present in fewer than the floor of positions must be absent.
        autopsy = error_contexts(self._grades(), "t", project)
        for a in autopsy.associations:
            assert a.support >= 3

    def test_insertions_never_enter_the_autopsy(self, project):
        # a spurious inserted /t/ has no target position (its target has no /t/ at all),
        # so it is not a /t/ trial.
        grades = (*self._grades(), _grade("taa", "aa", "ins"))
        autopsy = error_contexts(grades, "t", project)
        assert autopsy.total == 5  # unchanged by the insertion

    def test_too_few_errors_yields_no_associations(self, project):
        autopsy = error_contexts((_grade("ita", "ita"),), "t", project)
        assert autopsy.errors == 0 and autopsy.associations == ()


class TestDiagnose:
    def test_focuses_on_the_top_confusions_expected_phones(self, project):
        grades = (
            _grade("ada", "ata", "a1"),
            _grade("ada", "ata", "a2"),
            _grade("aba", "apa", "p1"),
        )
        autopsies = diagnose(grades, project, top=5)
        phones = [a.phone for a in autopsies]
        assert phones[0] == "t"  # the most frequent confusion's expected phone leads
        assert "p" in phones


class TestRendering:
    def _grades(self):
        return (
            _grade("ada", "ata", "one"),
            _grade("ada", "ata", "two"),
            _grade("aba", "apa", "three"),
        )

    def test_report_has_sections_and_confusion_rows(self, project):
        md = render_diagnosis(self._grades(), project, "`proj`")
        assert "# Diagnosis" in md
        assert "## Confusions" in md
        assert "## Context autopsy" in md
        assert "`t`" in md and "`d`" in md  # the t→d confusion

    def test_all_exact_report_is_short(self, project):
        md = render_diagnosis((_grade("ata", "ata"),), project, "`proj`")
        assert "no confusions" in md.lower()
        assert "## Confusions" not in md

    def test_summary_line_names_the_top_confusion(self):
        line = diagnosis_summary_line(self._grades())
        assert "t→d" in line and "error site" in line

    def test_summary_line_when_all_exact(self):
        assert "no confusions" in diagnosis_summary_line((_grade("ata", "ata"),)).lower()

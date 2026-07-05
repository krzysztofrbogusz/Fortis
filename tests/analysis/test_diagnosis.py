"""Tests for the diagnosis layer (src/fortis/analysis/diagnosis.py)."""

from src.fortis.analysis.blame import Blame, Residual
from src.fortis.analysis.diagnosis import (
    Confusion,
    ContextAssociation,
    FocusAutopsy,
    StageDiagnosis,
    TimeBucket,
    confusions,
    diagnose,
    diagnose_stages,
    diagnosis_summary_line,
    error_contexts,
    errors_by_time,
    f_score,
    phi_coefficient,
    render_diagnosis,
    render_timeline,
    timeline_summary_line,
)
from src.fortis.analysis.grading import AlignOp, Grade, align
from src.fortis.application.deriving import derive_all
from src.fortis.loaders.project import load_project


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
        # pata → ata: p is deleted; the deletion knows its target position, no derived one.
        ops = align(["p", "a", "t", "a"], ["a", "t", "a"])
        assert ops[0] == AlignOp("delete", "p", None, 0, None)

    def test_insertion_has_no_target_index(self):
        # ata → pata: p is inserted; it knows its derived position, no target one.
        ops = align(["a", "t", "a"], ["p", "a", "t", "a"])
        assert ops[0] == AlignOp("insert", None, "p", None, 0)

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


class TestFScore:
    def test_perfect(self):
        # predictor present ⟺ error: precision = recall = 1 → F1 = 1.
        assert f_score(err_here=4, ok_here=0, err_away=0) == 1.0

    def test_harmonic_mean(self):
        # precision 4/(4+4)=0.5, recall 4/(4+4)=0.5 → F1 = 0.5.
        assert f_score(err_here=4, ok_here=4, err_away=4) == 0.5

    def test_zero_when_predictor_covers_no_error(self):
        assert f_score(err_here=0, ok_here=5, err_away=3) == 0.0

    def test_high_f_at_low_phi_is_possible(self):
        # Predictor present in 90% of sites, same 10% error rate present vs absent:
        # phi is exactly 0 (independence), but F1 stays healthy on recall alone —
        # the reason ranking is by phi, not F.
        assert f_score(err_here=9, ok_here=81, err_away=1) > 0.15
        assert phi_coefficient(9, 81, 1, 9) == 0.0


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
        assert left_a.fscore == 1.0  # every /t/-after-/a/ is an error, and covers all errors
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

    def test_support_floor_scales_with_occurrences(self, project):
        # 50 occurrences of /t/: with the default 10%, the floor is max(3, ceil(5.0)) = 5,
        # so a predictor present in only 4 positions is dropped even though it clears the
        # absolute floor of 3 — the bar rises with the word base.
        grades = tuple(_grade("ada", "ata", f"a{i}") for i in range(46)) + tuple(
            _grade("ida", "ita", f"i{i}") for i in range(4)
        )
        autopsy = error_contexts(grades, "t", project)
        assert autopsy.total == 50
        assert autopsy.support_floor == 5
        predictors = {a.predictor for a in autopsy.associations}
        assert "left=a" in predictors  # support 46, kept
        assert "left=i" not in predictors  # support 4, below the scaled floor of 5


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


def _res(expected, got, culprit, time):
    return Residual(expected=expected, got=got, culprit=culprit, culprit_time=time,
                    attributed=culprit is not None)


def _blame(gloss, residuals):
    return Blame(gloss=gloss, ipa=gloss, target="x", surface="y", distance=1,
                 residuals=tuple(residuals), stage_divergence=None, trajectory=())


class TestErrorsByTime:
    def test_buckets_by_culprit_time_worst_first(self):
        blames = [
            _blame("one", [_res("a", "e", "r1", 600), _res("t", "d", "r2", 1000)]),
            _blame("two", [_res("a", "e", "r3", 600)]),
            _blame("three", [_res("x", None, None, None)]),  # deletion → no rule
        ]
        buckets = errors_by_time(blames)
        assert [b.time for b in buckets] == [600, 1000, None]  # 600 has 2, worst first
        t600 = buckets[0]
        assert t600.count == 2
        assert t600.confusions[0] == Confusion("a", "e", 2, ("one", "two"))

    def test_unattributed_and_omission_group_under_none(self):
        # culprit None (deletion, omission, unattributed) all bucket to time None.
        blames = [_blame("w", [_res("a", None, None, None), _res("b", "c", None, None)])]
        buckets = errors_by_time(blames)
        assert len(buckets) == 1
        assert buckets[0].time is None and buckets[0].count == 2

    def test_empty(self):
        assert errors_by_time([]) == []


class TestDiagnoseStages:
    def test_shape_ends_with_final(self):
        project = load_project().unwrap()  # fresh default, insulated from mutations
        stages = diagnose_stages(derive_all(project), project)
        assert stages, "expected at least the final stage"
        assert stages[-1].label == "final" and stages[-1].time is None
        assert all(isinstance(s, StageDiagnosis) for s in stages)


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

    def test_timeline_report_has_both_temporal_sections(self, project):
        buckets = [TimeBucket(600, 2, (Confusion("a", "e", 2, ("one",)),))]
        stages = [StageDiagnosis("final", None, (Confusion("t", "d", 1, ("x",)),), ())]
        md = render_timeline(buckets, stages, project, "`proj`")
        assert "# Timeline" in md
        assert "## Errors by rule-time" in md and "t=600" in md
        assert "## Per-stage diagnosis" in md and "### stage final" in md

    def test_diagnosis_snapshot_has_no_temporal_sections(self, project):
        md = render_diagnosis(self._grades(), project, "`proj`")
        assert "## Errors by rule-time" not in md and "## Per-stage diagnosis" not in md

    def test_empty_timeline(self, project):
        assert "no timeline" in render_timeline([], [], project, "`proj`").lower()

    def test_timeline_summary_line(self):
        buckets = [TimeBucket(1400, 28, ()), TimeBucket(None, 22, ()), TimeBucket(600, 10, ())]
        assert "t=1400" in timeline_summary_line(buckets)

    def test_summary_line_names_the_top_confusion(self):
        line = diagnosis_summary_line(self._grades())
        assert "t→d" in line and "error site" in line

    def test_summary_line_when_all_exact(self):
        assert "no confusions" in diagnosis_summary_line((_grade("ata", "ata"),)).lower()

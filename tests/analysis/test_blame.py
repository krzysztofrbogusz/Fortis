"""Tests for rule blame (src/fortis/analysis/blame.py).

Uses the real Latin→French project — it has genuinely wrong words with attributable
residuals — rather than synthesising Derivations by hand.
"""

from pathlib import Path

import pytest

from src.fortis.analysis.blame import (
    _phone_ids,
    blame_all,
    blame_summary_line,
    blame_word,
    render_blame,
)
from src.fortis.analysis.grading import grade, split_phones
from src.fortis.application.deriving import derive_all
from src.fortis.application.rendering import render_syllabified
from src.fortis.application.tiers import lower_tiers
from src.fortis.loaders.project import load_project


@pytest.fixture(scope="module")
def latin():
    return load_project(Path("projects/latin_to_french")).unwrap()


@pytest.fixture(scope="module")
def derivs(latin):
    return derive_all(latin)


@pytest.fixture(scope="module")
def blames(derivs, latin):
    return blame_all(derivs, latin)


class TestInvariants:
    def test_blame_distance_equals_grader_distance(self, blames, derivs, latin):
        graded = {g.gloss: g.distance for g in grade(derivs, latin).grades}
        for blame in blames:
            assert blame.distance == graded[blame.gloss]

    def test_trajectory_endpoint_is_the_surface(self, blames):
        # The final trajectory point is derivation.surface, so its distance is the grade.
        for blame in blames:
            assert blame.trajectory[-1].label == "surface"
            assert blame.trajectory[-1].distance == blame.distance

    def test_only_wrong_words_are_blamed(self, blames):
        assert blames  # Latin has wrong words
        for blame in blames:
            assert blame.distance > 0
            assert blame.residuals  # a wrong word has at least one residual


class TestProvenance:
    def test_culprits_are_rules_that_fired_on_that_word(self, blames, derivs):
        # Provenance may only name a rule that actually fired on the word in question.
        by_gloss = {d.word.gloss: d for d in derivs}
        for blame in blames:
            fired = {step.rule.id for step in by_gloss[blame.gloss].steps}
            for residual in blame.residuals:
                if residual.culprit is not None:
                    assert residual.culprit in fired

    def test_summary_line_names_a_culprit(self, blames):
        line = blame_summary_line(blames)
        assert "wrong word(s)" in line


class TestStructure:
    def test_exact_word_is_not_blamed(self, derivs, latin):
        # Find an exactly-derived word (there are hundreds) — it gets no blame.
        blamed = {b.gloss for b in blame_all(derivs, latin)}
        exact = next(d for d in derivs if d.word.final and d.word.gloss not in blamed)
        assert blame_word(exact, latin) is None

    def test_word_without_target_is_not_blamed(self, derivs, latin):
        target_less = next((d for d in derivs if d.word.final is None), None)
        if target_less is not None:
            assert blame_word(target_less, latin) is None

    def test_render_has_sections_and_caveat(self, blames):
        md = render_blame(blames, "`proj`")
        assert "# Blame" in md
        assert "notation artifact" in md  # the stage caveat
        assert "Residuals:" in md

    def test_render_empty_is_short(self):
        md = render_blame([], "`proj`")
        assert "nothing to blame" in md.lower()
        assert "Residuals:" not in md


class TestUnattributable:
    """When a surface phone doesn't map 1:1 to a segment (leading stress mark, tie-bar
    affricate), attribution is dropped rather than blaming a misaligned rule."""

    def test_length_mismatch_degrades_to_no_culprit(self):
        # A fresh default project (its word.final is mutated below, so not the shared
        # session fixture); it has a word whose render adds a phone with no segment.
        project = load_project().unwrap()
        derivations = derive_all(project)
        mismatch = next(
            d
            for d in derivations
            if len(split_phones(render_syllabified(lower_tiers(d.surface), d.surface_boundaries, project)))
            != len(_phone_ids(d.surface))
        )
        surface = render_syllabified(lower_tiers(mismatch.surface), mismatch.surface_boundaries, project)
        phones = split_phones(surface)
        # Mangle the last phone so the word is wrong and yields at least one residual.
        mismatch.word.final = "".join(phones[:-1]) + ("x" if phones[-1] != "x" else "y")

        blame = blame_word(mismatch, project)
        assert blame is not None and blame.residuals
        # Every residual: no rule blamed, flagged unattributed, and NOT mislabelled omission.
        assert all(not r.attributed for r in blame.residuals)
        assert all(r.culprit is None for r in blame.residuals)
        assert all(r.kind != "omission" for r in blame.residuals)
        assert "unattributed" in render_blame([blame], "`proj`")

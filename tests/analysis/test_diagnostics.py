"""Tests for the diagnostics match-set query (src/fortis/analysis/diagnostics.py)."""

from pathlib import Path

from src.fortis.analysis.diagnostics import match_set
from src.fortis.loaders.project import load_project


def _project():
    return load_project(Path("projects/default")).unwrap()


def test_match_set_returns_the_engines_denotation_of_a_bundle():
    # The whole point: the answer is the engine's own match, so a bundle's real reach is visible.
    proj = _project()
    result = match_set("+nasal", proj).unwrap()
    assert result.total == len(proj.letters)
    assert "m" in result.matched and "n" in result.matched and "ŋ" in result.matched
    assert "p" not in result.matched  # a plain oral stop is not nasal
    # inventory order is preserved (not sorted), so it reads like the letters file
    assert result.matched == [s for s in proj.letters if s in result.matched]


def test_coronal_front_overlap_is_surfaced_not_hidden():
    # The canonical feature-system surprise: [+front] is the coronal place node too, so a bundle
    # meaning "front glide/sonorant" also catches every coronal. The tool must show that.
    proj = _project()
    matched = match_set("+front, +sonorant, -syllabic", proj).unwrap().matched
    assert {"n", "l", "r", "j"} <= set(matched)  # coronals AND the palatal glide, together


def test_brackets_are_optional():
    proj = _project()
    bracketed = match_set("[+nasal]", proj).unwrap().matched
    assert bracketed == match_set("+nasal", proj).unwrap().matched


def test_empty_input_is_a_friendly_error():
    assert match_set("   ", _project()).unwrap_err().startswith("Enter a feature bundle")


def test_unknown_feature_surfaces_the_parse_error_as_a_string():
    err = match_set("+bogus", _project()).unwrap_err()
    assert isinstance(err, str) and "bogus" in err


def test_rule_only_specs_are_rejected_with_a_clear_message():
    # References, agreement variables, and conditionals silently match all-or-nothing without a
    # rule's bindings, so they are rejected up front rather than returning a misleading set.
    proj = _project()
    cases = [("oral: ~1", "oral"), ("αvoice", "voice"), ("<1: aperture: high>", "aperture")]
    for query, offender in cases:
        err = match_set(query, proj).unwrap_err()
        assert "inside a rule" in err and offender in err

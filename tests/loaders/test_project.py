"""Tests for project assembly (loaders/project.py)."""

from pathlib import Path

from src.fortis.loaders.project import load_project, unfired_scoped_rules

# A project dir with a lexicon: the PIE example has 'mother' (gloss) / 'meħˈteːr' (ipa).
_PIE = Path(__file__).resolve().parent.parent.parent / "projects" / "pie_to_germanic"


def test_word_scope_unknown_word_is_flagged(tmp_path):
    # A `words` entry matching no word (by ipa or gloss) is a likely typo → flagged,
    # not an error: the project still loads, and the rule is reported as never-firing.
    rules = tmp_path / "rules.toml"
    rules.write_text('[r]\nwords = ["snu"]\ndefinition = "a → e"\n', encoding="utf-8")
    project = load_project(_PIE, rules_path=rules).unwrap()
    assert ("r", "snu") in unfired_scoped_rules(project.rules, project.words)


def test_word_scope_known_word_is_not_flagged(tmp_path):
    # Matching by gloss ('mother') or by ipa ('meħˈteːr') is fine — nothing flagged.
    rules = tmp_path / "rules.toml"
    rules.write_text(
        '[r]\nwords = ["mother", "meħˈteːr"]\ndefinition = "a → e"\n', encoding="utf-8"
    )
    project = load_project(_PIE, rules_path=rules).unwrap()
    assert unfired_scoped_rules(project.rules, project.words) == []



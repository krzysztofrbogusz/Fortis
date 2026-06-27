"""Smoke test for the tonal showcase (examples/tonal) — spread + stability on real data."""

from pathlib import Path

from src.fortis.application.deriving import derive, resolve_rule_letters
from src.fortis.application.segmentation import string_to_sequence
from src.fortis.application.tiers import lower_tiers
from src.fortis.loaders.project import load_project

_EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "tonal"


def test_tonal_example_runs_and_preserves_tone():
    project = load_project(_EXAMPLE).unwrap()
    assert len(project.words) == 3  # spread, stability, and dock demos
    rules = resolve_rule_letters(project.rules, project)
    for ipa, word in project.words.items():
        form = string_to_sequence(ipa, project)
        result = derive(
            word,
            form,
            rules,
            project.letters,
            project.features,
            project.sonorities,
            project.syllable_parts,
            project.tiers,
        )
        assert result.steps  # a rule fired
        surface_tones = [b["tone"].value for b in lower_tiers(result.surface) if "tone" in b]
        assert surface_tones == [4]  # exactly one high tone survives to the surface


def test_displacement_variant_shifts_the_tone():
    # The rules_shift.toml variant: the high tone shifts off its sponsor onto the next vowel.
    project = load_project(_EXAMPLE, rules_path=_EXAMPLE / "rules_shift.toml").unwrap()
    rules = resolve_rule_letters(project.rules, project)
    ipa, word = next((i, w) for i, w in project.words.items() if i.startswith("ta"))
    surface = derive(
        word,
        string_to_sequence(ipa, project),
        rules,
        project.letters,
        project.features,
        project.sonorities,
        project.syllable_parts,
        project.tiers,
    ).surface
    tones = [b["tone"].value if "tone" in b else None for b in lower_tiers(surface)]
    assert tones == [None, None, None, 4]  # the high moved off vowel 1 onto vowel 2

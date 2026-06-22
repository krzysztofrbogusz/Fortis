"""Tests for result application (application/applying.py)."""

import pytest

from src.fortis.application.applying import apply_match
from src.fortis.application.matching import find_matches
from src.fortis.models.bundles import FeatureBundle
from src.fortis.models.inventories import Letter, LetterInventory
from src.fortis.models.specs import FeatureSpec
from src.fortis.parsing.notation import parse_definition


def _fb(**features: object) -> FeatureBundle:
    """Build a realized FeatureBundle from feature=value kwargs."""
    return FeatureBundle({f: FeatureSpec(feature=f, value=v) for f, v in features.items()})


@pytest.fixture
def letters() -> LetterInventory:
    """A small letter inventory for replacement results."""
    return LetterInventory(
        {
            "a": Letter(symbol="a", bundle=_fb(syllabic=1, high=0)),
            "u": Letter(symbol="u", bundle=_fb(syllabic=1, high=1, rounded=1)),
            "e": Letter(symbol="e", bundle=_fb(syllabic=1, high=0, front=1)),
            "x": Letter(symbol="x", bundle=_fb(consonantal=1, voice=0)),
        }
    )


def _apply(rule, segs, features, letters):
    """Parse *rule*, match it against *segs*, and apply at the first locus."""
    sd = parse_definition(rule, features).unwrap()
    matches = find_matches(sd, segs, letters)
    assert matches, f"rule {rule!r} found no locus"
    return apply_match(sd, matches[0], segs, letters, features)


def _values(bundles) -> list[dict]:
    """A comparable view of a list of bundles: feature → value dicts."""
    return [{f: s.value for f, s in b.items()} for b in bundles]


class TestMergePath:
    def test_bundle_merge_preserves_other_features(self, features, letters):
        out = _apply("[+nasal] -> [-voice]", [_fb(nasal=1, voice=1)], features, letters)
        assert _values(out) == [{"nasal": 1, "voice": 0}]

    def test_unlink_delinks_node_and_descendants(self, features, letters):
        # `manner` dominates continuant/sonorant/nasal/lateral.
        seg = _fb(nasal=1, manner=1, voice=1, continuant=0)
        out = _apply("[+nasal] -> [manner: none]", [seg], features, letters)
        assert _values(out) == [{"voice": 1}]

    def test_alpha_recall_in_result(self, features, letters):
        # α binds to the left neighbour's front; the result recalls it onto the target.
        segs = [_fb(front=1), _fb(high=1)]
        out = _apply("[+high] -> [αfront] / [αfront] _", segs, features, letters)
        assert _values(out) == [{"front": 1, "high": 1}]

    def test_mixed_null_and_bundle(self, features, letters):
        # ∅ deletes the consonant; the bundle modifies the vowel (§2.5.5).
        segs = [_fb(consonantal=1), _fb(syllabic=1)]
        out = _apply("[+cons][+syll] -> ∅[-syll]", segs, features, letters)
        assert _values(out) == [{"syllabic": 0}]

    def test_letter_in_merge_path_replaces_its_pair(self, features, letters):
        # Result has a bundle (→ merge path), but element 0 is a letter: it replaces
        # its paired segment wholesale while the bundle merges onto its own pair.
        segs = [_fb(consonantal=1, voice=1), _fb(syllabic=1)]
        out = _apply("[+cons][+syll] -> x[-syll]", segs, features, letters)
        assert _values(out) == [{"consonantal": 1, "voice": 0}, {"syllabic": 0}]

    def test_negated_class_target_merges(self, features, letters):
        # A natural class by negation as the target, with a feature-changing result.
        out = _apply("![+nasal] -> [+voice]", [_fb(consonantal=1)], features, letters)
        assert _values(out) == [{"consonantal": 1, "voice": 1}]

    def test_bound_single_segment_target_merges(self, features, letters):
        out = _apply("1=[+cons] -> [+voice]", [_fb(consonantal=1)], features, letters)
        assert _values(out) == [{"consonantal": 1, "voice": 1}]

    def test_mid_span_null_insertion(self, features, letters):
        # ∅ between two consumed segments: cursor advances past the bundles but the
        # ∅ inserts a fresh segment between them.
        segs = [_fb(consonantal=1), _fb(syllabic=1)]
        out = _apply("[+cons] ∅ [+syll] -> [+voice][+nasal][-syll]", segs, features, letters)
        assert _values(out) == [{"consonantal": 1, "voice": 1}, {"nasal": 1}, {"syllabic": 0}]

    def test_three_pair_merge_keeps_correspondence(self, features, letters):
        segs = [_fb(nasal=1), _fb(lateral=1), _fb(continuant=1)]
        out = _apply("[+nasal][+lateral][+cont] -> [-voice][+high][-high]", segs, features, letters)
        assert _values(out) == [
            {"nasal": 1, "voice": 0},
            {"lateral": 1, "high": 1},
            {"continuant": 1, "high": 0},
        ]


class TestReplacementPath:
    def test_letter_replaces_wholesale(self, features, letters):
        out = _apply("x -> a", [_fb(consonantal=1, voice=0)], features, letters)
        assert _values(out) == [{"syllabic": 1, "high": 0}]

    def test_collapse_two_into_one(self, features, letters):
        # `a u` is two letters (space-separated); they collapse into one.
        segs = [_fb(syllabic=1, high=0), _fb(syllabic=1, high=1, rounded=1)]
        out = _apply("a u -> e", segs, features, letters)
        assert _values(out) == [{"syllabic": 1, "high": 0, "front": 1}]

    def test_expand_one_into_two(self, features, letters):
        out = _apply("e -> a u", [_fb(syllabic=1, high=0, front=1)], features, letters)
        assert _values(out) == [
            {"syllabic": 1, "high": 0},
            {"syllabic": 1, "high": 1, "rounded": 1},
        ]

    def test_deletion(self, features, letters):
        out = _apply("[+cons] -> ∅", [_fb(consonantal=1)], features, letters)
        assert out == []

    def test_insertion(self, features, letters):
        # ∅ target is zero-width; the result bundle is inserted from scratch.
        out = _apply("∅ -> [+voice] / [+nasal] _", [_fb(nasal=1)], features, letters)
        assert _values(out) == [{"voice": 1}]

    def test_recall_in_result(self, features, letters):
        # @1 in the result re-emits the bound element wholesale.
        segs = [_fb(consonantal=1, voice=1)]
        out = _apply("1=[+cons] -> @1", segs, features, letters)
        assert _values(out) == [{"consonantal": 1, "voice": 1}]


class TestDeferredShapesRefused:
    def test_quantified_merge_refused(self, features, letters):
        sd = parse_definition("[+cons]{2} -> [-voice]{2}", features).unwrap()
        segs = [_fb(consonantal=1, voice=1), _fb(consonantal=1, voice=1)]
        match = find_matches(sd, segs, letters)[0]
        with pytest.raises(NotImplementedError):
            apply_match(sd, match, segs, letters, features)

    def test_conditional_result_feature_refused(self, features, letters):
        sd = parse_definition("[<1: +high>] -> [<1: +voice>]", features).unwrap()
        segs = [_fb(high=1)]
        match = find_matches(sd, segs, letters)[0]
        with pytest.raises(NotImplementedError):
            apply_match(sd, match, segs, letters, features)

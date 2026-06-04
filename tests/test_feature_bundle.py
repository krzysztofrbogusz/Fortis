"""Tests for src.fortis.models.feature_bundle — parsing, matching, diffing, combining."""

from __future__ import annotations

import pytest

from src.fortis.imports.features import FeatureInventory
from src.fortis.models.feature_bundle import FeatureBundle
from src.fortis.models.feature_spec import FeatureSpec
from tests.conftest import make_feature_inventory


@pytest.fixture
def features() -> FeatureInventory:
    return make_feature_inventory()


# ---------------------------------------------------------------------------
# from_str
# ---------------------------------------------------------------------------


class TestFromStr:
    def test_single_feature(self, features):
        result = FeatureBundle.from_str("+cons", features)
        assert result.is_ok()
        bundle = result.unwrap()
        assert "consonantal" in bundle

    def test_comma_separated(self, features):
        result = FeatureBundle.from_str("+cons, -syll", features)
        assert result.is_ok()
        bundle = result.unwrap()
        assert "consonantal" in bundle
        assert "syllabic" in bundle

    def test_semicolon_separated(self, features):
        result = FeatureBundle.from_str("+cons; -syll", features)
        assert result.is_ok()
        bundle = result.unwrap()
        assert "consonantal" in bundle
        assert "syllabic" in bundle

    def test_scalar_label(self, features):
        result = FeatureBundle.from_str("height: high", features)
        assert result.is_ok()
        bundle = result.unwrap()
        assert bundle["height"].value == 3

    def test_contour_value(self, features):
        result = FeatureBundle.from_str("tone: 1>3", features)
        assert result.is_ok()
        assert result.unwrap()["tone"].value == [1, 3]

    def test_bare_unary(self, features):
        result = FeatureBundle.from_str("nasal", features, bare_unary_means_present=True)
        assert result.is_ok()
        assert result.unwrap()["nasal"].value == 1

    def test_invalid_feature(self, features):
        result = FeatureBundle.from_str("+unknown", features)
        assert result.is_err()

    def test_mixed_valid_and_invalid(self, features):
        result = FeatureBundle.from_str("+cons, +unknown", features)
        assert result.is_err()

    def test_empty_string(self, features):
        result = FeatureBundle.from_str("", features)
        assert result.is_ok()
        assert len(result.unwrap()) == 0

    def test_whitespace_handling(self, features):
        result = FeatureBundle.from_str("  +cons  ,  -syll  ", features)
        assert result.is_ok()


# ---------------------------------------------------------------------------
# match_pattern
# ---------------------------------------------------------------------------


class TestMatchPattern:
    def test_subset_matches(self, features):
        segment = FeatureBundle.from_str("+cons, -syll", features).unwrap()
        pattern = FeatureBundle.from_str("+cons", features).unwrap()
        assert segment.match_pattern(pattern) is True

    def test_missing_feature_fails(self, features):
        segment = FeatureBundle.from_str("+cons", features).unwrap()
        pattern = FeatureBundle.from_str("+cons, +nasal", features).unwrap()
        assert segment.match_pattern(pattern) is False

    def test_value_mismatch_fails(self, features):
        segment = FeatureBundle.from_str("+cons, +syll", features).unwrap()
        pattern = FeatureBundle.from_str("+cons, -syll", features).unwrap()
        assert segment.match_pattern(pattern) is False

    def test_empty_pattern_matches_anything(self, features):
        segment = FeatureBundle.from_str("+cons", features).unwrap()
        pattern = FeatureBundle()
        assert segment.match_pattern(pattern) is True

    def test_absent_feature_never_satisfies(self, features):
        """A feature entirely absent from the segment never satisfies a positive pattern."""
        segment = FeatureBundle.from_str("+cons", features).unwrap()
        pattern = FeatureBundle.from_str("+nasal", features).unwrap()
        assert segment.match_pattern(pattern, ignore_none=True) is False

    def test_ignore_none_value_wildcard(self, features):
        """A None value in the segment is a wildcard when ignore_none=True."""
        segment = FeatureBundle({"consonantal": FeatureSpec("consonantal", None)})
        pattern = FeatureBundle.from_str("+cons", features).unwrap()
        assert segment.match_pattern(pattern, ignore_none=True) is True

    def test_no_ignore_none_value(self, features):
        """A None value in the segment does NOT match when ignore_none=False."""
        segment = FeatureBundle({"consonantal": FeatureSpec("consonantal", None)})
        pattern = FeatureBundle.from_str("+cons", features).unwrap()
        assert segment.match_pattern(pattern, ignore_none=False) is False


# ---------------------------------------------------------------------------
# match_exact
# ---------------------------------------------------------------------------


class TestMatchExact:
    def test_identical(self, features):
        a = FeatureBundle.from_str("+cons, -syll", features).unwrap()
        b = FeatureBundle.from_str("+cons, -syll", features).unwrap()
        assert a.match_exact(b) is True

    def test_different_keys(self, features):
        a = FeatureBundle.from_str("+cons", features).unwrap()
        b = FeatureBundle.from_str("+cons, -syll", features).unwrap()
        assert a.match_exact(b) is False

    def test_different_values(self, features):
        a = FeatureBundle.from_str("+cons", features).unwrap()
        b = FeatureBundle.from_str("-cons", features).unwrap()
        assert a.match_exact(b) is False


# ---------------------------------------------------------------------------
# differing
# ---------------------------------------------------------------------------


class TestDiffering:
    def test_identical(self, features):
        a = FeatureBundle.from_str("+cons, -syll", features).unwrap()
        b = FeatureBundle.from_str("+cons, -syll", features).unwrap()
        assert a.differing(b) == []

    def test_value_diff(self, features):
        a = FeatureBundle.from_str("+cons", features).unwrap()
        b = FeatureBundle.from_str("-cons", features).unwrap()
        assert "consonantal" in a.differing(b)

    def test_missing_feature(self, features):
        a = FeatureBundle.from_str("+cons", features).unwrap()
        b = FeatureBundle.from_str("+cons, +nasal", features).unwrap()
        diff = a.differing(b)
        assert "nasal" in diff

    def test_extra_feature(self, features):
        a = FeatureBundle.from_str("+cons, +nasal", features).unwrap()
        b = FeatureBundle.from_str("+cons", features).unwrap()
        diff = a.differing(b)
        assert "nasal" in diff


# ---------------------------------------------------------------------------
# combine_with
# ---------------------------------------------------------------------------


class TestCombineWith:
    def test_merge_new_feature(self, features):
        a = FeatureBundle.from_str("+cons", features).unwrap()
        b = FeatureBundle.from_str("+nasal", features).unwrap()
        result = a.combine_with(b)
        assert "consonantal" in result
        assert "nasal" in result

    def test_merge_overrides(self, features):
        a = FeatureBundle.from_str("+cons", features).unwrap()
        b = FeatureBundle.from_str("-cons", features).unwrap()
        result = a.combine_with(b)
        assert result["consonantal"].value == 0

    def test_preserves_unmentioned(self, features):
        a = FeatureBundle.from_str("+cons, -syll", features).unwrap()
        b = FeatureBundle.from_str("+nasal", features).unwrap()
        result = a.combine_with(b)
        assert result["syllabic"].value == 0
        assert result["nasal"].value == 1

    def test_form_contours(self, features):
        a = FeatureBundle.from_str("tone: 1", features).unwrap()
        b = FeatureBundle.from_str("tone: 3", features).unwrap()
        result = a.combine_with(b, form_contours=True)
        assert result["tone"].value == [1, 3]

    def test_no_form_contours(self, features):
        a = FeatureBundle.from_str("tone: 1", features).unwrap()
        b = FeatureBundle.from_str("tone: 3", features).unwrap()
        result = a.combine_with(b, form_contours=False)
        assert result["tone"].value == 3  # overridden, not appended

    def test_original_unchanged(self, features):
        a = FeatureBundle.from_str("+cons", features).unwrap()
        b = FeatureBundle.from_str("-cons", features).unwrap()
        _ = a.combine_with(b)
        assert a["consonantal"].value == 1  # original bundle unchanged

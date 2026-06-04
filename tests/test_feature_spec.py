"""Tests for src.fortis.models.feature_spec — FeatureSpec parsing, matching, and contour."""

from __future__ import annotations

import pytest

from src.fortis.imports.features import FeatureInventory
from src.fortis.models.feature_spec import FeatureSpec
from tests.conftest import make_feature_inventory


@pytest.fixture
def features() -> FeatureInventory:
    return make_feature_inventory()


# ---------------------------------------------------------------------------
# from_string
# ---------------------------------------------------------------------------


class TestFromString:
    def test_plus_binary(self, features):
        result = FeatureSpec.from_string("+consonantal", features)
        assert result.is_ok()
        spec = result.unwrap()
        assert spec.feature == "consonantal"
        assert spec.value == 1

    def test_minus_binary(self, features):
        result = FeatureSpec.from_string("-consonantal", features)
        assert result.is_ok()
        spec = result.unwrap()
        assert spec.feature == "consonantal"
        assert spec.value == 0

    def test_short_name(self, features):
        result = FeatureSpec.from_string("+cons", features)
        assert result.is_ok()
        assert result.unwrap().feature == "consonantal"

    def test_scalar_int(self, features):
        result = FeatureSpec.from_string("height:3", features)
        assert result.is_ok()
        spec = result.unwrap()
        assert spec.feature == "height"
        assert spec.value == 3

    def test_scalar_label(self, features):
        result = FeatureSpec.from_string("height:high", features)
        assert result.is_ok()
        assert result.unwrap().value == 3

    def test_short_name_scalar(self, features):
        result = FeatureSpec.from_string("hgt:2", features)
        assert result.is_ok()
        assert result.unwrap().feature == "height"

    def test_bare_unary(self, features):
        result = FeatureSpec.from_string("nasal", features, bare_unary_means_present=True)
        assert result.is_ok()
        assert result.unwrap().value == 1

    def test_bare_unary_false_is_error(self, features):
        result = FeatureSpec.from_string("nasal", features, bare_unary_means_present=False)
        assert result.is_err()

    def test_unknown_feature(self, features):
        result = FeatureSpec.from_string("+unknown", features)
        assert result.is_err()

    def test_contour_value(self, features):
        result = FeatureSpec.from_string("tone:1>3", features)
        assert result.is_ok()
        spec = result.unwrap()
        assert spec.feature == "tone"
        assert spec.value == [1, 3]

    def test_unspecified_value(self, features):
        result = FeatureSpec.from_string("consonantal:none", features)
        assert result.is_ok()
        assert result.unwrap().value is None

    def test_syllable_tier(self, features):
        result = FeatureSpec.from_string("tone:2", features)
        assert result.is_ok()
        assert result.unwrap().feature == "tone"


# ---------------------------------------------------------------------------
# matches — single vs single
# ---------------------------------------------------------------------------


class TestMatchesSingleSingle:
    def test_equal(self, features):
        a = FeatureSpec("consonantal", 1)
        b = FeatureSpec("consonantal", 1)
        assert a.matches(b) is True

    def test_not_equal(self, features):
        a = FeatureSpec("consonantal", 1)
        b = FeatureSpec("consonantal", 0)
        assert a.matches(b) is False

    def test_both_none(self, features):
        a = FeatureSpec("consonantal", None)
        b = FeatureSpec("consonantal", None)
        assert a.matches(b) is True


class TestMatchesNoneHandling:
    def test_self_none_other_int_ignore(self, features):
        a = FeatureSpec("consonantal", None)
        b = FeatureSpec("consonantal", 1)
        assert a.matches(b, ignore_none=True) is True

    def test_self_none_other_int_no_ignore(self, features):
        a = FeatureSpec("consonantal", None)
        b = FeatureSpec("consonantal", 1)
        assert a.matches(b, ignore_none=False) is False

    def test_self_int_other_none_ignore(self, features):
        a = FeatureSpec("consonantal", 1)
        b = FeatureSpec("consonantal", None)
        assert a.matches(b, ignore_none=True) is True

    def test_self_int_other_none_no_ignore(self, features):
        a = FeatureSpec("consonantal", 1)
        b = FeatureSpec("consonantal", None)
        assert a.matches(b, ignore_none=False) is False


# ---------------------------------------------------------------------------
# matches — single vs contour
# ---------------------------------------------------------------------------


class TestMatchesSingleContour:
    def test_any_existential(self, features):
        pattern = FeatureSpec("tone", 1)
        target = FeatureSpec("tone", [1, 3])
        assert pattern.matches(target, place="any") is True

    def test_any_not_present(self, features):
        pattern = FeatureSpec("tone", 5)
        target = FeatureSpec("tone", [1, 3])
        assert pattern.matches(target, place="any") is False

    def test_initial_match(self, features):
        pattern = FeatureSpec("tone", 1)
        target = FeatureSpec("tone", [1, 3])
        assert pattern.matches(target, place="initial") is True

    def test_initial_no_match(self, features):
        pattern = FeatureSpec("tone", 3)
        target = FeatureSpec("tone", [1, 3])
        assert pattern.matches(target, place="initial") is False

    def test_final_match(self, features):
        pattern = FeatureSpec("tone", 3)
        target = FeatureSpec("tone", [1, 3])
        assert pattern.matches(target, place="final") is True

    def test_final_no_match(self, features):
        pattern = FeatureSpec("tone", 1)
        target = FeatureSpec("tone", [1, 3])
        assert pattern.matches(target, place="final") is False

    def test_all_match(self, features):
        pattern = FeatureSpec("tone", 3)
        target = FeatureSpec("tone", [3, 3])
        assert pattern.matches(target, place="all") is True

    def test_all_not_uniform(self, features):
        pattern = FeatureSpec("tone", 3)
        target = FeatureSpec("tone", [1, 3])
        assert pattern.matches(target, place="all") is False

    def test_index_match(self, features):
        pattern = FeatureSpec("tone", 3)
        target = FeatureSpec("tone", [1, 3, 5])
        assert pattern.matches(target, place=1) is True

    def test_index_out_of_range(self, features):
        pattern = FeatureSpec("tone", 3)
        target = FeatureSpec("tone", [1, 3])
        assert pattern.matches(target, place=5) is False

    def test_index_list_match(self, features):
        pattern = FeatureSpec("tone", 1)
        target = FeatureSpec("tone", [1, 1, 3])
        assert pattern.matches(target, place=[0, 1]) is True

    def test_index_list_partial_fail(self, features):
        pattern = FeatureSpec("tone", 1)
        target = FeatureSpec("tone", [1, 3, 1])
        assert pattern.matches(target, place=[0, 1]) is False


# ---------------------------------------------------------------------------
# matches — contour vs contour
# ---------------------------------------------------------------------------


class TestMatchesContourContour:
    def test_any_existential(self, features):
        pattern = FeatureSpec("tone", [1, 3])
        target = FeatureSpec("tone", [1, 5])
        assert pattern.matches(target, place="any") is True  # position 0 matches

    def test_all_same_length(self, features):
        pattern = FeatureSpec("tone", [1, 3])
        target = FeatureSpec("tone", [1, 3])
        assert pattern.matches(target, place="all") is True

    def test_all_different_length(self, features):
        pattern = FeatureSpec("tone", [1, 3])
        target = FeatureSpec("tone", [1, 3, 5])
        assert pattern.matches(target, place="all") is False

    def test_initial(self, features):
        pattern = FeatureSpec("tone", [1, 99])
        target = FeatureSpec("tone", [1, 3])
        assert pattern.matches(target, place="initial") is True

    def test_final(self, features):
        pattern = FeatureSpec("tone", [99, 3])
        target = FeatureSpec("tone", [1, 3])
        assert pattern.matches(target, place="final") is True


# ---------------------------------------------------------------------------
# form_contour
# ---------------------------------------------------------------------------


class TestFormContour:
    def test_int_plus_int(self, features):
        a = FeatureSpec("tone", 1)
        b = FeatureSpec("tone", 3)
        result = a.form_contour(b)
        assert result.value == [1, 3]

    def test_int_plus_contour(self, features):
        a = FeatureSpec("tone", 1)
        b = FeatureSpec("tone", [2, 3])
        result = a.form_contour(b)
        assert result.value == [1, 2, 3]

    def test_contour_plus_int(self, features):
        a = FeatureSpec("tone", [1, 2])
        b = FeatureSpec("tone", 3)
        result = a.form_contour(b)
        assert result.value == [1, 2, 3]

    def test_contour_plus_contour(self, features):
        a = FeatureSpec("tone", [1, 2])
        b = FeatureSpec("tone", [3, 5])
        result = a.form_contour(b)
        assert result.value == [1, 2, 3, 5]

    def test_different_features_raises(self, features):
        a = FeatureSpec("tone", 1)
        b = FeatureSpec("height", 3)
        with pytest.raises(ValueError, match="not the same"):
            a.form_contour(b)

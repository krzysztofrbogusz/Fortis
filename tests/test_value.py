"""Tests for src.fortis.models.value — value_from_str and single_value_from_str."""

from __future__ import annotations

import pytest

from src.fortis.imports.features import FeatureInventory
from src.fortis.models.value import single_value_from_str, value_from_str
from tests.conftest import make_feature_inventory


@pytest.fixture
def features() -> FeatureInventory:
    return make_feature_inventory()


# ---------------------------------------------------------------------------
# single_value_from_str
# ---------------------------------------------------------------------------


class TestSingleValueBinary:
    def test_plus(self, features):
        assert single_value_from_str("+", "consonantal", features) == Ok(1)

    def test_one(self, features):
        assert single_value_from_str("1", "consonantal", features) == Ok(1)

    def test_present(self, features):
        assert single_value_from_str("present", "consonantal", features) == Ok(1)

    def test_minus(self, features):
        assert single_value_from_str("-", "consonantal", features) == Ok(0)

    def test_zero(self, features):
        assert single_value_from_str("0", "consonantal", features) == Ok(0)

    def test_absent(self, features):
        assert single_value_from_str("absent", "consonantal", features) == Ok(0)

    def test_invalid(self, features):
        result = single_value_from_str("maybe", "consonantal", features)
        assert result.is_err()


class TestSingleValueUnary:
    def test_plus(self, features):
        assert single_value_from_str("+", "nasal", features) == Ok(1)

    def test_minus_rejected(self, features):
        result = single_value_from_str("-", "nasal", features)
        assert result.is_err()

    def test_invalid(self, features):
        result = single_value_from_str("maybe", "nasal", features)
        assert result.is_err()


class TestSingleValueScalar:
    def test_integer_key(self, features):
        assert single_value_from_str("3", "height", features) == Ok(3)

    def test_label(self, features):
        assert single_value_from_str("high", "height", features) == Ok(3)

    def test_another_label(self, features):
        assert single_value_from_str("low", "height", features) == Ok(1)

    def test_invalid_label(self, features):
        result = single_value_from_str("ultrahigh", "height", features)
        assert result.is_err()


class TestSingleValueUnspecified:
    def test_none_symbol(self, features):
        assert single_value_from_str("none", "consonantal", features) == Ok(None)

    def test_null_symbol(self, features):
        assert single_value_from_str("null", "consonantal", features) == Ok(None)

    def test_unspecified_symbol(self, features):
        assert single_value_from_str("unspecified", "consonantal", features) == Ok(None)

    def test_empty_set_symbol(self, features):
        assert single_value_from_str("∅", "consonantal", features) == Ok(None)


# ---------------------------------------------------------------------------
# value_from_str
# ---------------------------------------------------------------------------


class TestValueFromStr:
    def test_simple_plus(self, features):
        result = value_from_str("+consonantal", "consonantal", features)
        assert result == Ok(1)

    def test_simple_minus(self, features):
        result = value_from_str("-consonantal", "consonantal", features)
        assert result == Ok(0)

    def test_scalar_by_label(self, features):
        result = value_from_str("height:high", "height", features)
        assert result == Ok(3)

    def test_scalar_by_int(self, features):
        result = value_from_str("height:3", "height", features)
        assert result == Ok(3)

    def test_unspecified(self, features):
        result = value_from_str("consonantal:none", "consonantal", features)
        assert result == Ok(None)

    def test_contour(self, features):
        result = value_from_str("tone:1>3", "tone", features)
        assert result == Ok([1, 3])

    def test_three_step_contour(self, features):
        result = value_from_str("tone:1>2>3", "tone", features)
        assert result == Ok([1, 2, 3])

    def test_bare_unary_means_present(self, features):
        result = value_from_str("nasal", "nasal", features, bare_unary_means_present=True)
        assert result == Ok(1)

    def test_bare_binary_is_error(self, features):
        result = value_from_str("consonantal", "consonantal", features, bare_unary_means_present=True)
        assert result.is_err()

    def test_bare_unary_not_present_by_default(self, features):
        result = value_from_str("nasal", "nasal", features, bare_unary_means_present=False)
        assert result.is_err()


# We need Ok for comparison in tests
from src.fortis.result import Ok

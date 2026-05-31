import pytest

from src.fortis.inventories.feature_definition import FeatureDefinition
from src.fortis.inventories.feature_inventory import FeatureInventory
from src.fortis.models.feature_spec import FeatureSpec
from src.fortis.models.feature_type import FeatureType
from src.fortis.models.tiers import Tier


@pytest.fixture
def inventory():
    """A small feature inventory for testing FeatureSpec."""
    return FeatureInventory(
        {
            "consonantal": FeatureDefinition(
                name="consonantal",
                tier=Tier.segment,
                type=FeatureType.binary,
                short="cons",
                values={0: "absent", 1: "present"},
                children=None,
            ),
            "nasal": FeatureDefinition(
                name="nasal",
                tier=Tier.segment,
                type=FeatureType.unary,
                short="nas",
                values={1: "present"},
                children=None,
            ),
            "height": FeatureDefinition(
                name="height",
                tier=Tier.segment,
                type=FeatureType.scalar,
                short="ht",
                values={1: "low", 2: "mid", 3: "high"},
                children=None,
            ),
            "glottal_aperture": FeatureDefinition(
                name="glottal_aperture",
                tier=Tier.segment,
                type=FeatureType.scalar,
                short="ga",
                values={-1: "constricted", 0: "neutral", 1: "spread"},
                children=None,
            ),
        }
    )


# ——————————————————————————————————————————————————————————————————————————————————————
# FeatureSpec: Binary features
# ——————————————————————————————————————————————————————————————————————————————————————


class TestBinaryFeatures:
    def test_plus_prefix(self, inventory):
        result = FeatureSpec.from_string("+consonantal", inventory)
        assert result.is_ok()
        spec = result.unwrap()
        assert spec.feature == "consonantal"
        assert spec.value == 1

    def test_minus_prefix(self, inventory):
        result = FeatureSpec.from_string("-consonantal", inventory)
        assert result.is_ok()
        spec = result.unwrap()
        assert spec.feature == "consonantal"
        assert spec.value == 0

    def test_name_colon_one(self, inventory):
        result = FeatureSpec.from_string("consonantal:1", inventory)
        assert result.is_ok()
        assert result.unwrap().value == 1

    def test_name_colon_zero(self, inventory):
        result = FeatureSpec.from_string("consonantal:0", inventory)
        assert result.is_ok()
        assert result.unwrap().value == 0

    def test_present_keyword(self, inventory):
        result = FeatureSpec.from_string("consonantal:present", inventory)
        assert result.is_ok()
        assert result.unwrap().value == 1

    def test_absent_keyword(self, inventory):
        result = FeatureSpec.from_string("consonantal:absent", inventory)
        assert result.is_ok()
        assert result.unwrap().value == 0

    def test_plus_with_colon(self, inventory):
        result = FeatureSpec.from_string("consonantal:+", inventory)
        assert result.is_ok()
        assert result.unwrap().value == 1

    def test_minus_with_colon(self, inventory):
        result = FeatureSpec.from_string("consonantal:-", inventory)
        assert result.is_ok()
        assert result.unwrap().value == 0


# ——————————————————————————————————————————————————————————————————————————————————————
# FeatureSpec: Unary features
# ——————————————————————————————————————————————————————————————————————————————————————


class TestUnaryFeatures:
    def test_present_via_one(self, inventory):
        result = FeatureSpec.from_string("nasal:1", inventory)
        assert result.is_ok()
        assert result.unwrap().value == 1

    def test_present_via_plus(self, inventory):
        result = FeatureSpec.from_string("+nasal", inventory)
        assert result.is_ok()
        assert result.unwrap().value == 1

    def test_present_via_keyword(self, inventory):
        result = FeatureSpec.from_string("nasal:present", inventory)
        assert result.is_ok()
        assert result.unwrap().value == 1

    def test_absent_value_rejected(self, inventory):
        result = FeatureSpec.from_string("-nasal", inventory)
        assert result.is_err()

    def test_bare_without_flag(self, inventory):
        result = FeatureSpec.from_string("nasal", inventory)
        assert result.is_err()

    def test_bare_with_flag(self, inventory):
        result = FeatureSpec.from_string("nasal", inventory, bare_unary_means_present=True)
        assert result.is_ok()
        assert result.unwrap().value == 1

    def test_bare_binary_ignored_even_with_flag(self, inventory):
        result = FeatureSpec.from_string("consonantal", inventory, bare_unary_means_present=True)
        assert result.is_err()

    def test_unspecified(self, inventory):
        result = FeatureSpec.from_string("nasal:∅", inventory)
        assert result.is_ok()
        assert result.unwrap().value is None


# ——————————————————————————————————————————————————————————————————————————————————————
# FeatureSpec: Scalar features
# ——————————————————————————————————————————————————————————————————————————————————————


class TestScalarFeatures:
    def test_value_by_integer(self, inventory):
        result = FeatureSpec.from_string("height:2", inventory)
        assert result.is_ok()
        assert result.unwrap().value == 2

    def test_value_by_label(self, inventory):
        result = FeatureSpec.from_string("height:low", inventory)
        assert result.is_ok()
        assert result.unwrap().value == 1

    def test_negative_scalar_value(self, inventory):
        result = FeatureSpec.from_string("glottal_aperture:-1", inventory)
        assert result.is_ok()
        assert result.unwrap().value == -1

    def test_negative_scalar_label(self, inventory):
        result = FeatureSpec.from_string("glottal_aperture:constricted", inventory)
        assert result.is_ok()
        assert result.unwrap().value == -1

    def test_zero_scalar(self, inventory):
        result = FeatureSpec.from_string("glottal_aperture:0", inventory)
        assert result.is_ok()
        assert result.unwrap().value == 0

    def test_plus_rejected_for_scalar(self, inventory):
        result = FeatureSpec.from_string("+height", inventory)
        assert result.is_err()

    def test_minus_rejected_for_scalar(self, inventory):
        result = FeatureSpec.from_string("-height", inventory)
        assert result.is_err()

    def test_out_of_range_integer(self, inventory):
        result = FeatureSpec.from_string("height:99", inventory)
        assert result.is_err()

    def test_unknown_label(self, inventory):
        result = FeatureSpec.from_string("height:tall", inventory)
        assert result.is_err()

    def test_unspecified(self, inventory):
        result = FeatureSpec.from_string("height:none", inventory)
        assert result.is_ok()
        assert result.unwrap().value is None


# ——————————————————————————————————————————————————————————————————————————————————————
# FeatureSpec: Short names
# ——————————————————————————————————————————————————————————————————————————————————————


class TestShortNames:
    def test_binary_short(self, inventory):
        result = FeatureSpec.from_string("+cons", inventory)
        assert result.is_ok()
        assert result.unwrap().feature == "consonantal"
        assert result.unwrap().value == 1

    def test_unary_short(self, inventory):
        result = FeatureSpec.from_string("+nas", inventory)
        assert result.is_ok()
        assert result.unwrap().feature == "nasal"
        assert result.unwrap().value == 1

    def test_scalar_short(self, inventory):
        result = FeatureSpec.from_string("ht:2", inventory)
        assert result.is_ok()
        assert result.unwrap().feature == "height"
        assert result.unwrap().value == 2

    def test_scalar_short_label(self, inventory):
        result = FeatureSpec.from_string("ga:spread", inventory)
        assert result.is_ok()
        assert result.unwrap().feature == "glottal_aperture"
        assert result.unwrap().value == 1


# ——————————————————————————————————————————————————————————————————————————————————————
# FeatureSpec: Greedy (longest-first) name matching
# ——————————————————————————————————————————————————————————————————————————————————————


class TestGreedyMatching:
    def test_full_name_preferred_over_short(self, inventory):
        result = FeatureSpec.from_string("+consonantal", inventory)
        assert result.is_ok()
        assert result.unwrap().feature == "consonantal"

    def test_short_name_used_when_full_absent(self, inventory):
        result = FeatureSpec.from_string("+cons", inventory)
        assert result.is_ok()
        assert result.unwrap().feature == "consonantal"

    def test_longer_name_wins(self, inventory):
        result = FeatureSpec.from_string("+glottal_aperture", inventory)
        assert result.is_err()
        assert "value" in result.unwrap_err().lower() or "identify value" in result.unwrap_err().lower()


# ——————————————————————————————————————————————————————————————————————————————————————
# FeatureSpec: Contour values
# ——————————————————————————————————————————————————————————————————————————————————————


class TestContourValues:
    def test_simple_contour(self, inventory):
        result = FeatureSpec.from_string("height:1>2", inventory)
        assert result.is_ok()
        assert result.unwrap().value == [1, 2]

    def test_three_step_contour(self, inventory):
        result = FeatureSpec.from_string("height:1>2>3", inventory)
        assert result.is_ok()
        assert result.unwrap().value == [1, 2, 3]

    def test_contour_with_labels(self, inventory):
        result = FeatureSpec.from_string("height:low>mid>high", inventory)
        assert result.is_ok()
        assert result.unwrap().value == [1, 2, 3]

    def test_contour_with_mixed(self, inventory):
        result = FeatureSpec.from_string("height:1>mid>3", inventory)
        assert result.is_ok()
        assert result.unwrap().value == [1, 2, 3]

    def test_contour_negative_values(self, inventory):
        result = FeatureSpec.from_string("glottal_aperture:-1>0>1", inventory)
        assert result.is_ok()
        assert result.unwrap().value == [-1, 0, 1]

    def test_contour_invalid_step(self, inventory):
        result = FeatureSpec.from_string("height:1>99", inventory)
        assert result.is_err()


# ——————————————————————————————————————————————————————————————————————————————————————
# FeatureSpec: Error cases
# ——————————————————————————————————————————————————————————————————————————————————————


class TestFeatureSpecErrors:
    def test_unknown_feature(self, inventory):
        result = FeatureSpec.from_string("+xyz", inventory)
        assert result.is_err()

    def test_empty_string(self, inventory):
        result = FeatureSpec.from_string("", inventory)
        assert result.is_err()

    def test_bare_binary_without_value(self, inventory):
        result = FeatureSpec.from_string("consonantal", inventory)
        assert result.is_err()

    def test_binary_invalid_value(self, inventory):
        result = FeatureSpec.from_string("consonantal:2", inventory)
        assert result.is_err()


# ——————————————————————————————————————————————————————————————————————————————————————
# FeatureSpec.matches: Single vs Single
# ——————————————————————————————————————————————————————————————————————————————————————


class TestMatchesSingleVsSingle:
    def test_same_binary_value(self):
        assert FeatureSpec("cons", 1).matches(FeatureSpec("cons", 1)) is True

    def test_different_binary_value(self):
        assert FeatureSpec("cons", 1).matches(FeatureSpec("cons", 0)) is False

    def test_same_scalar_value(self):
        assert FeatureSpec("ht", 2).matches(FeatureSpec("ht", 2)) is True

    def test_different_scalar_value(self):
        assert FeatureSpec("ht", 2).matches(FeatureSpec("ht", 1)) is False

    def test_both_none(self):
        assert FeatureSpec("cons", None).matches(FeatureSpec("cons", None)) is True

    def test_pattern_none_target_value(self):
        assert FeatureSpec("cons", None).matches(FeatureSpec("cons", 1)) is False

    def test_pattern_value_target_none(self):
        assert FeatureSpec("cons", 1).matches(FeatureSpec("cons", None)) is False

    def test_pattern_none_ignore_none(self):
        assert FeatureSpec("cons", None).matches(FeatureSpec("cons", 1), ignore_none=True) is True

    def test_target_none_ignore_none(self):
        assert FeatureSpec("cons", 1).matches(FeatureSpec("cons", None), ignore_none=True) is True


# ——————————————————————————————————————————————————————————————————————————————————————
# FeatureSpec.matches: Single vs Contour
# ——————————————————————————————————————————————————————————————————————————————————————


class TestMatchesSingleVsContour:
    def test_any_match(self):
        assert FeatureSpec("ht", 1).matches(FeatureSpec("ht", [0, 1])) is True

    def test_any_miss(self):
        assert FeatureSpec("ht", 1).matches(FeatureSpec("ht", [0, 0])) is False

    def test_initial_match(self):
        assert FeatureSpec("ht", 1).matches(FeatureSpec("ht", [1, 0]), place="initial") is True

    def test_initial_miss(self):
        assert FeatureSpec("ht", 1).matches(FeatureSpec("ht", [0, 1]), place="initial") is False

    def test_final_match(self):
        assert FeatureSpec("ht", 1).matches(FeatureSpec("ht", [0, 1]), place="final") is True

    def test_final_miss(self):
        assert FeatureSpec("ht", 1).matches(FeatureSpec("ht", [1, 0]), place="final") is False

    def test_all_match(self):
        assert FeatureSpec("ht", 1).matches(FeatureSpec("ht", [1, 1, 1]), place="all") is True

    def test_all_miss(self):
        assert FeatureSpec("ht", 1).matches(FeatureSpec("ht", [1, 0, 1]), place="all") is False

    def test_index_match(self):
        assert FeatureSpec("ht", 1).matches(FeatureSpec("ht", [0, 1, 0]), place=1) is True

    def test_index_miss(self):
        assert FeatureSpec("ht", 1).matches(FeatureSpec("ht", [0, 0, 1]), place=1) is False

    def test_index_out_of_bounds(self):
        assert FeatureSpec("ht", 1).matches(FeatureSpec("ht", [0, 1]), place=5) is False

    def test_index_negative_out_of_bounds(self):
        assert FeatureSpec("ht", 1).matches(FeatureSpec("ht", [1, 0]), place=-1) is False

    def test_list_indices_match(self):
        assert FeatureSpec("ht", 1).matches(FeatureSpec("ht", [0, 1, 1]), place=[1, 2]) is True

    def test_list_indices_partial_miss(self):
        assert FeatureSpec("ht", 1).matches(FeatureSpec("ht", [0, 1, 0]), place=[1, 2]) is False

    def test_none_in_contour_any_with_ignore(self):
        assert FeatureSpec("ht", 1).matches(FeatureSpec("ht", [None, 1]), ignore_none=True) is True

    def test_none_in_contour_all_no_ignore(self):
        assert FeatureSpec("ht", 1).matches(FeatureSpec("ht", [1, None]), place="all") is False


# ——————————————————————————————————————————————————————————————————————————————————————
# FeatureSpec.matches: Contour vs Contour
# ——————————————————————————————————————————————————————————————————————————————————————


class TestMatchesContourVsContour:
    def test_identical(self):
        assert FeatureSpec("ht", [1, 2]).matches(FeatureSpec("ht", [1, 2])) is True

    def test_different_any(self):
        assert FeatureSpec("ht", [1, 2]).matches(FeatureSpec("ht", [1, 3]), place="any") is True

    def test_fully_different_any(self):
        assert FeatureSpec("ht", [1, 2]).matches(FeatureSpec("ht", [3, 4]), place="any") is False

    def test_different_length_any_match(self):
        assert FeatureSpec("ht", [1, 2]).matches(FeatureSpec("ht", [1, 2, 3])) is True

    def test_different_length_any_miss(self):
        assert FeatureSpec("ht", [1, 2]).matches(FeatureSpec("ht", [0, 3, 4])) is False

    def test_different_length_all_requires_same_length(self):
        assert FeatureSpec("ht", [1, 2]).matches(FeatureSpec("ht", [1, 2, 3]), place="all") is False

    def test_same_length_all_match(self):
        assert FeatureSpec("ht", [1, 2]).matches(FeatureSpec("ht", [1, 2]), place="all") is True

    def test_same_length_all_mismatch(self):
        assert FeatureSpec("ht", [1, 2]).matches(FeatureSpec("ht", [1, 3]), place="all") is False

    def test_initial_match(self):
        assert FeatureSpec("ht", [1, 2]).matches(FeatureSpec("ht", [1, 3]), place="initial") is True

    def test_initial_miss(self):
        assert FeatureSpec("ht", [1, 2]).matches(FeatureSpec("ht", [0, 2]), place="initial") is False

    def test_final_match(self):
        assert FeatureSpec("ht", [1, 2]).matches(FeatureSpec("ht", [3, 2]), place="final") is True

    def test_final_miss(self):
        assert FeatureSpec("ht", [1, 2]).matches(FeatureSpec("ht", [1, 3]), place="final") is False

    def test_index_match(self):
        assert FeatureSpec("ht", [1, 2, 3]).matches(FeatureSpec("ht", [1, 2, 0]), place=1) is True

    def test_index_miss(self):
        assert FeatureSpec("ht", [1, 2, 3]).matches(FeatureSpec("ht", [1, 0, 3]), place=1) is False

    def test_none_wildcard_ignore(self):
        assert FeatureSpec("ht", [1, None]).matches(FeatureSpec("ht", [1, 2]), ignore_none=True) is True

    def test_none_no_ignore(self):
        assert FeatureSpec("ht", [1, None]).matches(FeatureSpec("ht", [1, 2]), place="all") is False

    def test_both_none_elements(self):
        assert FeatureSpec("ht", [None, 1]).matches(FeatureSpec("ht", [None, 1])) is True


# ——————————————————————————————————————————————————————————————————————————————————————
# FeatureSpec.matches: Contour vs Single
# ——————————————————————————————————————————————————————————————————————————————————————


class TestMatchesContourVsSingle:
    def test_length1_contour_matches(self):
        assert FeatureSpec("ht", [1]).matches(FeatureSpec("ht", 1)) is True

    def test_length1_contour_miss(self):
        assert FeatureSpec("ht", [1]).matches(FeatureSpec("ht", 0)) is False

    def test_length2_contour_vs_single_any(self):
        assert FeatureSpec("ht", [1, 0]).matches(FeatureSpec("ht", 1), place="any") is True

    def test_length2_contour_vs_single_initial(self):
        assert FeatureSpec("ht", [1, 0]).matches(FeatureSpec("ht", 1), place="initial") is True

    def test_length2_contour_vs_single_final(self):
        assert FeatureSpec("ht", [1, 0]).matches(FeatureSpec("ht", 1), place="final") is False

    def test_length2_contour_vs_single_all(self):
        assert FeatureSpec("ht", [1, 1]).matches(FeatureSpec("ht", 1), place="all") is True

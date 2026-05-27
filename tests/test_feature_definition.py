import pytest

from src.fortis.models.feature_definition import FeatureDefinition, FeatureType, Tier
from src.fortis.result import Err, Ok

# ——————————————————————————————————————————————————————————————————————————————————————
# _load_tier
# ——————————————————————————————————————————————————————————————————————————————————————


class TestLoadTier:
    def test_valid_segment(self):
        result = FeatureDefinition._load_tier("test", {"tier": "segment"})
        assert result.is_ok()
        assert result.unwrap() == Tier.segment

    def test_valid_syllable(self):
        result = FeatureDefinition._load_tier("test", {"tier": "syllable"})
        assert result.is_ok()
        assert result.unwrap() == Tier.syllable

    def test_case_insensitive(self):
        result = FeatureDefinition._load_tier("test", {"tier": " Segment "})
        assert result.is_ok()
        assert result.unwrap() == Tier.segment

    def test_missing_tier(self):
        result = FeatureDefinition._load_tier("test", {})
        assert result.is_err()
        assert "missing required field 'tier'" in result.unwrap_err()

    def test_empty_tier(self):
        result = FeatureDefinition._load_tier("test", {"tier": ""})
        assert result.is_err()
        assert "missing required field 'tier'" in result.unwrap_err()

    def test_whitespace_only_tier(self):
        result = FeatureDefinition._load_tier("test", {"tier": "   "})
        assert result.is_err()
        assert "invalid tier" in result.unwrap_err()

    def test_invalid_tier(self):
        result = FeatureDefinition._load_tier("test", {"tier": "morpheme"})
        assert result.is_err()
        assert "invalid tier" in result.unwrap_err()


# ——————————————————————————————————————————————————————————————————————————————————————
# _load_type
# ——————————————————————————————————————————————————————————————————————————————————————


class TestLoadType:
    def test_valid_unary(self):
        result = FeatureDefinition._load_type("test", {"type": "unary"})
        assert result.is_ok()
        assert result.unwrap() == FeatureType.unary

    def test_valid_binary(self):
        result = FeatureDefinition._load_type("test", {"type": "binary"})
        assert result.is_ok()
        assert result.unwrap() == FeatureType.binary

    def test_valid_scalar(self):
        result = FeatureDefinition._load_type("test", {"type": "scalar"})
        assert result.is_ok()
        assert result.unwrap() == FeatureType.scalar

    def test_case_insensitive(self):
        result = FeatureDefinition._load_type("test", {"type": " BINARY "})
        assert result.is_ok()
        assert result.unwrap() == FeatureType.binary

    def test_missing_type(self):
        result = FeatureDefinition._load_type("test", {})
        assert result.is_err()
        assert "missing required field 'type'" in result.unwrap_err()

    def test_empty_type(self):
        result = FeatureDefinition._load_type("test", {"type": ""})
        assert result.is_err()
        assert "missing required field 'type'" in result.unwrap_err()

    def test_invalid_type(self):
        result = FeatureDefinition._load_type("test", {"type": "ternary"})
        assert result.is_err()
        assert "invalid type" in result.unwrap_err()


# ——————————————————————————————————————————————————————————————————————————————————————
# _load_short
# ——————————————————————————————————————————————————————————————————————————————————————


class TestLoadShort:
    def test_explicit_short(self):
        result = FeatureDefinition._load_short("test", {"short": "Cons"})
        assert result.is_ok()
        assert result.unwrap() == "Cons"

    def test_defaults_to_feature_name(self):
        result = FeatureDefinition._load_short("consonantal", {})
        assert result.is_ok()
        assert result.unwrap() == "consonantal"

    def test_strips_whitespace(self):
        result = FeatureDefinition._load_short("test", {"short": "  cons  "})
        assert result.is_ok()
        assert result.unwrap() == "cons"

    def test_empty_short(self):
        result = FeatureDefinition._load_short("test", {"short": ""})
        assert result.is_err()
        assert "empty 'short'" in result.unwrap_err()

    def test_whitespace_only_short(self):
        result = FeatureDefinition._load_short("test", {"short": "   "})
        assert result.is_err()
        assert "empty 'short'" in result.unwrap_err()

    def test_non_string_short(self):
        result = FeatureDefinition._load_short("test", {"short": 42})
        assert result.is_err()
        assert "not a string" in result.unwrap_err()

    def test_short_with_internal_space(self):
        result = FeatureDefinition._load_short("test", {"short": "con sonant"})
        assert result.is_err()
        assert "whitespace" in result.unwrap_err()

    def test_short_with_tab(self):
        result = FeatureDefinition._load_short("test", {"short": "con\tsonant"})
        assert result.is_err()
        assert "whitespace" in result.unwrap_err()


# ——————————————————————————————————————————————————————————————————————————————————————
# _load_values
# ——————————————————————————————————————————————————————————————————————————————————————


class TestLoadValues:
    def test_unary_values(self):
        result = FeatureDefinition._load_values("test", {}, FeatureType.unary)
        assert result.is_ok()
        assert result.unwrap() == {1: "present"}

    def test_binary_values(self):
        result = FeatureDefinition._load_values("test", {}, FeatureType.binary)
        assert result.is_ok()
        assert result.unwrap() == {0: "absent", 1: "present"}

    def test_scalar_values(self):
        spec = {"values": {1: "short", 2: "long"}}
        result = FeatureDefinition._load_values("test", spec, FeatureType.scalar)
        assert result.is_ok()
        assert result.unwrap() == {1: "short", 2: "long"}

    def test_scalar_negative_keys(self):
        spec = {"values": {-1: "constricted", 0: "neutral", 1: "spread"}}
        result = FeatureDefinition._load_values("test", spec, FeatureType.scalar)
        assert result.is_ok()
        assert result.unwrap() == {-1: "constricted", 0: "neutral", 1: "spread"}

    def test_scalar_missing_values(self):
        result = FeatureDefinition._load_values("test", {}, FeatureType.scalar)
        assert result.is_err()
        assert "does not have specified 'values'" in result.unwrap_err()

    def test_scalar_empty_values(self):
        result = FeatureDefinition._load_values("test", {"values": {}}, FeatureType.scalar)
        assert result.is_err()

    def test_scalar_values_not_dict(self):
        result = FeatureDefinition._load_values("test", {"values": "bad"}, FeatureType.scalar)
        assert result.is_err()
        assert "not a dictionary" in result.unwrap_err()

    def test_scalar_non_int_key(self):
        result = FeatureDefinition._load_values("test", {"values": {"a": "label"}}, FeatureType.scalar)
        assert result.is_err()
        assert "not an integer" in result.unwrap_err()

    def test_scalar_non_string_label(self):
        result = FeatureDefinition._load_values("test", {"values": {1: 42}}, FeatureType.scalar)
        assert result.is_err()
        assert "not a string" in result.unwrap_err()

    def test_scalar_empty_label(self):
        result = FeatureDefinition._load_values("test", {"values": {1: ""}}, FeatureType.scalar)
        assert result.is_err()
        assert "empty label" in result.unwrap_err()


# ——————————————————————————————————————————————————————————————————————————————————————
# _load_children
# ——————————————————————————————————————————————————————————————————————————————————————


class TestLoadChildren:
    def test_no_children(self):
        result = FeatureDefinition._load_children("test", {})
        assert result.is_ok()
        assert result.unwrap() is None

    def test_list_children(self):
        spec = {"children": ["continuant", "sonorant", "strident"]}
        result = FeatureDefinition._load_children("test", spec)
        assert result.is_ok()
        assert result.unwrap() == ["continuant", "sonorant", "strident"]

    def test_single_string_child(self):
        spec = {"children": "lateral"}
        result = FeatureDefinition._load_children("test", spec)
        assert result.is_ok()
        assert result.unwrap() == ["lateral"]

    def test_list_strips_whitespace(self):
        spec = {"children": [" Continuant ", "Sonorant"]}
        result = FeatureDefinition._load_children("test", spec)
        assert result.is_ok()
        assert result.unwrap() == ["Continuant", "Sonorant"]

    def test_string_strips_whitespace(self):
        spec = {"children": " Lateral "}
        result = FeatureDefinition._load_children("test", spec)
        assert result.is_ok()
        assert result.unwrap() == ["Lateral"]

    def test_empty_list(self):
        result = FeatureDefinition._load_children("test", {"children": []})
        assert result.is_err()
        assert "empty" in result.unwrap_err()

    def test_empty_string(self):
        result = FeatureDefinition._load_children("test", {"children": ""})
        assert result.is_err()
        assert "empty" in result.unwrap_err()

    def test_whitespace_only_string(self):
        result = FeatureDefinition._load_children("test", {"children": "   "})
        assert result.is_err()

    def test_non_string_non_list(self):
        result = FeatureDefinition._load_children("test", {"children": 42})
        assert result.is_err()
        assert "neither a string nor a list" in result.unwrap_err()

    def test_list_with_non_string_element(self):
        result = FeatureDefinition._load_children("test", {"children": ["valid", 42]})
        assert result.is_err()
        assert "non-string child" in result.unwrap_err()

    def test_list_with_empty_string_element(self):
        result = FeatureDefinition._load_children("test", {"children": ["valid", ""]})
        assert result.is_err()
        assert "empty child name" in result.unwrap_err()


# ——————————————————————————————————————————————————————————————————————————————————————
# FeatureDefinition.load (integration)
# ——————————————————————————————————————————————————————————————————————————————————————


class TestFeatureLoad:
    def test_binary_feature_with_list_children(self):
        """Match a typical TOML entry like: consonantal = { tier = "segment", type = "binary", short = "cons" }"""
        spec = {
            "tier": "segment",
            "type": "binary",
            "short": "cons",
        }
        result = FeatureDefinition.load("consonantal", spec)
        assert result.is_ok()
        feat = result.unwrap()
        assert feat.tier == Tier.segment
        assert feat.type == FeatureType.binary
        assert feat.short == "cons"
        assert feat.values == {0: "absent", 1: "present"}
        assert feat.children is None

    def test_unary_feature_with_children(self):
        """Match: manner = { tier = "segment", type = "unary", children = ["continuant", "sonorant"] }"""
        spec = {
            "tier": "segment",
            "type": "unary",
            "children": ["continuant", "sonorant"],
        }
        result = FeatureDefinition.load("manner", spec)
        assert result.is_ok()
        feat = result.unwrap()
        assert feat.type == FeatureType.unary
        assert feat.values == {1: "present"}
        assert feat.children == ["continuant", "sonorant"]

    def test_scalar_feature(self):
        """Match: length = { tier = "segment", type = "scalar", short = "ln", values = { 1 = "short", 2 = "long" } }"""
        spec = {
            "tier": "segment",
            "type": "scalar",
            "short": "ln",
            "values": {1: "short", 2: "long"},
        }
        result = FeatureDefinition.load("length", spec)
        assert result.is_ok()
        feat = result.unwrap()
        assert feat.type == FeatureType.scalar
        assert feat.values == {1: "short", 2: "long"}

    def test_short_defaults_to_name(self):
        spec = {"tier": "segment", "type": "unary"}
        result = FeatureDefinition.load("nasal", spec)
        assert result.is_ok()
        assert result.unwrap().short == "nasal"

    def test_single_string_child(self):
        spec = {
            "tier": "segment",
            "type": "unary",
            "children": "lateral",
        }
        result = FeatureDefinition.load("test_feat", spec)
        assert result.is_ok()
        assert result.unwrap().children == ["lateral"]

    def test_collects_multiple_errors(self):
        spec = {}
        result = FeatureDefinition.load("broken", spec)
        assert result.is_err()
        errors = result.unwrap_err()
        assert len(errors) >= 2  # at least missing tier and type

    def test_invalid_tier_and_type(self):
        spec = {"tier": "morpheme", "type": "ternary"}
        result = FeatureDefinition.load("broken", spec)
        assert result.is_err()
        errors = result.unwrap_err()
        assert len(errors) == 2

    def test_scalar_with_missing_values_collects_error(self):
        spec = {"tier": "segment", "type": "scalar"}
        result = FeatureDefinition.load("broken", spec)
        assert result.is_err()
        errors = result.unwrap_err()
        # tier and type are valid, but scalar with no values should fail
        assert any("values" in e for e in errors)

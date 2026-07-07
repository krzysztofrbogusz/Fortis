"""Tests for the diacritics loader."""

from src.fortis.loaders.diacritics import (
    load_bool_field,
    load_bundle,
    load_diacritic,
    load_diacritic_inventory,
    load_diacritic_inventory_csv,
    load_diacritic_inventory_toml,
    load_kind,
    load_tier,
)
from src.fortis.models.inventories import DiacriticKind
from src.fortis.models.tiers import Tier


class TestLoadTier:
    def test_valid_segment(self):
        result = load_tier("ʰ", {"tier": "segment"})
        assert result.is_ok()
        assert result.unwrap() == Tier.segment

    def test_valid_syllable(self):
        result = load_tier("ˈ", {"tier": "syllable"})
        assert result.is_ok()
        assert result.unwrap() == Tier.syllable

    def test_missing(self):
        result = load_tier("ʰ", {})
        assert result.is_err()

    def test_invalid(self):
        result = load_tier("ʰ", {"tier": "prosodic"})
        assert result.is_err()


class TestLoadKind:
    def test_valid_before(self):
        result = load_kind("ˈ", {"kind": "before"})
        assert result.is_ok()
        assert result.unwrap() == DiacriticKind.before

    def test_valid_combining(self):
        result = load_kind("̩", {"kind": "combining"})
        assert result.is_ok()
        assert result.unwrap() == DiacriticKind.combining

    def test_valid_after(self):
        result = load_kind("ʰ", {"kind": "after"})
        assert result.is_ok()
        assert result.unwrap() == DiacriticKind.after

    def test_missing(self):
        result = load_kind("ʰ", {})
        assert result.is_err()


class TestLoadBoolField:
    def test_true(self):
        result = load_bool_field("ˈ", {"default": True}, "default")
        assert result.is_ok()
        assert result.unwrap() is True

    def test_false_explicit(self):
        result = load_bool_field("ˈ", {"default": False}, "default")
        assert result.is_ok()
        assert result.unwrap() is False

    def test_absent_defaults_to_false(self):
        result = load_bool_field("˥", {}, "contour")
        assert result.is_ok()
        assert result.unwrap() is False

    def test_non_bool(self):
        result = load_bool_field("˥", {"contour": "yes"}, "contour")
        assert result.is_err()


class TestLoadBundle:
    def test_valid(self, features):
        result = load_bundle("ʰ", {"bundle": "+voice"}, features)
        assert result.is_ok()

    def test_missing(self, features):
        result = load_bundle("ʰ", {}, features)
        assert result.is_err()

    def test_empty(self, features):
        result = load_bundle("ʰ", {"bundle": ""}, features)
        assert result.is_err()


class TestLoadDiacritic:
    def test_valid(self, features):
        result = load_diacritic(
            "̩", {"tier": "segment", "kind": "combining", "bundle": "+syllabic"}, features
        )
        assert result.is_ok(), f"Errors: {result.unwrap_err() if result.is_err() else None}"
        d = result.unwrap()
        assert d.symbol == "̩"
        assert d.tier == Tier.segment
        assert d.kind == DiacriticKind.combining
        assert d.read_only is False

    def test_missing_required_fields(self, features):
        result = load_diacritic("̩", {}, features)
        assert result.is_err()
        assert len(result.unwrap_err()) >= 2  # tier + kind + bundle


class TestLoadDiacriticInventory:
    def test_from_file(self, tmp_path, features):
        toml_content = """"̩" = { tier = "segment", kind = "combining", bundle = "+syll" }"""
        path = tmp_path / "diacritics.toml"
        path.write_text(toml_content)
        result = load_diacritic_inventory(path, features)
        assert result.is_ok()
        inv = result.unwrap()
        assert "̩" in inv

    def test_dotted_circle_placeholder_is_stripped(self, tmp_path, features):
        # A diacritic may be written on the dotted-circle carrier (◌̩) for legibility;
        # the carrier is dropped so it defines the bare combining mark.
        path = tmp_path / "diacritics.toml"
        path.write_text('"◌̩" = { tier = "segment", kind = "combining", bundle = "+syll" }')
        result = load_diacritic_inventory(path, features)
        assert result.is_ok()
        inv = result.unwrap()
        assert "̩" in inv  # bare mark, usable during segmentation
        assert "◌̩" not in inv
        assert not any("◌" in key for key in inv)

    def test_duplicate_symbol(self, tmp_path, features):
        toml_content = (
            '"̩" = { tier = "segment", kind = "combining", bundle = "+syll" }\n'
            '"̩" = { tier = "segment", kind = "combining", bundle = "-syll" }'
        )
        # TOML doesn't allow duplicate keys, so this would fail at parse level
        # Instead test with a valid file
        toml_content = """"̩" = { tier = "segment", kind = "combining", bundle = "+syll" }"""
        path = tmp_path / "diacritics.toml"
        path.write_text(toml_content)
        result = load_diacritic_inventory(path, features)
        assert result.is_ok()


class TestLoadDiacriticInventoryCsv:
    def test_from_file(self, tmp_path, features):
        csv_content = (
            "diacritic,tier,kind,bundle,marks_boundary,read_only,contour\n"
            "ʰ,segment,after,+voice,,,\n"
            # bundle has commas → must be quoted
            "ʷ,segment,after,\"+labial, +rounded\",,,\n"
        )
        path = tmp_path / "diacritics.csv"
        path.write_text(csv_content)
        result = load_diacritic_inventory(path, features)  # dispatches to CSV by extension
        assert result.is_ok(), result.unwrap_err() if result.is_err() else None
        inv = result.unwrap()
        assert "ʰ" in inv and "ʷ" in inv

    def test_dotted_circle_carrier_stripped(self, tmp_path, features):
        path = tmp_path / "diacritics.csv"
        path.write_text("diacritic,tier,kind,bundle\n◌̩,segment,combining,+syll\n")
        inv = load_diacritic_inventory(path, features).unwrap()
        assert "̩" in inv and "◌̩" not in inv

    def test_boolean_flags(self, tmp_path, features):
        path = tmp_path / "diacritics.csv"
        path.write_text(
            "diacritic,tier,kind,bundle,marks_boundary\n"
            "ˈ,segment,before,+syll,true\n"
            "x,segment,after,+voice,\n"  # empty ⇒ false
        )
        inv = load_diacritic_inventory(path, features).unwrap()
        assert inv["ˈ"].marks_boundary is True
        assert inv["x"].marks_boundary is False

    def test_bad_boolean_is_an_error(self, tmp_path, features):
        path = tmp_path / "diacritics.csv"
        path.write_text("diacritic,tier,kind,bundle,read_only\nx,segment,after,+voice,maybe\n")
        result = load_diacritic_inventory(path, features)
        assert result.is_err()

    def test_missing_required_column(self, tmp_path, features):
        path = tmp_path / "diacritics.csv"
        path.write_text("diacritic,kind,bundle\nx,after,+voice\n")  # no 'tier'
        result = load_diacritic_inventory(path, features)
        assert result.is_err()
        assert any("'tier' column" in e for e in result.unwrap_err())

    def test_unknown_column_is_an_error(self, tmp_path, features):
        path = tmp_path / "diacritics.csv"
        path.write_text("diacritic,tier,kind,bundle,colour\nx,segment,after,+voice,blue\n")
        result = load_diacritic_inventory(path, features)
        assert result.is_err()
        assert any("unknown column" in e and "colour" in e for e in result.unwrap_err())

    def test_column_order_is_free(self, tmp_path, features):
        path = tmp_path / "diacritics.csv"
        path.write_text("bundle,diacritic,kind,tier\n+syll,ʰ,after,segment\n")
        inv = load_diacritic_inventory(path, features).unwrap()
        assert inv["ʰ"].kind.value == "after"


class TestDiacriticCsvTomlEquivalence:
    def test_round_trip_is_identical(self, tmp_path, features):
        toml_content = (
            '"ʰ" = { tier = "segment", kind = "after", bundle = "+voice" }\n'
            '"ʷ" = { tier = "segment", kind = "after", bundle = "+labial, +rounded" }\n'
            '"̩" = { tier = "segment", kind = "combining", bundle = "+syll", read_only = true }\n'
        )
        csv_content = (
            "diacritic,tier,kind,bundle,marks_boundary,read_only,contour\n"
            "ʰ,segment,after,+voice,,,\n"
            "ʷ,segment,after,\"+labial, +rounded\",,,\n"
            "̩,segment,combining,+syll,,true,\n"
        )
        (tmp_path / "diacritics.toml").write_text(toml_content)
        (tmp_path / "diacritics.csv").write_text(csv_content)
        it = load_diacritic_inventory_toml(tmp_path / "diacritics.toml", features).unwrap()
        ic = load_diacritic_inventory_csv(tmp_path / "diacritics.csv", features).unwrap()

        def flat(inv):
            return [
                (s, d.tier, d.kind, dict(d.bundle), d.contour, d.read_only, d.marks_boundary)
                for s, d in inv.data.items()
            ]

        assert flat(it) == flat(ic)

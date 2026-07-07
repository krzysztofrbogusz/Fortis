"""Tests for the sonorities loader."""

from src.fortis.loaders.sonorities import (
    load_bundle,
    load_level,
    load_sonorities_inventory,
    load_sonorities_inventory_csv,
    load_sonorities_inventory_toml,
    load_sonority,
)


class TestLoadLevel:
    def test_valid(self):
        result = load_level("vowel", {"level": 7})
        assert result.is_ok()
        assert result.unwrap() == 7

    def test_missing(self):
        result = load_level("vowel", {})
        assert result.is_err()

    def test_zero(self):
        result = load_level("vowel", {"level": 0})
        assert result.is_err()

    def test_negative(self):
        result = load_level("vowel", {"level": -1})
        assert result.is_err()

    def test_non_integer(self):
        result = load_level("vowel", {"level": "high"})
        assert result.is_err()


class TestLoadBundle:
    def test_valid(self, features):
        result = load_bundle("vowel", {"bundle": "syllabic: +, consonantal: -"}, features)
        assert result.is_ok()
        assert result.unwrap() is not None

    def test_empty_string_returns_none(self, features):
        result = load_bundle("vowel", {"bundle": ""}, features)
        assert result.is_ok()
        assert result.unwrap() is None

    def test_missing(self, features):
        result = load_bundle("vowel", {}, features)
        assert result.is_err()


class TestLoadSonority:
    def test_valid(self, features):
        result = load_sonority(
            "vowel", {"level": 7, "bundle": "syllabic: +, consonantal: -"}, features
        )
        assert result.is_ok()
        s = result.unwrap()
        assert s.label == "vowel"
        assert s.level == 7
        assert s.bundle is not None

    def test_missing_level(self, features):
        result = load_sonority("vowel", {"bundle": "syllabic: +"}, features)
        assert result.is_err()


class TestLoadSonoritiesInventory:
    def test_from_file(self, tmp_path, features):
        toml_content = (
            'vowel = { level = 7, bundle = "syllabic: +, consonantal: -" }\n'
            'stop = { level = 1, bundle = "sonorant: -" }\n'
        )
        path = tmp_path / "sonorities.toml"
        path.write_text(toml_content)
        result = load_sonorities_inventory(path, features)
        assert result.is_ok()
        inv = result.unwrap()
        assert "vowel" in inv
        assert inv["vowel"].level == 7

    def test_duplicate_levels(self, tmp_path, features):
        toml_content = (
            'vowel = { level = 7, bundle = "syllabic: +" }\n'
            'glide = { level = 7, bundle = "consonantal: -" }\n'
        )
        path = tmp_path / "sonorities.toml"
        path.write_text(toml_content)
        result = load_sonorities_inventory(path, features)
        assert result.is_err()


class TestLoadSonoritiesInventoryCsv:
    def test_from_file_preserves_order(self, tmp_path, features):
        # Row order is first-match order — vowel outranks the rest.
        csv_content = (
            "name,level,bundle\n"
            "vowel,7,\"syllabic: +, consonantal: -\"\n"
            "nasal,3,\"sonorant: +, nasal: +\"\n"
            "stop,1,sonorant: -\n"
        )
        path = tmp_path / "sonorities.csv"
        path.write_text(csv_content)
        result = load_sonorities_inventory(path, features)  # dispatches to CSV by extension
        assert result.is_ok(), result.unwrap_err() if result.is_err() else None
        inv = result.unwrap()
        assert list(inv.data.keys()) == ["vowel", "nasal", "stop"]
        assert inv["vowel"].level == 7

    def test_empty_bundle_is_catch_all(self, tmp_path, features):
        path = tmp_path / "sonorities.csv"
        path.write_text("name,level,bundle\nother,1,\n")
        inv = load_sonorities_inventory(path, features).unwrap()
        assert inv["other"].bundle is None

    def test_duplicate_level_is_an_error(self, tmp_path, features):
        path = tmp_path / "sonorities.csv"
        path.write_text("name,level,bundle\na,1,sonorant: -\nb,1,sonorant: +\n")
        result = load_sonorities_inventory(path, features)
        assert result.is_err()

    def test_bad_level_is_an_error(self, tmp_path, features):
        path = tmp_path / "sonorities.csv"
        path.write_text("name,level,bundle\na,high,sonorant: -\n")
        result = load_sonorities_inventory(path, features)
        assert result.is_err()

    def test_missing_required_column(self, tmp_path, features):
        path = tmp_path / "sonorities.csv"
        path.write_text("name,bundle\na,sonorant: -\n")  # no 'level'
        result = load_sonorities_inventory(path, features)
        assert result.is_err()
        assert any("'level' column" in e for e in result.unwrap_err())

    def test_unknown_column_is_an_error(self, tmp_path, features):
        path = tmp_path / "sonorities.csv"
        path.write_text("name,level,bundle,colour\na,1,sonorant: -,blue\n")
        result = load_sonorities_inventory(path, features)
        assert result.is_err()
        assert any("unknown column" in e and "colour" in e for e in result.unwrap_err())


class TestSonorityCsvTomlEquivalence:
    def test_round_trip_is_identical(self, tmp_path, features):
        toml_content = (
            'vowel = { level = 7, bundle = "syllabic: +, consonantal: -" }\n'
            'nasal = { level = 3, bundle = "sonorant: +, nasal: +" }\n'
            'stop = { level = 1, bundle = "sonorant: -" }\n'
        )
        csv_content = (
            "name,level,bundle\n"
            "vowel,7,\"syllabic: +, consonantal: -\"\n"
            "nasal,3,\"sonorant: +, nasal: +\"\n"
            "stop,1,sonorant: -\n"
        )
        (tmp_path / "sonorities.toml").write_text(toml_content)
        (tmp_path / "sonorities.csv").write_text(csv_content)
        it = load_sonorities_inventory_toml(tmp_path / "sonorities.toml", features).unwrap()
        ic = load_sonorities_inventory_csv(tmp_path / "sonorities.csv", features).unwrap()

        def flat(inv):
            return [
                (s, x.level, (dict(x.bundle) if x.bundle else None))
                for s, x in inv.data.items()
            ]

        assert flat(it) == flat(ic)

"""Tests for the words loader."""

from src.fortis.loaders.words import load_word_inventory


class TestLoadWordInventory:
    def test_valid(self, tmp_path):
        toml_content = '"xenti" = "in front"\n"mexteːr" = "mother"\n'
        path = tmp_path / "words.toml"
        path.write_text(toml_content)
        result = load_word_inventory(path)
        assert result.is_ok()
        inv = result.unwrap()
        assert "xenti" in inv
        assert inv["xenti"].gloss == "in front"
        assert inv["mexteːr"].gloss == "mother"

    def test_empty_gloss(self, tmp_path):
        toml_content = '"test" = ""\n'
        path = tmp_path / "words.toml"
        path.write_text(toml_content)
        result = load_word_inventory(path)
        assert result.is_ok()
        inv = result.unwrap()
        assert inv["test"].gloss == ""

    def test_missing_file(self, tmp_path):
        path = tmp_path / "nonexistent.toml"
        result = load_word_inventory(path)
        assert result.is_err()

    def test_wrong_extension(self, tmp_path):
        path = tmp_path / "words.json"
        path.write_text("{}")
        result = load_word_inventory(path)
        assert result.is_err()


class TestWordTableForm:
    """The richer table form: gloss/final + integer-keyed stage forms."""

    def _load(self, tmp_path, content):
        path = tmp_path / "words.toml"
        path.write_text(content, encoding="utf-8")
        return load_word_inventory(path)

    def test_full_table(self, tmp_path):
        content = (
            '"ˈɑmɑt̪" = {gloss = "aime – loves", final = "ɛm", '
            '100 = "ˈɑ.mɑt̪", 300 = " ˈɑ.mɑt̪", 600 = "ˈãj̃.məθ", '
            '1000 = "ˈɛ̃j̃.mə", 1400 = "ˈɛ̃.mə", 1700 = "ɛm"}\n'
        )
        result = self._load(tmp_path, content)
        assert result.is_ok(), result.unwrap_err() if result.is_err() else None
        w = result.unwrap()["ˈɑmɑt̪"]
        assert w.ipa == "ˈɑmɑt̪"
        assert w.gloss == "aime – loves"
        assert w.final == "ɛm"
        assert w.stages == {
            100: "ˈɑ.mɑt̪",
            300: "ˈɑ.mɑt̪",  # leading space stripped
            600: "ˈãj̃.məθ",
            1000: "ˈɛ̃j̃.mə",
            1400: "ˈɛ̃.mə",
            1700: "ɛm",
        }

    def test_frequency_default_is_one(self, tmp_path):
        inv = self._load(tmp_path, '"ka" = {gloss = "x", final = "ka"}\n').unwrap()
        assert inv["ka"].frequency == 1

    def test_frequency_parsed(self, tmp_path):
        inv = self._load(tmp_path, '"ka" = {gloss = "x", final = "ka", frequency = 240}\n').unwrap()
        assert inv["ka"].frequency == 240

    def test_frequency_bool_rejected(self, tmp_path):
        # bool is an int subclass — `true` must not become 1.
        err = self._load(tmp_path, '"ka" = {gloss = "x", frequency = true}\n').unwrap_err()
        assert any("frequency" in e for e in err)

    def test_frequency_non_positive_rejected(self, tmp_path):
        err = self._load(tmp_path, '"ka" = {gloss = "x", frequency = 0}\n').unwrap_err()
        assert any("frequency" in e for e in err)

    def test_frequency_non_integer_rejected(self, tmp_path):
        err = self._load(tmp_path, '"ka" = {gloss = "x", frequency = 1.5}\n').unwrap_err()
        assert any("frequency" in e for e in err)

    def test_both_forms_coexist(self, tmp_path):
        # The explicit requirement: the plain string form and the table form
        # must both work in one inventory.
        content = (
            '"ˌɑbˈɑnte" = "avant"\n'
            '"ˈɑmɑt̪" = {gloss = "aime", final = "ɛm", 600 = "ˈãj̃.məθ"}\n'
        )
        result = self._load(tmp_path, content)
        assert result.is_ok()
        inv = result.unwrap()
        assert inv["ˌɑbˈɑnte"].gloss == "avant"
        assert inv["ˌɑbˈɑnte"].final is None
        assert inv["ˌɑbˈɑnte"].stages == {}
        assert inv["ˈɑmɑt̪"].final == "ɛm"
        assert inv["ˈɑmɑt̪"].stages == {600: "ˈãj̃.məθ"}

    def test_table_optional_fields(self, tmp_path):
        # gloss/final both optional; a table with only stages is valid.
        result = self._load(tmp_path, '"a" = {500 = "b"}\n')
        assert result.is_ok()
        w = result.unwrap()["a"]
        assert w.gloss == ""
        assert w.final is None
        assert w.stages == {500: "b"}

    def test_negative_stage_time_allowed(self, tmp_path):
        # -100 is a real rule time; stage times aren't constrained to boundaries.
        result = self._load(tmp_path, '"a" = {gloss = "x", -100 = "y"}\n')
        assert result.is_ok()
        assert result.unwrap()["a"].stages == {-100: "y"}

    def test_non_integer_stage_key_errors(self, tmp_path):
        result = self._load(tmp_path, '"a" = {gloss = "x", latin = "y"}\n')
        assert result.is_err()
        assert any("latin" in e for e in result.unwrap_err())

    def test_non_string_stage_form_errors(self, tmp_path):
        result = self._load(tmp_path, '"a" = {100 = 42}\n')
        assert result.is_err()

    def test_non_string_final_errors(self, tmp_path):
        result = self._load(tmp_path, '"a" = {final = 42}\n')
        assert result.is_err()

    def test_non_string_non_table_value_errors(self, tmp_path):
        result = self._load(tmp_path, '"a" = 42\n')
        assert result.is_err()
        assert any("gloss string or a table" in e for e in result.unwrap_err())


class TestLoadWordInventoryCsv:
    """The CSV lexicon form: same schema as TOML, dispatched by the .csv extension."""

    def _load(self, tmp_path, content):
        path = tmp_path / "words.csv"
        path.write_text(content, encoding="utf-8")
        return load_word_inventory(path)

    def test_dispatches_and_loads(self, tmp_path):
        inv = self._load(
            tmp_path,
            "word,gloss,final,-100,750\n"
            "avɑ̃te,avant,avɑ̃,,\n"
            "amat,aime,ɛm,ˈɑmɑt,ˈɛmə\n",
        ).unwrap()
        assert set(inv) == {"avɑ̃te", "amat"}
        assert inv["avɑ̃te"].gloss == "avant" and inv["avɑ̃te"].final == "avɑ̃"
        assert inv["avɑ̃te"].stages == {}  # empty cells → no stage
        assert inv["amat"].stages == {-100: "ˈɑmɑt", 750: "ˈɛmə"}

    def test_empty_final_is_none(self, tmp_path):
        inv = self._load(tmp_path, "word,gloss,final\nx,thing,\n").unwrap()
        assert inv["x"].final is None

    def test_quoted_comma_gloss(self, tmp_path):
        # A gloss with a comma must be read as one field (csv quoting), not split.
        inv = self._load(tmp_path, 'word,gloss,final\nx,"amère (bitter, f.)",amɛʁ\n').unwrap()
        assert inv["x"].gloss == "amère (bitter, f.)"

    def test_frequency_column(self, tmp_path):
        inv = self._load(tmp_path, "word,gloss,frequency\nx,thing,42\ny,other,\n").unwrap()
        assert inv["x"].frequency == 42
        assert inv["y"].frequency == 1  # blank → default

    def test_missing_word_column_errors(self, tmp_path):
        err = self._load(tmp_path, "gloss,final\navant,avɑ̃\n").unwrap_err()
        assert any("must have a 'word' column" in e for e in err)

    def test_unknown_column_errors(self, tmp_path):
        err = self._load(tmp_path, "word,gloss,notes\nx,thing,hi\n").unwrap_err()
        assert any("neither" in e and "notes" in e for e in err)

    def test_duplicate_word_errors(self, tmp_path):
        err = self._load(tmp_path, "word,gloss\nx,a\nx,b\n").unwrap_err()
        assert any("already defined" in e for e in err)

    def test_bad_frequency_errors(self, tmp_path):
        err = self._load(tmp_path, "word,gloss,frequency\nx,a,-3\n").unwrap_err()
        assert any("positive integer" in e for e in err)


class TestCsvTomlEquivalence:
    """A TOML and a CSV encoding the same lexicon load to the same inventory."""

    def test_same_inventory(self, tmp_path):
        from src.fortis.loaders.words import load_word_inventory_csv, load_word_inventory_toml

        toml = tmp_path / "w.toml"
        toml.write_text(
            '"amat" = {gloss = "aime", final = "ɛm", -100 = "ˈɑmɑt", 750 = "ˈɛmə", frequency = 3}\n'
            '"o" = {gloss = "eau", final = "o"}\n',
            encoding="utf-8",
        )
        csvp = tmp_path / "w.csv"
        csvp.write_text(
            "word,gloss,final,-100,750,frequency\n"
            "amat,aime,ɛm,ˈɑmɑt,ˈɛmə,3\n"
            "o,eau,o,,,\n",
            encoding="utf-8",
        )
        ti = load_word_inventory_toml(toml).unwrap()
        ci = load_word_inventory_csv(csvp).unwrap()
        assert set(ti) == set(ci)
        for k in ti:
            a, b = ti[k], ci[k]
            assert (a.gloss, a.final, a.stages, a.frequency) == (
                b.gloss, b.final, b.stages, b.frequency
            )

"""Tests for the induction CLI (src/fortis/induction/main.py)."""

from src.fortis.induction import main as cli
from src.fortis.loaders.rules import load_rule_inventory

from .conftest import SYNTH_DIR


class TestParseInterval:
    def test_stage_times(self):
        assert cli._parse_interval("-100:750") == (-100, 750)

    def test_input_and_final_keywords(self):
        assert cli._parse_interval("input:-200") == (None, -200)
        assert cli._parse_interval("1400:final") == (1400, None)


class TestRun:
    def test_writes_loadable_rules_and_report(self, tmp_path, synth):
        # A capped single-interval run must write an induced_rules.toml that itself reloads,
        # plus the induction.md report — the CLI's end-to-end contract.
        out = tmp_path / "induced_rules.toml"
        report = tmp_path / "induction.md"
        cli.main([
            "--project", str(SYNTH_DIR),
            "--interval", "750:1000", "--max-rules", "2",
            "--out", str(out), "--report", str(report), "--serial",
        ])
        assert out.is_file() and report.is_file()
        assert load_rule_inventory(out, synth.features).is_ok()  # reloads cleanly
        assert "# Induction" in report.read_text(encoding="utf-8")

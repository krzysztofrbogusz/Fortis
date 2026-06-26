"""Tests for tier-autosegment spread (the applier links one autosegment to many anchors)."""

from src.fortis.application.deriving import derive
from src.fortis.application.tiers import associate_tiers, lower_tiers
from src.fortis.models.bundles import FeatureBundle
from src.fortis.models.form import Form
from src.fortis.models.inventories import Word
from src.fortis.models.rules import Rule, RuleInventory
from src.fortis.models.specs import FeatureSpec
from src.fortis.parsing.notation import parse_definition


def _fb(**features):
    return FeatureBundle({f: FeatureSpec(feature=f, value=v) for f, v in features.items()})


def _rule(definition, features):
    sd = parse_definition(definition, features).unwrap()
    return Rule(id="r", time=0, raw_definition=definition, sd=sd)


def _derive(form, rule, project):
    return derive(
        Word(ipa="x"),
        form,
        RuleInventory({0: (rule,)}),
        project.letters,
        project.features,
        tiers=project.tiers,
    ).surface


def test_high_tone_spreads_as_one_autoseg(project):
    # a(H) a(toneless) → both high, sharing ONE autosegment (spread, not a copy).
    form = associate_tiers(
        Form.from_bundles([_fb(syllabic=1, tone=4), _fb(syllabic=1)]), project.tiers
    )
    rule = _rule(
        "[+syllabic, tone: ~1=high] [+syllabic, tone: none] "
        "-> [+syllabic, tone: ~1] [+syllabic, tone: ~1]",
        project.features,
    )
    surface = _derive(form, rule, project)
    tier = surface.tiers["tone"]
    assert len(tier.autosegs) == 1  # one H autosegment...
    assert tier.links == {(tier.autosegs[0].id, 0), (tier.autosegs[0].id, 1)}  # ...on both anchors
    assert [b["tone"].value for b in lower_tiers(surface)] == [4, 4]  # both read high


def test_unbound_recall_is_a_no_op(project):
    # Nothing binds ~1 — the recall must be a quiet no-op, not a crash or a phantom tone.
    form = associate_tiers(Form.from_bundles([_fb(syllabic=1)]), project.tiers)
    rule = _rule("[+syllabic, tone: none] -> [+syllabic, tone: ~1]", project.features)
    surface = _derive(form, rule, project)
    assert not surface.tiers["tone"].links

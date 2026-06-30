"""Tests for Bindings model."""

from src.fortis.models.bindings import Bindings
from src.fortis.models.bundles import FeatureBundle
from src.fortis.models.specs import FeatureSpec


class TestBindings:
    def test_default_empty(self):
        b = Bindings()
        assert b.alpha == {}
        assert b.reference == {}

    def test_with_alpha(self):
        b = Bindings(alpha={"α": 1})
        assert b.alpha["α"] == 1

    def test_with_reference(self):
        voice = FeatureSpec(feature="voice", value=1)
        bundle = FeatureBundle(voice=voice)
        b = Bindings(reference={0: (bundle,)})
        assert b.reference[0][0]["voice"].value == 1

    def test_mutation(self):
        b = Bindings()
        b.alpha["α"] = 1
        nasal = FeatureSpec(feature="nasal", value=0)
        b.reference[0] = (FeatureBundle(nasal=nasal),)
        assert b.alpha["α"] == 1
        assert b.reference[0][0]["nasal"].value == 0


def test_copy_isolates_every_mutable_field():
    """copy() must duplicate every mutable container, or a branch's edits leak to its siblings.

    The bug node_reference once had. Field-agnostic: a new mutable field added without copying
    it fails here.
    """
    import dataclasses

    original = Bindings(
        alpha={"α": 1},
        reference={0: (FeatureBundle(),)},
        autoseg_reference={0: 0},
        floating_reference={0: 0},
        node_reference={0: FeatureBundle()},
        conditions={0: True},
        pending_other=[("α", 1)],
        disjunction_choices=(0,),
        permissive_alpha=True,
    )
    clone = original.copy()
    assert clone == original  # same contents
    for f in dataclasses.fields(Bindings):
        value = getattr(original, f.name)
        if isinstance(value, dict | list | set):  # a mutable container must be a distinct object
            assert getattr(clone, f.name) is not value, f"copy() shares mutable field '{f.name}'"

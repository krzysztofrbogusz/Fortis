from __future__ import annotations

from src.fortis.models.specs import FeatureSpec, PatternSpec, ResultSpec


class _SpecDict(dict):
    """A ``dict`` with a ``UserDict``-compatible ``data`` view (the bundles' base).

    The bundle classes started as ``UserDict``s, but the matcher reads bundles
    millions of times per run and ``UserDict``'s Python-level ``__getitem__`` /
    ``__contains__`` dominated its profile. Subclassing ``dict`` keeps every read
    on the C fast path; ``data`` remains as a property so existing ``bundle.data``
    readers keep working unchanged.
    """

    @property
    def data(self) -> dict:
        return self

    def copy(self) -> _SpecDict:
        return type(self)(self)


class FeatureBundle(_SpecDict, dict[str, FeatureSpec]):
    """A collection of realized feature specifications, keyed by feature name.

    Used for concrete phonological material — segments in the lexicon,
    diacritics, letters, etc.
    """


class PatternBundle(_SpecDict, dict[str, PatternSpec]):
    """A collection of pattern feature specifications, keyed by feature name.

    Used in rule target, context, and exception positions.
    """


class ResultBundle(_SpecDict, dict[str, ResultSpec]):
    """A collection of result feature specifications, keyed by feature name.

    Used in rule result position.
    """


# A morpheme boundary (the ``-`` token) is a real, deletable segment on the segmental tier,
# not a phonological one. It is marked by this reserved key — deliberately un-typeable as a
# real feature name (a feature name may not contain control characters), so no inventory ever
# declares it, no pattern references it, and it never matches phonological material. Only a
# ``-`` rule element matches it, and the syllabifier reads it to force a syllable break. The
# key rides along through ``combine``/tier-lowering (a plain ``{**bundle}`` copy) so a boundary
# stays recognisable after those transforms.
MORPHEME_BOUNDARY = "\x00morpheme-boundary"


def morpheme_boundary_bundle() -> FeatureBundle:
    """A fresh bundle marking one morpheme-boundary segment."""
    return FeatureBundle({MORPHEME_BOUNDARY: FeatureSpec(feature=MORPHEME_BOUNDARY, value=1)})


def is_morpheme_boundary(bundle: FeatureBundle) -> bool:
    """Whether *bundle* is a morpheme-boundary marker rather than a phonological segment."""
    return MORPHEME_BOUNDARY in bundle

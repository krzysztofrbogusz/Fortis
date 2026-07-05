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

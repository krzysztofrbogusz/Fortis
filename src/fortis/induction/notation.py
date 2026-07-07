"""Render feature material back to Fortis notation — the inverse of the bundle parser.

The candidate generator (:mod:`src.fortis.induction.candidates`) builds rules as
notation *strings* and hands each to ``load_rule``, so the parser stays the single source of
truth for what is a legal rule. This module renders the one thing a string builder cannot
spell from a raw phone: a feature bundle (``[+nasal]``, ``[aperture: high]``) for a
context predictor or a natural-class target. It covers exactly the realized subset the
proposer emits — a single concrete value per feature — and is property-tested by round-trip
through ``parse_pattern_bundle`` (:mod:`tests`).

A value the notation cannot spell as one concrete token (a contour, an alpha reference, an
``any``) renders to ``None``; the proposer simply drops that predictor rather than emit an
unparseable rule.
"""
from __future__ import annotations

from collections.abc import Iterable

from src.fortis.models.bundles import FeatureBundle
from src.fortis.models.features import FeatureInventory


def render_feature(feature: str, value: object, features: FeatureInventory) -> str | None:
    """Render one feature/value pair as a notation spec token, or ``None`` if unrenderable.

    - unary present ``→`` the bare feature name (``nasal``),
    - binary ``→`` a signed name (``+voice`` / ``-voice``),
    - scalar ``→`` a colon-introduced label (``aperture: high``),

    matching what ``parse_pattern_spec`` accepts. A non-integer value (contour, alpha,
    ``any``, unspecified) has no single-token spelling and returns ``None``.
    """
    if feature not in features or not isinstance(value, int) or isinstance(value, bool):
        return None
    kind = features[feature].kind
    if kind == "unary":
        return feature if value == 1 else None
    if kind == "binary":
        return f"+{feature}" if value == 1 else f"-{feature}"
    if kind == "scalar":
        label = features[feature].values.get(value)
        return f"{feature}: {label}" if label is not None else None
    return None


def render_feature_element(feature: str, value: object, features: FeatureInventory) -> str | None:
    """Render one feature/value pair as a bracketed single-feature element (``[+nasal]``)."""
    token = render_feature(feature, value, features)
    return f"[{token}]" if token is not None else None


def render_feature_map(
    pairs: Iterable[tuple[str, object]], features: FeatureInventory
) -> str | None:
    """Render ``{feature: value}`` pairs as a bracketed bundle element (``[+cons, -voice]``).

    Returns ``None`` if no pair renders, so the caller never emits an empty ``[]`` (which the
    parser reads as a wildcard, not a bundle). The shared core of :func:`render_bundle` and the
    class-target proposer, which works from feature/value maps rather than spec bundles.
    """
    tokens = [
        token
        for feature, value in pairs
        if (token := render_feature(feature, value, features)) is not None
    ]
    return f"[{', '.join(tokens)}]" if tokens else None


def render_bundle(bundle: FeatureBundle, features: FeatureInventory) -> str | None:
    """Render a realized feature bundle as a bracketed pattern element (``[+cons, -voice]``)."""
    return render_feature_map(
        ((feature, spec.value) for feature, spec in bundle.items()), features
    )

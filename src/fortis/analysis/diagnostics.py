"""Diagnostics: what an authored bundle denotes against the project's own inventory.

These are statements about the feature *system*, independent of any derivation — the
consumer-layer tools behind the web app's Diagnostics pane (and a future ``--lint`` CLI).

The match-set query answers the question that trips up every hand-authored feature system:
*which segments does this bundle actually pick out?* It matches the bundle with the engine's
own matcher (:func:`pattern_matches`), so the answer is the engine's denotation — the surprise
that ``[+front]`` also catches every coronal is visible rather than latent.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.fortis.application.matching import _has_alpha, pattern_matches
from src.fortis.models.project import Project
from src.fortis.models.specs import PatternSpec
from src.fortis.models.values import AutosegBind, AutosegRecall
from src.fortis.parsing.bundles import parse_pattern_bundle
from src.fortis.result import Err, Ok, Result


@dataclass(frozen=True)
class MatchSet:
    """The segments a feature bundle matches, in inventory order, plus the inventory size."""

    matched: list[str]
    total: int


def _needs_rule_context(spec: PatternSpec) -> bool:
    """Whether *spec* is meaningless in a standalone query.

    A conditional (``<n: F>``), an agreement variable (``αF``), or a reference (``F: ~n``) each
    needs a rule's binding environment. With none, they don't error — they silently match
    all-or-nothing (an unbound α holds everywhere, a conditional never filters, a recall binds
    nothing), which misleads more than a clear rejection.
    """
    return (
        spec.condition_label is not None
        or _has_alpha(spec.value)
        or isinstance(spec.value, AutosegBind | AutosegRecall)
    )


def match_set(raw_bundle: str, project: Project) -> Result[MatchSet, str]:
    """The inventory segments a feature bundle matches — the engine's own denotation of it.

    Parses *raw_bundle* as a pattern bundle (brackets optional) and tests it against every
    letter in *project*. Returns an error string for empty input, a parse failure, or a spec
    that needs a rule context — each surfaced to the author verbatim.
    """
    raw = (raw_bundle or "").strip()
    if raw.startswith("[") and raw.endswith("]"):
        raw = raw[1:-1].strip()
    if not raw:
        return Err("Enter a feature bundle, e.g. +front, +sonorant, -syllabic")
    match parse_pattern_bundle(raw, project.features):
        case Err(error):
            return Err("; ".join(error) if isinstance(error, list) else error)
        case Ok(pattern):
            offenders = [f for f, spec in pattern.items() if _needs_rule_context(spec)]
            if offenders:
                return Err(
                    "References (~n), agreement variables (α), and conditionals (<n: …>) only "
                    f"mean something inside a rule — remove: {', '.join(offenders)}"
                )
            matched = [
                symbol
                for symbol, letter in project.letters.items()
                if pattern_matches(pattern, letter.bundle, None)
            ]
            return Ok(MatchSet(matched=matched, total=len(project.letters)))

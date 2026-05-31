"""Element types for phonological rule patterns.

Each position in a rule (target, result, context, exception) is expressed as a
list of Elements.  The element hierarchy supports the full Fortis rule notation;
individual element types are parsed and matched incrementally as implementation
progresses.
"""

from dataclasses import dataclass, field
from enum import StrEnum, auto
from typing import Literal

from src.fortis.models.feature_bundle import FeatureBundle


class Application(StrEnum):
    """How a rule's matches are applied within a single pass.

    - ``simultaneous``: find every locus against the original input, apply all
      changes at once.  No application sees another's output.
    - ``left-to-right``: scan from left to right, apply at each locus, resume
      just past the rewritten target.  Changed segments are visible as context
      for later applications in the same pass.
    - ``right-to-left``: mirror of ``left-to-right`` — scan from right to left.
    """

    simultaneous = auto()
    left_to_right = "left-to-right"
    right_to_left = "right-to-left"


@dataclass(frozen=True)
class Quantifier:
    """Repetition bounds for a pattern element.

    Args:
        min: Minimum number of occurrences (≥ 0).
        max: Maximum number of occurrences, or None for unbounded.
    """

    min: int
    max: int | None  # None = unbounded

    def __post_init__(self) -> None:
        """Validate quantifier bounds."""
        if self.min < 0:
            raise ValueError(f"Quantifier min must be ≥ 0, got {self.min}")
        if self.max is not None and self.max < self.min:
            raise ValueError(f"Quantifier max ({self.max}) must be ≥ min ({self.min})")


# Pre-allocated singleton for the common case.
_ONE = Quantifier(min=1, max=1)


@dataclass(frozen=True)
class Bundle:
    """A feature-bundle pattern with optional quantifier and negation.

    Matches one (or more, depending on quantifier) consecutive segments whose
    feature bundles satisfy the pattern.

    Args:
        bundle: The feature-bundle pattern to match against.
        quantifier: How many times this bundle must match consecutively.
        negated: If True, the match succeeds when the segment does NOT satisfy
            the bundle.
    """

    bundle: FeatureBundle
    quantifier: Quantifier = field(default_factory=lambda: _ONE)
    negated: bool = False


@dataclass(frozen=True)
class Boundary:
    """A zero-width positional assertion (# word boundary, $ syllable boundary).

    Boundaries never consume positions in the sequence; they only check that
    the cursor is at the appropriate edge.
    """

    kind: Literal["word", "syllable"]


@dataclass(frozen=True)
class Null:
    """Null segment (∅) for insertion and deletion rules.

    In target position, marks an insertion point (the result element is what
    gets inserted).  In result position, marks deletion of the matched target.
    """


@dataclass(frozen=True)
class Group:
    """A parenthesised group of elements, matched as a unit.

    The group's quantifier applies to the entire sequence of inner elements.
    """

    elements: list[Element]
    quantifier: Quantifier = field(default_factory=lambda: _ONE)


@dataclass(frozen=True)
class Disjunction:
    """Alternatives separated by | in the rule notation.

    Each branch is a list of Elements.  During matching, the generator tries
    each branch in order; the first branch that succeeds wins.
    """

    branches: list[list[Element]]


@dataclass(frozen=True)
class Ref:
    """Recall a previously saved reference (@V).

    During matching, the referenced span is re-matched against the current
    position.  During rewriting, the referenced span's content is copied.
    """

    name: str


@dataclass(frozen=True)
class Binding:
    """Save a reference to a matched element (V=[...]).

    The binding captures the segment(s) matched by *pattern* under the key
    *name*, making them available to later Ref elements or to the result
    template.
    """

    name: str
    pattern: list[Element]


# The union type for all element variants.
type Element = Bundle | Boundary | Null | Group | Disjunction | Ref | Binding


# ---- Match environment ----


@dataclass(frozen=True)
class Env:
    """Environment carried through the match generator.

    Carries alpha-variable bindings and named-reference spans.  Because Env
    is frozen, each branch of a backtracking match gets its own copy without
    any unwind logic.
    """

    alphas: dict[str, int | list[int]] = field(default_factory=dict)
    refs: dict[str, tuple[int, int]] = field(default_factory=dict)


# Pre-allocated empty Env for calls that don't need to carry state.
_EMPTY_ENV = Env()

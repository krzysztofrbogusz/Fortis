"""Stage 1 — Parse a rule definition string into a Rule AST.

The parser converts a definition string like::

    [+cons, -syll] → [-vc] / _#

into a Rule object whose target, result, and context fields are lists of
Element nodes.  This is the only stage that can produce Err; downstream
stages (match, locus-finding, rewrite) operate on validated Rules.

Phase 1 supports:
- Feature bundles in brackets: [+cons, -syll], [height:2], [hgt: high]
- Arrows: → (Unicode) or -> (ASCII)
- Context clause with ``_`` position marker
- Word boundary ``#``
- Multi-segment contexts: [+nas][+cons]_
- Exception clause ``//`` (parsed but stored; not yet matched)

Deferred to later phases:
- Quantifiers, negation (``!``), disjunction (``|``), groups (``(...)``)
- Alpha variables (``[α F]``), conditional features (``[<n: +F>]``)
- References (``V=``, ``@V``), null segment (``∅``)
- Syllable boundary (``$``), autosegmental notation (``===>``, ``=x=>``)
- Letter shorthands (``p``)
"""

from __future__ import annotations

import re

from src.fortis.inventories.feature_inventory import FeatureInventory
from src.fortis.models.feature_bundle import FeatureBundle
from src.fortis.result import Err, Ok, Result
from src.fortis.rules.elements import Application, Boundary, Bundle, Element
from src.fortis.rules.rule import Rule

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

type RuleParseResult = tuple[
    list[Element],  # target
    list[Element],  # result
    list[Element] | None,  # left_context
    list[Element] | None,  # right_context
    list[Element] | None,  # exception_left
    list[Element] | None,  # exception_right
]


def parse_rule_definition(
    definition: str,
    inventory: FeatureInventory,
    rule_id: str = "",
    name: str = "",
    description: str = "",
    time: int = 0,
    application: Application = Application.simultaneous,
) -> Result[Rule, list[str]]:
    """Parse a full rule definition string into a Rule object.

    Args:
        definition: The rule definition in SPE notation.
        inventory: Feature inventory for bundle parsing.
        rule_id: Rule identifier (from TOML key).
        name: Human-readable rule name.
        description: Rule description.
        time: Application time (lower = earlier).
        application: How the rule's matches are applied (simultaneous, left-to-right, right-to-left).

    Returns:
        Ok(Rule) on success, Err(list[str]) with accumulated errors on failure.
    """
    result = parse_spe_definition(definition, inventory)
    if result.is_err():
        return Err(result.unwrap_err())

    target, result_elems, left_ctx, right_ctx, exc_left, exc_right = result.unwrap()

    return Ok(
        Rule(
            rule_id=rule_id,
            name=name,
            time=time,
            description=description,
            target=target,
            result=result_elems,
            left_context=left_ctx,
            right_context=right_ctx,
            exception_left=exc_left,
            exception_right=exc_right,
            application=application,
        )
    )


def parse_spe_definition(definition: str, inventory: FeatureInventory) -> Result[RuleParseResult, list[str]]:
    """Parse an SPE-style rule definition string into Element lists.

    General form: ``A → B / C_D // E_F``

    Phase 1 supports feature bundles, arrows, context with ``_`` and ``#``,
    and exception clause parsing (stored but not yet applied).

    Args:
        definition: The rule definition string.
        inventory: Feature inventory for feature-bundle parsing.

    Returns:
        Ok(tuple) with (target, result, left_ctx, right_ctx, exc_left, exc_right),
        or Err(list[str]) with accumulated errors.
    """
    errors: list[str] = []
    definition = definition.strip()

    # ------------------------------------------------------------------
    # 1. Split on exception clause (//) — phase 1 parses but stores it
    # ------------------------------------------------------------------
    exception_part: str | None = None
    main_part = definition
    if "//" in definition:
        parts = definition.split("//", maxsplit=1)
        main_part = parts[0].strip()
        exception_part = parts[1].strip()

    # ------------------------------------------------------------------
    # 2. Split on arrow (→ or ->)
    # ------------------------------------------------------------------
    arrow_pos = _find_arrow(main_part)
    if arrow_pos is None:
        errors.append("Rule definition must contain '→' or '->'")
        return Err(errors)

    input_part = main_part[: arrow_pos[0]].strip()
    rest = main_part[arrow_pos[1] :].strip()

    # ------------------------------------------------------------------
    # 3. Split output + context on /
    # ------------------------------------------------------------------
    slash_pos = _find_unbracketed_slash(rest)
    if slash_pos is not None:
        output_part = rest[:slash_pos].strip()
        context_part = rest[slash_pos + 1 :].strip()
    else:
        output_part = rest
        context_part = None

    # ------------------------------------------------------------------
    # 4. Parse target and result as Element lists
    # ------------------------------------------------------------------
    target_result = _parse_element_list(input_part, inventory, "target")
    if target_result.is_err():
        errors.extend(target_result.unwrap_err())
        target_elems: list[Element] = []
    else:
        target_elems = target_result.unwrap()

    result_result = _parse_element_list(output_part, inventory, "result")
    if result_result.is_err():
        errors.extend(result_result.unwrap_err())
        result_elems: list[Element] = []
    else:
        result_elems = result_result.unwrap()

    # ------------------------------------------------------------------
    # 5. Parse context
    # ------------------------------------------------------------------
    left_ctx: list[Element] | None = None
    right_ctx: list[Element] | None = None
    if context_part is not None:
        ctx_result = _parse_context(context_part, inventory)
        if ctx_result.is_err():
            errors.extend(ctx_result.unwrap_err())
        else:
            left_ctx, right_ctx = ctx_result.unwrap()

    # ------------------------------------------------------------------
    # 6. Parse exception (phase 1: store only)
    # ------------------------------------------------------------------
    exc_left: list[Element] | None = None
    exc_right: list[Element] | None = None
    if exception_part is not None:
        exc_result = _parse_context(exception_part, inventory)
        if exc_result.is_err():
            errors.extend(exc_result.unwrap_err())
        else:
            exc_left, exc_right = exc_result.unwrap()

    if errors:
        return Err(errors)

    return Ok((target_elems, result_elems, left_ctx, right_ctx, exc_left, exc_right))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

# Unicode arrow or ASCII ->
_ARROW_RE = re.compile(r"→|->")


def _find_arrow(s: str) -> tuple[int, int] | None:
    """Find the first arrow (→ or ->) outside brackets.

    Returns (start, end) indices, or None if no arrow found.
    """
    depth = 0
    i = 0
    while i < len(s):
        if s[i] == "[":
            depth += 1
        elif s[i] == "]":
            depth -= 1
        elif depth == 0:
            m = _ARROW_RE.match(s, i)
            if m:
                return (m.start(), m.end())
        i += 1
    return None


def _find_unbracketed_slash(s: str) -> int | None:
    """Find the first '/' outside brackets.  Returns index or None."""
    depth = 0
    for i, ch in enumerate(s):
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        elif ch == "/" and depth == 0:
            return i
    return None


def _parse_element_list(text: str, inventory: FeatureInventory, label: str) -> Result[list[Element], list[str]]:
    """Parse a target or result string into a list of Elements.

    Phase 1 supports:
    - Feature bundles in brackets: [+cons, -syll]
    - Word boundaries: #
    - Whitespace is ignored between elements

    Quantifiers, negation, disjunction, etc. are deferred to later phases.
    """
    errors: list[str] = []
    elements: list[Element] = []
    text = text.strip()

    if not text:
        errors.append(f"Empty {label} in rule definition")
        return Err(errors)

    i = 0
    while i < len(text):
        ch = text[i]

        # Skip whitespace
        if ch in (" ", "\t"):
            i += 1
            continue

        # Word boundary
        if ch == "#":
            elements.append(Boundary(kind="word"))
            i += 1
            continue

        # Syllable boundary
        if ch == "$":
            elements.append(Boundary(kind="syllable"))
            i += 1
            continue

        # Feature bundle in brackets
        if ch == "[":
            end = text.find("]", i)
            if end == -1:
                errors.append(f"Unclosed bracket in {label} starting at position {i}")
                break
            inner = text[i + 1 : end].strip()
            bundle_result = FeatureBundle.from_str(inner, inventory)
            if bundle_result.is_err():
                errors.extend(bundle_result.unwrap_err())
            else:
                elements.append(Bundle(bundle=bundle_result.unwrap()))
            i = end + 1
            continue

        # Unrecognised character
        errors.append(
            f"Unexpected character '{ch}' in {label} at position {i} "
            f"(quantifiers, negation, disjunction not yet supported)"
        )
        break

    if errors:
        return Err(errors)
    return Ok(elements)


def _parse_context(
    context_str: str, inventory: FeatureInventory
) -> Result[tuple[list[Element] | None, list[Element] | None], list[str]]:
    """Parse a context string (after '/') into left and right context.

    The context string must contain ``_`` marking the target position.
    Everything before ``_`` is the left context; everything after ``_`` is
    the right context.

    ``#`` at the start/end indicates a word boundary.

    Returns (left_context, right_context).  Either may be None if that side
    is empty (meaning "unconstrained").
    """
    errors: list[str] = []
    underscore_pos = context_str.find("_")
    if underscore_pos == -1:
        errors.append("Context must contain '_' to mark the target position")
        return Err(errors)

    left_str = context_str[:underscore_pos].strip()
    right_str = context_str[underscore_pos + 1 :].strip()

    left_ctx = _parse_context_side(left_str, inventory, "left", errors)
    right_ctx = _parse_context_side(right_str, inventory, "right", errors)

    if errors:
        return Err(errors)
    return Ok((left_ctx, right_ctx))


def _parse_context_side(
    side_str: str,
    inventory: FeatureInventory,
    side_label: str,
    errors: list[str],
) -> list[Element] | None:
    """Parse one side of a context string.

    Returns a list of Elements, or None if the side is empty (unconstrained).
    ``#`` at the start or end is converted to a Boundary element.
    """
    if not side_str:
        return None

    # Check for boundary markers
    # # at the start of left context or end of right context
    has_boundary = False
    work = side_str

    if side_label == "left" and work.startswith("#"):
        has_boundary = True
        work = work[1:].strip()
    elif side_label == "right" and work.endswith("#"):
        has_boundary = True
        work = work[:-1].strip()

    # Parse the remaining string as element list
    # For left context, reverse the element order so that index 0 is the
    # segment nearest to the target (adjacent-first ordering).
    elements: list[Element] = []
    if work:
        # Extract bracket groups and boundaries
        i = 0
        while i < len(work):
            ch = work[i]

            if ch in (" ", "\t"):
                i += 1
                continue

            if ch == "[":
                end = work.find("]", i)
                if end == -1:
                    errors.append(f"Unclosed bracket in {side_label} context at position {i}")
                    return elements if elements else None
                inner = work[i + 1 : end].strip()
                bundle_result = FeatureBundle.from_str(inner, inventory)
                if bundle_result.is_err():
                    errors.extend(bundle_result.unwrap_err())
                else:
                    elements.append(Bundle(bundle=bundle_result.unwrap()))
                i = end + 1
                continue

            # Shouldn't have # here (already stripped)
            if ch == "#":
                errors.append(f"Misplaced '#' in {side_label} context (boundary markers must be at the outermost edge)")
                i += 1
                continue

            errors.append(
                f"Unexpected character '{ch}' in {side_label} context "
                f"(quantifiers, negation, disjunction not yet supported)"
            )
            break

    # Left context: reverse to adjacent-first order
    if side_label == "left":
        # The SPE notation writes left-to-right (away from target),
        # but we want nearest-first.
        elements.reverse()

    if has_boundary:
        # Boundary always goes at the outermost edge of the context.
        # For left context (already reversed to adjacent-first order),
        #   the outermost edge is the end of the list.
        # For right context (already in adjacent-first order),
        #   the outermost edge is also the end of the list.
        elements.append(Boundary(kind="word"))

    return elements

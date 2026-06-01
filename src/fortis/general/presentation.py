"""Presentation functions for Fortis model objects.

All display/formatting logic lives here so that model classes stay
focused on data and matching.  Every function takes the model object
as its first argument, keeping presentation separate from identity.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.fortis.inventories.feature_definition import FeatureDefinition
from src.fortis.inventories.feature_inventory import FeatureInventory
from src.fortis.inventories.inventories import Inventories
from src.fortis.models.feature_bundle import FeatureBundle
from src.fortis.models.feature_type import FeatureType
from src.fortis.models.sequence import Sequence
from src.fortis.models.tiers import Tier
from src.fortis.rules.apply import AppliedLocus, RuleStep
from src.fortis.transcription.rendering import render_segment, sequence_to_string

# ---------------------------------------------------------------------------
# Primitive formatters
# ---------------------------------------------------------------------------


def present_value(value: int | None) -> str:
    """Format a single feature value as a display string.

    Maps: ``None`` → ``"∅"``, ``1`` → ``"+"``, ``0`` → ``"-"``,
    otherwise ``str(value)``.
    """
    if value is None:
        return "∅"
    if value == 1:
        return "+"
    if value == 0:
        return "-"
    return str(value)


def format_feature(short: str, feature_type: str, value: int | list[int | None] | None, negated: bool = False) -> str:
    """Format a single feature as a display string.

    Args:
        short: Short/abbreviated feature name.
        feature_type: ``"unary"``, ``"binary"``, or ``"scalar"``.
        value: The feature value (int, contour list, or None).
        negated: If True, prefix with ``!`` (feature-level negation).
    """
    prefix = "!" if negated else ""
    if feature_type == "unary":
        if isinstance(value, list):
            vals = ">".join(present_value(v) for v in value)
            return f"{prefix}{short}: {vals}"
        return f"{prefix}{short}"
    if feature_type == "binary":
        if isinstance(value, list):
            vals = ">".join(present_value(v) for v in value)
            return f"{prefix}{short}: {vals}"
        return f"{prefix}{short}: {present_value(value)}"
    # scalar
    if isinstance(value, list):
        vals = ">".join(present_value(v) for v in value)
        return f"{prefix}{short}: {vals}"
    return f"{prefix}{short}: {value if value is not None else '∅'}"


# ---------------------------------------------------------------------------
# FeatureBundle presentation
# ---------------------------------------------------------------------------


def present_bundle(bundle: FeatureBundle, inventory: FeatureInventory) -> str:
    """Format a feature bundle as a boxed display string.

    Binary/unary features show as ``+name`` or ``-name`` (using short names).
    Scalar features show as ``name: label``.
    Contour values show as ``name: label>label>...``.

    Args:
        bundle: The feature bundle to present.
        inventory: Feature inventory for name/type/value lookups.
    """
    return "\n".join(present_bundle_lines(bundle, inventory))


def present_bundle_lines(bundle: FeatureBundle, inventory: FeatureInventory) -> list[str]:
    """Return the boxed lines for a feature bundle (for side-by-side display).

    Args:
        bundle: The feature bundle to present.
        inventory: Feature inventory for name/type/value lookups.
    """
    lines: list[str] = []
    has_syllable = False
    for feature_name in inventory:
        if feature_name not in bundle:
            continue
        ft_def = inventory[feature_name]
        if ft_def.tier == Tier.syllable and not has_syllable:
            lines.append("---")
            has_syllable = True
        short = ft_def.short
        spec = bundle[feature_name]
        lines.append(format_feature(short, ft_def.type, spec.value, spec.negated))

    if not lines:
        return ["⎡⎤"]

    width = max(len(line) for line in lines)
    result = [f"⎡{lines[0]:<{width}}⎤"]
    if len(lines) > 1:
        result.extend(f"⎢{line:<{width}}⎥" for line in lines[1:-1])
        result.append(f"⎣{lines[-1]:<{width}}⎦")

    return result


# ---------------------------------------------------------------------------
# Sequence presentation
# ---------------------------------------------------------------------------


def present_sequence(sequence: Sequence, inventory: FeatureInventory) -> str:
    """Format all bundles in a sequence side-by-side with aligned features.

    Features that are present in any bundle get a row. Features absent
    from a specific bundle appear as empty rows within that bundle's column.
    A ``---`` row separates segment and syllable features.

    Args:
        sequence: The sequence of feature bundles to present.
        inventory: Feature inventory for name/type/value lookups.
    """
    if not sequence.data:
        return ""

    # Build row template from inventory order
    rows: list[tuple[str, str | None]] = []  # (feature_name or "", separator_label or None)
    has_syllable = False
    for feature_name in inventory:
        ft_def = inventory[feature_name]
        if ft_def.tier == Tier.syllable and not has_syllable:
            rows.append(("", "---"))
            has_syllable = True
        if any(feature_name in bundle for bundle in sequence.data):
            rows.append((feature_name, None))

    # Format each feature value per bundle
    content: list[list[str]] = []  # content[row][col]
    is_separator: list[bool] = []
    for feature_name, separator in rows:
        is_separator.append(separator is not None)
        if separator:
            row = []
            for bundle in sequence.data:
                has_syl = any(inventory[fn].tier == Tier.syllable for fn in bundle if fn in inventory)
                row.append(separator if has_syl else "")
            content.append(row)
        else:
            ft_def = inventory[feature_name]
            short = ft_def.short
            row = []
            for bundle in sequence.data:
                if feature_name not in bundle:
                    row.append("")
                else:
                    spec = bundle[feature_name]
                    row.append(format_feature(short, ft_def.type, spec.value, spec.negated))
            content.append(row)

    if not content:
        return ""

    # Calculate column widths
    col_widths = [max(len(content[r][c]) for r in range(len(content))) for c in range(len(sequence.data))]

    # For each column, find the first and last non-empty content row
    col_ranges: list[tuple[int, int]] = []
    for c in range(len(sequence.data)):
        non_empty = [r for r in range(len(content)) if content[r][c]]
        col_ranges.append((non_empty[0], non_empty[-1]))

    result_lines: list[str] = []
    for r in range(len(content)):
        cells = []
        for c in range(len(sequence.data)):
            val = content[r][c]
            padded = f"{val:<{col_widths[c]}}"
            first_row, last_row = col_ranges[c]
            if r < first_row or r > last_row:
                cells.append(" " * (col_widths[c] + 2))
            elif r == first_row:
                cells.append(f"⎡{padded}⎤")
            elif r == last_row:
                cells.append(f"⎣{padded}⎦")
            else:
                cells.append(f"⎢{padded}⎥")
        result_lines.append(" ".join(cells))

    return "\n".join(result_lines)


# ---------------------------------------------------------------------------
# Change detection from applied loci
# ---------------------------------------------------------------------------


@dataclass
class SegmentChange:
    """A change to a segment at a specific position.

    Attributes:
        position: Index in the after-sequence where the change occurred.
        old_bundle: The feature bundle before the change (None if inserted).
        new_bundle: The feature bundle after the change (None if deleted).
        differing_features: Feature names that differ between old and new.
    """

    position: int
    old_bundle: FeatureBundle | None
    new_bundle: FeatureBundle | None
    differing_features: list[str]


def changes_from_loci(
    applied: list[AppliedLocus],
) -> list[SegmentChange]:
    """Convert applied loci into segment-level changes.

    Uses the ``change_kinds`` field of each AppliedLocus to determine
    whether each new segment is an insertion (paired with a Null target),
    a modification (paired with a Bundle target), or a deletion (target
    segment removed with no replacement).

    Args:
        applied: The loci applied by a rule, from :class:`RuleStep`.

    Returns:
        A list of :class:`SegmentChange` objects for each segment that
        actually changed (modifications, insertions, or deletions).
    """
    changes: list[SegmentChange] = []
    old_idx = 0  # index into old_segments, advanced by 'modify' and 'delete'

    for locus in applied:
        old_segs = locus.old_segments
        new_segs = locus.new_segments

        for i, kind in enumerate(locus.change_kinds):
            if kind == 'insert':
                changes.append(SegmentChange(
                    position=locus.start + i,
                    old_bundle=None,
                    new_bundle=new_segs[i],
                    differing_features=list(new_segs[i].keys()),
                ))
            elif kind == 'modify':
                if old_idx < len(old_segs):
                    diffs = list(old_segs[old_idx].differing(new_segs[i]))
                    for name in new_segs[i]:
                        if name not in old_segs[old_idx] and name not in diffs:
                            diffs.append(name)
                    if diffs:
                        changes.append(SegmentChange(
                            position=locus.start + i,
                            old_bundle=old_segs[old_idx],
                            new_bundle=new_segs[i],
                            differing_features=diffs,
                        ))
                    old_idx += 1
            elif kind == 'delete':
                if old_idx < len(old_segs):
                    changes.append(SegmentChange(
                        position=locus.start + old_idx,
                        old_bundle=old_segs[old_idx],
                        new_bundle=None,
                        differing_features=list(old_segs[old_idx].keys()),
                    ))
                    old_idx += 1

    return changes


# ---------------------------------------------------------------------------
# Change description
# ---------------------------------------------------------------------------


def describe_change(
    change: SegmentChange,
    inventories: Inventories,
) -> str:
    """Describe a segment change in human-readable IPA form.

    Returns a string like ``x → ç`` for a modification, ``∅ → u`` for
    an insertion, or ``t → ∅`` for a deletion.

    Args:
        change: The segment change to describe.
        inventories: Inventories for rendering feature bundles as IPA.

    Returns:
        A short description of the change.
    """
    old_ipa = (
        render_segment(change.old_bundle, inventories)
        if change.old_bundle is not None
        else "∅"
    )
    new_ipa = (
        render_segment(change.new_bundle, inventories)
        if change.new_bundle is not None
        else "∅"
    )
    return f"{old_ipa} → {new_ipa}"


def describe_feature_change(
    old: FeatureBundle,
    new: FeatureBundle,
    features: FeatureInventory,
    differing: list[str],
) -> str:
    """Describe how features changed between two bundles.

    Uses the feature inventory's value labels to produce human-readable
    descriptions like ``cor: coronal → none`` or ``+vc → −vc``.

    Args:
        old: The feature bundle before the change.
        new: The feature bundle after the change.
        features: Feature inventory for name/type/value lookups.
        differing: Feature names that differ between old and new.

    Returns:
        A comma-separated description of each changed feature.
    """
    parts: list[str] = []
    for feature_name in differing:
        ft_def = features.get(feature_name)
        if ft_def is None:
            parts.append(feature_name)
            continue

        old_spec = old.get(feature_name)
        new_spec = new.get(feature_name)

        old_label = _format_feature_value(ft_def, old_spec.value if old_spec else None)
        new_label = _format_feature_value(ft_def, new_spec.value if new_spec else None)
        parts.append(f"{old_label} → {new_label}")

    return ", ".join(parts)


def _format_feature_value(
    ft_def: FeatureDefinition,
    value: int | list[int | None] | None,
) -> str:
    """Format a feature value using the feature definition's labels.

    Args:
        ft_def: The feature definition with short name, type, and value labels.
        value: The feature value to format.

    Returns:
        A human-readable string for the value.
    """
    if value is None:
        return f"{ft_def.short}: ∅"

    if isinstance(value, list):
        # Contour value
        labels = ">".join(
            ft_def.values.get(v, str(v)) if v is not None else "∅" for v in value
        )
        return f"{ft_def.short}: {labels}"

    if ft_def.type == FeatureType.unary:
        return ft_def.short
    if ft_def.type == FeatureType.binary:
        prefix = "+" if value == 1 else "−"
        return f"{prefix}{ft_def.short}"
    # scalar
    label = ft_def.values.get(value, str(value))
    return f"{ft_def.short}: {label}"


# ---------------------------------------------------------------------------
# Derivation formatting
# ---------------------------------------------------------------------------


def format_derivation(
    ipa: str,
    gloss: str,
    steps: list[tuple[RuleStep, list[SegmentChange]]],
    inventories: Inventories,
) -> str:
    """Format a word derivation as a human-readable table.

    Each row shows a rule that caused a change, the segment-level change,
    and the resulting IPA form.  Steps where no change occurred are
    omitted.

    Args:
        ipa: The original IPA string.
        gloss: An optional gloss or translation.
        steps: List of (RuleStep, changes) tuples for rules that
            caused a change.
        inventories: Inventories for rendering and feature lookups.

    Returns:
        A formatted string with the derivation table.
    """
    # Header: IPA form (and gloss if present)
    header = ipa if not gloss else f"{ipa} ({gloss})"

    if not steps:
        return f"{header}\n  No rules applied."

    # Calculate column widths
    # Rule column: "TIME · NAME"
    rule_labels = [f"{step.rule.time} · {step.rule.name}" for step, _ in steps]

    # Change column: comma-separated segment changes
    change_labels = []
    for _step, changes in steps:
        parts = [describe_change(c, inventories) for c in changes]
        change_labels.append(", ".join(parts))

    # Form column: rendered IPA after the rule
    form_labels = [
        sequence_to_string(step.after, inventories) for step, _ in steps
    ]

    # Feature change column
    feature_labels = []
    for _step, changes in steps:
        fparts = []
        for c in changes:
            if c.old_bundle is not None and c.new_bundle is not None:
                fparts.append(
                    describe_feature_change(
                        c.old_bundle, c.new_bundle, inventories.features, c.differing_features
                    )
                )
        feature_labels.append("; ".join(fparts) if fparts else "")

    # Column widths (with minimums for readability)
    rule_width = max(len("Rule"), max(len(lbl) for lbl in rule_labels))
    change_width = max(len("Change"), max(len(lbl) for lbl in change_labels) if change_labels else len("Change"))
    form_width = max(len("Form"), max(len(lbl) for lbl in form_labels) if form_labels else len("Form"))

    # Build the table
    lines: list[str] = [header]
    lines.append(
        f"  {'Rule':<{rule_width}}  {'Change':<{change_width}}  {'Form':<{form_width}}  Features"
    )

    for i, (_step, _changes) in enumerate(steps):
        row = (
            f"  {rule_labels[i]:<{rule_width}}  "
            f"{change_labels[i]:<{change_width}}  "
            f"{form_labels[i]:<{form_width}}  "
            f"{feature_labels[i]}"
        )
        lines.append(row)

    return "\n".join(lines)

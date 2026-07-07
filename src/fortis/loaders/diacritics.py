from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from src.fortis.general.file_handling import load_toml_file
from src.fortis.general.presenting import present_symbol
from src.fortis.models.bundles import FeatureBundle
from src.fortis.models.features import FeatureInventory
from src.fortis.models.inventories import Diacritic, DiacriticInventory, DiacriticKind
from src.fortis.models.tiers import Tier
from src.fortis.parsing.bundles import parse_feature_bundle
from src.fortis.result import Err, Ok, Result, collect

# The dotted-circle placeholder (U+25CC) that combining marks are conventionally
# shown on so they're visible in isolation — ``◌̃`` for a combining tilde. It is a
# display carrier, never part of the actual symbol, so it's stripped from a
# diacritic key on load: ``◌̃`` and ``̃`` both define the same diacritic.
_DOTTED_CIRCLE = "◌"

# ---- Diacritic -----------------------------------------------------------------------------------


def load_diacritic(
    symbol: str, diacritic_def: dict[str, Any], features: FeatureInventory
) -> Result[Diacritic, list[str]]:
    """Load a Diacritic from a raw TOML entry.

    Args:
        symbol: The diacritic character(s).
        diacritic_def: Raw dictionary from the TOML file.
        features: Feature inventory for bundle parsing.
    """
    error_list: list[str] = []

    tier = collect(error_list, load_tier(symbol, diacritic_def), Tier.segment)
    kind = collect(error_list, load_kind(symbol, diacritic_def), DiacriticKind.combining)
    match load_bundle(symbol, diacritic_def, features):  # a list of errors → extend, not append
        case Err(err):
            error_list.extend(err)
            bundle = FeatureBundle()
        case Ok(result):
            bundle = result
    contour = collect(error_list, load_bool_field(symbol, diacritic_def, "contour"), False)
    read_only = collect(error_list, load_bool_field(symbol, diacritic_def, "read_only"), False)
    marks_boundary = collect(
        error_list, load_bool_field(symbol, diacritic_def, "marks_boundary"), False
    )

    if error_list:
        return Err(error_list)
    return Ok(
        Diacritic(
            symbol=symbol,
            tier=tier,
            kind=kind,
            bundle=bundle,
            contour=contour,
            read_only=read_only,
            marks_boundary=marks_boundary,
        )
    )


# ---- Per-field helpers ---------------------------------------------------------------------------


def load_tier(symbol: str, diacritic_def: dict[str, Any]) -> Result[Tier, str]:
    """Parse and validate the 'tier' field.

    Args:
        symbol: Diacritic symbol (for error messages).
        diacritic_def: Raw dictionary from the TOML file.
    """
    value = diacritic_def.get("tier")
    if not value:
        return Err(f"Diacritic '{present_symbol(symbol)}' is missing the required 'tier' field")
    try:
        tier = Tier(value.strip().lower())
    except ValueError:
        return Err(
            f"Diacritic '{present_symbol(symbol)}' has invalid tier '{value}' "
            f"(expected {', '.join(t.value for t in Tier)})"
        )
    return Ok(tier)


def load_kind(symbol: str, diacritic_def: dict[str, Any]) -> Result[DiacriticKind, str]:
    """Parse and validate the 'kind' field.

    Args:
        symbol: Diacritic symbol (for error messages).
        diacritic_def: Raw dictionary from the TOML file.
    """
    value = diacritic_def.get("kind")
    if not value:
        return Err(f"Diacritic '{present_symbol(symbol)}' is missing the required 'kind' field")
    try:
        kind = DiacriticKind(value.strip().lower())
    except ValueError:
        return Err(
            f"Diacritic '{present_symbol(symbol)}' has invalid kind '{value}' "
            f"(expected {', '.join(t.value for t in DiacriticKind)})"
        )
    return Ok(kind)


def load_bundle(
    symbol: str, diacritic_def: dict[str, Any], features: FeatureInventory
) -> Result[FeatureBundle, list[str]]:
    """Parse the 'bundle' field.

    Args:
        symbol: Diacritic symbol (for error messages).
        diacritic_def: Raw dictionary from the TOML file.
        features: Feature inventory for bundle parsing.
    """
    value = diacritic_def.get("bundle")
    if not value:
        return Err([f"Diacritic '{present_symbol(symbol)}' is missing the required 'bundle' field"])
    match parse_feature_bundle(value, features):
        case Err(err):
            return Err(err)
        case Ok(result):
            return Ok(result)


def load_bool_field(symbol: str, diacritic_def: dict[str, Any], field: str) -> Result[bool, str]:
    """Parse an optional boolean diacritic field (``default``/``contour``/``marks_boundary``).

    Absent ⇒ False.

    Args:
        symbol: Diacritic symbol (for error messages).
        diacritic_def: Raw dictionary from the TOML file.
        field: The boolean field name to read.
    """
    value = diacritic_def.get(field)
    if value is None:
        return Ok(False)
    if not isinstance(value, bool):
        return Err(f"Diacritic '{present_symbol(symbol)}' '{field}' must be 'true' or 'false'")
    return Ok(value)


# ---- Diacritic Inventory -------------------------------------------------------------------------


def load_diacritic_inventory(
    path: Path, features: FeatureInventory
) -> Result[DiacriticInventory, list[str]]:
    """Load the diacritic inventory from a TOML or CSV file, dispatched by extension.

    Both formats carry the same schema (a symbol with a ``tier``/``kind``/``bundle`` and the
    optional ``marks_boundary``/``read_only``/``contour`` flags). A ``.csv`` path is read as a
    diacritics table (:func:`load_diacritic_inventory_csv`); any other path is read as TOML.

    Args:
        path: Path to the diacritics file (``.csv`` for CSV, else TOML).
        features: Feature inventory for bundle parsing.
    """
    if path.suffix.lower() == ".csv":
        return load_diacritic_inventory_csv(path, features)
    return load_diacritic_inventory_toml(path, features)


def load_diacritic_inventory_toml(
    path: Path, features: FeatureInventory
) -> Result[DiacriticInventory, list[str]]:
    """Load all diacritics from a TOML file.

    Args:
        path: Path to the TOML file.
        features: Feature inventory for bundle parsing.
    """
    error_list: list[str] = []

    match load_toml_file(path):
        case Err(err):
            return Err([err])
        case Ok(result):
            data = result

    inventory = DiacriticInventory()
    for symbol, diacritic_def in data.items():
        symbol = symbol.strip().replace(_DOTTED_CIRCLE, "")  # ◌̃ → ̃ (drop the display carrier)
        if not symbol:
            error_list.append("Diacritic has an empty symbol")
            continue
        if symbol in inventory:
            error_list.append(f"Diacritic '{present_symbol(symbol)}' is already defined")
            continue

        match load_diacritic(symbol, diacritic_def, features):
            case Err(err):
                error_list.extend(err)
                continue
            case Ok(result):
                diacritic = result

        inventory[symbol] = diacritic

    if error_list:
        return Err(error_list)

    return validate_diacritic_inventory(inventory, features).map(lambda _: inventory)


# Columns the CSV loader understands. ``diacritic``/``tier``/``kind``/``bundle`` are required;
# the three flags are optional booleans (empty cell ⇒ false).
_DIACRITIC_FLAGS = ("marks_boundary", "read_only", "contour")
_DIACRITIC_COLUMNS = ("diacritic", "tier", "kind", "bundle", *_DIACRITIC_FLAGS)


def _csv_bool(value: str) -> bool | str:
    """A CSV boolean cell → a Python bool.

    Empty or ``false`` ⇒ False, ``true`` ⇒ True; anything else is returned verbatim so the
    reused per-field loader reports it uniformly.
    """
    stripped = value.strip().lower()
    if stripped in ("", "false"):
        return False
    if stripped == "true":
        return True
    return value


def load_diacritic_inventory_csv(
    path: Path, features: FeatureInventory
) -> Result[DiacriticInventory, list[str]]:
    """Load all diacritics from a CSV file — the same schema as the TOML form, one per row.

    A header row names the columns, read **by name** so any order works. The canonical order::

        diacritic, tier, kind, bundle, marks_boundary, read_only, contour

    - ``diacritic`` — the symbol (required). A combining mark may be written on the dotted-circle
      carrier (``◌̃``); the carrier is stripped on load, exactly as in TOML.
    - ``tier`` — ``segment`` or ``syllable`` (required).
    - ``kind`` — ``before``, ``after``, or ``combining`` (required).
    - ``bundle`` — the feature bundle the diacritic contributes (required). It usually contains
      commas, so quote it (``"+labial, +rounded"``).
    - ``marks_boundary`` / ``read_only`` / ``contour`` — optional booleans (``true``/``false``;
      an empty cell is false).

    Args:
        path: Path to the CSV file.
        features: Feature inventory for bundle parsing.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        return Err([f"could not read '{path}': {error}"])

    reader = csv.DictReader(text.splitlines())
    if reader.fieldnames is None:
        return Err([f"'{path}' is empty (no header row)"])
    unknown = [name for name in reader.fieldnames if name not in _DIACRITIC_COLUMNS]
    if unknown:
        return Err([f"'{path}' has unknown column(s): {', '.join(unknown)}"])
    for required in ("diacritic", "tier", "kind", "bundle"):
        if required not in reader.fieldnames:
            return Err([f"'{path}' must have a '{required}' column"])

    error_list: list[str] = []
    inventory = DiacriticInventory()
    for row in reader:
        symbol = (row.get("diacritic") or "").strip().replace(_DOTTED_CIRCLE, "")
        if not symbol:
            error_list.append("Diacritic has an empty symbol")
            continue
        if symbol in inventory:
            error_list.append(f"Diacritic '{present_symbol(symbol)}' is already defined")
            continue

        diacritic_def: dict[str, Any] = {
            "tier": (row.get("tier") or "").strip(),
            "kind": (row.get("kind") or "").strip(),
            "bundle": (row.get("bundle") or "").strip(),
        }
        for flag in _DIACRITIC_FLAGS:
            if flag in reader.fieldnames:
                diacritic_def[flag] = _csv_bool(row.get(flag) or "")

        match load_diacritic(symbol, diacritic_def, features):
            case Err(err):
                error_list.extend(err)
            case Ok(result):
                inventory[symbol] = result

    if error_list:
        return Err(error_list)

    return validate_diacritic_inventory(inventory, features).map(lambda _: inventory)


def validate_diacritic_inventory(
    inventory: DiacriticInventory, features: FeatureInventory
) -> Result[None, list[str]]:
    """Check for cross-diacritic consistency issues.

    Validates that each diacritic's bundle features match its declared tier.
    Duplicate bundles on the same tier and type are allowed — the same
    feature bundle may be expressed by multiple input symbols.

    Args:
        inventory: The loaded diacritic inventory.
        features: Feature inventory for tier lookups.
    """
    error_list: list[str] = []

    for symbol, diacritic in inventory.data.items():
        for feature_name in diacritic.bundle:
            if feature_name not in features:
                continue  # already caught during bundle parsing
            feature_tier = features[feature_name].tier
            if feature_tier != diacritic.tier:
                error_list.append(
                    f"Diacritic '{present_symbol(symbol)}' (tier: {diacritic.tier.value}) "
                    f"uses feature '{feature_name}' which belongs to tier: {feature_tier.value}"
                )

    if error_list:
        return Err(error_list)
    return Ok(None)

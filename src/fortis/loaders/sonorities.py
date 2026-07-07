from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from src.fortis.general.file_handling import load_toml_file
from src.fortis.general.utils import safe_int
from src.fortis.models.bundles import PatternBundle
from src.fortis.models.features import FeatureInventory
from src.fortis.models.inventories import SonoritiesInventory, Sonority
from src.fortis.parsing.bundles import parse_pattern_bundle
from src.fortis.result import Err, Ok, Result

# ---- Sonority ------------------------------------------------------------------------------------


def load_sonority(
    label: str, sonority_def: dict[str, Any], features: FeatureInventory
) -> Result[Sonority, list[str]]:
    """Load a Sonority from a raw TOML entry.

    Args:
        label: Sonority level label.
        sonority_def: Raw dictionary from the TOML file.
        features: Feature inventory for bundle parsing.
    """
    error_list: list[str] = []

    match load_level(label, sonority_def):
        case Err(err):
            error_list.append(err)
            level = 0  # Dummy value for the type checker
        case Ok(result):
            level = result

    match load_bundle(label, sonority_def, features):
        case Err(err):
            error_list.extend(err)
            bundle = None  # Dummy value for the type checker
        case Ok(result):
            bundle = result

    if error_list:
        return Err(error_list)
    return Ok(Sonority(label=label, level=level, bundle=bundle))


# ---- Per-field helpers ---------------------------------------------------------------------------


def load_level(label: str, sonority_def: dict[str, Any]) -> Result[int, str]:
    """Parse and validate the 'level' field.

    Args:
        label: Sonority label (for error messages).
        sonority_def: Raw dictionary from the TOML file.
    """
    value = sonority_def.get("level")
    if value is None:
        return Err(f"Sonority '{label}' is missing the required 'level' field")
    level = safe_int(str(value).strip())
    if level is None or level <= 0:
        return Err(f"Sonority '{label}' has invalid level '{value}' (expected a positive integer)")
    return Ok(level)


def load_bundle(
    label: str, sonority_def: dict[str, Any], features: FeatureInventory
) -> Result[PatternBundle | None, list[str]]:
    """Parse the 'bundle' field; empty string yields None.

    Args:
        label: Sonority label (for error messages).
        sonority_def: Raw dictionary from the TOML file.
        features: Feature inventory for bundle parsing.
    """
    value = sonority_def.get("bundle")
    if value is None:
        return Err([f"Sonority '{label}' is missing the required 'bundle' field"])
    value = value.strip()
    if not value:
        return Ok(None)
    match parse_pattern_bundle(value, features):
        case Err(err):
            return Err(err)
        case Ok(result):
            return Ok(result)


# ---- Sonority Inventory --------------------------------------------------------------------------


def load_sonorities_inventory(
    path: Path, features: FeatureInventory
) -> Result[SonoritiesInventory, list[str]]:
    """Load the sonority inventory from a TOML or CSV file, dispatched by extension.

    Both formats carry the same schema (a level's ``name``, integer ``level``, and matching
    ``bundle``) and both are **order-sensitive** — levels are tried first-match in file/row
    order. A ``.csv`` path is read as a sonorities table (:func:`load_sonorities_inventory_csv`);
    any other path is read as TOML.

    Args:
        path: Path to the sonorities file (``.csv`` for CSV, else TOML).
        features: Feature inventory for bundle parsing.
    """
    if path.suffix.lower() == ".csv":
        return load_sonorities_inventory_csv(path, features)
    return load_sonorities_inventory_toml(path, features)


def load_sonorities_inventory_toml(
    path: Path, features: FeatureInventory
) -> Result[SonoritiesInventory, list[str]]:
    """Load all sonority levels from a TOML file.

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

    inventory = SonoritiesInventory()
    for label, sonority_def in data.items():
        label = label.strip()
        if label in inventory:
            error_list.append(f"Sonority '{label}' is already defined")
            continue

        match load_sonority(label, sonority_def, features):
            case Err(err):
                error_list.extend(err)
                continue
            case Ok(result):
                sonority = result

        inventory[label] = sonority

    if error_list:
        return Err(error_list)

    return validate_sonorities_inventory(inventory).map(lambda _: inventory)


# The CSV columns; all three are required (an empty ``bundle`` cell is the catch-all level).
_SONORITY_COLUMNS = ("name", "level", "bundle")


def load_sonorities_inventory_csv(
    path: Path, features: FeatureInventory
) -> Result[SonoritiesInventory, list[str]]:
    """Load all sonority levels from a CSV file — the same schema as the TOML form, one per row.

    Row order is significant: levels are matched first-to-last, exactly like the TOML table
    order. A header row names the columns (read by name); the canonical order::

        name, level, bundle

    - ``name`` — the level's label (required, unique).
    - ``level`` — a positive integer rank (required, unique across rows).
    - ``bundle`` — the feature-bundle predicate a segment must match for this level (required
      column; usually contains commas, so quote it — ``"sonorant: +, nasal: +"``). An empty
      cell is the catch-all that matches anything.

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
    unknown = [name for name in reader.fieldnames if name not in _SONORITY_COLUMNS]
    if unknown:
        return Err([f"'{path}' has unknown column(s): {', '.join(unknown)}"])
    for required in _SONORITY_COLUMNS:
        if required not in reader.fieldnames:
            return Err([f"'{path}' must have a '{required}' column"])

    error_list: list[str] = []
    inventory = SonoritiesInventory()
    for row in reader:
        label = (row.get("name") or "").strip()
        if not label:
            error_list.append("Sonority has an empty name")
            continue
        if label in inventory:
            error_list.append(f"Sonority '{label}' is already defined")
            continue

        sonority_def: dict[str, Any] = {
            "level": (row.get("level") or "").strip(),
            "bundle": row.get("bundle") or "",  # load_bundle strips; empty ⇒ catch-all (None)
        }
        match load_sonority(label, sonority_def, features):
            case Err(err):
                error_list.extend(err)
                continue
            case Ok(result):
                inventory[label] = result

    if error_list:
        return Err(error_list)

    return validate_sonorities_inventory(inventory).map(lambda _: inventory)


def validate_sonorities_inventory(inventory: SonoritiesInventory) -> Result[None, list[str]]:
    """Check for cross-sonority consistency issues.

    Validates that sonority levels are unique.

    Args:
        inventory: The loaded sonority inventory.
    """
    error_list: list[str] = []

    seen_levels: dict[int, str] = {}
    for label, sonority in inventory.data.items():
        if sonority.level in seen_levels:
            error_list.append(
                f"Sonority '{label}' and '{seen_levels[sonority.level]}' "
                f"share level {sonority.level}"
            )
        else:
            seen_levels[sonority.level] = label

    if error_list:
        return Err(error_list)
    return Ok(None)

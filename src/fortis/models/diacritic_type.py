"""Diacritic type enum — before, combining, or after."""

from enum import StrEnum, auto


class DiacriticType(StrEnum):
    """Where a diacritic attaches relative to its base symbol."""

    before = auto()
    combining = auto()
    after = auto()

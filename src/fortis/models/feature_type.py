"""Feature type enum — unary, binary, or scalar."""

from enum import StrEnum, auto


class FeatureType(StrEnum):
    """Whether a feature is unary, binary, or scalar."""

    unary = auto()
    binary = auto()
    scalar = auto()

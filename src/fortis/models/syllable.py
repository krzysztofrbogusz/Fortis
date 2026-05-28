from dataclasses import dataclass

from src.fortis.models.feature_bundle import FeatureBundle


@dataclass
class Syllable:
    """Syllable."""

    segments: list[FeatureBundle]
    bundle: FeatureBundle

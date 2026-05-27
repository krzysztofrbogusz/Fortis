from dataclasses import dataclass
from pathlib import Path

from src.fortis.config import config
from src.fortis.models.diacritics import DiacriticInventory
from src.fortis.models.feature_inventory import FeatureInventory
from src.fortis.models.letters import LetterInventory
from src.fortis.models.sonorities import SonorityInventory
from src.fortis.result import Err, Ok, Result


@dataclass
class Inventories:
    """Top-level container holding all loaded inventories.

    Args:
        features: Feature definitions keyed by name.
        letters: Segment symbols keyed by their feature bundles.
        diacritics: Diacritic symbols keyed by their definitions.
        sonorities: Sonority levels keyed by label.
    """

    features: FeatureInventory
    letters: LetterInventory
    diacritics: DiacriticInventory
    sonorities: SonorityInventory

    @classmethod
    def load(cls, inventories_dir: Path | None = None) -> Result[Inventories, list[str]]:
        """Load all inventories from the given directory, or the configured default.

        Args:
            inventories_dir: Directory containing features.toml, letters.csv, etc.
                Falls back to ``config.paths.inventories`` if None.
        """
        error_list = []
        dir_path = inventories_dir or config.paths.inventories

        features_result = FeatureInventory.load(dir_path / "features.toml")
        if features_result.is_err():
            error_list.extend(features_result.unwrap_err())
            return Err(error_list)
        features = features_result.unwrap()

        letters_result = LetterInventory.load(dir_path / "letters.csv", features)
        if letters_result.is_err():
            error_list.extend(letters_result.unwrap_err())

        diacritics_result = DiacriticInventory.load(dir_path / "diacritics.toml", features)
        if diacritics_result.is_err():
            error_list.extend(diacritics_result.unwrap_err())

        sonorities_result = SonorityInventory.load(dir_path / "sonorities.toml", features)
        if sonorities_result.is_err():
            error_list.extend(sonorities_result.unwrap_err())

        if error_list:
            return Err(error_list)
        return Ok(
            cls(
                features=features,
                letters=letters_result.unwrap(),
                diacritics=diacritics_result.unwrap(),
                sonorities=sonorities_result.unwrap(),
            )
        )

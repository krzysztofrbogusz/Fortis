from collections import UserDict
from pathlib import Path

from src.fortis.general.file_handling import load_toml_file
from src.fortis.inventories.feature_definition import FeatureDefinition
from src.fortis.result import Err, Ok, Result


class FeatureInventory(UserDict[str, FeatureDefinition]):
    """Feature definitions keyed by name, loaded from TOML with cross-feature validation."""

    @classmethod
    def load(cls, path: Path) -> Result[FeatureInventory, list[str]]:
        """Load from a TOML file, assign parents, and run cross-feature checks.

        Args:
            path: Path to the TOML file.
        """
        error_list = []

        data_result = load_toml_file(path)
        if data_result.is_err():
            return Err([data_result.unwrap_err()])
        data = data_result.unwrap()

        feature_inventory = {}
        for feature_name, feature_def_dict in data.items():
            feature_name = feature_name.strip()
            if " " in feature_name or "\t" in feature_name:
                error_list.append(f"Feature name '{feature_name}' contains whitespace")
                continue
            if feature_name in feature_inventory:
                error_list.append(f"Feature name '{feature_name}' is already in use")
                continue

            feature_def_result = FeatureDefinition.load(feature_name, feature_def_dict)
            if feature_def_result.is_err():
                error_list.extend(feature_def_result.unwrap_err())
                continue

            feature_inventory[feature_name] = feature_def_result.unwrap()

        for feature_name, feature_def in feature_inventory.items():
            if not feature_def.children:
                continue
            for child_name in feature_def.children:
                if child_name not in feature_inventory:
                    error_list.append(f"Feature '{feature_name}' references unknown child '{child_name}'")
                    continue
                feature_inventory[child_name].parent = feature_name

        if error_list:
            return Err(error_list)

        inventory = cls(feature_inventory)
        check_result = inventory.validate()
        if check_result.is_err():
            return Err(check_result.unwrap_err())

        return Ok(inventory)

    def validate(self) -> Result[None, list[str]]:
        """Validate unique names/shorts, tier consistency, and no circular parent chains."""
        error_list = []

        seen_names: dict[str, str] = {}
        seen_shorts: dict[str, str] = {}

        for feature_name, ft_def in self.data.items():
            # Unique long names
            if feature_name in seen_names:
                error_list.append(
                    f"Feature name '{feature_name}' is already used by feature '{seen_names[feature_name]}'"
                )
            seen_names[feature_name] = feature_name

            # Unique short names — a feature's own long name matching its short is fine
            if ft_def.short in seen_shorts:
                other = seen_shorts[ft_def.short]
                if other != feature_name:
                    error_list.append(
                        f"Feature '{feature_name}' has short name '{ft_def.short}' already used by feature '{other}'"
                    )
            if ft_def.short != feature_name:
                seen_shorts[ft_def.short] = feature_name

        # Children on the same tier as parent
        for feature_name, ft_def in self.data.items():
            if not ft_def.children:
                continue
            for child_name in ft_def.children:
                if child_name not in self.data:
                    continue  # already caught in load
                child_def = self.data[child_name]
                if child_def.tier != ft_def.tier:
                    error_list.append(
                        f"Feature '{child_name}' (tier: {child_def.tier.value}) "
                        f"cannot be a child of '{feature_name}' (tier: {ft_def.tier.value})"
                    )

        # No circular parent chains
        for feature_name in self.data:
            visited: set[str] = set()
            current = feature_name
            while current is not None:
                if current in visited:
                    error_list.append(f"Feature '{feature_name}' has a circular parent chain")
                    break
                visited.add(current)
                current = self.data[current].parent

        if error_list:
            return Err(error_list)

        return Ok(None)

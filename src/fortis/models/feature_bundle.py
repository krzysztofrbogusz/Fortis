from collections import UserDict

from src.fortis.models.feature_inventory import FeatureInventory
from src.fortis.models.feature_spec import FeatureSpec, Place
from src.fortis.result import Err, Ok, Result


class FeatureBundle(UserDict[str, FeatureSpec]):
    """A collection of feature specifications, keyed by feature name."""

    def matches(self, other: FeatureBundle, ignore_none: bool = False, place: Place = "any") -> bool:
        """Check if every feature in this bundle matches the corresponding feature in *other*.

        Features present in *other* but not in *self* are unconstrained (the pattern
        doesn't care about them). Features present in *self* but not in *other* are
        treated as unspecified values.

        Args:
            other: The target bundle to match against.
            ignore_none: Treat missing features and None values as wildcards.
            place: Positional control for contour matching, passed to FeatureSpec.matches.
        """
        for feature, spec in self.data.items():
            if feature not in other.data:
                # Feature not present in target — unspecified
                if ignore_none:
                    continue
                return False
            if not spec.matches(other.data[feature], ignore_none=ignore_none, place=place):
                return False
        return True

    @classmethod
    def from_str(
        cls, raw_string: str, inventory: FeatureInventory, bare_unary_means_present: bool = False
    ) -> Result[FeatureBundle, list[str]]:
        """Parse a comma-separated feature bundle string (e.g. '+syll, -cons, height:2').

        Args:
            raw_string: Comma- or semicolon-separated feature specs.
            inventory: Feature inventory for name/value resolution.
            bare_unary_means_present: If True, a bare feature name on a unary
                feature is interpreted as present (value 1).
        """
        error_list = []
        string = raw_string.replace(" ", "").replace(";", ",")
        tokens = [t for t in string.split(",") if t]

        bundle = cls()
        for token in tokens:
            result = FeatureSpec.from_string(token, inventory, bare_unary_means_present)
            if result.is_err():
                error_list.append(result.unwrap_err())
                continue
            spec = result.unwrap()
            bundle[spec.feature] = spec

        if error_list:
            return Err(error_list)

        return Ok(bundle)

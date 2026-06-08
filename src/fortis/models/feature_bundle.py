from collections import UserDict

from src.fortis.imports.features import FeatureInventory
from src.fortis.models.feature_value import FeatureValue
from src.fortis.result import Err, Ok, Result


class FeatureBundle(UserDict[str, FeatureValue]):
    """A collection of realized feature values, keyed by feature name.

    Used for concrete phonological material — segments in the lexicon,
    diacritics, syllable parts, etc. No matching or negation methods;
    those belong on PatternBundle.
    """

    def __repr__(self) -> str:
        """Represent a feature bundle."""
        parts: list[str] = []
        for feature, value in self.data.items():
            parts.append(f"{feature}: {value}")
        return "[" + ", ".join(parts) + "]"

    @classmethod
    def from_string(cls, raw_string: str, features: FeatureInventory) -> Result[FeatureBundle, list[str]]:
        """Parse a comma-separated feature bundle string (e.g. '+syll, -cons, height:2').

        Args:
            raw_string: Comma- or semicolon-separated feature specs.
            features: Feature inventory for name/value resolution.
        """
        error_list = []
        string = raw_string.replace(";", ",")
        tokens = [t.strip() for t in string.split(",") if t.strip()]

        bundle = cls()
        for token in tokens:
            # Identify feature name first, then parse value
            match features.identify_feature(token.replace(" ", "")):
                case Ok(feature_name):
                    pass
                case Err() as err:
                    error_list.append(err.unwrap_err())
                    continue

            value_result = FeatureValue.from_str(token, feature_name, features)
            if value_result.is_err():
                error_list.append(value_result.unwrap_err())
                continue
            bundle[feature_name] = value_result.unwrap()

        if error_list:
            return Err(error_list)

        return Ok(bundle)

    def combine_with(self, other: FeatureBundle, form_contours: bool = False) -> FeatureBundle:
        """Combine this feature bundle with another.

        Args:
            other: The bundle to merge in.
            form_contours: If True, overlapping features form contours instead of overriding.
        """
        result = FeatureBundle(dict(self.data))
        for feature_name, value in other.items():
            if feature_name not in result:
                result[feature_name] = value
            elif form_contours:
                new_value = result[feature_name].form_contour_with(value)
                result[feature_name] = new_value
            else:
                result[feature_name] = value

        return result

    def matches_exactly(self, other: FeatureBundle) -> bool:
        """Check if this bundle is exactly identical to *other*.

        Both bundles must have the same set of features and the same value
        for every feature.
        """
        if set(self.data.keys()) != set(other.data.keys()):
            return False
        for feature in self.data:
            if self.data[feature].value != other.data[feature].value:
                return False
        return True

    def differing(self, other: FeatureBundle) -> list[str]:
        """Return the features that are different between this bundle and *other*."""
        differing: list[str] = []
        for feature in self.data:
            if feature not in other.data:
                differing.append(feature)
                continue
            if self.data[feature].value != other.data[feature].value:
                differing.append(feature)
                continue
        for feature in other.data:
            if feature not in self.data and feature not in differing:
                differing.append(feature)
                continue
        return differing
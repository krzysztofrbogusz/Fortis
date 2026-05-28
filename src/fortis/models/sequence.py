from collections import UserList

from src.fortis.models.feature_bundle import FeatureBundle
from src.fortis.models.feature_inventory import FeatureInventory


class Sequence(UserList[FeatureBundle]):
    """An ordered sequence of feature bundles (segments)."""

    def present(self, inventory: FeatureInventory) -> str:
        """Format all bundles side-by-side with aligned box drawing.

        Args:
            inventory: Feature inventory for name/type/value lookups.
        """
        if not self.data:
            return ""

        boxed = [bundle.present_lines(inventory) for bundle in self.data]
        row_count = max(len(lines) for lines in boxed)

        # Pad shorter bundles with blank lines of matching width
        for lines in boxed:
            width = len(lines[0]) if lines else 0
            pad = " " * width
            while len(lines) < row_count:
                lines.append(pad)

        rows: list[str] = []
        for i in range(row_count):
            rows.append(" ".join(lines[i] for lines in boxed))

        return "\n".join(rows)

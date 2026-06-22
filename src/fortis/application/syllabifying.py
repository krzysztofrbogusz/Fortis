"""Syllabification: place syllable boundaries on a form from sonority.

``syllabify`` is a structural pass (not a rule). It identifies nuclei (segments
matching the time-appropriate nucleus definition), then divides the consonants
between each adjacent pair of nuclei into a coda + onset by the **Maximal Onset
Principle** under **sonority sequencing**: the onset is the longest rightmost run
whose sonority strictly rises toward the following nucleus; whatever is left
becomes the preceding nucleus's coda. No segments are inserted or deleted (§7).

The result is the set of boundary positions — a boundary at index ``k`` sits
*before* segment ``k`` (between ``k-1`` and ``k``). A syllabified word also counts
its two word edges (``0`` and ``len``) as syllable boundaries, so the ``$``
assertion holds there as well as at interior divisions; a word with no nucleus is
unsyllabifiable and yields no boundaries at all.

Sonority levels come from the user's scale by first-match in file order
(``SonoritiesInventory`` preserves it); a segment matching no predicate is
treated as least sonorous. Onset/coda *constraint enforcement* (legal clusters
from ``syllable_parts``) is a deferred next layer — the data defines no onset or
coda parts yet, and the Maximal Onset division is a complete syllabifier without
them.
"""

from src.fortis.application.matching import pattern_matches
from src.fortis.models.bundles import FeatureBundle
from src.fortis.models.inventories import SonoritiesInventory, SyllablePartsInventory


def _sonority(segment: FeatureBundle, sonorities: SonoritiesInventory) -> int:
    """The sonority level of *segment* by first-match; least sonorous if unmatched."""
    for sonority in sonorities.values():
        if sonority.bundle is not None and pattern_matches(sonority.bundle, segment):
            return sonority.level
    return 0


def _onset_start(cluster: list[int]) -> int:
    """Index within an intervocalic *cluster* where the onset begins.

    *cluster* is the sonority levels of the consonants strictly between two
    nuclei. The onset is the maximal suffix whose sonority strictly rises toward
    the nucleus; the returned index splits coda (``cluster[:i]``) from onset
    (``cluster[i:]``). An empty cluster returns ``0``.
    """
    if not cluster:
        return 0
    start = len(cluster) - 1  # the consonant adjacent to the nucleus is always onset
    i = start - 1
    while i >= 0 and cluster[i] < cluster[i + 1]:
        start = i
        i -= 1
    return start


def syllabify(
    segments: list[FeatureBundle],
    sonorities: SonoritiesInventory,
    syllable_parts: SyllablePartsInventory,
    time: int,
) -> frozenset[int]:
    """Return the syllable-boundary positions of *segments* at *time*.

    Args:
        segments: The form to syllabify.
        sonorities: The sonority scale (first-match in file order).
        syllable_parts: Syllable-part constraints; supplies the nucleus definition.
        time: Derivation time, selecting the nucleus definition in force.
    """
    nucleus_part = syllable_parts.get_nucleus(time)
    if nucleus_part is None or nucleus_part.definition is None:
        return frozenset()

    nuclei = [i for i, seg in enumerate(segments) if pattern_matches(nucleus_part.definition, seg)]
    if not nuclei:
        return frozenset()

    levels = [_sonority(seg, sonorities) for seg in segments]
    boundaries = {0, len(segments)}  # word edges are syllable edges
    for left, right in zip(nuclei, nuclei[1:], strict=False):
        cluster = levels[left + 1 : right]
        boundaries.add(left + 1 + _onset_start(cluster))
    return frozenset(boundaries)

"""The syllable: a computed view over a span of segments (never stored)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Syllable:
    """A syllable as a computed view over a segment span — never stored.

    Derived from segments + boundaries (by ``application.syllabifying.syllables``), so it can't go
    stale across a rewrite. ``segments[start:end]`` is the syllable; ``nucleus`` is the index of its
    nucleus segment (the tone-bearing unit) or ``None``. The onset is ``range(start, nucleus)`` and
    the coda ``range(nucleus + 1, end)``.
    """

    start: int
    end: int
    nucleus: int | None

    @property
    def onset(self) -> range:
        """The onset segment indices (everything before the nucleus)."""
        return range(self.start, self.nucleus if self.nucleus is not None else self.end)

    @property
    def coda(self) -> range:
        """The coda segment indices (everything after the nucleus)."""
        return range(self.nucleus + 1, self.end) if self.nucleus is not None else range(0)

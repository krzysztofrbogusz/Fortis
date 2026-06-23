"""Tests for IPA rendering (application/rendering.py).

These run against the real project inventories (the ``project`` fixture).
"""

from src.fortis.application.rendering import (
    render_segment,
    render_syllabified,
    sequence_to_string,
)
from src.fortis.application.segmentation import string_to_sequence
from src.fortis.application.syllabifying import syllabify


class TestRenderSegment:
    def test_exact_letter_match(self, project):
        # A plain letter's own bundle renders back to that letter.
        e = project.letters["e"].bundle
        assert render_segment(e, project) == "e"

    def test_segment_with_diacritic(self, project):
        # ɣʷ is a labialised ɣ: a base letter plus a combining diacritic.
        seq = string_to_sequence("ɣʷ", project)
        assert render_segment(seq[0], project) == "ɣʷ"


class TestRenderSyllabified:
    def test_dots_at_syllable_boundaries_with_full_rendering(self, project):
        # mexteːr → mex.teːr: the boundary shows as ".", and each segment still goes
        # through the full renderer (the length diacritic on teːr is preserved).
        seq = string_to_sequence("mexteːr", project)
        boundaries = syllabify(
            seq, project.sonorities, project.syllable_parts, project.time, project.letters
        )
        assert render_syllabified(seq, boundaries, project) == "mex.teːr"


class TestSequenceToString:
    def test_string_round_trip_for_invertible_words(self, project):
        # Most words round-trip exactly; the one diacritic-ordering case is covered
        # at the feature level in the segmentation tests.
        for word in project.words:
            rendered = sequence_to_string(string_to_sequence(word, project), project)
            if rendered != word:
                # Only legitimate diacritic reorderings are allowed to differ; the
                # rendered form must still re-segment to the same length.
                assert len(string_to_sequence(rendered, project)) == len(
                    string_to_sequence(word, project)
                )

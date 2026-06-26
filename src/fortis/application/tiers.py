"""Autosegmental tier operations over a Form.

For now this is just *construction*: lifting the suprasegmental features already sitting
in the segment bundles onto their declared tiers, as autosegments linked to their anchor.
The in-bundle copy is left in place (dual representation) — task 3c removes it and flips
the readers (matcher, rendering) to consult the tier instead.
"""
from __future__ import annotations

from src.fortis.application.matching import pattern_matches
from src.fortis.models.autosegment import Autoseg, AutosegmentalTier
from src.fortis.models.bundles import FeatureBundle
from src.fortis.models.form import Form
from src.fortis.models.tier_declaration import TierInventory


def associate_tiers(form: Form, tiers: TierInventory) -> Form:
    """Build each declared tier from the carried features already in *form*'s segments.

    For every declared tier, each anchor segment that carries the tier's feature(s) gets
    an autosegment (those features lifted out) linked to it by id. Mutates and returns
    *form*; an absent or empty tier declaration leaves the form untouched.
    """
    for name, declaration in tiers.items():
        tier = AutosegmentalTier()
        for segment in form.segments:
            if not pattern_matches(declaration.anchor, segment.bundle):
                continue
            carried = {
                feature: segment.bundle[feature]
                for feature in declaration.carries
                if feature in segment.bundle
            }
            if not carried:
                continue
            autoseg = Autoseg(FeatureBundle(carried), form.fresh_id())
            tier.autosegs.append(autoseg)
            tier.links.add((autoseg.id, segment.id))
        form.tiers[name] = tier
    return form

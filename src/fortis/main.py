"""Main entry point for the Fortis phonology engine.

Loads all inventories, processes every word through all phonological
rules, and prints a step-by-step derivation table showing which rules
applied and what changed at each stage.
"""

from src.fortis.general.presentation import (
    SegmentChange,
    changes_from_loci,
    format_derivation,
)
from src.fortis.inventories.inventories import Inventories
from src.fortis.rules.apply import RuleStep, apply_rules_step_by_step
from src.fortis.transcription.parsing import string_to_sequence


def main() -> None:
    """Load inventories, run derivations for all words, and print results."""
    inventories = Inventories.load()
    print(f"Loaded {len(inventories.features)} features")
    print(f"Loaded {len(inventories.letters)} letters")
    print(f"Loaded {len(inventories.rules)} rules")
    print(f"Loaded {len(inventories.words)} words")
    print()

    for ipa, word in inventories.words.items():
        sequence = string_to_sequence(ipa, inventories)
        steps = apply_rules_step_by_step(sequence, inventories.rules.sorted_rules)

        # Filter to only steps that caused a change
        changed_steps: list[tuple[RuleStep, list[SegmentChange]]] = []
        for step in steps:
            if step.applied:
                changes = changes_from_loci(step.applied)
                if changes:
                    changed_steps.append((step, changes))

        output = format_derivation(ipa, word.gloss, changed_steps, inventories)
        print(output)
        print()


if __name__ == "__main__":
    main()

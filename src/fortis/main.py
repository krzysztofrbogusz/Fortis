"""Main entry point for the Fortis phonology engine.

Loads all inventories, processes every word through all phonological
rules, and prints a step-by-step derivation table showing which rules
applied and what changed at each stage.
"""

from src.fortis.general.presentation import present_sequence
from src.fortis.imports.inventories import Inventories
from src.fortis.transcription.parsing import string_to_sequence
from src.fortis.transcription.rendering import sequence_to_string


def main() -> None:
    """Load inventories, run derivations for all words, and print results."""
    inventories = Inventories.load()
    print(f"Loaded {len(inventories.features)} features")
    print(f"Loaded {len(inventories.letters)} letters")
    print(f"Loaded {len(inventories.words)} words")
    print()
    word = "xenti"
    sequence = string_to_sequence(word, inventories)
    print(present_sequence(sequence, inventories.features))
    string = sequence_to_string(sequence, inventories)
    print(string)


if __name__ == "__main__":
    main()

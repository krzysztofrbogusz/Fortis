from src.fortis.models.inventories import Inventories
from src.fortis.parsing.transcription import string_to_sequence


def main():
    """Main entry point for the project."""
    inventories = Inventories.load()
    print(f"Loaded {len(inventories.features)} features")
    print(f"Loaded {len(inventories.letters)} letters")

    sequence = string_to_sequence("ˈɣʷet͡s.roː", inventories)
    for segment in sequence:
        print(segment)
        print(" ")
    print(sequence.present(inventories.features))
    sequence = string_to_sequence("ˈbʱleɣʷ.moː", inventories)
    print(sequence.present(inventories.features))


if __name__ == "__main__":
    main()

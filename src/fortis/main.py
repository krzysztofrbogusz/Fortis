from src.fortis.models.inventories import Inventories


def main():
    """Main entry point for the project."""
    result = Inventories.load()
    if result.is_err():
        for error in result.unwrap_err():
            print(f"Error: {error}")
        return
    inventories = result.unwrap()
    print(f"Loaded {len(inventories.features)} features")
    print(f"Loaded {len(inventories.letters)} letters")


if __name__ == "__main__":
    main()

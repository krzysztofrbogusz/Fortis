import unicodedata


def safe_int(input: str) -> int | None:
    """Check if a string can be safely converted to a string.

    Returns an int on success or None if it cannot.
    """
    try:
        return int(input)
    except Exception:
        return None


def is_combining(ch: str) -> bool:
    """Return True if `ch` is a combining mark (nonspacing, spacing, or enclosing)."""
    return unicodedata.category(ch).startswith("M")


def present_symbol(symbol: str) -> str:
    """Return a str with the ◌ if the first character is combining, otherwise return character."""
    if len(symbol) == 1 and is_combining(symbol):
        return "◌" + symbol
    else:
        return symbol

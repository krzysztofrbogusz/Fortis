from collections import UserDict
from dataclasses import dataclass
from pathlib import Path

from src.fortis.general.file_handling import load_toml_file
from src.fortis.result import Err, Ok, Result


@dataclass
class WordDefinition:
    """A word with its IPA transcription and optional gloss.

    Attributes:
        ipa: The IPA transcription string.
        gloss: An optional gloss or translation.
    """

    ipa: str
    gloss: str = ""


class WordInventory(UserDict[str, WordDefinition]):
    """Words keyed by their IPA form, loaded from TOML.

    The key is the IPA string itself (same as ``Word.ipa``).
    """

    @classmethod
    def load(cls, path: Path) -> Result[WordInventory, list[str]]:
        """Load words from a TOML file.

        Args:
            path: Path to the TOML file.
        """
        data_result = load_toml_file(path)
        if data_result.is_err():
            return Err([data_result.unwrap_err()])

        data = data_result.unwrap()
        words: dict[str, WordDefinition] = {}
        error_list: list[str] = []

        for key, value in data.items():
            if not isinstance(value, str):
                error_list.append(f"Word '{key}' must be a simple string value, got {type(value).__name__}")
                continue
            words[key] = WordDefinition(ipa=key, gloss=value)

        if error_list:
            return Err(error_list)

        inv = cls(words)
        check_result = inv.validate()
        if check_result.is_err():
            return Err(check_result.unwrap_err())

        return Ok(inv)

    def validate(self) -> Result[None, list[str]]:
        """Check for cross-word consistency issues."""
        return Ok(None)

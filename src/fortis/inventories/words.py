"""WordInventory — load word list from TOML.

Each entry is a simple key-value pair where the key is the IPA
transcription and the value is an optional gloss::

    "xenti" = "into"
    "kʲm̩tom" = "hundred"
    "ɣʷeroː" = ""

The gloss may be an empty string.
"""

from __future__ import annotations

from collections import UserDict
from dataclasses import dataclass
from pathlib import Path

from src.fortis.general.file_handling import load_toml_file
from src.fortis.result import Err, Ok, Result


@dataclass
class Word:
    """A word with its IPA transcription and optional gloss.

    Attributes:
        ipa: The IPA transcription string.
        gloss: An optional gloss or translation.
    """

    ipa: str
    gloss: str = ""


class WordInventory(UserDict[str, Word]):
    """Words keyed by their IPA form, loaded from TOML.

    The key is the IPA string itself (same as ``Word.ipa``).
    """

    @classmethod
    def load(cls, path: Path) -> Result[WordInventory, list[str]]:
        """Load words from a TOML file.

        Args:
            path: Path to the TOML file.

        Returns:
            Ok(WordInventory) on success, Err(list[str]) with error messages
            on failure.
        """
        data_result = load_toml_file(path)
        if data_result.is_err():
            return Err([data_result.unwrap_err()])

        data = data_result.unwrap()
        words: dict[str, Word] = {}
        error_list: list[str] = []

        for key, value in data.items():
            if isinstance(value, str):
                # Simple format: "xenti" = "language" or "xenti" = ""
                words[key] = Word(ipa=key, gloss=value)
            elif isinstance(value, dict):
                # Rich format: [xenti] ipa = "xenti" gloss = "language"
                ipa = value.get("ipa", key)
                gloss = value.get("gloss", "")
                if not isinstance(ipa, str):
                    error_list.append(f"Word '{key}' has non-string 'ipa' field")
                    continue
                if not isinstance(gloss, str):
                    error_list.append(f"Word '{key}' has non-string 'gloss' field")
                    continue
                words[ipa] = Word(ipa=ipa, gloss=gloss)
            else:
                error_list.append(f"Word '{key}' has unexpected type {type(value).__name__}")

        if error_list:
            return Err(error_list)

        return Ok(cls(words))

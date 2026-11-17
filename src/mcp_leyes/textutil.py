"""Small text helpers shared by the parser, the search and the diffs."""

from __future__ import annotations

import re

# Accent folding that keeps "ñ" (año and ano are different words in Spanish law).
_FOLD = str.maketrans(
    {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ü": "u",
        "à": "a",
        "è": "e",
        "ì": "i",
        "ò": "o",
        "ù": "u",
        "Á": "a",
        "É": "e",
        "Í": "i",
        "Ó": "o",
        "Ú": "u",
        "Ü": "u",
        "Ñ": "ñ",
    }
)

_SPACE = re.compile(r"\s+")


def fold(text: str) -> str:
    """Lowercase and strip Spanish accents, keeping ñ. Length is preserved."""
    return text.lower().translate(_FOLD)


def normalize_space(text: str) -> str:
    return _SPACE.sub(" ", text).strip()


def truncate(text: str, limit: int) -> str:
    """Cut ``text`` at a word boundary near ``limit`` characters, marking the cut."""
    if len(text) <= limit:
        return text
    cut = text.rfind(" ", 0, limit)
    return text[: cut if cut > limit // 2 else limit].rstrip() + " …"

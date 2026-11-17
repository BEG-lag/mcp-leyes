"""Full-text query parsing and matching, accent and case insensitive."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .textutil import fold, normalize_space

_QUOTED = re.compile(r'"([^"]+)"|(\S+)')


class QueryError(ValueError):
    pass


@dataclass(frozen=True)
class Query:
    raw: str
    patterns: tuple[re.Pattern[str], ...]
    excluded: tuple[re.Pattern[str], ...] = ()

    def score(self, folded: str) -> int:
        """Total number of hits, or 0 unless every term matches and no excluded term does."""
        if any(p.search(folded) for p in self.excluded):
            return 0
        total = 0
        for pattern in self.patterns:
            hits = len(pattern.findall(folded))
            if not hits:
                return 0
            total += hits
        return total

    def first_match(self, folded: str) -> re.Match[str] | None:
        found = [m for p in self.patterns if (m := p.search(folded))]
        return min(found, key=lambda m: m.start()) if found else None


def _term_pattern(term: str) -> re.Pattern[str]:
    words = [re.escape(w) for w in fold(term).split()]
    # Prefix match at a word start: "subcontrat" finds "subcontratación".
    return re.compile(r"(?<![\wñ])" + r"\s+".join(words))


def parse_query(text: str) -> Query:
    """Words are ANDed prefixes; "quoted phrases" stay together; -word excludes."""
    raw = normalize_space(text or "")
    if not raw:
        raise QueryError("La búsqueda está vacía. Ejemplo: 'subcontratación', '\"caso fortuito\"'.")
    include: list[re.Pattern[str]] = []
    exclude: list[re.Pattern[str]] = []
    for m in _QUOTED.finditer(raw):
        phrase = m[1] or m[2]
        negative = False
        if m[2] and phrase.startswith("-") and len(phrase) > 1:
            negative, phrase = True, phrase[1:]
        phrase = phrase.strip(".,;:()¿?¡!")
        if len(fold(phrase).strip()) < 2:
            continue
        (exclude if negative else include).append(_term_pattern(phrase))
    if not include:
        raise QueryError("Usa al menos una palabra de 2 letras o más.")
    return Query(raw=raw, patterns=tuple(include), excluded=tuple(exclude))


def snippet(text: str, query: Query, width: int = 260) -> str:
    """A window of ``text`` around the first hit, with the hit in bold."""
    flat = normalize_space(re.sub(r"^\*|\*$", "", text, flags=re.MULTILINE))
    folded = fold(flat)
    m = query.first_match(folded) if len(folded) == len(flat) else None
    if m is None:
        return flat[:width] + (" …" if len(flat) > width else "")
    start = max(0, m.start() - width // 3)
    end = min(len(flat), start + width)
    if start > 0:
        space = flat.find(" ", start)
        start = space + 1 if 0 <= space < m.start() else start
    piece = flat[start:end]
    a, b = m.start() - start, m.end() - start
    highlighted = piece[:a] + "**" + piece[a:b] + "**" + piece[b:]
    return ("… " if start > 0 else "") + highlighted + (" …" if end < len(flat) else "")

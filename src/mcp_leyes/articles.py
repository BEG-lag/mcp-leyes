"""Split a leyes-mx law file into articles and transitorios.

leyes-mx renders every law with the same conventions (see its ``parse.py``):

* YAML front matter, then ``# TITLE`` and the header lines of the source;
* divisions (Libro, Parte, Título, Capítulo, Sección) as headings whose level
  depends on the divisions the law uses;
* every article of the body as a heading: ``##### Artículo 3o. Bis.``,
  ``##### Artículo 15-A.``, ``###### Artículo 21 bis 1.``, ``#### Artículos 135.``;
* editorial notes of the Cámara in italics (``*Párrafo reformado DOF 01-05-2019*``);
* the transitorios of the original text under a ``## TRANSITORIOS`` heading, and
  those of every reform decree under ``## ARTÍCULOS TRANSITORIOS DE DECRETOS DE
  REFORMA``, one ``### DECRETO ...`` heading per decree followed by
  ``*Publicado en el Diario Oficial de la Federación el ...*``. Inside transitorios
  the labels are bold text, not headings.

This module only reads that Markdown; it never guesses structure from prose.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date

import yaml

from .dates import parse_dof_dates, parse_spanish_date
from .textutil import fold, normalize_space

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
ARTICLE_HEADING_RE = re.compile(r"^art[ií]culos?\s+\d", re.IGNORECASE)
TRANSITORIOS_HEADING_RE = re.compile(
    r"^(?:art[ií]culos?\s+)?(?:transitorios?|disposiciones\s+transitorias)\b", re.IGNORECASE
)
REFORM_TRANSITORIOS_RE = re.compile(
    r"^art[ií]culos\s+transitorios\s+de\s+decretos\s+de\s+reforma", re.IGNORECASE
)
PUBLISHED_RE = re.compile(r"publicad[oa]s?\s+en\s+el\s+diario\s+oficial", re.IGNORECASE)
NOTE_RE = re.compile(r"^\*(?!\*)(.+?)\*$")

# Latin suffixes; synonyms used by different laws map to one canonical form so
# that "5 Quintus" and "5 Quinquies" find the same article.
SUFFIX_WORDS = {
    "bis": "bis",
    "ter": "ter",
    "quater": "quater",
    "quintus": "quinquies",
    "quinquies": "quinquies",
    "sextus": "sexies",
    "sexies": "sexies",
    "septimus": "septies",
    "septies": "septies",
    "octavus": "octies",
    "octies": "octies",
    "nonus": "nonies",
    "nonies": "nonies",
    "novies": "nonies",
    "decimus": "decies",
    "decies": "decies",
    "undecies": "undecies",
    "duodecies": "duodecies",
    "terdecies": "terdecies",
    "quaterdecies": "quaterdecies",
    "quindecies": "quindecies",
}

_LABEL_RE = re.compile(r"^(?:art[ií]culos?|arts?)?\.?\s*(\d+)(.*)$", re.IGNORECASE | re.DOTALL)
# An ordinal mark right after the number: 1o., 3º, 2°. With a space before it, a
# lone "o" is a letter suffix instead (the LGTOC has "Artículo 228 o.").
_ORDINAL_RE = re.compile(r"^(?:[oº°ª]|\s+[º°ª])(?![A-Za-zÁÉÍÓÚáéíóúÑñ])\.?")
_RANGE_RE = re.compile(r"^\s*\.?\s*(?:a|al|y)\s+(\d+)\s*(?:[oº°ª](?![A-Za-zñ]))?\.?", re.IGNORECASE)
_TOKEN_SPLIT = re.compile(r"[\s.,;:\-–]+")


class LabelError(ValueError):
    """An article reference could not be parsed."""


@dataclass(frozen=True)
class ArticleRef:
    """An article reference, from a heading or typed by a user."""

    number: int
    suffix: tuple[str, ...] = ()
    last: int | None = None  # "Artículos 133 a 135."
    ignored: str = ""  # trailing text that is not part of the label ("fracción IV")

    @property
    def key(self) -> str:
        return "-".join([str(self.number), *self.suffix])

    @property
    def display(self) -> str:
        parts = [str(self.number)]
        for token in self.suffix:
            parts.append(token.upper() if len(token) == 1 else token.capitalize())
        text = " ".join(parts)
        if self.last is not None:
            text += f" a {self.last}"
        return text


def parse_label(text: str) -> ArticleRef | None:
    """Parse ``Artículo 3o. Bis.``, ``15-A``, ``353-Ñ``, ``29-A Bis``, ``21 bis 1``...

    Returns None when ``text`` does not start with an article number.
    """
    raw = normalize_space(text)
    m = _LABEL_RE.match(raw)
    if not m:
        return None
    number = int(m[1])
    rest = m[2]
    if om := _ORDINAL_RE.match(rest):
        rest = rest[om.end() :]
    last = None
    if rm := _RANGE_RE.match(rest):
        last = int(rm[1])
        rest = rest[rm.end() :]
    suffix: list[str] = []
    ignored = ""
    tokens = [t for t in _TOKEN_SPLIT.split(rest) if t]
    for i, token in enumerate(tokens):
        word = fold(token)
        if word in SUFFIX_WORDS:
            suffix.append(SUFFIX_WORDS[word])
        elif len(word) == 1 and word.isalpha():
            suffix.append(word)
        elif word.isdigit() and suffix and suffix[-1] in SUFFIX_WORDS.values():
            suffix.append(word)  # "bis 1", "Bis 2"
        else:
            ignored = " ".join(tokens[i:])
            break
    return ArticleRef(number=number, suffix=tuple(suffix), last=last, ignored=ignored)


def title_mentions(title: str, number: int) -> bool:
    """Whether a decree title cites article ``number`` ("los artículos 4o. y 27 de ...").

    Only a hint: titles that amend several laws can cite the same number for another law.
    """
    folded = fold(title)
    for m in re.finditer(r"\bart(?:iculos?|s?\.)\s", folded):
        window = folded[m.end() : m.end() + 160].split(";")[0]
        if re.search(rf"(?<![\d.,]){number}(?:o\.?|º)?(?![\d])", window):
            return True
    return False


def parse_user_article(text: str) -> ArticleRef:
    """Parse an article typed by a user; raises LabelError with a helpful message."""
    ref = parse_label(text or "")
    if ref is None:
        raise LabelError(
            f"No reconozco el artículo {text!r}. Escribe el número como aparece en la ley: "
            "'27', '3o. Bis', '15-A', '353-Ñ', '29-A Bis' o '21 bis 1'."
        )
    return ref


# --------------------------------------------------------------------------
# Sections of a law file
# --------------------------------------------------------------------------


@dataclass
class Section:
    """An article (or range of articles) of the body, or a block of transitorios."""

    kind: str  # "article" | "transitorios"
    key: str  # "27", "3-bis", "15-a"; "original" or "decreto:2019-05-01" for transitorios
    label: str  # as written: "Artículo 3o. Bis.", "DECRETO por el que ..."
    number: int | None
    last: int | None
    line_start: int  # 1-based line of the heading
    line_end: int  # 1-based last non-blank line of the section
    text: str  # body without the heading
    digest: str = ""
    note_dates: tuple[date, ...] = ()
    decree_date: date | None = None  # transitorios of a reform decree

    @property
    def repealed(self) -> bool:
        return is_repealed(self.text)


@dataclass
class Heading:
    line: int
    level: int
    text: str


@dataclass
class Anomalies:
    missing: list[int] = field(default_factory=list)
    duplicates: list[str] = field(default_factory=list)
    out_of_order: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return bool(self.missing or self.duplicates or self.out_of_order)

    def describe(self, limit: int = 8) -> str:
        parts = []
        if self.missing:
            shown = ", ".join(map(str, self.missing[:limit]))
            more = f" y {len(self.missing) - limit} más" if len(self.missing) > limit else ""
            parts.append(f"faltan los números {shown}{more}")
        if self.duplicates:
            shown = ", ".join(self.duplicates[:limit])
            more = f" y {len(self.duplicates) - limit} más" if len(self.duplicates) > limit else ""
            parts.append(f"encabezados repetidos: {shown}{more}")
        if self.out_of_order:
            shown = ", ".join(self.out_of_order[:limit])
            more = (
                f" y {len(self.out_of_order) - limit} más" if len(self.out_of_order) > limit else ""
            )
            parts.append(f"fuera de orden: {shown}{more}")
        return "; ".join(parts)

    def to_dict(self) -> dict:
        return {
            "missing": self.missing,
            "duplicates": self.duplicates,
            "out_of_order": self.out_of_order,
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> Anomalies:
        data = data or {}
        return cls(
            missing=list(data.get("missing", [])),
            duplicates=list(data.get("duplicates", [])),
            out_of_order=list(data.get("out_of_order", [])),
        )


@dataclass
class ParsedLaw:
    front_matter: dict
    title: str
    lines: list[str]
    sections: list[Section]
    headings: list[Heading]
    body_end: int  # 1-based line where the transitorios start (len(lines) + 1 if none)

    @property
    def articles(self) -> list[Section]:
        return [s for s in self.sections if s.kind == "article"]

    @property
    def transitorios(self) -> list[Section]:
        return [s for s in self.sections if s.kind == "transitorios"]

    def anomalies(self) -> Anomalies:
        return check_numbering(self.articles)


def digest(text: str) -> str:
    """Fingerprint of an article's text, insensitive to whitespace."""
    return hashlib.sha1(normalize_space(text).encode("utf-8")).hexdigest()[:16]


def is_repealed(text: str) -> bool:
    body = [ln for ln in text.splitlines() if ln.strip() and not NOTE_RE.match(ln.strip())]
    joined = fold(" ".join(body)).strip()
    # "Se deroga.", "Se derogan.", "(Se deroga)", "Derogado."; not "Se derogan las
    # disposiciones que se opongan...", which is a rule, not a repealed article.
    return len(joined) < 60 and joined.lstrip("(").startswith(("se deroga", "derogad"))


def note_dates(text: str) -> tuple[date, ...]:
    """DOF dates cited by the editorial notes of a section (``*Párrafo reformado DOF ...*``)."""
    found: list[date] = []
    for line in text.splitlines():
        m = NOTE_RE.match(line.strip())
        if m and "DOF" in m[1]:
            for day in parse_dof_dates(m[1]):
                if day not in found:
                    found.append(day)
    return tuple(found)


def split_front_matter(text: str) -> tuple[dict, list[str], int]:
    """Return (front matter, all lines, index of the first line after it)."""
    lines = text.split("\n")
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                try:
                    data = yaml.safe_load("\n".join(lines[1:i])) or {}
                except yaml.YAMLError:
                    data = {}
                return (data if isinstance(data, dict) else {}), lines, i + 1
    return {}, lines, 0


def parse_law(text: str) -> ParsedLaw:
    """Split a law file into sections. Line numbers match the file (1-based)."""
    front, lines, start = split_front_matter(text)
    title = str(front.get("title") or "")
    headings: list[Heading] = []
    for i in range(start, len(lines)):
        line = lines[i]
        if not line.startswith("#"):
            continue
        m = HEADING_RE.match(line)
        if m:
            headings.append(Heading(line=i + 1, level=len(m[1]), text=m[2]))
            if not title and len(m[1]) == 1:
                title = m[2]

    body_end = len(lines) + 1
    for h in headings:
        if h.level >= 2 and TRANSITORIOS_HEADING_RE.match(h.text):
            body_end = h.line
            break

    sections: list[Section] = []
    # Body: every article heading runs until the next heading of any level.
    body_headings = [h for h in headings if h.line < body_end]
    for n, h in enumerate(body_headings):
        if h.level < 2 or not ARTICLE_HEADING_RE.match(h.text):
            continue
        ref = parse_label(h.text)
        if ref is None:  # pragma: no cover - guarded by ARTICLE_HEADING_RE
            continue
        stop = body_headings[n + 1].line if n + 1 < len(body_headings) else body_end
        sections.append(_make_section("article", ref.key, h, stop, lines, ref=ref))

    # Transitorios: the original block, then one block per reform decree.
    trans_headings = [h for h in headings if h.line >= body_end]
    in_reforms = False
    decree_dates_seen: dict[str, int] = {}
    for n, h in enumerate(trans_headings):
        stop = trans_headings[n + 1].line if n + 1 < len(trans_headings) else len(lines) + 1
        if REFORM_TRANSITORIOS_RE.match(h.text):
            in_reforms = True
            continue
        if not in_reforms and h.level == 2 and TRANSITORIOS_HEADING_RE.match(h.text):
            if not any(s.key == "original" for s in sections):
                sections.append(_make_section("transitorios", "original", h, stop, lines))
            continue
        if in_reforms and h.level >= 3:
            head = "\n".join(lines[h.line : min(stop - 1, h.line + 6)])
            day = parse_spanish_date(head) if PUBLISHED_RE.search(head) else None
            base = f"decreto:{day.isoformat()}" if day else "decreto:s-f"
            count = decree_dates_seen.get(base, 0) + 1
            decree_dates_seen[base] = count
            key = base if count == 1 else f"{base}#{count}"
            section = _make_section("transitorios", key, h, stop, lines)
            section.decree_date = day
            sections.append(section)
    return ParsedLaw(
        front_matter=front,
        title=title,
        lines=lines,
        sections=sections,
        headings=headings,
        body_end=body_end,
    )


def _make_section(
    kind: str,
    key: str,
    heading: Heading,
    stop: int,
    lines: list[str],
    *,
    ref: ArticleRef | None = None,
) -> Section:
    # lines is 0-based; heading.line is 1-based, so lines[heading.line] is the line after it.
    body = lines[heading.line : stop - 1]
    while body and not body[-1].strip():
        body.pop()
    while body and not body[0].strip():
        body.pop(0)
    end = heading.line
    for i in range(stop - 2, heading.line - 1, -1):
        if lines[i].strip():
            end = i + 1
            break
    text = "\n".join(body)
    return Section(
        kind=kind,
        key=key,
        label=heading.text,
        number=ref.number if ref else None,
        last=ref.last if ref else None,
        line_start=heading.line,
        line_end=max(end, heading.line),
        text=text,
        digest=digest(text),
        note_dates=note_dates(text),
    )


def section_text(lines: list[str], line_start: int, line_end: int) -> str:
    """Text of a section from its line span (heading excluded), as stored in the index."""
    body = lines[line_start:line_end]
    while body and not body[0].strip():
        body.pop(0)
    return "\n".join(body).rstrip()


def check_numbering(articles: list[Section]) -> Anomalies:
    """Same rule as ``leyes validate``: the body numbers 1..N with no gaps or repeats.

    Repealed articles stay in the text ("Se deroga."), so a gap or a repeated
    heading means the source itself is irregular (for example the old Códigos
    de Comercio that type article 291 as "29l").
    """
    result = Anomalies()
    seen: set[str] = set()
    numbers: set[int] = set()
    previous: int | None = None
    for a in articles:
        if a.number is None:
            continue
        if a.key in seen:
            result.duplicates.append(normalize_space(a.label))
        seen.add(a.key)
        if previous is not None and a.number < previous:
            result.out_of_order.append(normalize_space(a.label))
        previous = a.number
        numbers.update(range(a.number, (a.last or a.number) + 1))
    highest = max(numbers, default=0)
    result.missing = [n for n in range(1, highest + 1) if n not in numbers]
    return result

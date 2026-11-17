"""Read the metadata leyes-mx writes in the message of every version commit.

Examples of subjects (one commit per archived version of a law)::

    LFT: reforma DOF 12-06-2015
    LFT: reformas DOF 01-05-2019 a 02-07-2019        (several decrees, one commit)
    CPEUM: 3 decretos de reforma, DOF 02-12-2024     (several decrees, same day)
    LGSM: actualización DOF 26-12-2025               (amounts updated, SCJN, no decree listed)
    LFT: texto vigente al DOF 17-01-2006             (oldest archived version)
    LGAg: publicación original DOF 11-12-2025

The body lists each decree as ``- TITLE (DOF dd-mm-yyyy)`` followed by an
indented link, then ``Texto consolidado: URL`` and ``Copia archivada: URL``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from .dates import parse_dof_dates

_BULLET_DATE = re.compile(r"\(DOF\s+(\d{2}-\d{2}-\d{4})\)\s*$")
_URL = re.compile(r"https?://\S+")


@dataclass
class Decree:
    title: str
    dof_date: date | None
    url: str | None = None

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "dof_date": self.dof_date.isoformat() if self.dof_date else None,
            "url": self.url,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Decree:
        day = data.get("dof_date")
        return cls(
            title=data.get("title", ""),
            dof_date=date.fromisoformat(day) if day else None,
            url=data.get("url"),
        )


@dataclass
class CommitInfo:
    subject: str
    kind: str  # reforma | reformas | actualizacion | texto_vigente | original | otro
    decrees: list[Decree] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    consolidated_url: str | None = None
    archived_url: str | None = None
    first_date: date | None = None  # earliest DOF date the commit covers
    last_date: date | None = None  # latest (the commit date)

    @property
    def grouped(self) -> bool:
        """True when one commit carries several decrees published on different days."""
        days = {d.dof_date for d in self.decrees if d.dof_date}
        return len(days) > 1 or (
            self.first_date is not None
            and self.last_date is not None
            and self.first_date != self.last_date
        )

    def to_dict(self) -> dict:
        return {
            "subject": self.subject,
            "kind": self.kind,
            "decrees": [d.to_dict() for d in self.decrees],
            "notes": self.notes,
            "consolidated_url": self.consolidated_url,
            "archived_url": self.archived_url,
            "first_date": self.first_date.isoformat() if self.first_date else None,
            "last_date": self.last_date.isoformat() if self.last_date else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> CommitInfo:
        def day(key: str) -> date | None:
            return date.fromisoformat(data[key]) if data.get(key) else None

        return cls(
            subject=data.get("subject", ""),
            kind=data.get("kind", "otro"),
            decrees=[Decree.from_dict(d) for d in data.get("decrees", [])],
            notes=list(data.get("notes", [])),
            consolidated_url=data.get("consolidated_url"),
            archived_url=data.get("archived_url"),
            first_date=day("first_date"),
            last_date=day("last_date"),
        )


def _kind(subject: str) -> str:
    s = subject.lower()
    if "decretos de reforma" in s or "reformas dof" in s:
        return "reformas"
    if "reforma dof" in s:
        return "reforma"
    if "actualizaci" in s:
        return "actualizacion"
    if "texto vigente" in s:
        return "texto_vigente"
    if "publicaci" in s and "original" in s:
        return "original"
    return "otro"


def parse_commit_message(message: str) -> CommitInfo:
    lines = message.strip().split("\n")
    subject = lines[0].strip() if lines else ""
    info = CommitInfo(subject=subject, kind=_kind(subject))
    subject_dates = parse_dof_dates(subject)
    current: Decree | None = None
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            info.notes.append(" ".join(paragraph))
            paragraph.clear()

    for raw in lines[1:]:
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            current = None
            continue
        if stripped.startswith("- "):
            flush_paragraph()
            text = stripped[2:].strip()
            m = _BULLET_DATE.search(text)
            if m:
                day = parse_dof_dates(m[1])
                current = Decree(title=text[: m.start()].strip(), dof_date=day[0] if day else None)
            else:
                days = parse_dof_dates(text)
                current = Decree(title=text, dof_date=days[-1] if days else None)
            info.decrees.append(current)
            continue
        if current is not None and line.startswith((" ", "\t")) and _URL.match(stripped):
            current.url = stripped
            continue
        if stripped.lower().startswith("texto consolidado:"):
            flush_paragraph()
            m = _URL.search(stripped)
            info.consolidated_url = m[0] if m else None
            continue
        if stripped.lower().startswith("copia archivada:"):
            flush_paragraph()
            m = _URL.search(stripped)
            info.archived_url = m[0] if m else None
            continue
        if stripped.lower().startswith(("co-authored-by:", "signed-off-by:")):
            continue
        paragraph.append(stripped)
    flush_paragraph()

    days = sorted({d.dof_date for d in info.decrees if d.dof_date} | set(subject_dates))
    if days:
        info.first_date, info.last_date = days[0], days[-1]
    return info

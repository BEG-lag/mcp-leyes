"""SQLite index of the articles of every version, built from the git history.

The texts stay in git. The index only records, for each version of each law,
where every article and every block of transitorios starts and ends, plus a
fingerprint of its text and the DOF dates cited by its editorial notes. That is
enough to answer "which version was in force on this date", "when did this
article change" and "what did this reform touch" without reading every blob,
and it keeps the cache small (a few MB next to a 4 MB clone).
"""

from __future__ import annotations

import json
import sqlite3
import threading
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .articles import Anomalies, ParsedLaw, Section
from .commits import CommitInfo

SCHEMA_VERSION = "1"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS versions (
    id INTEGER PRIMARY KEY,
    slug TEXT NOT NULL,
    commit_sha TEXT NOT NULL,
    blob TEXT,
    dof_date TEXT NOT NULL,
    committed TEXT NOT NULL,
    author TEXT NOT NULL,
    info TEXT NOT NULL,
    front_matter TEXT NOT NULL,
    title TEXT NOT NULL,
    articles INTEGER NOT NULL,
    anomalies TEXT NOT NULL,
    UNIQUE (slug, commit_sha)
);
CREATE INDEX IF NOT EXISTS versions_slug ON versions (slug, dof_date);
CREATE TABLE IF NOT EXISTS sections (
    version_id INTEGER NOT NULL,
    ord INTEGER NOT NULL,
    kind TEXT NOT NULL,
    key TEXT NOT NULL,
    label TEXT NOT NULL,
    number INTEGER,
    last INTEGER,
    line_start INTEGER NOT NULL,
    line_end INTEGER NOT NULL,
    digest TEXT NOT NULL,
    note_dates TEXT NOT NULL,
    decree_date TEXT,
    PRIMARY KEY (version_id, ord)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS sections_key ON sections (version_id, kind, key);
"""


@dataclass
class VersionRow:
    id: int
    slug: str
    commit: str
    blob: str | None
    dof_date: date
    committed: str
    author: str
    info: CommitInfo
    front_matter: dict
    title: str
    articles: int
    anomalies: Anomalies

    @property
    def short(self) -> str:
        return self.commit[:7]


@dataclass
class SectionRow:
    version_id: int
    ord: int
    kind: str
    key: str
    label: str
    number: int | None
    last: int | None
    line_start: int
    line_end: int
    digest: str
    note_dates: tuple[date, ...]
    decree_date: date | None


def _version(row: sqlite3.Row) -> VersionRow:
    return VersionRow(
        id=row["id"],
        slug=row["slug"],
        commit=row["commit_sha"],
        blob=row["blob"],
        dof_date=date.fromisoformat(row["dof_date"]),
        committed=row["committed"],
        author=row["author"],
        info=CommitInfo.from_dict(json.loads(row["info"])),
        front_matter=json.loads(row["front_matter"]),
        title=row["title"],
        articles=row["articles"],
        anomalies=Anomalies.from_dict(json.loads(row["anomalies"])),
    )


def _section(row: sqlite3.Row) -> SectionRow:
    notes = tuple(date.fromisoformat(d) for d in row["note_dates"].split(",") if d)
    return SectionRow(
        version_id=row["version_id"],
        ord=row["ord"],
        kind=row["kind"],
        key=row["key"],
        label=row["label"],
        number=row["number"],
        last=row["last"],
        line_start=row["line_start"],
        line_end=row["line_end"],
        digest=row["digest"],
        note_dates=notes,
        decree_date=date.fromisoformat(row["decree_date"]) if row["decree_date"] else None,
    )


def _jsonable(value: object) -> object:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    return value


class Index:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.RLock()
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = self._open()

    def _open(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=60, check_same_thread=False)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=NORMAL")
        db.executescript(_SCHEMA)
        current = db.execute("SELECT value FROM meta WHERE key='schema'").fetchone()
        if current is None or current["value"] != SCHEMA_VERSION:
            # A different layout (older mcp-leyes): rebuild from git, which is cheap.
            db.executescript("DROP TABLE sections; DROP TABLE versions; DROP TABLE meta;")
            db.executescript(_SCHEMA)
            db.execute("INSERT INTO meta (key, value) VALUES ('schema', ?)", (SCHEMA_VERSION,))
            db.commit()
        return db

    def close(self) -> None:
        with self._lock:
            self._db.close()

    # ------------------------------------------------------------------ meta

    def get_meta(self, key: str) -> str | None:
        with self._lock:
            row = self._db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
            return row["value"] if row else None

    def set_meta(self, **values: str | None) -> None:
        with self._lock:
            for key, value in values.items():
                if value is None:
                    self._db.execute("DELETE FROM meta WHERE key=?", (key,))
                else:
                    self._db.execute(
                        "INSERT INTO meta (key, value) VALUES (?, ?) "
                        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                        (key, value),
                    )
            self._db.commit()

    # ---------------------------------------------------------------- writes

    def known_commits(self) -> set[tuple[str, str]]:
        with self._lock:
            rows = self._db.execute("SELECT slug, commit_sha FROM versions").fetchall()
        return {(r["slug"], r["commit_sha"]) for r in rows}

    def add_version(
        self,
        *,
        slug: str,
        commit: str,
        blob: str | None,
        dof_date: date,
        committed: str,
        author: str,
        info: CommitInfo,
        parsed: ParsedLaw | None,
    ) -> int:
        """Insert one version and its sections (no commit; call :meth:`commit`)."""
        sections: list[Section] = parsed.sections if parsed else []
        front = _jsonable(parsed.front_matter) if parsed else {}
        with self._lock:
            cur = self._db.execute(
                "INSERT OR IGNORE INTO versions (slug, commit_sha, blob, dof_date, committed, "
                "author, info, front_matter, title, articles, anomalies) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    slug,
                    commit,
                    blob,
                    dof_date.isoformat(),
                    committed,
                    author,
                    json.dumps(info.to_dict(), ensure_ascii=False),
                    json.dumps(front, ensure_ascii=False),
                    parsed.title if parsed else "",
                    len(parsed.articles) if parsed else 0,
                    json.dumps(parsed.anomalies().to_dict() if parsed else {}),
                ),
            )
            if cur.rowcount == 0:  # another process indexed it first
                row = self._db.execute(
                    "SELECT id FROM versions WHERE slug=? AND commit_sha=?", (slug, commit)
                ).fetchone()
                return int(row["id"])
            version_id = int(cur.lastrowid or 0)
            self._db.executemany(
                "INSERT INTO sections (version_id, ord, kind, key, label, number, last, "
                "line_start, line_end, digest, note_dates, decree_date) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        version_id,
                        n,
                        s.kind,
                        s.key,
                        s.label,
                        s.number,
                        s.last,
                        s.line_start,
                        s.line_end,
                        s.digest,
                        ",".join(d.isoformat() for d in s.note_dates),
                        s.decree_date.isoformat() if s.decree_date else None,
                    )
                    for n, s in enumerate(sections)
                ],
            )
            return version_id

    def prune(self, keep: set[tuple[str, str]]) -> int:
        """Drop versions whose commit is no longer in the history (a rewritten source)."""
        with self._lock:
            rows = self._db.execute("SELECT id, slug, commit_sha FROM versions").fetchall()
            stale = [r["id"] for r in rows if (r["slug"], r["commit_sha"]) not in keep]
            for version_id in stale:
                self._db.execute("DELETE FROM sections WHERE version_id=?", (version_id,))
                self._db.execute("DELETE FROM versions WHERE id=?", (version_id,))
            return len(stale)

    def commit(self) -> None:
        with self._lock:
            self._db.commit()

    # ----------------------------------------------------------------- reads

    def slugs(self) -> list[str]:
        with self._lock:
            rows = self._db.execute("SELECT DISTINCT slug FROM versions ORDER BY slug").fetchall()
        return [r["slug"] for r in rows]

    def versions(self, slug: str) -> list[VersionRow]:
        """Every version of a law, oldest first (DOF date, then commit order)."""
        with self._lock:
            rows = self._db.execute(
                "SELECT * FROM versions WHERE slug=? ORDER BY dof_date, committed, id", (slug,)
            ).fetchall()
        return [_version(r) for r in rows]

    def version_counts(self) -> dict[str, tuple[int, str, str]]:
        with self._lock:
            rows = self._db.execute(
                "SELECT slug, COUNT(*) AS n, MIN(dof_date) AS first, MAX(dof_date) AS last "
                "FROM versions WHERE blob IS NOT NULL GROUP BY slug"
            ).fetchall()
        return {r["slug"]: (r["n"], r["first"], r["last"]) for r in rows}

    def sections(self, version_id: int, kind: str | None = None) -> list[SectionRow]:
        with self._lock:
            if kind:
                rows = self._db.execute(
                    "SELECT * FROM sections WHERE version_id=? AND kind=? ORDER BY ord",
                    (version_id, kind),
                ).fetchall()
            else:
                rows = self._db.execute(
                    "SELECT * FROM sections WHERE version_id=? ORDER BY ord", (version_id,)
                ).fetchall()
        return [_section(r) for r in rows]

    def find(self, version_id: int, kind: str, key: str) -> list[SectionRow]:
        with self._lock:
            rows = self._db.execute(
                "SELECT * FROM sections WHERE version_id=? AND kind=? AND key=? ORDER BY ord",
                (version_id, kind, key),
            ).fetchall()
        return [_section(r) for r in rows]

    def find_range(self, version_id: int, number: int) -> list[SectionRow]:
        with self._lock:
            rows = self._db.execute(
                "SELECT * FROM sections WHERE version_id=? AND kind='article' AND last IS NOT NULL "
                "AND number<=? AND last>=? ORDER BY ord",
                (version_id, number, number),
            ).fetchall()
        return [_section(r) for r in rows]

    def keys_with_number(self, version_id: int, number: int) -> list[str]:
        with self._lock:
            rows = self._db.execute(
                "SELECT label FROM sections WHERE version_id=? AND kind='article' AND number=? "
                "ORDER BY ord",
                (version_id, number),
            ).fetchall()
        return [r["label"] for r in rows]

    def history_rows(self, slug: str, kind: str, keys: Iterable[str]) -> dict[int, SectionRow]:
        """For each version of ``slug``, the first section with one of ``keys`` (if any)."""
        keys = list(keys)
        marks = ",".join("?" * len(keys))
        with self._lock:
            rows = self._db.execute(
                f"SELECT s.* FROM sections s JOIN versions v ON v.id = s.version_id "
                f"WHERE v.slug=? AND s.kind=? AND s.key IN ({marks}) ORDER BY s.version_id, s.ord",
                (slug, kind, *keys),
            ).fetchall()
        found: dict[int, SectionRow] = {}
        for r in rows:
            found.setdefault(r["version_id"], _section(r))
        return found

    def stats(self) -> dict[str, int]:
        with self._lock:
            versions = self._db.execute("SELECT COUNT(*) AS n FROM versions").fetchone()["n"]
            sections = self._db.execute("SELECT COUNT(*) AS n FROM sections").fetchone()["n"]
        return {"versions": versions, "sections": sections}

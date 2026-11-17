"""The leyes-mx history as a queryable corpus: sync, index and point-in-time reads.

Design:

* **git is the database.** A full bare clone of leyes-mx (about 4 MB) holds all
  375+ versions; each version is a commit dated on its DOF publication. Texts
  are read with ``git cat-file`` from that clone, never copied elsewhere.
* **SQLite is the index.** On first use (and whenever the clone moves), every
  new version is parsed once and the line span, fingerprint and editorial-note
  dates of each article are stored. Queries then touch one or two blobs.
* **Offline after the first sync.** ``git fetch`` runs at most once per
  ``MCP_LEYES_REFRESH_HOURS`` (24 by default). If it fails, the cached clone is
  used and the error is reported in the status, never as a tool failure.
"""

from __future__ import annotations

import bisect
import json
import logging
import re
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import UTC, date, datetime

import yaml

from .articles import (
    ArticleRef,
    LabelError,
    is_repealed,
    parse_law,
    parse_user_article,
    section_text,
    title_mentions,
)
from .commits import CommitInfo, Decree, parse_commit_message
from .config import Settings
from .dates import dmy, today_mx
from .diffing import classify_change
from .gitrepo import BareRepo, GitError, GitMissingError, git_executable
from .index import Index, SectionRow, VersionRow
from .search import Query, parse_query, snippet
from .textutil import fold, normalize_space, truncate

log = logging.getLogger("mcp_leyes")

_LAW_PATH = re.compile(r"^leyes/([A-Za-z0-9_-]+)\.md$")
_ZERO_SHA = "0" * 40
ALIASES = {
    "constitucion": "cpeum",
    "constitucion politica": "cpeum",
    "constitucion federal": "cpeum",
    "carta magna": "cpeum",
    "ley del trabajo": "lft",
    "ley de amparo": "lamp",
    "codigo civil": "ccf",
    "codigo penal": "cpf",
    "codigo fiscal": "cff",
    "ley minera": "lmin",
}


class LeyesError(Exception):
    """A user-facing error: the message is shown to the MCP client as is."""


class NotFoundError(LeyesError):
    pass


# --------------------------------------------------------------------------
# Results
# --------------------------------------------------------------------------


@dataclass
class Law:
    slug: str
    abbreviation: str
    title: str
    group: str
    position: int
    published_dof: date | None
    last_reform_dof: date | None
    index_date: date | None  # last reform per the LeyesBiblio index (data/indice.json)
    articles: int
    versions: int
    first_version: date | None
    last_version: date | None
    reforms_url: str | None
    source_url: str | None


@dataclass
class Pick:
    """The version of a law that applies on a requested date, with its caveats."""

    law: Law
    requested: date
    version: VersionRow
    previous: VersionRow | None
    next: VersionRow | None
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    pending: dict[date, str] = field(default_factory=dict)  # reforms not reflected yet


@dataclass
class ArticleText:
    law: Law
    pick: Pick
    ref: ArticleRef
    section: SectionRow
    text: str
    context: list[str]
    link: str
    duplicates: int = 0  # other headings with the same number in this version
    via_range: bool = False
    since: VersionRow | None = None  # oldest version, back from this one, with the same text
    since_is_oldest: bool = False
    pending_note: str | None = None  # what the next archived version says about this article


@dataclass
class HistoryEvent:
    version: VersionRow
    change: str  # presente | añadido | modificado | derogado | eliminado | sin_cambio
    label: str | None
    digest: str | None
    attributed: list[date] = field(default_factory=list)  # note dates new in this version
    decrees: list[Decree] = field(default_factory=list)
    editorial: str | None = None  # "notas" or "menor" when no reform note explains the change
    mentioned: list[Decree] = field(default_factory=list)  # decree titles citing the number


@dataclass
class History:
    law: Law
    ref: ArticleRef
    events: list[HistoryEvent]
    versions_total: int
    first_version: VersionRow
    earlier_notes: list[date]  # note dates older than the first archived version


@dataclass
class ArticleDiff:
    law: Law
    ref: ArticleRef
    old: ArticleText | None
    new: ArticleText | None
    old_pick: Pick
    new_pick: Pick
    changes_between: list[HistoryEvent]


@dataclass
class ChangedArticle:
    key: str
    label: str
    change: str  # modificado | añadido | eliminado
    old_text: str
    new_text: str
    cites_date: bool  # editorial notes of the new text cite the reform date
    note_dates: list[date]
    editorial: str | None
    line_start: int
    line_end: int


@dataclass
class ReformDiff:
    law: Law
    reform_date: date
    version: VersionRow
    previous: VersionRow
    changed: list[ChangedArticle]
    added_transitorios: list[SectionRow]
    headings_added: list[str]
    headings_removed: list[str]
    matching_decrees: list[Decree]
    listed_decrees: list[dict]  # from data/reformas for that date
    warnings: list[str]


@dataclass
class SearchHit:
    law: Law
    version: VersionRow
    section: SectionRow
    score: int
    snippet: str
    link: str


@dataclass
class SearchResult:
    query: Query
    requested: date
    hits: list[SearchHit]
    total: int
    per_law: dict[str, int]
    scanned_laws: int
    scanned_sections: int
    skipped: list[str]


@dataclass
class ReformEntry:
    number: int | None
    dof_date: date | None
    title: str
    pdf_url: str | None
    status: str
    version: VersionRow | None


@dataclass
class Reforms:
    law: Law
    entries: list[ReformEntry]
    original: dict | None
    since: date | None
    total_listed: int
    versions_without_decree: int
    ref_url: str | None
    warnings: list[str]


@dataclass
class Transitorios:
    law: Law
    pick: Pick
    decree_date: date | None
    blocks: list[tuple[SectionRow, str, str]]  # (section, text, link)
    nearby: list[date]


# --------------------------------------------------------------------------
# Corpus
# --------------------------------------------------------------------------


class Corpus:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.from_env()
        self._lock = threading.RLock()
        self._repo: BareRepo | None = None
        self._index: Index | None = None
        self._laws: dict[str, Law] | None = None
        self._reformas: dict[str, dict | None] = {}
        self._lines: OrderedDict[str, list[str]] = OrderedDict()
        self._folded: OrderedDict[int, list[tuple[SectionRow, str, str]]] = OrderedDict()
        self._cache_lock = threading.Lock()
        self._checked_at = 0.0
        self.last_sync: dict[str, object] = {}

    # ------------------------------------------------------------- lifecycle

    def close(self) -> None:
        with self._lock:
            if self._repo:
                self._repo.close()
            if self._index:
                self._index.close()
            self._repo = None
            self._index = None

    @property
    def repo(self) -> BareRepo:
        self.ensure_ready()
        assert self._repo is not None
        return self._repo

    @property
    def index(self) -> Index:
        self.ensure_ready()
        assert self._index is not None
        return self._index

    def ensure_ready(self) -> None:
        """Clone on first use, fetch at most once per refresh period, keep the index current."""
        if self._index is not None and time.monotonic() - self._checked_at < 60:
            return
        with self._lock:
            if self._index is not None and time.monotonic() - self._checked_at < 60:
                return
            self.sync()

    def sync(self, *, force_fetch: bool = False) -> dict[str, object]:
        """Make sure the clone exists, maybe fetch, and index new versions. Returns a report."""
        with self._lock:
            git_executable()  # raises GitMissingError with install instructions
            settings = self.settings
            if self._index is None:
                self._index = Index(settings.index_path)
            index = self._index
            repo = BareRepo(settings.repo_path)
            report: dict[str, object] = {"source": settings.source, "cache": str(settings.workdir)}
            now = datetime.now(UTC)
            if not repo.exists():
                started = time.perf_counter()
                try:
                    BareRepo.clone(settings.source, settings.repo_path)
                except GitMissingError:
                    raise
                except GitError as exc:
                    raise LeyesError(
                        f"No pude descargar leyes-mx desde {settings.source}: {exc}. "
                        "La primera sincronización necesita conexión; después mcp-leyes "
                        "funciona sin red."
                    ) from exc
                report["cloned_seconds"] = round(time.perf_counter() - started, 2)
                index.set_meta(
                    last_fetch_ok=now.isoformat(),
                    last_fetch_attempt=now.isoformat(),
                    last_fetch_error=None,
                )
            elif force_fetch or self._fetch_due(index, now):
                started = time.perf_counter()
                try:
                    repo.fetch()
                    index.set_meta(
                        last_fetch_ok=now.isoformat(),
                        last_fetch_attempt=now.isoformat(),
                        last_fetch_error=None,
                    )
                    report["fetched_seconds"] = round(time.perf_counter() - started, 2)
                except GitError as exc:
                    log.warning("git fetch failed, using cached data: %s", exc)
                    index.set_meta(last_fetch_attempt=now.isoformat(), last_fetch_error=str(exc))
                    report["fetch_error"] = str(exc)
            if self._repo is None or self._repo.path != repo.path:
                self._repo = repo
            started = time.perf_counter()
            added = self._refresh_index()
            if added:
                report["indexed_versions"] = added
                report["indexed_seconds"] = round(time.perf_counter() - started, 2)
            self._checked_at = time.monotonic()
            report.update(self.status())
            self.last_sync = report
            return report

    def _fetch_due(self, index: Index, now: datetime) -> bool:
        hours = self.settings.refresh_hours
        if hours <= 0:
            return False

        def age(key: str) -> float:
            value = index.get_meta(key)
            if not value:
                return float("inf")
            try:
                return (now - datetime.fromisoformat(value)).total_seconds() / 3600
            except ValueError:
                return float("inf")

        # Daily (by default) after a success; retry hourly after a failure.
        return age("last_fetch_ok") >= hours and age("last_fetch_attempt") >= min(1.0, hours)

    def _refresh_index(self) -> int:
        assert self._repo is not None
        assert self._index is not None
        repo, index = self._repo, self._index
        head = repo.head()
        if index.get_meta("indexed_head") == head:
            if self._laws is None:
                self._load_laws()
            return 0
        known = index.known_commits()
        added = 0
        for commit in reversed(repo.log(["leyes"])):
            info: CommitInfo | None = None
            for path, blob in commit.files.items():
                m = _LAW_PATH.match(path)
                if not m or path.endswith(".reformas.md"):
                    continue
                slug = m[1]
                if (slug, commit.sha) in known:
                    continue
                info = info or parse_commit_message(commit.message)
                if blob == _ZERO_SHA:  # the law file was removed in this commit
                    parsed, blob_id = None, None
                else:
                    parsed, blob_id = parse_law(repo.blob(blob)), blob
                index.add_version(
                    slug=slug,
                    commit=commit.sha,
                    blob=blob_id,
                    dof_date=commit.dof_date,
                    committed=commit.committer_date.isoformat(),
                    author=commit.author,
                    info=info,
                    parsed=parsed,
                )
                added += 1
        catalog = repo.show("HEAD", "catalog.yml")
        indice = repo.show("HEAD", "data/indice.json")
        index.set_meta(
            catalog=catalog or "",
            indice=indice or "",
            indexed_head=head,
            indexed_at=datetime.now(UTC).isoformat(),
        )
        index.commit()
        self._laws = None
        self._reformas.clear()
        with self._cache_lock:
            self._folded.clear()
        self._load_laws()
        return added

    # ------------------------------------------------------------------ laws

    def _load_laws(self) -> None:
        assert self._index is not None
        index = self._index
        try:
            catalog = yaml.safe_load(index.get_meta("catalog") or "") or {}
        except yaml.YAMLError:
            catalog = {}
        try:
            indice = json.loads(index.get_meta("indice") or "{}")
        except json.JSONDecodeError:
            indice = {}
        groups = catalog.get("groups") or {}
        order: dict[str, tuple[int, str]] = {}
        for n, entry in enumerate(catalog.get("laws") or []):
            if isinstance(entry, dict) and entry.get("slug"):
                group = entry.get("group") or ""
                order[str(entry["slug"])] = (n, str(groups.get(group, group)))
        counts = index.version_counts()
        laws: dict[str, Law] = {}
        for slug in index.slugs():
            versions = [v for v in index.versions(slug) if v.blob]
            if not versions:
                continue
            latest = versions[-1]
            fm = latest.front_matter
            position, group = order.get(slug, (10_000 + len(laws), "Otras"))
            n, first, last = counts.get(slug, (len(versions), None, None))
            laws[slug] = Law(
                slug=slug,
                abbreviation=str(fm.get("abbreviation") or slug.upper()),
                title=str(fm.get("title") or latest.title or slug),
                group=group,
                position=position,
                published_dof=_as_date(fm.get("published_dof")),
                last_reform_dof=_as_date(fm.get("last_reform_dof")),
                index_date=_as_date(indice.get(slug)),
                articles=int(fm.get("articles") or latest.articles),
                versions=n,
                first_version=date.fromisoformat(first) if first else None,
                last_version=date.fromisoformat(last) if last else None,
                reforms_url=fm.get("reforms"),
                source_url=fm.get("source"),
            )
        self._laws = dict(sorted(laws.items(), key=lambda kv: kv[1].position))

    def laws(self) -> list[Law]:
        self.ensure_ready()
        if self._laws is None:
            self._load_laws()
        return list((self._laws or {}).values())

    def resolve_law(self, text: str) -> Law:
        laws = {law.slug: law for law in self.laws()}
        query = fold(normalize_space(text or "")).strip(" .")
        if not query:
            raise LeyesError("Indica la ley: abreviatura (LFT, CPEUM) o slug (lft, cpeum).")
        if query in laws:
            return laws[query]
        for law in laws.values():
            if fold(law.abbreviation) == query or fold(law.abbreviation).replace(".", "") == query:
                return law
        alias = ALIASES.get(query)
        if alias and alias in laws:
            return laws[alias]
        if len(query) >= 4:
            matches = [law for law in laws.values() if query in fold(law.title)]
            if len(matches) == 1:
                return matches[0]
            if len(matches) > 1:
                names = "; ".join(f"{m.abbreviation} ({m.title})" for m in matches[:8])
                raise LeyesError(
                    f"'{text}' coincide con varias leyes: {names}. Usa la abreviatura."
                )
        available = ", ".join(law.abbreviation for law in laws.values())
        raise NotFoundError(f"No encontré la ley '{text}'. Disponibles: {available}.")

    def versions(self, law: Law) -> list[VersionRow]:
        return list(self.index.versions(law.slug))

    def reformas_data(self, law: Law) -> dict | None:
        if law.slug not in self._reformas:
            raw = self.repo.show("HEAD", f"data/reformas/{law.slug}.json")
            try:
                self._reformas[law.slug] = json.loads(raw) if raw else None
            except json.JSONDecodeError:
                self._reformas[law.slug] = None
        return self._reformas[law.slug]

    def listed_decrees(self, law: Law) -> list[dict]:
        data = self.reformas_data(law) or {}
        out = []
        for d in data.get("decrees") or []:
            day = _as_date(d.get("dof_date"))
            out.append({**d, "dof_date": day})
        return out

    # ----------------------------------------------------------- versions

    def pick(self, law: Law, requested: date) -> Pick:
        versions = self.versions(law)
        if not versions:
            raise NotFoundError(f"No hay versiones de {law.abbreviation} en el índice.")
        first = versions[0]
        if requested < first.dof_date:
            extra = ""
            if law.published_dof and requested < law.published_dof:
                extra = f" La ley se publicó en el DOF el {dmy(law.published_dof)}."
            raise NotFoundError(
                f"La versión más antigua de {law.abbreviation} en leyes-mx es la del DOF "
                f"{dmy(first.dof_date)}; no hay texto archivado para el {dmy(requested)}.{extra} "
                "El historial solo existe donde el Internet Archive guardó una copia del texto "
                "consolidado."
            )
        dates = [v.dof_date for v in versions]
        i = bisect.bisect_right(dates, requested) - 1
        version = versions[i]
        previous = versions[i - 1] if i > 0 else None
        nxt = versions[i + 1] if i + 1 < len(versions) else None
        pick = Pick(law=law, requested=requested, version=version, previous=previous, next=nxt)
        if version.blob is None:
            raise NotFoundError(
                f"{law.abbreviation} dejó de estar en leyes-mx a partir del DOF "
                f"{dmy(version.dof_date)} ({version.info.subject})."
            )

        # Reforms published after this version and on or before the requested date
        # that have no version of their own (they are inside the next commit).
        pending: dict[date, str] = {}
        if nxt is not None:
            for d in nxt.info.decrees:
                if d.dof_date and version.dof_date < d.dof_date <= requested:
                    pending.setdefault(d.dof_date, d.title)
            first_next = nxt.info.first_date
            if first_next and version.dof_date < first_next <= requested and not pending:
                pending[first_next] = nxt.info.subject
        for d in self.listed_decrees(law):
            day = d.get("dof_date")
            if day and version.dof_date < day <= requested:
                pending.setdefault(day, d.get("title") or "")
        pick.pending = pending
        if pending:
            listed = "; ".join(
                f"DOF {dmy(day)}: {truncate(title, 110)}" for day, title in sorted(pending.items())
            )
            where = (
                f"Su texto aparece en la siguiente versión del archivo, DOF {dmy(nxt.dof_date)}"
                if nxt
                else "Todavía no hay una versión del texto consolidado que las incluya"
            )
            pick.warnings.append(
                f"Entre el DOF {dmy(version.dof_date)} y el {dmy(requested)} se publicaron "
                f"reformas sin versión propia en el archivo ({listed}). {where}; el texto "
                "mostrado NO las refleja."
            )
        if (
            nxt is None
            and law.index_date
            and law.index_date > version.dof_date
            and law.index_date not in pending
        ):
            pick.warnings.append(
                f"El índice de LeyesBiblio registra una reforma del DOF {dmy(law.index_date)} "
                f"que el texto consolidado más reciente (DOF {dmy(version.dof_date)}) aún no "
                "incluye."
            )
        if requested > today_mx():
            pick.notes.append("La fecha es futura: se usa la versión más reciente disponible.")
        if version.info.grouped:
            days = sorted({d.dof_date for d in version.info.decrees if d.dof_date})
            span = (
                f"entre el DOF {dmy(days[0])} y el {dmy(days[-1])}"
                if days
                else f"hasta el DOF {dmy(version.dof_date)}"
            )
            pick.notes.append(
                f"Esta versión agrupa {len(version.info.decrees) or 'varias'} reformas publicadas "
                f"{span}: no hay copia archivada intermedia, así que el commit lleva la fecha "
                "de la última."
            )
        if version.anomalies:
            pick.notes.append(
                "Esta versión archivada tiene irregularidades de numeración que vienen de la "
                f"fuente, no del procesamiento: {version.anomalies.describe(5)}."
            )
        return pick

    def version_for_reform(self, law: Law, reform_date: date) -> tuple[VersionRow, VersionRow]:
        versions = self.versions(law)
        candidates = [v for v in versions if v.dof_date >= reform_date]
        if not candidates:
            latest = versions[-1]
            raise NotFoundError(
                f"No hay versión de {law.abbreviation} posterior al DOF {dmy(reform_date)}; la "
                f"más reciente es la del DOF {dmy(latest.dof_date)}."
            )
        version = candidates[0]
        i = versions.index(version)
        if i == 0:
            raise NotFoundError(
                f"La reforma del DOF {dmy(reform_date)} cae en la versión más antigua de "
                f"{law.abbreviation} en el archivo (DOF {dmy(version.dof_date)}); no hay una "
                "versión anterior con qué compararla."
            )
        previous = versions[i - 1]
        covers = (
            version.dof_date == reform_date
            or any(d.dof_date == reform_date for d in version.info.decrees)
            or any(d.get("dof_date") == reform_date for d in self.listed_decrees(law))
        )
        if not covers:
            near = sorted(
                {v.dof_date for v in versions}
                | {d["dof_date"] for d in self.listed_decrees(law) if d.get("dof_date")},
                key=lambda d: abs((d - reform_date).days),
            )[:5]
            raise NotFoundError(
                f"No encontré una reforma de {law.abbreviation} publicada el DOF "
                f"{dmy(reform_date)}. Fechas cercanas con reforma o versión: "
                + ", ".join(dmy(d) for d in sorted(near))
                + ". Consulta `reforms` para la lista completa."
            )
        return version, previous

    # ------------------------------------------------------------- texts

    def lines(self, blob: str) -> list[str]:
        with self._cache_lock:
            cached = self._lines.get(blob)
            if cached is not None:
                self._lines.move_to_end(blob)
                return cached
        text = self.repo.blob(blob)
        lines = text.split("\n")
        with self._cache_lock:
            self._lines[blob] = lines
            while len(self._lines) > 48:
                self._lines.popitem(last=False)
        return lines

    def file_text(self, version: VersionRow) -> str:
        assert version.blob
        return "\n".join(self.lines(version.blob))

    def link(self, version: VersionRow, start: int | None = None, end: int | None = None) -> str:
        url = f"{self.settings.web_url}/blob/{version.commit}/leyes/{version.slug}.md"
        if start:
            url += f"?plain=1#L{start}" + (f"-L{end}" if end and end != start else "")
        return url

    def commit_link(self, version: VersionRow) -> str:
        return f"{self.settings.web_url}/commit/{version.commit}"

    def _lookup(self, version: VersionRow, ref: ArticleRef) -> tuple[list[SectionRow], bool]:
        rows = self.index.find(version.id, "article", ref.key)
        if rows:
            return rows, False
        if not ref.suffix:
            ranged = self.index.find_range(version.id, ref.number)
            if ranged:
                return ranged, True
        return [], False

    def _article(self, law: Law, pick: Pick, ref: ArticleRef) -> ArticleText | None:
        version = pick.version
        rows, via_range = self._lookup(version, ref)
        if not rows:
            return None
        section = rows[0]
        assert version.blob
        lines = self.lines(version.blob)
        text = section_text(lines, section.line_start, section.line_end)
        return ArticleText(
            law=law,
            pick=pick,
            ref=ref,
            section=section,
            text=text,
            context=_context(lines, section.line_start),
            link=self.link(version, section.line_start, section.line_end),
            duplicates=len(rows) - 1,
            via_range=via_range,
        )

    def article(self, law_text: str, article: str, requested: date) -> ArticleText:
        law = self.resolve_law(law_text)
        ref = _parse_ref(article)
        pick = self.pick(law, requested)
        found = self._article(law, pick, ref)
        if found is None:
            raise NotFoundError(self._not_found_message(law, pick, ref))
        # Walk back while the text is the same, to report the version that produced it.
        history = self.index.history_rows(law.slug, "article", [found.section.key])
        versions = self.versions(law)
        idx = next(i for i, v in enumerate(versions) if v.id == pick.version.id)
        since = pick.version
        for v in reversed(versions[:idx]):
            row = history.get(v.id)
            if row is None or row.digest != found.section.digest:
                break
            since = v
        found.since = since
        found.since_is_oldest = since.id == versions[0].id
        found.pending_note = self._pending_note(found, history)
        return found

    def _pending_note(self, found: ArticleText, history: dict[int, SectionRow]) -> str | None:
        """Does the next archived version change this article, and can the notes say when?"""
        pick = found.pick
        if not pick.pending or pick.next is None:
            return None
        nxt = history.get(pick.next.id)
        when = f"DOF {dmy(pick.next.dof_date)}"
        if nxt is not None and nxt.digest == found.section.digest:
            return (
                f"En la siguiente versión archivada ({when}) este artículo no cambia: esas "
                "reformas no lo modificaron."
            )
        cited = sorted(d for d in (nxt.note_dates if nxt else ()) if d in pick.pending)
        if cited:
            return (
                f"En la siguiente versión archivada ({when}) este artículo sí cambia y su nota "
                "editorial cita la reforma del DOF "
                + ", ".join(dmy(d) for d in cited)
                + f", publicada antes del {dmy(pick.requested)}: el texto mostrado está "
                "desactualizado para esa fecha. Usa diff_article o la fecha "
                f"{pick.next.dof_date.isoformat()} para ver el cambio."
            )
        return (
            f"En la siguiente versión archivada ({when}) este artículo cambia, pero el archivo no "
            "permite saber si ese cambio ya estaba publicado en la fecha pedida."
        )

    def _not_found_message(self, law: Law, pick: Pick, ref: ArticleRef) -> str:
        version = pick.version
        msg = (
            f"{law.abbreviation} no tiene el artículo {ref.display} en la versión del DOF "
            f"{dmy(version.dof_date)} (aplicable al {dmy(pick.requested)})."
        )
        same_number = self.index.keys_with_number(version.id, ref.number)
        if same_number:
            msg += " Con ese número existen: " + ", ".join(same_number[:12]) + "."
        rows = self.index.history_rows(law.slug, "article", [ref.key])
        if rows:
            by_id = {v.id: v for v in self.versions(law)}
            days = sorted(by_id[i].dof_date for i in rows if i in by_id)
            msg += (
                f" El artículo {ref.display} sí aparece en versiones del DOF {dmy(days[0])} al "
                f"{dmy(days[-1])}."
            )
        if version.anomalies:
            msg += (
                " Ojo: esta versión archivada tiene irregularidades de numeración en la fuente ("
                + version.anomalies.describe(4)
                + ")."
            )
        return msg

    # ------------------------------------------------------------ history

    def history(self, law_text: str, article: str) -> History:
        law = self.resolve_law(law_text)
        ref = _parse_ref(article)
        versions = self.versions(law)
        rows = self.index.history_rows(law.slug, "article", [ref.key])
        if not ref.suffix:
            for v in versions:
                if v.id not in rows and v.blob:
                    ranged = self.index.find_range(v.id, ref.number)
                    if ranged:
                        rows[v.id] = ranged[0]
        if not rows:
            latest = versions[-1]
            pick = Pick(
                law=law, requested=latest.dof_date, version=latest, previous=None, next=None
            )
            raise NotFoundError(self._not_found_message(law, pick, ref))
        events: list[HistoryEvent] = []
        prev_row: SectionRow | None = None
        prev_version: VersionRow | None = None
        repealed_before = False
        for n, v in enumerate(versions):
            row = rows.get(v.id)
            if n == 0:
                change = "presente" if row else "ausente"
            elif row is None and prev_row is None:
                change = "ausente"
            elif row is None:
                change = "eliminado"
            elif prev_row is None:
                change = "añadido"
            elif row.digest == prev_row.digest:
                change = "sin_cambio"
            else:
                change = "modificado"
            if change in {"presente", "añadido", "modificado"}:
                repealed = bool(row and v.blob and self._is_repealed(v, row))
            elif change in {"eliminado", "ausente"}:
                repealed = False
            else:
                repealed = repealed_before
            if change == "modificado" and repealed and not repealed_before:
                change = "derogado"
            attributed: list[date] = []
            if row and change in {"añadido", "modificado", "derogado"} and prev_version:
                old_notes = set(prev_row.note_dates) if prev_row else set()
                attributed = sorted(
                    d
                    for d in row.note_dates
                    if d not in old_notes and prev_version.dof_date < d <= v.dof_date
                )
            editorial = None
            if change == "modificado" and not attributed and prev_row and prev_version:
                editorial = classify_change(
                    self._text(prev_version, prev_row),
                    self._text(v, row),  # type: ignore[arg-type]
                )
            mentioned = []
            if change in {"añadido", "modificado", "derogado"} and not attributed and not editorial:
                mentioned = [d for d in v.info.decrees if title_mentions(d.title, ref.number)]
            events.append(
                HistoryEvent(
                    version=v,
                    change=change,
                    label=row.label if row else None,
                    digest=row.digest if row else None,
                    attributed=attributed,
                    decrees=v.info.decrees,
                    editorial=editorial,
                    mentioned=mentioned,
                )
            )
            prev_row, prev_version = row, v
            repealed_before = repealed
        first_row = next((rows[v.id] for v in versions if v.id in rows), None)
        earlier = sorted(
            d for d in (first_row.note_dates if first_row else ()) if d < versions[0].dof_date
        )
        return History(
            law=law,
            ref=ref,
            events=events,
            versions_total=len(versions),
            first_version=versions[0],
            earlier_notes=earlier,
        )

    def _text(self, version: VersionRow, row: SectionRow) -> str:
        assert version.blob
        return section_text(self.lines(version.blob), row.line_start, row.line_end)

    def _is_repealed(self, version: VersionRow, row: SectionRow) -> bool:
        return is_repealed(self._text(version, row))

    # -------------------------------------------------------------- diffs

    def diff_article(
        self, law_text: str, article: str, date_from: date, date_to: date
    ) -> ArticleDiff:
        law = self.resolve_law(law_text)
        ref = _parse_ref(article)
        if date_from > date_to:
            date_from, date_to = date_to, date_from
        old_pick = self.pick(law, date_from)
        new_pick = self.pick(law, date_to)
        old = self._article(law, old_pick, ref)
        new = self._article(law, new_pick, ref)
        if old is None and new is None:
            raise NotFoundError(self._not_found_message(law, new_pick, ref))
        between: list[HistoryEvent] = []
        if old_pick.version.id != new_pick.version.id:
            history = self.history(law.slug, article)
            between = [
                e
                for e in history.events
                if old_pick.version.dof_date < e.version.dof_date <= new_pick.version.dof_date
                and e.change not in {"sin_cambio", "ausente"}
            ]
        return ArticleDiff(
            law=law,
            ref=ref,
            old=old,
            new=new,
            old_pick=old_pick,
            new_pick=new_pick,
            changes_between=between,
        )

    def diff_reform(self, law_text: str, reform_date: date) -> ReformDiff:
        law = self.resolve_law(law_text)
        version, previous = self.version_for_reform(law, reform_date)
        assert version.blob
        assert previous.blob
        new_lines = self.lines(version.blob)
        old_lines = self.lines(previous.blob)
        new_sections = self.index.sections(version.id)
        old_sections = self.index.sections(previous.id)
        old_articles = {s.key: s for s in old_sections if s.kind == "article"}
        new_articles = {s.key: s for s in new_sections if s.kind == "article"}
        changed: list[ChangedArticle] = []
        for key, s in new_articles.items():
            o = old_articles.get(key)
            if o is not None and o.digest == s.digest:
                continue
            new_text = section_text(new_lines, s.line_start, s.line_end)
            old_text = section_text(old_lines, o.line_start, o.line_end) if o else ""
            changed.append(
                ChangedArticle(
                    key=key,
                    label=normalize_space(s.label),
                    change="modificado" if o else "añadido",
                    old_text=old_text,
                    new_text=new_text,
                    cites_date=reform_date in s.note_dates,
                    note_dates=list(s.note_dates),
                    editorial=(
                        classify_change(old_text, new_text)
                        if o is not None
                        and not any(
                            previous.dof_date < d <= version.dof_date and d not in o.note_dates
                            for d in s.note_dates
                        )
                        else None
                    ),
                    line_start=s.line_start,
                    line_end=s.line_end,
                )
            )
        for key, o in old_articles.items():
            if key not in new_articles:
                changed.append(
                    ChangedArticle(
                        key=key,
                        label=normalize_space(o.label),
                        change="eliminado",
                        old_text=section_text(old_lines, o.line_start, o.line_end),
                        new_text="",
                        cites_date=False,
                        note_dates=[],
                        editorial=None,
                        line_start=o.line_start,
                        line_end=o.line_end,
                    )
                )
        old_trans = {s.key for s in old_sections if s.kind == "transitorios"}
        added_trans = [
            s for s in new_sections if s.kind == "transitorios" and s.key not in old_trans
        ]
        old_heads = _division_headings(old_lines)
        new_heads = _division_headings(new_lines)
        headings_added = [h for h in new_heads if h not in old_heads]
        headings_removed = [h for h in old_heads if h not in new_heads]
        listed = [d for d in self.listed_decrees(law) if d.get("dof_date") == reform_date]
        matching = [d for d in version.info.decrees if d.dof_date == reform_date]
        warnings: list[str] = []
        if version.info.grouped or version.dof_date != reform_date:
            others = sorted(
                {
                    d.dof_date
                    for d in version.info.decrees
                    if d.dof_date and d.dof_date != reform_date
                }
            )
            other_text = (
                " Los otros decretos de esa versión son del DOF "
                + ", ".join(dmy(d) for d in others)
                + "."
                if others
                else ""
            )
            warnings.append(
                f"No hay copia archivada justo después del DOF {dmy(reform_date)}: esta "
                f"comparación es entre las versiones DOF {dmy(previous.dof_date)} y DOF "
                f"{dmy(version.dof_date)}, así que incluye cambios de todas las reformas "
                f"publicadas en ese lapso.{other_text} Los artículos cuya nota editorial cita el "
                f"DOF {dmy(reform_date)} se listan primero; los demás pueden venir de otra reforma."
            )
        if version.anomalies or previous.anomalies:
            warnings.append(
                "Alguna de las dos versiones tiene irregularidades de numeración en la fuente; "
                "puede haber artículos que parezcan añadidos o eliminados sin serlo."
            )
        changed.sort(key=lambda c: (not c.cites_date, c.editorial is not None, c.line_start))
        return ReformDiff(
            law=law,
            reform_date=reform_date,
            version=version,
            previous=previous,
            changed=changed,
            added_transitorios=added_trans,
            headings_added=headings_added,
            headings_removed=headings_removed,
            matching_decrees=matching,
            listed_decrees=listed,
            warnings=warnings,
        )

    # ------------------------------------------------------------- search

    def _folded_sections(
        self, version: VersionRow, include_transitorios: bool
    ) -> list[tuple[SectionRow, str, str]]:
        cache_key = version.id * 2 + int(include_transitorios)
        with self._cache_lock:
            cached = self._folded.get(cache_key)
            if cached is not None:
                self._folded.move_to_end(cache_key)
                return cached
        assert version.blob
        lines = self.lines(version.blob)
        out = []
        for s in self.index.sections(version.id):
            if s.kind != "article" and not include_transitorios:
                continue
            text = section_text(lines, s.line_start, s.line_end)
            out.append((s, text, fold(s.label + "\n" + text)))
        with self._cache_lock:
            self._folded[cache_key] = out
            while len(self._folded) > 80:
                self._folded.popitem(last=False)
        return out

    def search(
        self,
        query_text: str,
        *,
        law_text: str | None,
        requested: date,
        limit: int,
        include_transitorios: bool = False,
    ) -> SearchResult:
        query = parse_query(query_text)
        laws = [self.resolve_law(law_text)] if law_text else self.laws()
        hits: list[SearchHit] = []
        per_law: dict[str, int] = {}
        skipped: list[str] = []
        scanned = 0
        for law in laws:
            try:
                pick = self.pick(law, requested)
            except NotFoundError:
                skipped.append(f"{law.abbreviation} (desde DOF {dmy(law.first_version)})")
                continue
            for section, text, folded in self._folded_sections(pick.version, include_transitorios):
                scanned += 1
                score = query.score(folded)
                if not score:
                    continue
                per_law[law.abbreviation] = per_law.get(law.abbreviation, 0) + 1
                hits.append(
                    SearchHit(
                        law=law,
                        version=pick.version,
                        section=section,
                        score=score,
                        snippet=snippet(text, query),
                        link=self.link(pick.version, section.line_start, section.line_end),
                    )
                )
        hits.sort(key=lambda h: (-h.score, h.law.position, h.section.ord))
        return SearchResult(
            query=query,
            requested=requested,
            hits=hits[:limit],
            total=len(hits),
            per_law=per_law,
            scanned_laws=len(laws) - len(skipped),
            scanned_sections=scanned,
            skipped=skipped,
        )

    # ------------------------------------------------------------ reforms

    def reforms(self, law_text: str, since: date | None) -> Reforms:
        law = self.resolve_law(law_text)
        data = self.reformas_data(law) or {}
        versions = [v for v in self.versions(law) if v.blob]
        decrees = sorted(
            self.listed_decrees(law),
            key=lambda d: (d.get("dof_date") or date.min, d.get("number") or 0),
        )
        entries: list[ReformEntry] = []
        for d in decrees:
            day = d.get("dof_date")
            if since and day and day < since:
                continue
            status, version = "sin fecha", None
            if day:
                later = [v for v in versions if v.dof_date >= day]
                if day < versions[0].dof_date:
                    status = "anterior al archivo"
                    version = versions[0]
                elif not later:
                    status = "sin versión todavía"
                elif later[0].dof_date == day:
                    status = "versión propia"
                    version = later[0]
                else:
                    status = "agrupada"
                    version = later[0]
            entries.append(
                ReformEntry(
                    number=d.get("number"),
                    dof_date=day,
                    title=d.get("title") or "",
                    pdf_url=d.get("pdf_url"),
                    status=status,
                    version=version,
                )
            )
        listed_dates = {d["dof_date"] for d in decrees if d.get("dof_date")}
        without = [
            v
            for v in versions[1:]
            if v.dof_date not in listed_dates and (not since or v.dof_date >= since)
        ]
        warnings: list[str] = []
        if law.index_date and law.index_date > versions[-1].dof_date:
            warnings.append(
                f"El índice de LeyesBiblio registra una reforma del DOF {dmy(law.index_date)} que "
                f"el texto consolidado más reciente (DOF {dmy(versions[-1].dof_date)}) aún no "
                "incluye."
            )
        return Reforms(
            law=law,
            entries=entries,
            original=data.get("original"),
            since=since,
            total_listed=len(decrees),
            versions_without_decree=len(without),
            ref_url=data.get("ref_url") or law.reforms_url,
            warnings=warnings,
        )

    # -------------------------------------------------------- transitorios

    def transitorios(
        self, law_text: str, decree_date: date | None, requested: date
    ) -> Transitorios:
        law = self.resolve_law(law_text)
        pick = self.pick(law, requested)
        version = pick.version
        sections = self.index.sections(version.id, "transitorios")
        if decree_date is None:
            chosen = [s for s in sections if s.key == "original"]
        else:
            chosen = [s for s in sections if s.decree_date == decree_date]
        nearby: list[date] = []
        if not chosen:
            days = sorted({s.decree_date for s in sections if s.decree_date})
            if decree_date:
                nearby = sorted(days, key=lambda d: abs((d - decree_date).days))[:6]
            else:
                nearby = days[-6:]
        assert version.blob
        lines = self.lines(version.blob)
        blocks = [
            (
                s,
                section_text(lines, s.line_start, s.line_end),
                self.link(version, s.line_start, s.line_end),
            )
            for s in chosen
        ]
        return Transitorios(
            law=law, pick=pick, decree_date=decree_date, blocks=blocks, nearby=sorted(nearby)
        )

    # ---------------------------------------------------------------- misc

    def status(self) -> dict[str, object]:
        index = self._index
        if index is None:
            return {"ready": False}
        stats = index.stats()
        return {
            "ready": True,
            "source": self.settings.source,
            "cache": str(self.settings.workdir),
            "head": (index.get_meta("indexed_head") or "")[:12],
            "last_fetch_ok": index.get_meta("last_fetch_ok"),
            "last_fetch_error": index.get_meta("last_fetch_error"),
            "refresh_hours": self.settings.refresh_hours,
            "versions": stats["versions"],
            "sections": stats["sections"],
        }


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def _as_date(value: object) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def _parse_ref(article: str) -> ArticleRef:
    try:
        return parse_user_article(article)
    except LabelError as exc:
        raise LeyesError(str(exc)) from exc


_HEADING = re.compile(r"^(#{2,6})\s+(.*?)\s*$")
_ARTICLE = re.compile(r"^art[ií]culos?\s+\d", re.IGNORECASE)


def _context(lines: list[str], line: int) -> list[str]:
    """Division headings (Título, Capítulo...) above a 1-based line."""
    stack: list[tuple[int, str]] = []
    for raw in lines[: line - 1]:
        if not raw.startswith("##"):
            continue
        m = _HEADING.match(raw)
        if not m or _ARTICLE.match(m[2]):
            continue
        level = len(m[1])
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, m[2]))
    return [text for _, text in stack]


def _division_headings(lines: list[str]) -> list[str]:
    out = []
    for raw in lines:
        if not raw.startswith("##"):
            continue
        m = _HEADING.match(raw)
        if m and not _ARTICLE.match(m[2]):
            if re.match(r"^(?:art[ií]culos?\s+)?transitori", m[2], re.IGNORECASE):
                break
            out.append(m[2])
    return out


__all__ = [
    "ArticleDiff",
    "ArticleText",
    "Corpus",
    "History",
    "Law",
    "LeyesError",
    "NotFoundError",
    "Pick",
    "ReformDiff",
    "Reforms",
    "SearchResult",
    "Transitorios",
]

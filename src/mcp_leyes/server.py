"""The mcp-leyes MCP server: point-in-time Mexican federal law over the leyes-mx git history."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import threading
import time
from collections.abc import Callable
from typing import Annotated, Literal, TypeVar

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from . import __version__
from .articles import split_front_matter
from .config import Settings
from .corpus import Corpus, LeyesError
from .dates import DateError, dmy, parse_date
from .formatting import (
    render_article,
    render_article_diff,
    render_history,
    render_law_text,
    render_laws,
    render_reform_diff,
    render_reforms,
    render_search,
    render_transitorios,
)
from .gitrepo import GitError
from .index import VersionRow
from .search import QueryError

log = logging.getLogger("mcp_leyes")

INSTRUCTIONS = """\
Point-in-time access to 36 Mexican federal laws (Constitution, codes and federal laws) and
375+ historical versions, from the leyes-mx git repository: every version is a commit dated on
its publication in the Diario Oficial de la Federación (DOF).

Typical flow: list_laws (abbreviations) -> get_article(law, article, date) for the exact text
as it stood on a date -> article_history to see when it changed -> diff_article or diff_reform
to see what a reform did -> transitorios for entry into force. search finds articles by words.
reforms lists the reform decrees of a law.

Laws accept the abbreviation (LFT, CPEUM, LGSM) or slug (lft). Articles accept '27', '3o. Bis',
'15-A', '353-Ñ', '29-A Bis'. Dates accept YYYY-MM-DD, DD-MM-YYYY or 'hoy'/'today'.

Always relay the caveats the tools print: the date of a version is its DOF publication, not its
entry into force; history starts at the oldest archived copy; several reforms between two
archived copies are grouped in one version. Cite the GitHub line link and the DOF date. Texts
are the Cámara de Diputados' consolidated versions: unofficial, only the DOF is authoritative,
and nothing here is legal advice.
"""

READ_ONLY = {"readOnlyHint": True, "idempotentHint": True, "openWorldHint": False}

DiffMode = Literal["words", "unified"]
LawArg = Annotated[
    str,
    Field(description="Law abbreviation or slug, e.g. 'LFT', 'CPEUM', 'lgsm'. See list_laws."),
]
ArticleArg = Annotated[
    str,
    Field(
        description="Article number as written in the law: '27', '1o', '3o. Bis', '15-A', "
        "'353-Ñ', '29-A Bis', '21 bis 1'. Extra words such as 'fracción IV' are ignored."
    ),
]

_corpus: Corpus | None = None
_corpus_lock = threading.Lock()


def get_corpus() -> Corpus:
    """Return the shared corpus, creating it from the environment on first use."""
    global _corpus
    with _corpus_lock:
        if _corpus is None:
            _corpus = Corpus(Settings.from_env())
        return _corpus


def set_corpus(corpus: Corpus | None) -> None:
    """Swap the shared corpus (tests point it at a fixture repository)."""
    global _corpus
    with _corpus_lock:
        if _corpus is not None and _corpus is not corpus:
            _corpus.close()
        _corpus = corpus


T = TypeVar("T")


def _guard[T](fn: Callable[[], T]) -> T:
    try:
        return fn()
    except (LeyesError, DateError, QueryError, GitError) as exc:
        raise ToolError(str(exc)) from exc


def _commit_url(version: VersionRow) -> str:
    return get_corpus().commit_link(version)


mcp = FastMCP(
    name="leyes",
    instructions=INSTRUCTIONS,
    version=__version__,
    website_url="https://github.com/BEG-lag/mcp-leyes",
)


# ---------------------------------------------------------------------- tools


@mcp.tool(annotations=READ_ONLY)
def list_laws() -> str:
    """List the federal laws available: abbreviation, name, last reform (DOF), number of
    articles, number of versions in git and the date of the oldest archived version."""

    def run() -> str:
        corpus = get_corpus()
        return render_laws(corpus.laws(), corpus.status())

    return _guard(run)


@mcp.tool(annotations=READ_ONLY)
def get_article(
    law: LawArg,
    article: ArticleArg,
    date: Annotated[
        str,
        Field(
            description="Date the text should reflect (YYYY-MM-DD, DD-MM-YYYY or 'hoy'). "
            "Returns the latest version published in the DOF on or before that day."
        ),
    ] = "hoy",
) -> str:
    """Exact text of one article as it stood on a date, with the DOF date and commit of the
    version, the decree(s) that version reflects, since when the article has this wording, and
    a link to the exact lines on GitHub at that commit."""

    def run() -> str:
        corpus = get_corpus()
        found = corpus.article(law, article, parse_date(date))
        since_url = corpus.commit_link(found.since) if found.since else None
        return render_article(
            found, commit_url=corpus.commit_link(found.pick.version), since_url=since_url
        )

    return _guard(run)


@mcp.tool(annotations=READ_ONLY)
def article_history(law: LawArg, article: ArticleArg) -> str:
    """Every change to one article across the archived versions: when it was added, modified,
    repealed or removed, with the DOF date, commit and decree of each change. In versions that
    group several reforms, the Cámara's editorial note tells which decree touched it."""

    def run() -> str:
        corpus = get_corpus()
        return render_history(corpus.history(law, article), commit_url=_commit_url)

    return _guard(run)


@mcp.tool(annotations=READ_ONLY)
def diff_article(
    law: LawArg,
    article: ArticleArg,
    date_from: Annotated[str, Field(description="Earlier date (YYYY-MM-DD).")],
    date_to: Annotated[str, Field(description="Later date (YYYY-MM-DD or 'hoy').")] = "hoy",
    mode: Annotated[
        DiffMode,
        Field(
            description="'words': changed paragraphs with [-removed-] {+added+} marks; "
            "'unified': classic unified diff by paragraph."
        ),
    ] = "words",
) -> str:
    """What changed in one article between two dates, as a word-level or unified diff, plus the
    versions in between that touched it."""

    def run() -> str:
        corpus = get_corpus()
        result = corpus.diff_article(law, article, parse_date(date_from), parse_date(date_to))
        return render_article_diff(result, mode=mode, commit_url=_commit_url)

    return _guard(run)


@mcp.tool(annotations=READ_ONLY)
def diff_reform(
    law: LawArg,
    reform_date: Annotated[
        str, Field(description="DOF publication date of the reform decree (YYYY-MM-DD).")
    ],
    mode: Annotated[DiffMode, Field(description="'words' or 'unified'.")] = "words",
    limit: Annotated[
        int, Field(description="Maximum number of article diffs to return.", ge=1, le=100)
    ] = 15,
    offset: Annotated[int, Field(description="Skip this many changed articles.", ge=0)] = 0,
) -> str:
    """What a reform changed in a law: every article modified, added or removed between the
    version before and the version that carries the reform, new transitorios and headings, and
    the diffs. When the archive groups several reforms in one version, articles whose editorial
    note cites this reform date are listed first."""

    def run() -> str:
        corpus = get_corpus()
        result = corpus.diff_reform(law, parse_date(reform_date, default_today=False))
        return render_reform_diff(
            result, mode=mode, limit=limit, offset=offset, commit_url=_commit_url
        )

    return _guard(run)


@mcp.tool(annotations=READ_ONLY)
def search(
    query: Annotated[
        str,
        Field(
            description="Words to find (accent and case insensitive, each word is a prefix, all "
            'must appear in the same article). Use "quotes" for phrases and -word to exclude. '
            "Example: 'subcontrat \"servicios especializados\"'."
        ),
    ],
    law: Annotated[
        str | None, Field(description="Restrict to one law (abbreviation or slug).")
    ] = None,
    date: Annotated[
        str, Field(description="Search the texts as they stood on this date (default: today).")
    ] = "hoy",
    limit: Annotated[int, Field(description="Maximum results.", ge=1, le=100)] = 20,
    include_transitorios: Annotated[
        bool, Field(description="Also search the transitorios of the original text and decrees.")
    ] = False,
) -> str:
    """Full-text search over the articles of every law (or one law) as they stood on a date,
    ranked by number of hits, with a snippet and a link to each article."""

    def run() -> str:
        corpus = get_corpus()
        result = corpus.search(
            query,
            law_text=law,
            requested=parse_date(date),
            limit=limit,
            include_transitorios=include_transitorios,
        )
        return render_search(result)

    return _guard(run)


@mcp.tool(annotations=READ_ONLY)
def reforms(
    law: LawArg,
    since: Annotated[
        str | None, Field(description="Only decrees published on or after this date.")
    ] = None,
    limit: Annotated[int, Field(description="Maximum decrees (newest first).", ge=1, le=400)] = 50,
) -> str:
    """Reform timeline of a law from the LeyesBiblio data in leyes-mx: number, DOF date, title
    and PDF of each decree, and which version in git carries it (own version, grouped with
    others, older than the archive, or not consolidated yet)."""

    def run() -> str:
        corpus = get_corpus()
        start = parse_date(since, default_today=False) if since else None
        return render_reforms(corpus.reforms(law, start), limit=limit, commit_url=_commit_url)

    return _guard(run)


@mcp.tool(annotations=READ_ONLY)
def transitorios(
    law: LawArg,
    decree_date: Annotated[
        str | None,
        Field(
            description="DOF date of the reform decree whose transitorios you want. Omit it for "
            "the transitorios of the original text."
        ),
    ] = None,
    date: Annotated[
        str, Field(description="Read them from the version applicable on this date.")
    ] = "hoy",
    max_chars: Annotated[
        int, Field(description="Maximum characters of text.", ge=1000, le=100_000)
    ] = 20_000,
) -> str:
    """Transitory articles (entry into force, deadlines, repeals) of the original text of a law
    or of one reform decree, as kept at the end of the consolidated text."""

    def run() -> str:
        corpus = get_corpus()
        decree = parse_date(decree_date, default_today=False) if decree_date else None
        result = corpus.transitorios(law, decree, parse_date(date))
        return render_transitorios(
            result, max_chars=max_chars, commit_url=corpus.commit_link(result.pick.version)
        )

    return _guard(run)


# ------------------------------------------------------------------ resources


@mcp.resource(
    "ley://{law}@{date}",
    mime_type="text/markdown",
    description="Full text of a law as it stood on a date (YYYY-MM-DD or 'hoy'), e.g. "
    "ley://lft@2019-01-01. Front matter replaced by a header with the version and caveats.",
)
def law_resource(law: str, date: str) -> str:
    def run() -> str:
        corpus = get_corpus()
        found = corpus.resolve_law(law)
        pick = corpus.pick(found, parse_date(date))
        _, lines, start = split_front_matter(corpus.file_text(pick.version))
        body = "\n".join(lines[start:])
        return render_law_text(pick, body, corpus.commit_link(pick.version))

    return _guard(run)


@mcp.resource(
    "ley://{law}/articulo/{article}@{date}",
    mime_type="text/markdown",
    description="One article as it stood on a date, e.g. ley://cpeum/articulo/27@2013-01-01.",
)
def article_resource(law: str, article: str, date: str) -> str:
    return get_article(law, article, date)


@mcp.resource(
    "leyes://catalogo",
    mime_type="application/json",
    description="The laws available, with abbreviation, slug, dates and number of versions.",
)
def catalog_resource() -> str:
    def run() -> str:
        laws = get_corpus().laws()
        data = [
            {
                "slug": law.slug,
                "abbreviation": law.abbreviation,
                "title": law.title,
                "group": law.group,
                "published_dof": law.published_dof.isoformat() if law.published_dof else None,
                "last_reform_dof": (
                    law.last_reform_dof.isoformat() if law.last_reform_dof else None
                ),
                "articles": law.articles,
                "versions": law.versions,
                "first_version": law.first_version.isoformat() if law.first_version else None,
                "last_version": law.last_version.isoformat() if law.last_version else None,
                "reforms_url": law.reforms_url,
            }
            for law in laws
        ]
        return json.dumps(data, ensure_ascii=False, indent=2)

    return _guard(run)


@mcp.resource(
    "leyes://estado",
    mime_type="application/json",
    description="Sync status: data source, cache directory, indexed commit, last fetch.",
)
def status_resource() -> str:
    def run() -> str:
        corpus = get_corpus()
        corpus.ensure_ready()
        return json.dumps(corpus.status(), ensure_ascii=False, indent=2)

    return _guard(run)


# -------------------------------------------------------------------- prompts


@mcp.prompt
def explain_reform(
    law: Annotated[str, Field(description="Law abbreviation, e.g. LFT.")],
    reform_date: Annotated[str, Field(description="DOF date of the reform, YYYY-MM-DD.")],
    audience: Annotated[
        str, Field(description="Who reads the explanation, e.g. 'abogado', 'empresa', 'público'.")
    ] = "abogado",
    language: Annotated[str, Field(description="Language of the answer, e.g. es or en.")] = "es",
) -> str:
    """Explain what a reform changed in a law, article by article, with entry into force."""
    return f"""Explica qué cambió la reforma publicada en el DOF el {reform_date} en la ley {law}.
Audiencia: {audience}. Idioma de la respuesta: {language}.

Pasos:
1. Llama reforms(law="{law}", since="{reform_date}") para identificar el decreto, su título y
   su PDF.
2. Llama diff_reform(law="{law}", reform_date="{reform_date}"). Si hay más artículos que el límite,
   continúa con offset hasta cubrirlos o resume los restantes por tema.
3. Si la herramienta advierte que la versión agrupa varias reformas, separa lo que la nota
   editorial atribuye a esta fecha de lo que puede venir de otro decreto, y dilo.
4. Llama transitorios(law="{law}", decree_date="{reform_date}") para la entrada en vigor, plazos
   y derogaciones. No infieras fechas que el texto no diga.
5. Para los 3 a 5 artículos más importantes, usa diff_article o get_article para citar el texto
   exacto antes y después.

Entrega:
- Resumen ejecutivo (3 a 5 viñetas).
- Tabla: artículo, qué decía, qué dice, efecto práctico.
- Entrada en vigor y plazos, citando el transitorio exacto.
- Huecos o dudas: lo que el archivo no permite saber (versiones agrupadas, historia incompleta).
- Cita la fecha DOF y el enlace a GitHub de cada texto.
- Cierra con: "Texto consolidado no oficial (leyes-mx). Solo el DOF es fuente auténtica. No es
  asesoría legal; valida con la autoridad competente."
"""


@mcp.prompt
def trace_article(
    law: Annotated[str, Field(description="Law abbreviation, e.g. CPEUM.")],
    article: Annotated[str, Field(description="Article, e.g. 27 or 3o. Bis.")],
    language: Annotated[str, Field(description="Language of the answer, e.g. es or en.")] = "es",
) -> str:
    """Trace how one article evolved across every archived version, reform by reform."""
    return f"""Reconstruye la evolución del artículo {article} de {law}. Idioma: {language}.

1. Llama article_history(law="{law}", article="{article}").
2. Para cada cambio, llama diff_article con la fecha anterior y la del cambio para describir
   qué se añadió, suprimió o reformuló. Usa el decreto que indique la nota editorial.
3. Presenta una línea de tiempo: fecha DOF, decreto, cambio en una frase, enlace.
4. Señala los límites del archivo: el historial empieza en la versión más antigua archivada y
   las notas editoriales pueden citar reformas anteriores que no tienen texto en el archivo.
5. Cierra con: "Texto consolidado no oficial (leyes-mx). Solo el DOF es fuente auténtica. No es
   asesoría legal."
"""


# ----------------------------------------------------------------- entrypoint


def _warm_up() -> None:
    try:
        get_corpus().ensure_ready()
    except Exception as exc:  # logged, the tools report the same error when called
        log.warning("mcp-leyes: initial sync failed: %s", exc)


def _sync_command() -> int:
    corpus = get_corpus()
    started = time.perf_counter()
    try:
        report = corpus.sync(force_fetch=True)
    except (LeyesError, GitError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    report["total_seconds"] = round(time.perf_counter() - started, 2)
    laws = corpus.laws()
    latest = max((law.last_version for law in laws if law.last_version), default=None)
    report["laws"] = len(laws)
    report["latest_version"] = dmy(latest)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="mcp-leyes",
        description="MCP server for Mexican federal law at any point in time (leyes-mx).",
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=["serve", "sync"],
        default="serve",
        help="serve (default): run the MCP server. sync: clone or update the data and exit.",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="stdio (default, for Claude Desktop/Code) or streamable HTTP.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host for --transport http.")
    parser.add_argument("--port", type=int, default=8000, help="Port for --transport http.")
    parser.add_argument("--version", action="version", version=f"mcp-leyes {__version__}")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, stream=sys.stderr, format="%(message)s")
    if args.command == "sync":
        raise SystemExit(_sync_command())
    threading.Thread(target=_warm_up, name="mcp-leyes-sync", daemon=True).start()
    if args.transport == "http":
        mcp.run(transport="http", host=args.host, port=args.port, show_banner=False)
    else:
        mcp.run(show_banner=False)


if __name__ == "__main__":
    main()

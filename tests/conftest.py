"""Shared fixtures: a tiny leyes-mx look-alike git repository, built in the test run.

The fake "Ley Federal de Pruebas" (LFPr) has three versions, written with the same
conventions as leyes-mx (front matter, article headings, editorial notes, transitorios
of the original text and of each decree, bot author, commits dated on the DOF date):

* DOF 15-01-2010: oldest archived text (articles 1o. to 15-A, "Artículos 5 a 14." range).
* DOF 12-06-2015: one decree; amends 2o. and 15-A, adds 3o. Bis, fixes a typo in 4.
* DOF 10-03-2020: groups two decrees (05-11-2019 and 10-03-2020); amends 3o. Bis and
  15-A, adds 15-Ñ, and only touches the editorial notes of 3o.

data/reformas/lfpr.json lists a fifth decree (01-02-2021) that has no version yet, and
data/indice.json says so too. A second law (LOtra) has one version with a repeated
article heading, like the numbering anomalies of some archived sources.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import textwrap
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from fastmcp import Client

from mcp_leyes import server
from mcp_leyes.config import Settings
from mcp_leyes.corpus import Corpus

BOT = ("Diario Oficial (leyes-mx)", "dof@leyes-mx.invalid")
HUMAN = ("Benjamín Esponda García", "272673676+BEG-lag@users.noreply.github.com")


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--live", action="store_true", help="run tests against the real leyes-mx")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--live") or os.environ.get("MCP_LEYES_LIVE") == "1":
        return
    skip = pytest.mark.skip(reason="live test: pass --live or set MCP_LEYES_LIVE=1")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


# --------------------------------------------------------------------------
# Fixture repository
# --------------------------------------------------------------------------

FRONT = """\
---
title: Ley Federal de Pruebas
abbreviation: LFPr
slug: lfpr
published_dof: 2001-03-01
last_reform_dof: {last}
articles: {articles}
source: https://example.invalid/LeyesBiblio/doc/LFPr.doc
reforms: https://example.invalid/LeyesBiblio/ref/lfpr.htm
---

# LEY FEDERAL DE PRUEBAS

Nueva Ley publicada en el Diario Oficial de la Federación el 1o. de marzo de 2001

TEXTO VIGENTE

Última reforma publicada DOF {last_dmy}

## TÍTULO PRIMERO · Disposiciones Generales

### CAPÍTULO I · Del objeto

##### Artículo 1o.

La presente Ley es de orden público y tiene por objeto regular las pruebas.
"""

ART_2_V1 = """\
##### Artículo 2o.

Para los efectos de esta Ley se entiende por prueba el medio de convicción.

*Artículo reformado DOF 30-06-2009*
"""

ART_2_V2 = """\
##### Artículo 2o.

Para los efectos de esta Ley se entiende por prueba todo medio de convicción lícito.

Las pruebas obtenidas con violación de derechos fundamentales son nulas.

*Artículo reformado DOF 30-06-2009, 12-06-2015*
"""

ART_3_V1 = """\
##### Artículo 3o.

Las pruebas se rigen por los principios de legalidad y de buena fe.
"""

ART_3_V3 = """\
##### Artículo 3o.

Las pruebas se rigen por los principios de legalidad y de buena fe.

*Fe de erratas al artículo DOF 20-01-2010*
"""

ART_3BIS_V2 = """\
##### Artículo 3o. Bis.

La autoridad valorará las pruebas de manera libre y lógica.

*Artículo adicionado DOF 12-06-2015*
"""

ART_3BIS_V3 = """\
##### Artículo 3o. Bis.

La autoridad valorará las pruebas conforme a las reglas de la sana crítica.

*Artículo adicionado DOF 12-06-2015. Reformado DOF 05-11-2019*
"""

CHAPTER_2 = """\
### CAPÍTULO II · De las autoridades
"""

ART_4_V1 = """\
##### Artículo 4.

Son autoridades en materia de pruebas la Secretaría y los Tribunales.
"""

ART_4_V2 = """\
##### Artículo 4.

Son autoridades en materia de pruebas la Secretaría y los tribunales.
"""

RANGE_5_14 = """\
##### Artículos 5 a 14.

Se derogan.

*Artículos derogados DOF 30-06-2009*
"""

ART_15 = """\
##### Artículo 15.

La Secretaría llevará un registro de peritos en materia de energía eléctrica.
"""

ART_15A_V1 = """\
##### Artículo 15-A.

El registro de peritos será público.
"""

ART_15A_V2 = """\
##### Artículo 15-A.

El registro de peritos será público y gratuito.

*Artículo reformado DOF 12-06-2015*
"""

ART_15A_V3 = """\
##### Artículo 15-A.

El registro de peritos será público, gratuito y electrónico.

*Párrafo reformado DOF 12-06-2015, 10-03-2020*
"""

ART_15N_V3 = """\
##### Artículo 15-Ñ.

Los peritos registrados podrán actuar en todo el territorio nacional.

*Artículo adicionado DOF 10-03-2020*
"""

TRANSITORIOS = """\
## TRANSITORIOS

**Primero.** La presente Ley entrará en vigor al día siguiente de su publicación en el Diario Oficial de la Federación.

**Segundo.** Se abroga la Ley de Pruebas de 1950.

## ARTÍCULOS TRANSITORIOS DE DECRETOS DE REFORMA

### DECRETO por el que se reforman diversas disposiciones de la Ley Federal de Pruebas.

*Publicado en el Diario Oficial de la Federación el 30 de junio de 2009*

**ARTÍCULO ÚNICO.-** Se reforma el artículo 2o. y se derogan los artículos 5 a 14.

**TRANSITORIO**

**Único.** El presente Decreto entrará en vigor el 1o. de enero de 2010.
"""

DECREE_2015 = """\
### DECRETO por el que se reforman y adicionan los artículos 2o., 3o. Bis y 15-A de la Ley Federal de Pruebas.

*Publicado en el Diario Oficial de la Federación el 12 de junio de 2015*

**Artículo Único.-** Se reforman los artículos 2o. y 15-A, y se adiciona el artículo 3o. Bis.

**Transitorios**

**Primero.** El presente Decreto entrará en vigor a los noventa días naturales siguientes a su publicación.

**Segundo.** La Secretaría emitirá los lineamientos dentro de los ciento ochenta días siguientes.
"""

DECREES_2019_2020 = """\
### DECRETO por el que se reforma el artículo 3o. Bis de la Ley Federal de Pruebas.

*Publicado en el Diario Oficial de la Federación el 5 de noviembre de 2019*

**Único.** Se reforma el artículo 3o. Bis.

**TRANSITORIO**

**Único.** El presente Decreto entrará en vigor el día siguiente al de su publicación.

### DECRETO por el que se reforma el artículo 15-A y se adiciona el artículo 15-Ñ de la Ley Federal de Pruebas.

*Publicado en el Diario Oficial de la Federación el 10 de marzo 2020*

**Único.** Se reforma el artículo 15-A y se adiciona el artículo 15-Ñ.

**Transitorio**

**Único.** Este Decreto entrará en vigor el 1o. de enero de 2021.
"""

V1 = (
    FRONT.format(last="2009-06-30", last_dmy="30-06-2009", articles=7)
    + "\n"
    + "\n".join([ART_2_V1, ART_3_V1, CHAPTER_2, ART_4_V1, RANGE_5_14, ART_15, ART_15A_V1])
    + "\n"
    + TRANSITORIOS
)
V2 = (
    FRONT.format(last="2015-06-12", last_dmy="12-06-2015", articles=8)
    + "\n"
    + "\n".join(
        [ART_2_V2, ART_3_V1, ART_3BIS_V2, CHAPTER_2, ART_4_V2, RANGE_5_14, ART_15, ART_15A_V2]
    )
    + "\n"
    + TRANSITORIOS
    + "\n"
    + DECREE_2015
)
V3 = (
    FRONT.format(last="2020-03-10", last_dmy="10-03-2020", articles=9)
    + "\n"
    + "\n".join(
        [
            ART_2_V2,
            ART_3_V3,
            ART_3BIS_V3,
            CHAPTER_2,
            ART_4_V2,
            RANGE_5_14,
            ART_15,
            ART_15A_V3,
            ART_15N_V3,
        ]
    )
    + "\n"
    + TRANSITORIOS
    + "\n"
    + DECREE_2015
    + "\n"
    + DECREES_2019_2020
)

LOTRA = """\
---
title: Ley de Otra Materia
abbreviation: LOtra
slug: lotra
published_dof: 2018-01-10
last_reform_dof: null
articles: 4
---

# LEY DE OTRA MATERIA

TEXTO VIGENTE

Nueva Ley publicada en el Diario Oficial de la Federación el 10 de enero de 2018

## Artículo 1.

Esta Ley regula la generación de energía eléctrica en pequeña escala.

## Artículo 2.

Se entiende por energía limpia la que no emite gases de efecto invernadero.

## Artículo 2.

Texto repetido en la fuente archivada.

## Artículo 3.

Las tarifas eléctricas se publicarán en el Diario Oficial de la Federación.

## TRANSITORIOS

**Único.** Esta Ley entrará en vigor al día siguiente de su publicación.
"""

CATALOG = """\
# Catálogo de prueba.
groups:
  pruebas: "Leyes de prueba"
  otras: "Otras leyes"

laws:
  - {key: lfpr, slug: lfpr, group: pruebas}
  - {key: lotra, slug: lotra, group: otras}
"""

REFORMAS = {
    "slug": "lfpr",
    "title": "Ley Federal de Pruebas",
    "abbreviation": "LFPr",
    "published_dof": "2001-03-01",
    "ref_url": "https://example.invalid/LeyesBiblio/ref/lfpr.htm",
    "original": {"dof_date": "2001-03-01", "url": "https://example.invalid/ref/lfpr/orig.pdf"},
    "errata": [],
    "decrees": [
        {
            "number": 1,
            "title": "DECRETO por el que se reforman diversas disposiciones de la Ley Federal de "
            "Pruebas.",
            "dof_date": "2009-06-30",
            "pdf_url": "https://example.invalid/ref/lfpr/ref01.pdf",
            "doc_url": None,
        },
        {
            "number": 2,
            "title": "DECRETO por el que se reforman y adicionan los artículos 2o., 3o. Bis y 15-A "
            "de la Ley Federal de Pruebas.",
            "dof_date": "2015-06-12",
            "pdf_url": "https://example.invalid/ref/lfpr/ref02.pdf",
            "doc_url": None,
        },
        {
            "number": 3,
            "title": "DECRETO por el que se reforma el artículo 3o. Bis de la Ley Federal de "
            "Pruebas.",
            "dof_date": "2019-11-05",
            "pdf_url": "https://example.invalid/ref/lfpr/ref03.pdf",
            "doc_url": None,
        },
        {
            "number": 4,
            "title": "DECRETO por el que se reforma el artículo 15-A y se adiciona el artículo "
            "15-Ñ de la Ley Federal de Pruebas.",
            "dof_date": "2020-03-10",
            "pdf_url": "https://example.invalid/ref/lfpr/ref04.pdf",
            "doc_url": None,
        },
        {
            "number": 5,
            "title": "DECRETO por el que se reforma el artículo 1o. de la Ley Federal de Pruebas.",
            "dof_date": "2021-02-01",
            "pdf_url": "https://example.invalid/ref/lfpr/ref05.pdf",
            "doc_url": None,
        },
    ],
}

MSG_V1 = """\
LFPr: texto vigente al DOF 15-01-2010

Texto consolidado más antiguo disponible en el archivo; refleja todas las reformas publicadas hasta el DOF 15-01-2010.

Texto consolidado: https://example.invalid/LeyesBiblio/doc/LFPr.doc
"""

MSG_V2 = """\
LFPr: reforma DOF 12-06-2015

- DECRETO por el que se reforman y adicionan los artículos 2o., 3o. Bis y 15-A de la Ley Federal de Pruebas. (DOF 12-06-2015)
  https://example.invalid/ref/lfpr/ref02.pdf

Texto consolidado: https://example.invalid/LeyesBiblio/doc/LFPr.doc

Copia archivada: https://web.archive.org/web/20150701000000/https://example.invalid/LFPr.doc
"""

MSG_V3 = """\
LFPr: reformas DOF 05-11-2019 a 10-03-2020

No hay una versión archivada entre estos decretos, así que este commit los agrupa.

- DECRETO por el que se reforma el artículo 3o. Bis de la Ley Federal de Pruebas. (DOF 05-11-2019)
  https://example.invalid/ref/lfpr/ref03.pdf

- DECRETO por el que se reforma el artículo 15-A y se adiciona el artículo 15-Ñ de la Ley Federal de Pruebas. (DOF 10-03-2020)
  https://example.invalid/ref/lfpr/ref04.pdf

Texto consolidado: https://example.invalid/LeyesBiblio/doc/LFPr.doc
"""

MSG_LOTRA = """\
LOtra: publicación original DOF 10-01-2018

Texto consolidado: https://example.invalid/LeyesBiblio/doc/LOtra.doc
"""


def git(repo: Path, *args: str, who: tuple[str, str] = BOT, when: str | None = None) -> str:
    env = dict(os.environ)
    env.update(
        {
            "GIT_AUTHOR_NAME": who[0],
            "GIT_AUTHOR_EMAIL": who[1],
            "GIT_COMMITTER_NAME": who[0],
            "GIT_COMMITTER_EMAIL": who[1],
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
        }
    )
    if when:
        env["GIT_AUTHOR_DATE"] = when
        env["GIT_COMMITTER_DATE"] = when
    out = subprocess.run(
        ["git", *args], cwd=repo, env=env, check=True, capture_output=True, text=True
    )
    return out.stdout


def write(repo: Path, path: str, text: str) -> None:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def commit(repo: Path, message: str, when: str, who: tuple[str, str] = BOT) -> str:
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message, who=who, when=when)
    return git(repo, "rev-parse", "HEAD").strip()


def noon(day: str) -> str:
    return f"{day}T12:00:00-06:00"


def build_fixture_repo(repo: Path) -> dict[str, str]:
    """Create the fixture repository; returns the commit of each version."""
    repo.mkdir(parents=True)
    git(repo, "init", "-q", "-b", "main")
    write(repo, "README.md", "# leyes-mx (fixture)\n")
    write(repo, "catalog.yml", CATALOG)
    commits = {"tooling": commit(repo, "chore: scaffold", "2026-11-01T10:00:00-06:00", HUMAN)}
    write(repo, "leyes/lfpr.md", V1)
    commits["v1"] = commit(repo, MSG_V1, noon("2010-01-15"))
    write(repo, "leyes/lfpr.md", V2)
    commits["v2"] = commit(repo, MSG_V2, noon("2015-06-12"))
    write(repo, "leyes/lotra.md", LOTRA)
    commits["lotra"] = commit(repo, MSG_LOTRA, noon("2018-01-10"))
    write(repo, "leyes/lfpr.md", V3)
    commits["v3"] = commit(repo, MSG_V3, noon("2020-03-10"))
    write(repo, "leyes/lfpr.reformas.md", "# Ley Federal de Pruebas: reformas\n")
    write(repo, "data/reformas/lfpr.json", json.dumps(REFORMAS, ensure_ascii=False, indent=1))
    write(repo, "data/indice.json", json.dumps({"lfpr": "2021-02-01", "lotra": "2018-01-10"}))
    commits["data"] = commit(
        repo, "chore(data): reform timelines and index dates", "2026-11-17T08:00:00-06:00"
    )
    write(repo, "README.md", "# leyes-mx (fixture)\n\nDocs.\n")
    commits["docs"] = commit(repo, "docs: readme", "2026-11-17T09:00:00-06:00", HUMAN)
    return commits


@pytest.fixture(scope="session")
def fixture_repo(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, str]]:
    root = tmp_path_factory.mktemp("source") / "leyes-mx"
    commits = build_fixture_repo(root)
    return root, commits


@pytest.fixture
def source_copy(fixture_repo, tmp_path: Path) -> Path:
    """A private copy of the fixture repository that a test may add commits to."""
    root, _ = fixture_repo
    copy = tmp_path / "source" / "leyes-mx"
    shutil.copytree(root, copy)
    return copy


def make_settings(source: Path | str, cache: Path, **kwargs) -> Settings:
    return Settings(cache_dir=cache, source=str(source), **kwargs)


@pytest.fixture(scope="session")
def corpus(fixture_repo, tmp_path_factory) -> Iterator[Corpus]:
    root, _ = fixture_repo
    cache = tmp_path_factory.mktemp("cache")
    c = Corpus(make_settings(root, cache))
    c.sync()
    yield c
    c.close()


@pytest.fixture
async def mcp_client(corpus: Corpus) -> AsyncIterator[Client]:
    server.set_corpus(corpus)
    async with Client(server.mcp) as client:
        yield client
    server._corpus = None  # keep the session corpus open for other tests


def dedent(text: str) -> str:
    return textwrap.dedent(text).lstrip("\n")

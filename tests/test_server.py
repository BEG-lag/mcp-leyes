"""End-to-end through a real MCP client session (in memory, fixture repository)."""

import json

import pytest

from mcp_leyes import server

pytestmark = pytest.mark.anyio

TOOLS = {
    "list_laws",
    "get_article",
    "article_history",
    "diff_article",
    "diff_reform",
    "search",
    "reforms",
    "transitorios",
}
FOOTER = "Solo el DOF es fuente auténtica. No es asesoría legal."


async def call(client, tool: str, **arguments) -> str:
    result = await client.call_tool(tool, arguments)
    assert not result.is_error, result.content
    return result.content[0].text


async def call_error(client, tool: str, **arguments) -> str:
    result = await client.call_tool(tool, arguments, raise_on_error=False)
    assert result.is_error
    return result.content[0].text


async def test_tools_are_listed_as_read_only(mcp_client) -> None:
    tools = {t.name: t for t in await mcp_client.list_tools()}
    assert set(tools) == TOOLS
    for tool in tools.values():
        assert tool.annotations.read_only_hint is True
        assert tool.description


async def test_prompts_and_resources_are_listed(mcp_client) -> None:
    prompts = {p.name for p in await mcp_client.list_prompts()}
    assert prompts == {"explain_reform", "trace_article"}
    templates = {t.uri_template for t in await mcp_client.list_resource_templates()}
    assert templates == {"ley://{law}@{date}", "ley://{law}/articulo/{article}@{date}"}
    resources = {str(r.uri) for r in await mcp_client.list_resources()}
    assert resources == {"leyes://catalogo", "leyes://estado"}


async def test_list_laws(mcp_client) -> None:
    text = await call(mcp_client, "list_laws")
    assert text.startswith("# Leyes federales disponibles")
    assert "2 leyes · 4 versiones en git" in text
    assert "## Leyes de prueba" in text
    assert (
        "| LFPr (`lfpr`) | Ley Federal de Pruebas | 10-03-2020 (índice LeyesBiblio: 01-02-2021, "
        "aún no en el texto) | 9 | 3 | 15-01-2010 |"
    ) in text
    assert "| LOtra (`lotra`) | Ley de Otra Materia | sin reformas | 4 | 1 | 10-01-2018 |" in text
    assert FOOTER in text


async def test_get_article_with_provenance_and_link(mcp_client, fixture_repo) -> None:
    _, commits = fixture_repo
    text = await call(mcp_client, "get_article", law="LFPr", article="3o. Bis", date="2016-01-01")
    assert text.startswith("# LFPr · Artículo 3o. Bis.")
    assert "Texto aplicable al 01-01-2016: versión DOF 12-06-2015" in text
    assert "La autoridad valorará las pruebas de manera libre y lógica." in text
    assert f"https://github.com/BEG-lag/leyes-mx/commit/{commits['v2']}" in text
    assert f"/blob/{commits['v2']}/leyes/lfpr.md?plain=1#L" in text
    assert "DOF 12-06-2015: DECRETO por el que se reforman y adicionan" in text
    assert "La entrada en vigor la fijan los transitorios" in text
    assert FOOTER in text


async def test_get_article_in_grouped_gap_warns(mcp_client) -> None:
    text = await call(mcp_client, "get_article", law="lfpr", article="3 bis", date="01-12-2019")
    assert "**Advertencias**" in text
    assert "NO las refleja" in text
    assert "sí cambia y su nota editorial cita la reforma del DOF 05-11-2019" in text


async def test_get_article_errors_are_tool_errors(mcp_client) -> None:
    assert "más antigua de LFPr" in await call_error(
        mcp_client, "get_article", law="lfpr", article="1", date="2005-01-01"
    )
    assert "No encontré la ley" in await call_error(
        mcp_client, "get_article", law="nada", article="1"
    )
    assert "Fecha no reconocida" in await call_error(
        mcp_client, "get_article", law="lfpr", article="1", date="ayer por la tarde"
    )
    assert "No reconozco el artículo" in await call_error(
        mcp_client, "get_article", law="lfpr", article="primero"
    )


async def test_ignored_words_are_reported(mcp_client) -> None:
    text = await call(mcp_client, "get_article", law="lfpr", article="2o., fracción I")
    assert "Se ignoró «fracción I»" in text


async def test_article_history(mcp_client) -> None:
    text = await call(mcp_client, "article_history", law="lfpr", article="3o bis")
    assert text.startswith("# LFPr · historia del artículo 3 Bis")
    assert "### DOF 12-06-2015 · añadido" in text
    assert "### DOF 10-03-2020 · modificado" in text
    assert "Decreto (según la nota editorial del artículo)" in text
    assert "DOF 05-11-2019: DECRETO por el que se reforma el artículo 3o. Bis" in text
    four = await call(mcp_client, "article_history", law="lfpr", article="4")
    assert "posible corrección editorial" in four


async def test_diff_article_modes(mcp_client) -> None:
    words = await call(
        mcp_client,
        "diff_article",
        law="lfpr",
        article="15-A",
        date_from="2012-01-01",
        date_to="2021-01-01",
    )
    assert "El registro de peritos será público{+, gratuito y electrónico+}." in words
    assert "{+*Párrafo reformado DOF 12-06-2015, 10-03-2020*+}" in words
    assert "**Versiones que cambiaron el artículo en ese lapso**" in words
    unified = await call(
        mcp_client,
        "diff_article",
        law="lfpr",
        article="15-A",
        date_from="2012-01-01",
        date_to="2021-01-01",
        mode="unified",
    )
    assert "```diff" in unified
    assert "-El registro de peritos será público." in unified
    same = await call(
        mcp_client,
        "diff_article",
        law="lfpr",
        article="15",
        date_from="2016-01-01",
        date_to="2016-02-01",
    )
    assert "misma versión del archivo" in same


async def test_diff_reform(mcp_client) -> None:
    text = await call(mcp_client, "diff_reform", law="lfpr", reform_date="2019-11-05", limit=1)
    assert text.startswith("# LFPr · reforma DOF 05-11-2019")
    assert "versión DOF 12-06-2015" in text
    assert "## Artículo 3o. Bis. (modificado; nota cita DOF 05-11-2019)" in text
    assert "Mostrando artículos 1-1 de 4. Usa offset=1" in text
    assert "**Con nota que cita el DOF 05-11-2019 (1):** 3o. Bis." in text
    assert "incluye cambios de todas las reformas" in text


async def test_search(mcp_client) -> None:
    text = await call(mcp_client, "search", query='"energia electrica"')
    assert "2 coincidencia(s) en 2 ley(es)" in text
    assert "**energía eléctrica**" in text
    empty = await call(mcp_client, "search", query="inexistente")
    assert "Sin resultados" in empty
    assert "La búsqueda está vacía" in await call_error(mcp_client, "search", query=" ")


async def test_reforms(mcp_client) -> None:
    text = await call(mcp_client, "reforms", law="lfpr")
    assert "Decretos de reforma listados por LeyesBiblio: 5" in text
    assert "| 5 | 01-02-2021 |" in text
    assert "sin versión todavía" in text
    assert "agrupada en la versión DOF 10-03-2020" in text
    limited = await call(mcp_client, "reforms", law="lfpr", limit=2)
    assert "Mostrando los 2 más recientes de 5" in limited


async def test_transitorios(mcp_client) -> None:
    text = await call(mcp_client, "transitorios", law="lfpr", decree_date="2015-06-12")
    assert text.startswith("# LFPr · transitorios del decreto DOF 12-06-2015")
    assert "noventa días naturales" in text
    original = await call(mcp_client, "transitorios", law="lfpr")
    assert "transitorios del texto original" in original


async def test_resources(mcp_client) -> None:
    (law,) = await mcp_client.read_resource("ley://lfpr@2016-01-01")
    assert law.text.startswith("<!-- mcp-leyes: LFPr, versión DOF 2015-06-12")
    assert "# LEY FEDERAL DE PRUEBAS" in law.text
    assert "title: Ley Federal de Pruebas" not in law.text  # front matter replaced
    (article,) = await mcp_client.read_resource("ley://lfpr/articulo/15-A@hoy")
    assert "público, gratuito y electrónico" in article.text
    (catalog,) = await mcp_client.read_resource("leyes://catalogo")
    data = json.loads(catalog.text)
    assert [d["slug"] for d in data] == ["lfpr", "lotra"]
    assert data[0]["versions"] == 3
    (status,) = await mcp_client.read_resource("leyes://estado")
    assert json.loads(status.text)["versions"] == 4


async def test_prompts(mcp_client) -> None:
    prompt = await mcp_client.get_prompt(
        "explain_reform", {"law": "LFT", "reform_date": "2019-05-01"}
    )
    text = prompt.messages[0].content.text
    assert 'diff_reform(law="LFT", reform_date="2019-05-01")' in text
    assert 'transitorios(law="LFT", decree_date="2019-05-01")' in text
    trace = await mcp_client.get_prompt("trace_article", {"law": "CPEUM", "article": "27"})
    assert 'article_history(law="CPEUM", article="27")' in trace.messages[0].content.text


async def test_missing_git_surfaces_as_tool_error(mcp_client, monkeypatch, tmp_path) -> None:
    from mcp_leyes import gitrepo
    from mcp_leyes.corpus import Corpus

    from .conftest import make_settings

    monkeypatch.setattr(gitrepo.shutil, "which", lambda name: None)
    original = server._corpus
    server._corpus = Corpus(make_settings(tmp_path / "x", tmp_path / "cache"))
    try:
        text = await call_error(mcp_client, "list_laws")
    finally:
        server._corpus = original
    assert "necesita git instalado" in text

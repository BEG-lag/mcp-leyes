"""Dates, commit messages, diffs and search queries."""

from datetime import date

import pytest

from mcp_leyes.commits import parse_commit_message
from mcp_leyes.config import Settings, web_url_for
from mcp_leyes.dates import DateError, dmy, parse_date, parse_dof_dates, parse_spanish_date
from mcp_leyes.diffing import classify_change, unified_diff, word_diff, word_diff_line
from mcp_leyes.search import QueryError, parse_query, snippet
from mcp_leyes.textutil import fold

from .conftest import MSG_V1, MSG_V3

# ------------------------------------------------------------------- dates


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2019-05-01", date(2019, 5, 1)),
        ("01-05-2019", date(2019, 5, 1)),
        ("1/5/2019", date(2019, 5, 1)),
        ("2019-5-1", date(2019, 5, 1)),
    ],
)
def test_parse_date(text: str, expected: date) -> None:
    assert parse_date(text) == expected


def test_parse_date_today_and_errors() -> None:
    assert parse_date("hoy") == parse_date("today")
    with pytest.raises(DateError, match="no reconocida"):
        parse_date("mayo 2019")
    with pytest.raises(DateError, match="inválida"):
        parse_date("2019-02-30")
    with pytest.raises(DateError, match="Falta la fecha"):
        parse_date("", default_today=False)


def test_spanish_and_dof_dates() -> None:
    assert parse_spanish_date("el 1o. de mayo de 2019") == date(2019, 5, 1)
    assert parse_spanish_date("el 13 de marzo 2025") == date(2025, 3, 13)
    assert parse_spanish_date("Publicado el 9 de abril del 2012") == date(2012, 4, 9)
    assert parse_spanish_date("sin fecha") is None
    assert parse_dof_dates("DOF 30-06-2009, 12-06-2015 y 31-02-2020") == [
        date(2009, 6, 30),
        date(2015, 6, 12),
    ]
    assert dmy(date(2019, 5, 1)) == "01-05-2019"


# ------------------------------------------------------------------ commits


def test_grouped_commit_message() -> None:
    info = parse_commit_message(MSG_V3)
    assert info.kind == "reformas"
    assert info.grouped
    assert [d.dof_date for d in info.decrees] == [date(2019, 11, 5), date(2020, 3, 10)]
    assert info.decrees[0].url == "https://example.invalid/ref/lfpr/ref03.pdf"
    assert info.decrees[1].title.startswith("DECRETO por el que se reforma el artículo 15-A")
    assert info.notes == [
        "No hay una versión archivada entre estos decretos, así que este commit los agrupa."
    ]
    assert info.consolidated_url == "https://example.invalid/LeyesBiblio/doc/LFPr.doc"
    assert (info.first_date, info.last_date) == (date(2019, 11, 5), date(2020, 3, 10))


def test_oldest_version_message_and_roundtrip() -> None:
    info = parse_commit_message(MSG_V1)
    assert info.kind == "texto_vigente"
    assert not info.grouped
    assert info.decrees == []
    assert info.notes[0].startswith("Texto consolidado más antiguo")
    assert type(info).from_dict(info.to_dict()) == info


def test_update_without_decree() -> None:
    msg = (
        "LGSM: actualización DOF 26-12-2025\n\n- Cantidades actualizadas por Acuerdo DOF "
        "26-12-2025\n\nTexto consolidado: https://example.invalid/LGSM.doc\n"
    )
    info = parse_commit_message(msg)
    assert info.kind == "actualizacion"
    assert info.decrees[0].dof_date == date(2025, 12, 26)
    assert info.decrees[0].url is None
    assert not info.grouped


def test_same_day_decrees_are_not_grouped() -> None:
    msg = (
        "CPEUM: 3 decretos de reforma, DOF 02-12-2024\n\n"
        "- DECRETO uno. (DOF 02-12-2024)\n  https://x.invalid/1.pdf\n\n"
        "- DECRETO dos. (DOF 02-12-2024)\n  https://x.invalid/2.pdf\n"
    )
    info = parse_commit_message(msg)
    assert info.kind == "reformas"
    assert len(info.decrees) == 2
    assert not info.grouped


# -------------------------------------------------------------------- diffs


def test_word_diff_marks_only_changed_words() -> None:
    old = "El trabajo es un derecho y un deber sociales. No es artículo de comercio."
    new = "El trabajo es un derecho y un deber social. No es artículo de comercio."
    assert word_diff_line(old, new) == (
        "El trabajo es un derecho y un deber [-sociales-] {+social+}. No es artículo de comercio."
    )


def test_word_diff_keeps_dates_whole() -> None:
    assert word_diff_line(
        "*Fracción reformada DOF 30-11-2012*", "*Fracción reformada DOF 01-05-2019*"
    ) == ("*Fracción reformada DOF [-30-11-2012-] {+01-05-2019+}*")


def test_word_diff_pairs_similar_paragraphs_and_elides_the_rest() -> None:
    old = (
        "Primero igual.\n\nIV. Por cada seis días de trabajo deberá disfrutar el operario."
        "\n\nFinal."
    )
    new = (
        "Primero igual.\n\nIV. La jornada será de cuarenta horas.\n\n"
        "Por cada seis días de trabajo las personas deberán disfrutar.\n\nFinal."
    )
    out = word_diff(old, new)
    assert out.startswith("… (1 párrafo sin cambios)")
    assert "{+IV. La jornada será de cuarenta horas.+}" in out
    assert "[-IV.-] Por cada seis días de trabajo" in out
    assert out.endswith("… (1 párrafo sin cambios)")


def test_unified_diff_by_paragraph() -> None:
    out = unified_diff("a\n\nb", "a\n\nc", "antes", "después")
    assert out.splitlines()[:2] == ["--- antes", "+++ después"]
    assert "-b" in out
    assert "+c" in out


def test_classify_change() -> None:
    base = "Las pruebas se rigen por los principios de legalidad."
    assert classify_change(base, base + "\n\n*Fe de erratas DOF 20-01-2010*") == "notas"
    assert classify_change(base, base.replace("rigen", "regirán")) == "menor"
    assert classify_change(base, base + "\n\nNuevo párrafo con reglas.") is None
    longer = base.replace(
        "legalidad", "legalidad, publicidad, contradicción, inmediación y oralidad"
    )
    assert classify_change(base, longer) is None


# ------------------------------------------------------------------- search


def test_query_terms_are_accent_insensitive_prefixes() -> None:
    query = parse_query('subcontrat "servicios especializados" -vivienda')
    text = fold("La SUBCONTRATACIÓN de servicios   especializados está regulada.")
    assert query.score(text) == 2
    assert query.score(fold("Subcontratación de vivienda y servicios especializados")) == 0
    assert query.score(fold("Servicios especializados sin la otra palabra")) == 0
    assert parse_query("energia").score(fold("Energía eléctrica")) == 1
    assert parse_query("año").score(fold("el ano")) == 0  # ñ is kept


def test_query_errors() -> None:
    with pytest.raises(QueryError):
        parse_query("   ")
    with pytest.raises(QueryError):
        parse_query("a -b")


def test_snippet_highlights_first_hit() -> None:
    query = parse_query("energia")
    text = "Inicio. " + "x " * 200 + "La generación de energía eléctrica limpia. " + "y " * 200
    out = snippet(text, query, width=120)
    assert "**energía**" in out
    assert out.startswith("… ")
    assert out.endswith(" …")


# ------------------------------------------------------------------- config


def test_settings_from_env(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MCP_LEYES_CACHE", str(tmp_path / "cache"))
    monkeypatch.setenv("MCP_LEYES_SOURCE", str(tmp_path / "leyes-mx"))
    monkeypatch.setenv("MCP_LEYES_REFRESH_HOURS", "6")
    settings = Settings.from_env()
    assert settings.cache_dir == tmp_path / "cache"
    assert settings.source == str((tmp_path / "leyes-mx").resolve())
    assert settings.refresh_hours == 6
    assert settings.web_url == "https://github.com/BEG-lag/leyes-mx"
    assert settings.repo_path.parent.parent == tmp_path / "cache"
    assert settings.repo_path.parent.name.startswith("leyes-mx-")
    other = Settings(cache_dir=settings.cache_dir, source="https://github.com/a/b.git")
    assert other.workdir != settings.workdir  # one cache per source


def test_web_url_for() -> None:
    assert web_url_for("https://github.com/BEG-lag/leyes-mx.git") == (
        "https://github.com/BEG-lag/leyes-mx"
    )
    assert web_url_for("git@github.com:someone/fork.git") == "https://github.com/someone/fork"
    assert web_url_for("/tmp/local") == "https://github.com/BEG-lag/leyes-mx"

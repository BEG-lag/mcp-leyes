"""Article labels and law structure, with the edge cases found in leyes-mx."""

from datetime import date

import pytest

from mcp_leyes.articles import (
    LabelError,
    check_numbering,
    is_repealed,
    parse_label,
    parse_law,
    parse_user_article,
    section_text,
    title_mentions,
)

from .conftest import LOTRA, V1, V3


@pytest.mark.parametrize(
    ("text", "key", "display"),
    [
        ("Artículo 1o.", "1", "1"),
        ("Artículo 3o. Bis.", "3-bis", "3 Bis"),
        ("Artículo 3o. Ter.", "3-ter", "3 Ter"),
        ("Artículo 1o Bis.", "1-bis", "1 Bis"),
        ("Artículo 15-A.", "15-a", "15 A"),
        ("Artículo 353-Ñ.", "353-ñ", "353 Ñ"),
        ("Artículo 8o.-A.", "8-a", "8 A"),
        ("Artículo 29-A Bis.", "29-a-bis", "29 A Bis"),
        ("Artículo 39-B Ter.", "39-b-ter", "39 B Ter"),
        ("Artículo 2o.-A Bis.", "2-a-bis", "2 A Bis"),
        ("Artículo 21 bis 1.", "21-bis-1", "21 Bis 1"),
        ("Artículo 1067 Bis 33.", "1067-bis-33", "1067 Bis 33"),
        ("Artículo 279 Quáter.", "279-quater", "279 Quater"),
        ("Artículo 5 Quintus.", "5-quinquies", "5 Quinquies"),
        ("Artículo 199 Sextus.", "199-sexies", "199 Sexies"),
        ("Artículo 228 a.", "228-a", "228 A"),
        ("Artículo 27.", "27", "27"),
        ("Artículo 1º.", "1", "1"),
    ],
)
def test_heading_labels(text: str, key: str, display: str) -> None:
    ref = parse_label(text)
    assert ref is not None
    assert ref.key == key
    assert ref.display == display
    assert ref.ignored == ""


def test_lone_o_after_a_space_is_a_letter_not_an_ordinal() -> None:
    # The LGTOC runs 228 a. to 228 v.; "228 o." must not collapse into "228".
    assert parse_label("Artículo 228 o.").key == "228-o"
    assert parse_label("Artículo 1o.").key == "1"


def test_ranges() -> None:
    ref = parse_label("Artículos 133 a 135.")
    assert (ref.number, ref.last, ref.key) == (133, 135, "133")
    assert parse_label("Artículos 5o. a 10.").last == 10
    single = parse_label("Artículos 135.")  # LFDA writes one article with a plural label
    assert (single.key, single.last) == ("135", None)


@pytest.mark.parametrize(
    ("typed", "key", "ignored"),
    [
        ("27", "27", ""),
        ("art. 27", "27", ""),
        ("artículo 27", "27", ""),
        ("3 bis", "3-bis", ""),
        ("3o bis", "3-bis", ""),
        ("15 A", "15-a", ""),
        ("15a", "15-a", ""),
        ("353 ñ", "353-ñ", ""),
        ("27, fracción IV", "27", "fracción IV"),
        ("123 apartado A", "123", "apartado A"),
        ("1o", "1", ""),
    ],
)
def test_user_input(typed: str, key: str, ignored: str) -> None:
    ref = parse_user_article(typed)
    assert ref.key == key
    assert ref.ignored == ignored


def test_user_input_without_number_is_rejected() -> None:
    with pytest.raises(LabelError, match="No reconozco el artículo"):
        parse_user_article("primero transitorio")


def test_parse_fixture_law_sections() -> None:
    law = parse_law(V3)
    assert law.title == "Ley Federal de Pruebas"
    assert [a.key for a in law.articles] == [
        "1", "2", "3", "3-bis", "4", "5", "15", "15-a", "15-ñ",
    ]  # fmt: skip
    rng = next(a for a in law.articles if a.key == "5")
    assert (rng.number, rng.last) == (5, 14)
    assert rng.repealed
    two = next(a for a in law.articles if a.key == "2")
    assert two.note_dates == (date(2009, 6, 30), date(2015, 6, 12))
    assert two.text.startswith("Para los efectos de esta Ley")
    assert two.text.endswith("*Artículo reformado DOF 30-06-2009, 12-06-2015*")
    # Line numbers point at the file: heading and last non-blank line.
    lines = V3.split("\n")
    assert lines[two.line_start - 1] == "##### Artículo 2o."
    assert lines[two.line_end - 1] == "*Artículo reformado DOF 30-06-2009, 12-06-2015*"
    assert section_text(lines, two.line_start, two.line_end) == two.text
    assert not law.anomalies()


def test_transitorios_are_not_articles() -> None:
    law = parse_law(V3)
    # "**ARTÍCULO ÚNICO.-**" and "**Primero.**" live in the transitorios as bold text.
    assert all(not a.label.startswith("ARTÍCULO") for a in law.articles)
    keys = [t.key for t in law.transitorios]
    assert keys == [
        "original",
        "decreto:2009-06-30",
        "decreto:2015-06-12",
        "decreto:2019-11-05",
        "decreto:2020-03-10",  # "10 de marzo 2020", without "de" before the year
    ]
    original = law.transitorios[0]
    assert "entrará en vigor al día siguiente" in original.text
    assert "DECRETO" not in original.text
    decree = next(t for t in law.transitorios if t.key == "decreto:2015-06-12")
    assert decree.decree_date == date(2015, 6, 12)
    assert "noventa días naturales" in decree.text


def test_articles_stop_at_division_headings() -> None:
    law = parse_law(V1)
    three = next(a for a in law.articles if a.key == "3")
    assert "CAPÍTULO II" not in three.text
    assert three.text == "Las pruebas se rigen por los principios de legalidad y de buena fe."


def test_numbering_anomalies_are_detected() -> None:
    law = parse_law(LOTRA)
    anomalies = law.anomalies()
    assert anomalies.duplicates == ["Artículo 2."]
    assert "encabezados repetidos: Artículo 2." in anomalies.describe()
    gap = parse_law(LOTRA.replace("## Artículo 1.", "## Artículo 4."))
    assert check_numbering(gap.articles).out_of_order


def test_repealed_detection() -> None:
    assert is_repealed("Se deroga.\n\n*Artículo derogado DOF 01-05-2019*")
    assert is_repealed("(Se deroga)")
    assert is_repealed("Derogado.")
    assert not is_repealed("Se derogan todas las disposiciones que se opongan a la presente Ley.")
    assert not is_repealed("El trabajo es un derecho y un deber social.")


def test_title_mentions() -> None:
    title = "DECRETO por el que se reforman y adicionan los artículos 4o. y 27 de la Constitución"
    assert title_mentions(title, 27)
    assert title_mentions(title, 4)
    assert not title_mentions(title, 7)
    assert not title_mentions("DECRETO que reforma el artículo 270 del Código", 27)

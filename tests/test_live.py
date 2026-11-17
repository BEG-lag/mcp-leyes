"""Checks against the real leyes-mx history. Opt in with ``pytest --live``.

By default they clone https://github.com/BEG-lag/leyes-mx into a temporary cache. Point
MCP_LEYES_LIVE_SOURCE at a local clone to run them offline, and MCP_LEYES_LIVE_CACHE at a
directory to reuse the clone and index between runs.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest

from mcp_leyes.config import DEFAULT_SOURCE, Settings
from mcp_leyes.corpus import Corpus

pytestmark = pytest.mark.live


@pytest.fixture(scope="module")
def real(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Corpus]:
    source = os.environ.get("MCP_LEYES_LIVE_SOURCE", DEFAULT_SOURCE)
    if "://" not in source:
        source = str(Path(source).expanduser().resolve())
    cache = os.environ.get("MCP_LEYES_LIVE_CACHE")
    cache_dir = Path(cache) if cache else tmp_path_factory.mktemp("live-cache")
    corpus = Corpus(Settings(cache_dir=cache_dir, source=source))
    corpus.sync()
    yield corpus
    corpus.close()


def test_catalog_and_history_size(real: Corpus) -> None:
    laws = {law.slug: law for law in real.laws()}
    assert len(laws) >= 36
    assert sum(law.versions for law in laws.values()) >= 375
    assert laws["cpeum"].first_version == date(2006, 4, 7)
    assert laws["lagra"].first_version == date(1993, 7, 9)


def test_known_numbering_anomalies_are_detected(real: Corpus) -> None:
    """leyes-mx documents 14 archived versions with numbering anomalies from the source."""
    anomalous = [
        (law.slug, v.dof_date)
        for law in real.laws()
        for v in real.versions(law)
        if v.anomalies and v.dof_date < date(2026, 1, 1)
    ]
    assert len(anomalous) == 14
    assert sum(1 for slug, _ in anomalous if slug == "ccom") == 13
    assert ("lfce", date(2014, 5, 23)) in anomalous


def test_constitution_article_27_before_and_after_the_energy_reform(real: Corpus) -> None:
    old = real.article("cpeum", "27", date(2013, 1, 1))
    assert old.pick.version.dof_date == date(2012, 10, 15)
    assert "Tratándose del petróleo y de los carburos de hidrógeno" in old.text
    new = real.article("cpeum", "27", date(2026, 11, 17))
    assert new.text != old.text
    assert "Párrafo adicionado DOF 20-12-2013" in new.text
    assert date(2013, 12, 20) in new.section.note_dates


def test_labor_reform_of_2019(real: Corpus) -> None:
    diff = real.diff_reform("lft", date(2019, 5, 1))
    assert diff.version.dof_date == date(2019, 7, 2)  # grouped with 04-06-2019 and 02-07-2019
    cited = [c for c in diff.changed if c.cites_date]
    assert len(cited) > 500
    assert any(c.key == "390-ter" and c.change == "añadido" for c in cited)
    assert diff.warnings


def test_edge_case_labels_resolve(real: Corpus) -> None:
    today = date(2026, 11, 17)
    assert real.article("lft", "3o. Bis", today).section.label == "Artículo 3o. Bis."
    assert real.article("lft", "15-A", today).section.label == "Artículo 15-A."
    assert real.article("lft", "353-Ñ", today).section.label == "Artículo 353-Ñ."
    assert real.article("lgtoc", "228 o", today).section.label == "Artículo 228 o."
    assert real.article("ccom", "21 bis 1", today).section.label == "Artículo 21 bis 1."

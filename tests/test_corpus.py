"""Sync, index and point-in-time queries against the fixture repository."""

from datetime import UTC, date, datetime, timedelta

import pytest

from mcp_leyes import gitrepo
from mcp_leyes.corpus import Corpus, LeyesError, NotFoundError
from mcp_leyes.gitrepo import BareRepo, GitMissingError, run_git

from .conftest import V3, commit, git, make_settings, noon, write

# --------------------------------------------------------------------- sync


def test_first_sync_clones_and_indexes(fixture_repo, tmp_path) -> None:
    root, commits = fixture_repo
    corpus = Corpus(make_settings(root, tmp_path))
    report = corpus.sync()
    try:
        assert report["indexed_versions"] == 4  # three of LFPr, one of LOtra
        assert "cloned_seconds" in report
        assert report["head"] == commits["docs"][:12]
        assert (corpus.settings.repo_path / "HEAD").exists()
        assert not (corpus.settings.repo_path / "leyes").exists()  # bare: no working tree
        # Tooling, data and docs commits are not versions; nor is lfpr.reformas.md.
        versions = corpus.versions(corpus.resolve_law("lfpr"))
        assert [v.commit for v in versions] == [commits["v1"], commits["v2"], commits["v3"]]
        assert [v.dof_date for v in versions] == [
            date(2010, 1, 15),
            date(2015, 6, 12),
            date(2020, 3, 10),
        ]
    finally:
        corpus.close()


def test_second_process_reuses_the_cache(fixture_repo, tmp_path) -> None:
    root, _ = fixture_repo
    first = Corpus(make_settings(root, tmp_path))
    first.sync()
    first.close()
    second = Corpus(make_settings(root, tmp_path))
    report = second.sync()
    try:
        assert "cloned_seconds" not in report
        assert "indexed_versions" not in report
        assert "fetched_seconds" not in report  # fetched less than 24 h ago
        assert second.article("lfpr", "15-A", date(2021, 1, 1)).text.startswith(
            "El registro de peritos será público, gratuito y electrónico."
        )
    finally:
        second.close()


def test_fetch_picks_up_new_versions_incrementally(source_copy, tmp_path) -> None:
    corpus = Corpus(make_settings(source_copy, tmp_path))
    corpus.sync()
    try:
        write(
            source_copy,
            "leyes/lfpr.md",
            V3.replace(
                "tiene por objeto regular las pruebas.",
                "tiene por objeto regular "
                "las pruebas y los peritajes.\n\n*Artículo reformado DOF 01-02-2021*",
            ),
        )
        new = commit(
            source_copy,
            "LFPr: reforma DOF 01-02-2021\n\n- DECRETO por el que se "
            "reforma el artículo 1o. (DOF 01-02-2021)\n",
            noon("2021-02-01"),
        )
        report = corpus.sync(force_fetch=True)
        assert report["indexed_versions"] == 1
        assert "fetched_seconds" in report
        article = corpus.article("lfpr", "1", date(2021, 2, 1))
        assert article.pick.version.commit == new
        assert "peritajes" in article.text
        assert corpus.article("lfpr", "1", date(2021, 1, 31)).pick.version.dof_date == date(
            2020, 3, 10
        )
    finally:
        corpus.close()


def test_rewritten_source_history_drops_stale_versions(source_copy, tmp_path) -> None:
    corpus = Corpus(make_settings(source_copy, tmp_path))
    corpus.sync()
    try:
        old_v3 = corpus.versions(corpus.resolve_law("lfpr"))[-1].commit
        git(source_copy, "reset", "-q", "--hard", "HEAD~3")  # back to LOtra; lfpr.md at v2
        write(source_copy, "leyes/lfpr.md", V3)
        new_v3 = commit(
            source_copy, "LFPr: reformas DOF 05-11-2019 a 10-03-2020", noon("2020-03-11")
        )
        corpus.sync(force_fetch=True)
        commits = [v.commit for v in corpus.versions(corpus.resolve_law("lfpr"))]
        assert len(commits) == 3
        assert commits[-1] == new_v3
        assert old_v3 not in commits
        assert corpus.index.stats()["versions"] == 4
    finally:
        corpus.close()


def test_fetch_is_throttled_and_failures_keep_cached_data(source_copy, tmp_path) -> None:
    corpus = Corpus(make_settings(source_copy, tmp_path, refresh_hours=24))
    corpus.sync()
    try:
        index = corpus.index
        now = datetime.now(UTC)
        assert not corpus._fetch_due(index, now)
        index.set_meta(
            last_fetch_ok=(now - timedelta(hours=25)).isoformat(),
            last_fetch_attempt=(now - timedelta(hours=25)).isoformat(),
        )
        assert corpus._fetch_due(index, now)
        # Offline: the remote disappears. Sync reports the error and keeps working.
        run_git(
            ["remote", "set-url", "origin", str(tmp_path / "gone")], cwd=corpus.settings.repo_path
        )
        report = corpus.sync()
        assert "fetch_error" in report
        assert corpus.status()["last_fetch_error"]
        assert corpus.article("lfpr", "2o", date(2016, 1, 1)).pick.version.dof_date == date(
            2015, 6, 12
        )
        # After a failure, retry hourly rather than on every call.
        assert not corpus._fetch_due(index, datetime.now(UTC))
    finally:
        corpus.close()


def test_refresh_hours_zero_never_fetches(fixture_repo, tmp_path) -> None:
    root, _ = fixture_repo
    corpus = Corpus(make_settings(root, tmp_path, refresh_hours=0))
    corpus.sync()
    try:
        assert not corpus._fetch_due(corpus.index, datetime.now(UTC) + timedelta(days=30))
    finally:
        corpus.close()


def test_first_sync_without_source_fails_clearly(tmp_path) -> None:
    corpus = Corpus(make_settings(tmp_path / "missing-repo", tmp_path / "cache"))
    with pytest.raises(LeyesError, match="La primera sincronización necesita conexión"):
        corpus.sync()
    corpus.close()


def test_missing_git_is_reported_with_install_help(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(gitrepo.shutil, "which", lambda name: None)
    corpus = Corpus(make_settings(tmp_path / "x", tmp_path / "cache"))
    with pytest.raises(GitMissingError, match="necesita git instalado"):
        corpus.sync()


def test_blob_reader_survives_a_dead_batch_process(corpus) -> None:
    repo: BareRepo = corpus.repo
    version = corpus.versions(corpus.resolve_law("lfpr"))[-1]
    assert version.blob
    assert repo.blob(version.blob).startswith("---\ntitle: Ley Federal de Pruebas")
    assert repo._batch is not None
    repo._batch.kill()
    repo._batch.wait()
    assert repo.blob(version.blob).startswith("---\ntitle: Ley Federal de Pruebas")


# --------------------------------------------------------------- versions


def test_laws_and_resolution(corpus) -> None:
    laws = corpus.laws()
    assert [law.slug for law in laws] == ["lfpr", "lotra"]  # catalog order
    lfpr = laws[0]
    assert lfpr.abbreviation == "LFPr"
    assert lfpr.group == "Leyes de prueba"
    assert lfpr.versions == 3
    assert lfpr.first_version == date(2010, 1, 15)
    assert lfpr.index_date == date(2021, 2, 1)
    assert corpus.resolve_law("LFPR").slug == "lfpr"
    assert corpus.resolve_law("Ley Federal de Pruebas").slug == "lfpr"
    assert corpus.resolve_law("pruebas").slug == "lfpr"
    with pytest.raises(NotFoundError, match="Disponibles: LFPr, LOtra"):
        corpus.resolve_law("xyz")


def test_pick_before_first_version_fails(corpus) -> None:
    law = corpus.resolve_law("lfpr")
    with pytest.raises(NotFoundError, match="más antigua de LFPr en leyes-mx es la del DOF 15-01"):
        corpus.pick(law, date(2009, 12, 31))
    with pytest.raises(NotFoundError, match="La ley se publicó en el DOF el 01-03-2001"):
        corpus.pick(law, date(2000, 1, 1))


def test_pick_exact_date_and_grouped_notes(corpus) -> None:
    law = corpus.resolve_law("lfpr")
    pick = corpus.pick(law, date(2015, 6, 12))
    assert pick.version.dof_date == date(2015, 6, 12)
    assert not pick.warnings
    latest = corpus.pick(law, date(2020, 6, 1))
    assert any("agrupa 2 reformas" in n for n in latest.notes)


def test_pick_inside_a_grouped_gap_warns(corpus) -> None:
    pick = corpus.pick(corpus.resolve_law("lfpr"), date(2019, 12, 1))
    assert pick.version.dof_date == date(2015, 6, 12)
    assert list(pick.pending) == [date(2019, 11, 5)]
    (warning,) = pick.warnings
    assert "DOF 05-11-2019" in warning
    assert "NO las refleja" in warning
    assert "DOF 10-03-2020" in warning


def test_pick_after_latest_warns_about_unconsolidated_reforms(corpus) -> None:
    pick = corpus.pick(corpus.resolve_law("lfpr"), date(2021, 6, 1))
    assert pick.version.dof_date == date(2020, 3, 10)
    assert any("DOF 01-02-2021" in w and "Todavía no hay una versión" in w for w in pick.warnings)


# --------------------------------------------------------------- articles


def test_article_text_and_provenance(corpus) -> None:
    found = corpus.article("lfpr", "3o bis", date(2016, 1, 1))
    assert found.section.label == "Artículo 3o. Bis."
    assert found.text == (
        "La autoridad valorará las pruebas de manera libre y lógica.\n\n"
        "*Artículo adicionado DOF 12-06-2015*"
    )
    assert found.context == ["TÍTULO PRIMERO · Disposiciones Generales", "CAPÍTULO I · Del objeto"]
    assert found.since.dof_date == date(2015, 6, 12)
    assert not found.since_is_oldest
    assert found.link.endswith(
        f"/blob/{found.pick.version.commit}/leyes/lfpr.md?plain=1"
        f"#L{found.section.line_start}-L{found.section.line_end}"
    )
    assert found.link.startswith("https://github.com/BEG-lag/leyes-mx/blob/")


def test_article_unchanged_since_oldest_version(corpus) -> None:
    found = corpus.article("lfpr", "15", date(2025, 1, 1))
    assert found.since.dof_date == date(2010, 1, 15)
    assert found.since_is_oldest


def test_article_in_a_range_heading(corpus) -> None:
    found = corpus.article("lfpr", "7", date(2025, 1, 1))
    assert found.via_range
    assert found.section.label == "Artículos 5 a 14."
    assert found.section.key == "5"


def test_article_pending_note_tells_whether_the_gap_matters(corpus) -> None:
    changed = corpus.article("lfpr", "3 bis", date(2019, 12, 1))
    assert changed.pending_note is not None
    assert "sí cambia" in changed.pending_note
    assert "DOF 05-11-2019" in changed.pending_note
    assert "desactualizado" in changed.pending_note
    untouched = corpus.article("lfpr", "15", date(2019, 12, 1))
    assert "no cambia" in untouched.pending_note


def test_article_not_found_explains(corpus) -> None:
    with pytest.raises(NotFoundError, match=r"no tiene el artículo 15 Ñ.*sí aparece en versiones"):
        corpus.article("lfpr", "15-Ñ", date(2016, 1, 1))
    with pytest.raises(
        NotFoundError, match=r"Con ese número existen: Artículo 15\., Artículo 15-A"
    ):
        corpus.article("lfpr", "15-B", date(2016, 1, 1))


def test_duplicate_headings_in_anomalous_source(corpus) -> None:
    found = corpus.article("lotra", "2", date(2020, 1, 1))
    assert found.duplicates == 1
    assert found.text.startswith("Se entiende por energía limpia")
    assert any("irregularidades de numeración" in n for n in found.pick.notes)


# ---------------------------------------------------------------- history


def test_history_of_an_article(corpus) -> None:
    history = corpus.history("lfpr", "3o. Bis")
    changes = [(e.version.dof_date, e.change) for e in history.events]
    assert changes == [
        (date(2010, 1, 15), "ausente"),
        (date(2015, 6, 12), "añadido"),
        (date(2020, 3, 10), "modificado"),
    ]
    last = history.events[-1]
    assert last.attributed == [date(2019, 11, 5)]  # the note names the grouped decree
    assert [d.dof_date for d in last.decrees] == [date(2019, 11, 5), date(2020, 3, 10)]


def test_history_flags_editorial_changes(corpus) -> None:
    four = corpus.history("lfpr", "4")
    assert [e.editorial for e in four.events if e.change == "modificado"] == ["menor"]
    three = corpus.history("lfpr", "3")
    assert [e.editorial for e in three.events if e.change == "modificado"] == ["notas"]


def test_history_of_repealed_range(corpus) -> None:
    history = corpus.history("lfpr", "9")
    assert history.events[0].change == "presente"
    assert history.events[0].label == "Artículos 5 a 14."
    assert history.earlier_notes == [date(2009, 6, 30)]


# ------------------------------------------------------------------ diffs


def test_diff_article_between_dates(corpus) -> None:
    diff = corpus.diff_article("lfpr", "15-A", date(2012, 1, 1), date(2021, 1, 1))
    assert diff.old.pick.version.dof_date == date(2010, 1, 15)
    assert diff.new.pick.version.dof_date == date(2020, 3, 10)
    assert [e.version.dof_date for e in diff.changes_between] == [
        date(2015, 6, 12),
        date(2020, 3, 10),
    ]
    swapped = corpus.diff_article("lfpr", "15-A", date(2021, 1, 1), date(2012, 1, 1))
    assert swapped.old_pick.version.dof_date == date(2010, 1, 15)


def test_diff_reform_with_own_version(corpus) -> None:
    diff = corpus.diff_reform("lfpr", date(2015, 6, 12))
    assert diff.previous.dof_date == date(2010, 1, 15)
    by_key = {c.key: c for c in diff.changed}
    assert set(by_key) == {"2", "3-bis", "4", "15-a"}
    assert by_key["3-bis"].change == "añadido"
    assert by_key["4"].editorial == "menor"
    assert by_key["2"].cites_date
    assert [s.key for s in diff.added_transitorios] == ["decreto:2015-06-12"]
    assert not diff.warnings
    assert [d["number"] for d in diff.listed_decrees] == [2]


def test_diff_reform_inside_a_grouped_version(corpus) -> None:
    diff = corpus.diff_reform("lfpr", date(2019, 11, 5))
    assert diff.version.dof_date == date(2020, 3, 10)
    assert diff.changed[0].key == "3-bis"  # its note cites 05-11-2019, so it comes first
    assert diff.changed[0].cites_date
    assert {c.key for c in diff.changed} == {"3", "3-bis", "15-a", "15-ñ"}
    assert diff.changed[-1].editorial == "notas"  # article 3o.: only a note changed
    assert "incluye cambios de todas las reformas" in diff.warnings[0]


def test_diff_reform_errors(corpus) -> None:
    with pytest.raises(NotFoundError, match="versión más antigua"):
        corpus.diff_reform("lfpr", date(2009, 6, 30))
    with pytest.raises(NotFoundError, match="Fechas cercanas"):
        corpus.diff_reform("lfpr", date(2017, 1, 1))
    with pytest.raises(NotFoundError, match="No hay versión de LFPr posterior"):
        corpus.diff_reform("lfpr", date(2021, 2, 1))


# ------------------------------------------------------------ search etc.


def test_search_point_in_time(corpus) -> None:
    now = corpus.search("electronico", law_text=None, requested=date(2021, 1, 1), limit=10)
    assert [h.section.key for h in now.hits] == ["15-a"]
    before = corpus.search("electronico", law_text=None, requested=date(2016, 1, 1), limit=10)
    assert before.total == 0
    energy = corpus.search("energia electrica", law_text=None, requested=date(2021, 1, 1), limit=10)
    assert {h.law.slug for h in energy.hits} == {"lfpr", "lotra"}
    early = corpus.search("peritos", law_text=None, requested=date(2012, 1, 1), limit=10)
    assert early.skipped == ["LOtra (desde DOF 10-01-2018)"]
    trans = corpus.search(
        "noventa dias",
        law_text="lfpr",
        requested=date(2021, 1, 1),
        limit=5,
        include_transitorios=True,
    )
    assert [h.section.key for h in trans.hits] == ["decreto:2015-06-12"]


def test_reforms_timeline(corpus) -> None:
    reforms = corpus.reforms("lfpr", None)
    status = {e.number: e.status for e in reforms.entries}
    assert status == {
        1: "anterior al archivo",
        2: "versión propia",
        3: "agrupada",
        4: "versión propia",
        5: "sin versión todavía",
    }
    assert reforms.total_listed == 5
    assert any("01-02-2021" in w for w in reforms.warnings)
    recent = corpus.reforms("lfpr", date(2019, 1, 1))
    assert [e.number for e in recent.entries] == [3, 4, 5]


def test_transitorios(corpus) -> None:
    original = corpus.transitorios("lfpr", None, date(2021, 1, 1))
    assert len(original.blocks) == 1
    assert "Se abroga la Ley de Pruebas de 1950" in original.blocks[0][1]
    decree = corpus.transitorios("lfpr", date(2020, 3, 10), date(2021, 1, 1))
    assert "1o. de enero de 2021" in decree.blocks[0][1]
    missing = corpus.transitorios("lfpr", date(2020, 3, 10), date(2016, 1, 1))
    assert missing.blocks == []
    assert date(2015, 6, 12) in missing.nearby

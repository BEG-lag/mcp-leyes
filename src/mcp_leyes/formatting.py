"""Markdown rendering of tool results. Content is in Spanish; dates in DOF style."""

from __future__ import annotations

from datetime import UTC, date, datetime

from .commits import Decree
from .corpus import (
    ArticleDiff,
    ArticleText,
    History,
    HistoryEvent,
    Law,
    Pick,
    ReformDiff,
    Reforms,
    SearchResult,
    Transitorios,
)
from .dates import MEXICO_CITY, dmy
from .diffing import LEGEND, unified_diff, word_diff
from .index import VersionRow
from .textutil import normalize_space, truncate

FOOTER = (
    "_No oficial. Solo el DOF es fuente auténtica. No es asesoría legal. Textos: versiones "
    "consolidadas de la Cámara de Diputados vía [leyes-mx](https://github.com/BEG-lag/leyes-mx)._"
)
EFFECTIVE_NOTE = (
    "La fecha de cada versión es la de su publicación en el DOF. La entrada en vigor la fijan "
    "los transitorios de cada decreto (herramienta `transitorios`)."
)

CHANGE_LABELS = {
    "presente": "presente en la versión más antigua del archivo",
    "ausente": "no existe en la versión más antigua del archivo",
    "añadido": "añadido",
    "modificado": "modificado",
    "derogado": "derogado",
    "eliminado": "ya no aparece",
    "sin_cambio": "sin cambio",
}


def _commit(corpus_link: str, version: VersionRow) -> str:
    return f"[`{version.short}`]({corpus_link})"


def _decree_line(d: Decree, limit: int = 160) -> str:
    title = truncate(normalize_space(d.title), limit)
    when = f"DOF {dmy(d.dof_date)}: " if d.dof_date else ""
    link = f" ([PDF]({d.url}))" if d.url else ""
    return f"{when}{title}{link}"


def _bullets(items: list[str], indent: str = "") -> str:
    return "\n".join(f"{indent}- {item}" for item in items)


def _warnings(items: list[str], title: str = "Advertencias") -> str:
    seen: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.append(item)
    if not seen:
        return ""
    return f"**{title}**\n\n" + _bullets(seen)


def _version_line(version: VersionRow, commit_url: str) -> str:
    commit = _commit(commit_url, version)
    return f"DOF {dmy(version.dof_date)} · {version.info.subject} · commit {commit}"


def _join(*parts: str) -> str:
    return "\n\n".join(p.strip("\n") for p in parts if p and p.strip()) + "\n"


# --------------------------------------------------------------------- laws


def render_laws(laws: list[Law], status: dict) -> str:
    total_versions = sum(law.versions for law in laws)
    latest = max((law.last_version for law in laws if law.last_version), default=None)
    synced = _when(status.get("last_fetch_ok"))
    head = status.get("head") or ""
    lines = [
        "# Leyes federales disponibles",
        f"{len(laws)} leyes · {total_versions} versiones en git · versión más reciente: DOF "
        f"{dmy(latest)} · leyes-mx `{head[:7]}`" + (f" · sincronizado {synced}" if synced else ""),
    ]
    group = None
    for law in laws:
        if law.group != group:
            group = law.group
            lines.append(
                f"## {group}\n\n"
                "| Abrev. | Ley | Última reforma (DOF) | Artículos | Versiones | Desde |\n"
                "|---|---|---|---:|---:|---|"
            )
        last = dmy(law.last_reform_dof) if law.last_reform_dof else "sin reformas"
        if law.index_date and law.last_version and law.index_date > law.last_version:
            last += f" (índice LeyesBiblio: {dmy(law.index_date)}, aún no en el texto)"
        lines[-1] += (
            f"\n| {law.abbreviation} (`{law.slug}`) | {law.title} | {last} | {law.articles:,} | "
            f"{law.versions} | {dmy(law.first_version)} |"
        )
    lines.append(
        "Usa la abreviatura o el slug en las demás herramientas. «Desde» es la versión más "
        "antigua archivada: no hay texto anterior a esa fecha."
    )
    lines.append(FOOTER)
    return _join(*lines)


def _when(value: object) -> str:
    if not isinstance(value, str) or not value:
        return ""
    try:
        moment = datetime.fromisoformat(value)
    except ValueError:
        return ""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return moment.astimezone(MEXICO_CITY).strftime("%d-%m-%Y %H:%M") + " (CDMX)"


# ------------------------------------------------------------------ article


def _pick_warnings(pick: Pick) -> list[str]:
    return [*pick.warnings, *pick.notes]


def render_article(a: ArticleText, *, commit_url: str, since_url: str | None) -> str:
    law, pick, version = a.law, a.pick, a.pick.version
    label = normalize_space(a.section.label)
    where = " › ".join([f"**{law.title}**", *a.context])
    head = [
        f"# {law.abbreviation} · {label}",
        where,
        f"Texto aplicable al {dmy(pick.requested)}: versión DOF {dmy(version.dof_date)} "
        f"(commit {_commit(commit_url, version)}).",
    ]
    provenance = [f"Versión: {_version_line(version, commit_url)}"]
    if version.info.decrees:
        decrees = version.info.decrees
        shown = [_decree_line(d) for d in decrees[:6]]
        more = f" (y {len(decrees) - 6} más)" if len(decrees) > 6 else ""
        provenance.append("Decretos que recoge esa versión" + more + ":\n" + _bullets(shown, "  "))
    elif version.info.notes:
        provenance.append("Nota del commit: " + " ".join(version.info.notes))
    if a.since is not None and a.since.id != version.id:
        oldest = " (la más antigua del archivo)" if a.since_is_oldest else ""
        link = f" ({_commit(since_url, a.since)})" if since_url else ""
        provenance.append(
            f"El texto de este artículo no cambia desde la versión DOF {dmy(a.since.dof_date)}"
            f"{oldest}{link}."
        )
    elif a.since is not None and a.since_is_oldest:
        provenance.append("Es la versión más antigua del archivo: no hay versiones previas.")
    else:
        provenance.append("Este artículo cambió en esta versión respecto de la anterior.")
    if a.section.note_dates:
        provenance.append(
            "Notas editoriales de la Cámara en el artículo citan: DOF "
            + ", ".join(dmy(d) for d in a.section.note_dates)
            + "."
        )
    provenance.append(
        f"En GitHub: [leyes/{law.slug}.md, líneas {a.section.line_start}-{a.section.line_end}, "
        f"commit {version.short}]({a.link})"
    )
    warnings = _pick_warnings(pick)
    if a.pending_note:
        warnings.append(a.pending_note)
    if a.ref.ignored:
        warnings.append(
            f"Se ignoró «{a.ref.ignored}»: la herramienta devuelve el artículo completo."
        )
    if a.via_range:
        warnings.append(f"El artículo forma parte del encabezado «{label}».")
    if a.duplicates:
        warnings.append(
            f"Esta versión tiene {a.duplicates} encabezado(s) más con el mismo número "
            "(irregularidad de la fuente); se muestra el primero."
        )
    return _join(
        *head,
        "---",
        a.text or "_(sin texto)_",
        "---",
        "**Procedencia**\n\n" + _bullets(provenance),
        _warnings(warnings),
        f"> {EFFECTIVE_NOTE}",
        FOOTER,
    )


# ------------------------------------------------------------------ history


EDITORIAL_LABELS = {
    "notas": "solo cambian las notas editoriales de la Cámara",
    "menor": "cambio menor sin nota de reforma (posible corrección editorial de la Cámara)",
}


def _event_block(e: HistoryEvent, commit_url: str, previous_label: str | None) -> str:
    v = e.version
    change = CHANGE_LABELS[e.change]
    if e.editorial:
        change += f": {EDITORIAL_LABELS[e.editorial]}"
    title = f"### DOF {dmy(v.dof_date)} · {change} · {_commit(commit_url, v)}"
    items: list[str] = []
    label = normalize_space(e.label) if e.label else None
    if label and e.change not in {"eliminado", "ausente"} and label != previous_label:
        items.append(f"Encabezado: {label}")
    attributed = set(e.attributed)
    decrees = e.decrees
    if attributed:
        hit = [d for d in decrees if d.dof_date in attributed]
        if hit:
            items.append(
                "Decreto (según la nota editorial del artículo):\n"
                + _bullets([_decree_line(d) for d in hit], "  ")
            )
        else:
            items.append(
                "Nota editorial nueva: DOF " + ", ".join(dmy(d) for d in sorted(attributed))
            )
        others = [d for d in decrees if d.dof_date not in attributed]
        if others and e.version.info.grouped:
            items.append(
                f"La versión agrupa además {len(others)} decreto(s) de otras fechas que no "
                "citan este artículo en sus notas."
            )
    elif decrees and not e.editorial:
        shown = [_decree_line(d) for d in decrees[:4]]
        more = f" (y {len(decrees) - 4} más)" if len(decrees) > 4 else ""
        label = "Decretos de la versión" if len(decrees) > 1 else "Decreto de la versión"
        items.append(f"{label}{more}:\n" + _bullets(shown, "  "))
        if e.version.info.grouped and e.change != "presente":
            hint = ""
            if e.mentioned and len(e.mentioned) < len(decrees):
                hint = (
                    " Pista: el título del decreto del DOF "
                    + ", ".join(dmy(d.dof_date) for d in e.mentioned)
                    + " menciona ese número de artículo."
                )
            items.append(
                "Versión que agrupa varias reformas y la nota editorial no indica cuál tocó el "
                "artículo." + hint
            )
    elif e.editorial:
        items.append(
            "Ninguna nota editorial nueva explica el cambio; revisa el detalle con diff_article."
        )
    elif v.info.notes:
        items.append("Nota del commit: " + " ".join(v.info.notes))
    return title + ("\n\n" + _bullets(items) if items else "")


def render_history(h: History, *, commit_url) -> str:
    law = h.law
    shown = [e for e in h.events if e.change not in {"sin_cambio"}]
    if shown and shown[0].change == "ausente":
        shown = [shown[0], *[e for e in shown[1:] if e.change != "ausente"]]
    else:
        shown = [e for e in shown if e.change != "ausente"]
    changes = sum(
        1 for e in h.events if e.change in {"añadido", "modificado", "derogado", "eliminado"}
    )
    editorial = sum(1 for e in h.events if e.editorial)
    last = h.events[-1].version
    intro = (
        f"{changes} cambio(s) en {h.versions_total} versiones archivadas de {law.abbreviation} "
        f"(DOF {dmy(h.first_version.dof_date)} a DOF {dmy(last.dof_date)})"
        + (f", de los cuales {editorial} parecen solo editoriales" if editorial else "")
        + ". Versiones sin cambios en este artículo: "
        f"{sum(1 for e in h.events if e.change == 'sin_cambio')}."
    )
    blocks = []
    previous_label: str | None = None
    for e in shown:
        blocks.append(_event_block(e, commit_url(e.version), previous_label))
        if e.label:
            previous_label = normalize_space(e.label)
    notes = []
    if h.earlier_notes:
        notes.append(
            "Reformas anteriores al archivo según las notas editoriales: DOF "
            + ", ".join(dmy(d) for d in h.earlier_notes)
            + ". El archivo no tiene esos textos anteriores."
        )
    notes.append(
        "El historial empieza en la versión más antigua archivada; cuando varias reformas caen "
        "entre dos copias archivadas, un solo commit las agrupa con la fecha de la última. "
        "La nota editorial de la Cámara («Artículo reformado DOF ...») indica cuál de ellas "
        "tocó el artículo."
    )
    return _join(
        f"# {law.abbreviation} · historia del artículo {h.ref.display}",
        f"**{law.title}**",
        intro,
        *blocks,
        _warnings(notes, "Notas"),
        f"> {EFFECTIVE_NOTE}",
        FOOTER,
    )


# -------------------------------------------------------------------- diffs


def _diff_body(old: str, new: str, mode: str, old_name: str, new_name: str) -> str:
    if mode == "unified":
        text = unified_diff(old, new, old_name, new_name)
        return f"```diff\n{text}\n```"
    return LEGEND + "\n\n" + word_diff(old, new)


def render_article_diff(d: ArticleDiff, *, mode: str, commit_url) -> str:
    law = d.law
    ov, nv = d.old_pick.version, d.new_pick.version
    label = normalize_space((d.new or d.old).section.label)  # type: ignore[union-attr]
    head = [
        f"# {law.abbreviation} · {label} · DOF {dmy(ov.dof_date)} → DOF {dmy(nv.dof_date)}",
        f"Comparación entre el texto aplicable al {dmy(d.old_pick.requested)} (versión DOF "
        f"{dmy(ov.dof_date)}, {_commit(commit_url(ov), ov)}) y al {dmy(d.new_pick.requested)} "
        f"(versión DOF {dmy(nv.dof_date)}, {_commit(commit_url(nv), nv)}).",
    ]
    if ov.id == nv.id:
        body = "Ambas fechas caen en la misma versión del archivo: el texto es idéntico."
    elif d.old and d.new and d.old.section.digest == d.new.section.digest:
        body = "El texto del artículo no cambió entre esas versiones."
    elif d.old is None:
        body = (
            f"El artículo no existe en la versión DOF {dmy(ov.dof_date)}; aparece después. "
            f"Texto en la versión DOF {dmy(nv.dof_date)}:\n\n{d.new.text}"  # type: ignore[union-attr]
        )
    elif d.new is None:
        body = (
            f"El artículo ya no aparece en la versión DOF {dmy(nv.dof_date)}. Texto en la "
            f"versión DOF {dmy(ov.dof_date)}:\n\n{d.old.text}"
        )
    else:
        body = _diff_body(
            d.old.text,
            d.new.text,
            mode,
            f"{label} DOF {dmy(ov.dof_date)}",
            f"{label} DOF {dmy(nv.dof_date)}",
        )
    between = ""
    if d.changes_between:
        between = "**Versiones que cambiaron el artículo en ese lapso**\n\n" + _bullets(
            [
                f"DOF {dmy(e.version.dof_date)} · {CHANGE_LABELS[e.change]} · "
                + (
                    "nota editorial: DOF " + ", ".join(dmy(x) for x in e.attributed)
                    if e.attributed
                    else truncate(e.version.info.subject, 90)
                )
                for e in d.changes_between
            ]
        )
    links = []
    if d.old:
        links.append(f"Antes: [leyes/{law.slug}.md en {ov.short}]({d.old.link})")
    if d.new:
        links.append(f"Después: [leyes/{law.slug}.md en {nv.short}]({d.new.link})")
    warnings = _pick_warnings(d.old_pick) + _pick_warnings(d.new_pick)
    return _join(
        *head,
        between,
        body,
        _bullets(links),
        _warnings(warnings),
        f"> {EFFECTIVE_NOTE}",
        FOOTER,
    )


MAX_REFORM_CHARS = 40_000


def render_reform_diff(r: ReformDiff, *, mode: str, limit: int, offset: int, commit_url) -> str:
    law, v, p = r.law, r.version, r.previous
    decrees: list[str] = []
    if r.listed_decrees:
        for d in r.listed_decrees:
            url = d.get("pdf_url")
            decrees.append(
                truncate(normalize_space(d.get("title") or ""), 220)
                + (f" ([PDF]({url}))" if url else "")
            )
    elif r.matching_decrees:
        decrees = [_decree_line(d, 220) for d in r.matching_decrees]
    counts = {
        k: sum(1 for c in r.changed if c.change == k)
        for k in ("modificado", "añadido", "eliminado")
    }
    summary = [
        f"{counts['modificado']} artículo(s) modificado(s), {counts['añadido']} añadido(s), "
        f"{counts['eliminado']} que ya no aparece(n)."
    ]
    cites = [c for c in r.changed if c.cites_date]
    if v.info.grouped or v.dof_date != r.reform_date:
        summary.append(
            f"De ellos, {len(cites)} tienen una nota editorial que cita el DOF "
            f"{dmy(r.reform_date)}."
        )
    editorial = [c for c in r.changed if c.editorial]
    if editorial:
        summary.append(
            f"{len(editorial)} cambio(s) parecen solo editoriales (notas o correcciones de pocas "
            "palabras sin nota de reforma); van al final."
        )
    if r.added_transitorios:
        days = sorted({s.decree_date for s in r.added_transitorios if s.decree_date})
        summary.append(
            f"Transitorios nuevos de {len(r.added_transitorios)} decreto(s)"
            + (" (DOF " + ", ".join(dmy(x) for x in days) + ")" if days else "")
            + ": consúltalos con `transitorios`."
        )
    if r.headings_added:
        summary.append(
            "Encabezados nuevos: " + "; ".join(truncate(h, 80) for h in r.headings_added[:8])
        )
    if r.headings_removed:
        summary.append(
            "Encabezados que ya no aparecen: "
            + "; ".join(truncate(h, 80) for h in r.headings_removed[:8])
        )

    def short(c) -> str:
        text = c.label.removeprefix("Artículo ").removeprefix("Artículos ")
        return text + ("" if c.change == "modificado" else f" ({c.change})")

    def listing(items: list, cap: int = 200) -> str:
        text = ", ".join(short(c) for c in items[:cap])
        return text + (f" y {len(items) - cap} más" if len(items) > cap else "")

    grouped_view = v.info.grouped or v.dof_date != r.reform_date
    if grouped_view:
        cited = [c for c in r.changed if c.cites_date]
        rest = [c for c in r.changed if not c.cites_date]
        labels = ""
        if cited:
            labels += f"**Con nota que cita el DOF {dmy(r.reform_date)} ({len(cited)}):** "
            labels += listing(cited)
        if rest:
            labels += ("\n\n" if labels else "") + (
                f"**Sin esa nota ({len(rest)}; otras reformas de la versión o cambios "
                "editoriales):** " + listing(rest)
            )
    else:
        labels = ("**Artículos con cambios:** " + listing(r.changed)) if r.changed else ""
    page = r.changed[offset : offset + limit]
    sections: list[str] = []
    used = 0
    shown = 0
    for c in page:
        if sections and used > MAX_REFORM_CHARS:
            break  # keep one answer readable; the rest is one offset away
        tag = c.change + (f"; nota cita DOF {dmy(r.reform_date)}" if c.cites_date else "")
        if c.editorial:
            tag += "; " + EDITORIAL_LABELS[c.editorial]
        if c.change == "añadido":
            body = (
                f"{{+{c.new_text}+}}"
                if mode != "unified"
                else _diff_body("", c.new_text, mode, "antes", "después")
            )
        elif c.change == "eliminado":
            body = (
                f"[-{c.old_text}-]"
                if mode != "unified"
                else _diff_body(c.old_text, "", mode, "antes", "después")
            )
        else:
            body = _diff_body(
                c.old_text,
                c.new_text,
                mode,
                f"{c.label} DOF {dmy(p.dof_date)}",
                f"{c.label} DOF {dmy(v.dof_date)}",
            )
            if mode != "unified":
                body = body.removeprefix(LEGEND + "\n\n")
        sections.append(f"## {c.label} ({tag})\n\n{body}")
        used += len(sections[-1])
        shown += 1
    nav = ""
    if r.changed:
        end = offset + shown
        nav = f"Mostrando artículos {offset + 1}-{end} de {len(r.changed)}."
        if end < len(r.changed):
            nav += f" Usa offset={end} para continuar, o diff_article para uno en particular."
    return _join(
        f"# {law.abbreviation} · reforma DOF {dmy(r.reform_date)}",
        f"**{law.title}**",
        ("Decreto(s) publicado(s) ese día:\n\n" + _bullets(decrees)) if decrees else "",
        f"Comparación: versión DOF {dmy(p.dof_date)} ({_commit(commit_url(p), p)}) → versión "
        f"DOF {dmy(v.dof_date)} ({_commit(commit_url(v), v)}).",
        "**Resumen**\n\n" + _bullets(summary),
        labels,
        (LEGEND if mode != "unified" and page else ""),
        *sections,
        nav,
        _warnings(r.warnings),
        f"> {EFFECTIVE_NOTE}",
        FOOTER,
    )


# ------------------------------------------------------------------- search


def render_search(res: SearchResult) -> str:
    per_law = ", ".join(f"{k} {v}" for k, v in sorted(res.per_law.items(), key=lambda kv: -kv[1]))
    lines = [
        f"# Búsqueda: `{res.query.raw}` · texto aplicable al {dmy(res.requested)}",
        f"{res.total} coincidencia(s) en {len(res.per_law)} ley(es)"
        + (f" ({per_law})" if per_law else "")
        + f". Se revisaron {res.scanned_sections:,} secciones de {res.scanned_laws} ley(es)."
        + (
            f" Mostrando las {len(res.hits)} con más menciones."
            if res.total > len(res.hits)
            else ""
        ),
    ]
    for n, hit in enumerate(res.hits, start=1):
        label = normalize_space(hit.section.label)
        if hit.section.kind == "transitorios":
            label = "Transitorios: " + truncate(label, 90)
        lines.append(
            f"{n}. **{hit.law.abbreviation} · {label}** · versión DOF "
            f"{dmy(hit.version.dof_date)} · [ver]({hit.link})\n   {hit.snippet}"
        )
    if not res.hits:
        lines.append(
            "Sin resultados. Prueba con menos palabras, con la raíz de la palabra "
            "(«subcontrat») o sin filtro de ley."
        )
    if res.skipped:
        lines.append("Sin versión archivada a esa fecha: " + ", ".join(res.skipped) + ".")
    lines.append(
        "Búsqueda sin acentos ni mayúsculas; cada palabra es un prefijo y todas deben aparecer "
        "en el mismo artículo. Usa get_article para el texto completo."
    )
    lines.append(FOOTER)
    return _join(*lines)


# ------------------------------------------------------------------ reforms


STATUS_LABELS = {
    "versión propia": "versión propia",
    "agrupada": "agrupada en la versión",
    "anterior al archivo": "anterior al archivo; incluida en la versión más antigua",
    "sin versión todavía": "sin versión todavía",
    "sin fecha": "sin fecha",
}


def render_reforms(r: Reforms, *, limit: int, commit_url) -> str:
    law = r.law
    original = r.original or {}
    orig = ""
    if original.get("dof_date"):
        url = original.get("url")
        orig = f"Publicación original: DOF {dmy(date.fromisoformat(original['dof_date']))}" + (
            f" ([PDF]({url}))" if url else ""
        )
    entries = list(reversed(r.entries))
    shown = entries[:limit]
    head = (
        f"Decretos de reforma listados por LeyesBiblio: {r.total_listed}"
        + (f"; desde el DOF {dmy(r.since)}: {len(r.entries)}" if r.since else "")
        + f". Versiones de {law.abbreviation} en git: {law.versions} (desde DOF "
        f"{dmy(law.first_version)})."
    )
    rows = ["| # | DOF | Decreto | En git |", "|---:|---|---|---|"]
    for e in shown:
        title = truncate(normalize_space(e.title), 170).replace("|", "\\|")
        if e.pdf_url:
            title = f"[{title}]({e.pdf_url})"
        status = STATUS_LABELS.get(e.status, e.status)
        if e.version is not None and e.status in {"versión propia", "agrupada"}:
            status += (
                f" DOF {dmy(e.version.dof_date)} ({_commit(commit_url(e.version), e.version)})"
            )
        rows.append(f"| {e.number or ''} | {dmy(e.dof_date)} | {title} | {status} |")
    more = ""
    if len(entries) > len(shown):
        more = f"Mostrando los {len(shown)} más recientes de {len(entries)}; usa `since` o `limit`."
    notes = []
    if r.versions_without_decree:
        notes.append(
            f"Además hay {r.versions_without_decree} versión(es) en git sin un decreto en esta "
            "lista (actualizaciones de cantidades, declaratorias de la SCJN o cambios de la "
            "Cámara sin decreto listado). La lista de LeyesBiblio puede estar incompleta."
        )
    notes.append(
        "«Agrupada» significa que no hay copia archivada justo después de ese decreto: su texto "
        "aparece en la siguiente versión, junto con otras reformas."
    )
    return _join(
        f"# {law.abbreviation} · reformas",
        f"**{law.title}**" + (f" · [página de reformas]({r.ref_url})" if r.ref_url else ""),
        orig,
        head,
        "\n".join(rows) if shown else "Sin decretos en el periodo.",
        more,
        _warnings(r.warnings),
        _warnings(notes, "Notas"),
        FOOTER,
    )


# ------------------------------------------------------------- transitorios


def render_transitorios(t: Transitorios, *, max_chars: int, commit_url: str) -> str:
    law, pick = t.law, t.pick
    which = (
        "del texto original" if t.decree_date is None else f"del decreto DOF {dmy(t.decree_date)}"
    )
    head = [
        f"# {law.abbreviation} · transitorios {which}",
        f"Según la versión DOF {dmy(pick.version.dof_date)} (commit "
        f"{_commit(commit_url, pick.version)}), aplicable al {dmy(pick.requested)}.",
    ]
    if not t.blocks:
        near = ", ".join(dmy(d) for d in t.nearby)
        msg = (
            f"No encontré transitorios {which} en esa versión."
            + (f" Decretos con transitorios en esa versión, cercanos: DOF {near}." if near else "")
            + " Los transitorios de un decreto aparecen a partir de la primera versión archivada "
            "posterior a su publicación; prueba con una fecha más reciente."
        )
        return _join(*head, msg, FOOTER)
    blocks = []
    budget = max_chars
    for section, text, link in t.blocks:
        body = text
        cut = ""
        if len(body) > budget:
            body = truncate(body, max(budget, 500))
            cut = (
                f"\n\n_(texto recortado a {max(budget, 500):,} caracteres; ver completo en GitHub)_"
            )
        budget = max(0, budget - len(body))
        blocks.append(
            f"## {truncate(normalize_space(section.label), 300)}\n\n{body}{cut}\n\n"
            f"[leyes/{law.slug}.md, líneas {section.line_start}-{section.line_end}]({link})"
        )
    return _join(*head, *blocks, _warnings(_pick_warnings(pick)), FOOTER)


# ---------------------------------------------------------------- full text


def render_law_text(pick: Pick, body: str, commit_url: str) -> str:
    law, v = pick.law, pick.version
    head = [
        f"<!-- mcp-leyes: {law.abbreviation}, versión DOF {v.dof_date.isoformat()}, commit "
        f"{v.commit}, aplicable al {pick.requested.isoformat()} -->",
        f"> **{law.title}** · versión DOF {dmy(v.dof_date)} ({_commit(commit_url, v)}), "
        f"aplicable al {dmy(pick.requested)}. {EFFECTIVE_NOTE}",
    ]
    for w in _pick_warnings(pick):
        head.append(f"> Advertencia: {w}")
    head.append(f"> {FOOTER}")
    return "\n".join(head) + "\n\n" + body.lstrip("\n")

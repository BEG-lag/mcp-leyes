"""Paragraph and word-level diffs of article texts.

Law paragraphs are long single lines, so a line diff shows a whole paragraph as
changed when a reform swapped one word. The word diff pairs changed paragraphs
and marks only the words that changed, in git's ``--word-diff=plain`` notation:
``[-removed-]`` and ``{+added+}``.
"""

from __future__ import annotations

import difflib
import re

# Dates (30-11-2012) are one token, so a changed note reads [-30-11-2012-] {+01-05-2019+}.
_TOKENS = re.compile(r"\s+|\d{1,2}-\d{1,2}-\d{4}|[\wÀ-ÿ]+|[^\w\s]", re.UNICODE)

LEGEND = "Leyenda: `[-texto eliminado-]` · `{+texto añadido+}`"


def paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n|\n", text) if p.strip()]


def word_diff_line(old: str, new: str) -> str:
    a = _TOKENS.findall(old)
    b = _TOKENS.findall(new)
    matcher = difflib.SequenceMatcher(None, a, b, autojunk=False)
    # (equal?, old text, new text); runs of changes split only by spaces are merged so
    # the output reads "[-old phrase-] {+new phrase+}" instead of alternating words.
    segments: list[list] = []
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        old_text, new_text = "".join(a[i1:i2]), "".join(b[j1:j2])
        equal = op == "equal"
        if (
            not equal
            and len(segments) >= 2
            and not segments[-2][0]
            and segments[-1][0]
            and not segments[-1][1].strip()
        ):
            gap = segments.pop()[1]
            prev = segments[-1]
            prev[1] += gap + old_text
            prev[2] += gap + new_text
            continue
        if not equal and segments and not segments[-1][0]:
            segments[-1][1] += old_text
            segments[-1][2] += new_text
            continue
        segments.append([equal, old_text, new_text])
    out: list[str] = []
    for equal, old_text, new_text in segments:
        if equal:
            out.append(old_text)
            continue
        lead = " " if old_text[:1].isspace() or new_text[:1].isspace() else ""
        trail = " " if old_text[-1:].isspace() or new_text[-1:].isspace() else ""
        marks = []
        if old_text.strip():
            marks.append(f"[-{old_text.strip()}-]")
        if new_text.strip():
            marks.append(f"{{+{new_text.strip()}+}}")
        out.append(lead + " ".join(marks) + trail)
    return re.sub(r" {2,}", " ", "".join(out)).strip()


def _align(old_block: list[str], new_block: list[str]) -> list[tuple[str | None, str | None]]:
    """Pair each old paragraph with the most similar new one, keeping order."""
    pairs: list[tuple[str | None, str | None]] = []
    j = 0
    for old in old_block:
        best, best_ratio = None, 0.0
        for k in range(j, len(new_block)):
            ratio = difflib.SequenceMatcher(None, old, new_block[k], autojunk=False).ratio()
            if ratio > best_ratio:
                best, best_ratio = k, ratio
        if best is not None and best_ratio >= 0.5:
            pairs.extend((None, new) for new in new_block[j:best])
            pairs.append((old, new_block[best]))
            j = best + 1
        else:
            pairs.append((old, None))
    pairs.extend((None, new) for new in new_block[j:])
    return pairs


def word_diff(old: str, new: str, *, context: int = 0) -> str:
    """Changed paragraphs only, with word-level marks. ``context`` keeps nearby paragraphs."""
    a = paragraphs(old)
    b = paragraphs(new)
    matcher = difflib.SequenceMatcher(None, a, b, autojunk=False)
    blocks: list[str] = []
    skipped = 0

    def flush_skipped() -> None:
        nonlocal skipped
        if skipped:
            blocks.append(f"… ({skipped} párrafo{'s' if skipped != 1 else ''} sin cambios)")
            skipped = 0

    opcodes = matcher.get_opcodes()
    for n, (op, i1, i2, j1, j2) in enumerate(opcodes):
        if op == "equal":
            same = a[i1:i2]
            head = same[:context] if n > 0 else []
            tail = same[-context:] if context and n < len(opcodes) - 1 else []
            if len(head) + len(tail) >= len(same):
                head, tail = same, []
            middle = len(same) - len(head) - len(tail)
            blocks.extend(head)
            skipped += middle
            if tail:
                flush_skipped()
                blocks.extend(tail)
            continue
        flush_skipped()
        for old_para, new_para in _align(a[i1:i2], b[j1:j2]):
            if old_para is not None and new_para is not None:
                blocks.append(word_diff_line(old_para, new_para))
            elif old_para is not None:
                blocks.append(f"[-{old_para}-]")
            elif new_para is not None:
                blocks.append(f"{{+{new_para}+}}")
    flush_skipped()
    return "\n\n".join(blocks)


def unified_diff(old: str, new: str, old_name: str, new_name: str, *, context: int = 1) -> str:
    lines = difflib.unified_diff(
        paragraphs(old),
        paragraphs(new),
        fromfile=old_name,
        tofile=new_name,
        lineterm="",
        n=context,
    )
    return "\n".join(lines)


_NOTE_LINE = re.compile(r"^\*(?!\*).+\*$")
_WORDS = re.compile(r"[\wÀ-ÿ]+", re.UNICODE)


def _without_notes(text: str) -> list[str]:
    return [p for p in paragraphs(text) if not _NOTE_LINE.match(p)]


def classify_change(old: str, new: str, *, max_words: int = 3) -> str | None:
    """Tell editorial touch-ups from substantive changes.

    Returns ``"notas"`` when only the Cámara's editorial notes differ, ``"menor"``
    when every change inside the same paragraphs swaps at most ``max_words`` words
    (spelling fixes, punctuation, "sic DOF dd-mm-yyyy" marks, whose numbers and the
    words "sic" and "DOF" do not count), and None otherwise: paragraphs added or
    removed, or longer rewrites.
    """
    a, b = _without_notes(old), _without_notes(new)
    if [normalize(p) for p in a] == [normalize(p) for p in b]:
        return "notas"
    if len(a) != len(b):
        return None
    for pa, pb in zip(a, b, strict=True):
        if pa == pb:
            continue
        wa = [w for w in _WORDS.findall(pa) if not w.isdigit()]
        wb = [w for w in _WORDS.findall(pb) if not w.isdigit()]
        matcher = difflib.SequenceMatcher(None, wa, wb, autojunk=False)
        for op, i1, i2, j1, j2 in matcher.get_opcodes():
            if op == "equal":
                continue
            removed = [w for w in wa[i1:i2] if w.lower() not in _EDITORIAL_WORDS]
            added = [w for w in wb[j1:j2] if w.lower() not in _EDITORIAL_WORDS]
            if max(len(removed), len(added)) > max_words:
                return None
    return "menor"


_EDITORIAL_WORDS = {"sic", "dof"}


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

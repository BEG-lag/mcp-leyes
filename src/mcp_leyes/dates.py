"""Date parsing and formatting. Dates are calendar days in Mexico City time."""

from __future__ import annotations

import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

MEXICO_CITY = ZoneInfo("America/Mexico_City")

_ISO = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})$")
_DMY = re.compile(r"^(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})$")
_TODAY = {"today", "hoy", "now", "ahora", "vigente", "current", "actual"}

MONTHS = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}
_SPANISH = re.compile(
    r"(\d{1,2})\s*(?:o\.?|º|°)?\s+de\s+(" + "|".join(MONTHS) + r")\s+(?:del?\s+)?(\d{4})",
    re.IGNORECASE,
)
_DOF_DATE = re.compile(r"(\d{2})-(\d{2})-(\d{4})")


class DateError(ValueError):
    """A date given by the user could not be understood."""


def today_mx() -> date:
    return datetime.now(MEXICO_CITY).date()


def parse_date(text: str | date | None, *, default_today: bool = True) -> date:
    """Parse YYYY-MM-DD, DD-MM-YYYY (or with / or .), or 'today'/'hoy'."""
    if isinstance(text, date):
        return text
    raw = (text or "").strip()
    if not raw:
        if default_today:
            return today_mx()
        raise DateError("Falta la fecha. Usa AAAA-MM-DD, por ejemplo 2019-05-01.")
    if raw.lower() in _TODAY:
        return today_mx()
    m = _ISO.match(raw)
    parts: tuple[int, int, int] | None = None
    if m:
        parts = (int(m[1]), int(m[2]), int(m[3]))
    elif m := _DMY.match(raw):
        parts = (int(m[3]), int(m[2]), int(m[1]))
    if parts is None:
        raise DateError(
            f"Fecha no reconocida: {raw!r}. Usa AAAA-MM-DD (2019-05-01), DD-MM-AAAA o 'hoy'."
        )
    try:
        return date(*parts)
    except ValueError as exc:
        raise DateError(f"Fecha inválida: {raw!r} ({exc}).") from exc


def parse_spanish_date(text: str) -> date | None:
    """Find a date written in words, e.g. 'el 1o. de mayo de 2019'."""
    m = _SPANISH.search(text)
    if not m:
        return None
    try:
        return date(int(m[3]), MONTHS[m[2].lower()], int(m[1]))
    except ValueError:
        return None


def parse_dof_dates(text: str) -> list[date]:
    """Every DD-MM-YYYY date in ``text``, in order (invalid ones are skipped)."""
    found = []
    for m in _DOF_DATE.finditer(text):
        try:
            found.append(date(int(m[3]), int(m[2]), int(m[1])))
        except ValueError:
            continue
    return found


def dmy(day: date | None) -> str:
    """DOF style: 01-05-2019."""
    return day.strftime("%d-%m-%Y") if day else "s/f"

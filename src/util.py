"""Small helpers shared across the build: slugs, escaping, dates, money."""
import datetime
import html
import re

MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July",
             "August", "September", "October", "November", "December"]
MONTHS_HU = ["január", "február", "március", "április", "május", "június",
             "július", "augusztus", "szeptember", "október", "november", "december"]


def esc(s):
    """HTML-escape plain text (not for strings that already contain markup)."""
    if s is None:
        return ""
    return html.escape(str(s), quote=True)


def slugify(s):
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")


def parse_date(s):
    if not s:
        return None
    s = s[:10]
    try:
        return datetime.date.fromisoformat(s)
    except ValueError:
        return None


def fmt_date_range(start, end, lang):
    """Format a Notion date range for display, e.g. '12-15 Jun 2027' / '2027. jún. 12-15.'"""
    d1, d2 = parse_date(start), parse_date(end)
    if not d1:
        return ""
    months = MONTHS_HU if lang == "hu" else MONTHS_EN
    if lang == "hu":
        mon = months[d1.month - 1][:3] + "."
        if d2 and (d2.year, d2.month) == (d1.year, d1.month) and d2.day != d1.day:
            return f"{d1.year}. {mon} {d1.day}–{d2.day}."
        if d2 and d2 != d1:
            mon2 = months[d2.month - 1][:3] + "."
            return f"{d1.year}. {mon} {d1.day}. – {d2.year}. {mon2} {d2.day}."
        return f"{d1.year}. {mon} {d1.day}."
    else:
        mon = months[d1.month - 1][:3]
        if d2 and (d2.year, d2.month) == (d1.year, d1.month) and d2.day != d1.day:
            return f"{d1.day}–{d2.day} {mon} {d1.year}"
        if d2 and d2 != d1:
            mon2 = months[d2.month - 1][:3]
            return f"{d1.day} {mon} – {d2.day} {mon2} {d2.year}"
        return f"{d1.day} {mon} {d1.year}"


def fmt_date_short(s, lang):
    d = parse_date(s)
    if not d:
        return ""
    months = MONTHS_HU if lang == "hu" else MONTHS_EN
    if lang == "hu":
        return f"{d.year}. {months[d.month - 1][:3]}."
    return f"{months[d.month - 1][:3]} {d.year}"


def fmt_huf(n):
    if n is None:
        return ""
    n = int(round(n))
    s = f"{n:,}".replace(",", " ")
    return f"{s} Ft"


def fmt_date_full(s, lang):
    d = parse_date(s)
    if not d:
        return ""
    months = MONTHS_HU if lang == "hu" else MONTHS_EN
    if lang == "hu":
        return f"{d.year}. {months[d.month - 1][:3]}. {d.day}."
    return f"{d.day} {months[d.month - 1][:3]} {d.year}"


def month_year(s, lang):
    d = parse_date(s)
    if not d:
        return ""
    months = MONTHS_HU if lang == "hu" else MONTHS_EN
    if lang == "hu":
        return f"{d.year}. {months[d.month - 1][:3]}."
    return f"{months[d.month - 1]} {d.year}"

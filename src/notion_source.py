"""
Pulls hikes from the Notion "Hikes" database at build time and turns each
published row into a Hike object with parsed EN/HU body content.

Requires env var NOTION_TOKEN (a Notion internal integration secret that has
been shared with the Hikes database — see README). NOTION_DATABASE_ID defaults
to the Magic Mountain > Hikes database used during development.

If NOTION_TOKEN is not set, returns an empty list so local builds and preview
builds without secrets still work (the site renders its "no hikes yet" empty
states).
"""
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from util import slugify

API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
DEFAULT_DATABASE_ID = "0a12493f-74f6-4b79-838b-88d3ecbb6512"

SECTION_HEADINGS = {
    "en": {
        "like": "What this one is like",
        "days": "Day by day",
        "getting_there": "Getting there and what to bring",
        "included": "Included in the price",
        "paid_separately": "Paid separately",
        "how_it_went": "How it went",
    },
    "hu": {
        "like": "Milyen ez a túra",
        "days": "Napról napra",
        "getting_there": "Odajutás és felszerelés",
        "included": "Az ár tartalmazza",
        "paid_separately": "Külön fizetendő",
        "how_it_went": "Hogy sikerült",
    },
}


@dataclass
class DayPlan:
    n: int
    title: str
    stats: str
    text: str


@dataclass
class LangContent:
    like: list = field(default_factory=list)
    days: list = field(default_factory=list)
    getting_there: list = field(default_factory=list)
    included: list = field(default_factory=list)
    paid_separately: list = field(default_factory=list)
    how_it_went: list = field(default_factory=list)


@dataclass
class Hike:
    page_id: str
    title_en: str
    title_hu: str
    teaser_en: str
    teaser_hu: str
    slug: str
    status: str
    audience: str
    country: str
    region_en: str
    region_hu: str
    difficulty: str
    days: int
    date_start: str
    date_end: str
    signup_deadline: str
    meeting_point: str
    highest_point: str
    places_total: int
    places_left: int
    price_huf: float
    child_price_huf: float
    min_age: int
    accommodation_huf: float
    cover_image: str = ""
    photos: list = field(default_factory=list)
    en: LangContent = field(default_factory=LangContent)
    hu: LangContent = field(default_factory=LangContent)

    @property
    def is_upcoming(self):
        return self.status in ("Upcoming", "Full")

    @property
    def is_past(self):
        return self.status == "Past"

    @property
    def is_full(self):
        return self.status == "Full" or (self.places_left is not None and self.places_left <= 0)


def _headers(token):
    return {"Authorization": f"Bearer {token}", "Notion-Version": NOTION_VERSION, "Content-Type": "application/json"}


def _request(url, token, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=_headers(token), method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def _rich_text_to_html(rich_text):
    out = []
    for seg in rich_text:
        text = seg.get("plain_text", "")
        if text == "":
            continue
        escaped = (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        ann = seg.get("annotations", {})
        if ann.get("bold"):
            escaped = f"<strong>{escaped}</strong>"
        if ann.get("italic"):
            escaped = f"<em>{escaped}</em>"
        href = seg.get("href")
        if href:
            escaped = f'<a href="{href}">{escaped}</a>'
        out.append(escaped)
    return "".join(out)


def _plain(rich_text):
    return "".join(seg.get("plain_text", "") for seg in rich_text)


def fetch_blocks(page_id, token):
    blocks = []
    cursor = None
    while True:
        url = f"{API}/blocks/{page_id}/children?page_size=100"
        if cursor:
            url += f"&start_cursor={cursor}"
        data = _request(url, token)
        blocks.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return blocks


def _blocks_to_flat(blocks):
    """Flatten Notion blocks into a simple event list the section parser can walk."""
    events = []
    for b in blocks:
        btype = b.get("type")
        val = b.get(btype, {})
        rt = val.get("rich_text", [])
        if btype in ("heading_1", "heading_2", "heading_3"):
            events.append({"kind": btype, "text": _plain(rt), "html": _rich_text_to_html(rt)})
        elif btype == "paragraph":
            html = _rich_text_to_html(rt)
            if html.strip():
                events.append({"kind": "p", "html": html})
        elif btype in ("bulleted_list_item", "numbered_list_item"):
            events.append({"kind": "li", "html": _rich_text_to_html(rt)})
        elif btype == "quote":
            events.append({"kind": "quote", "html": _rich_text_to_html(rt)})
        elif btype == "divider":
            events.append({"kind": "divider"})
    return events


DAY_RE_EN = re.compile(r"^Day\s+(\d+)\s*·\s*(.+?)\s*·\s*(.+)$", re.IGNORECASE)
DAY_RE_HU = re.compile(r"^(\d+)\.\s*nap\s*·\s*(.+?)\s*·\s*(.+)$", re.IGNORECASE)


def _parse_lang_block(events, lang):
    headings = SECTION_HEADINGS[lang]
    content = LangContent()
    current_section = None
    current_day = None
    bullets_buffer = []

    def flush_bullets():
        nonlocal bullets_buffer
        if current_section == "included":
            content.included.extend(bullets_buffer)
        bullets_buffer = []

    for ev in events:
        kind = ev["kind"]
        if kind == "heading_1":
            break  # next language section starts
        if kind == "heading_2":
            flush_bullets()
            text = ev["text"].strip()
            current_day = None
            current_section = None
            for key, heading in headings.items():
                if text.lower() == heading.lower():
                    current_section = key
                    break
            continue
        if kind == "heading_3" and current_section == "days":
            m = DAY_RE_EN.match(ev["text"].strip()) if lang == "en" else DAY_RE_HU.match(ev["text"].strip())
            if m:
                n, title, stats = m.groups()
                current_day = DayPlan(n=int(n), title=title.strip(), stats=stats.strip(), text="")
                content.days.append(current_day)
            continue
        if kind == "li":
            bullets_buffer.append(ev["html"])
            continue
        else:
            flush_bullets()
        if kind == "p" or kind == "quote":
            html = ev["html"] if kind == "p" else f'<span class="quote-mark">“</span>{ev["html"]}'
            if current_section == "days" and current_day is not None:
                current_day.text = (current_day.text + " " + html).strip() if current_day.text else html
            elif current_section == "like":
                content.like.append(html)
            elif current_section == "getting_there":
                content.getting_there.append(html)
            elif current_section == "paid_separately":
                content.paid_separately.append(html)
            elif current_section == "how_it_went":
                content.how_it_went.append(html)
    flush_bullets()
    return content


def parse_page_content(blocks):
    events = _blocks_to_flat(blocks)
    # split on the two top-level "# EN" / "# HU" headings
    en_start = hu_start = None
    for i, ev in enumerate(events):
        if ev["kind"] == "heading_1":
            if ev["text"].strip().upper() == "EN" and en_start is None:
                en_start = i
            elif ev["text"].strip().upper() == "HU" and hu_start is None:
                hu_start = i
    en_events = events[en_start + 1: hu_start] if en_start is not None else []
    hu_events = events[hu_start + 1:] if hu_start is not None else []
    return _parse_lang_block(en_events, "en"), _parse_lang_block(hu_events, "hu")


def _prop_text(props, name):
    p = props.get(name, {})
    t = p.get("type")
    if t == "title":
        return _plain(p.get("title", []))
    if t == "rich_text":
        return _plain(p.get("rich_text", []))
    return ""


def _prop_select(props, name):
    p = props.get(name, {})
    sel = p.get("select")
    return sel["name"] if sel else ""


def _prop_number(props, name):
    return props.get(name, {}).get("number")


def _prop_checkbox(props, name):
    return props.get(name, {}).get("checkbox", False)


def _prop_date(props, name):
    d = props.get(name, {}).get("date")
    if not d:
        return "", ""
    return d.get("start") or "", d.get("end") or ""


def _prop_files(props, name):
    urls = []
    for f in props.get(name, {}).get("files", []):
        if f.get("type") == "external":
            urls.append(f["external"]["url"])
        elif f.get("type") == "file":
            urls.append(f["file"]["url"])
    return urls


def _download(url, dest_path):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "wb") as f:
            f.write(data)
        return True
    except (urllib.error.URLError, OSError):
        return False


def fetch_hikes(dist_dir, database_id=None, token=None):
    token = token or os.environ.get("NOTION_TOKEN")
    database_id = database_id or os.environ.get("NOTION_DATABASE_ID", DEFAULT_DATABASE_ID)
    if not token:
        print("NOTION_TOKEN not set — building with zero hikes (empty states only).")
        return []

    hikes = []
    cursor = None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        try:
            data = _request(f"{API}/databases/{database_id}/query", token, "POST", body)
        except urllib.error.HTTPError as e:
            print(f"Notion query failed: {e.code} {e.read().decode()[:300]}")
            return []
        for row in data.get("results", []):
            props = row["properties"]
            if not _prop_checkbox(props, "Published"):
                continue
            status = _prop_select(props, "Status")
            if status in ("Draft", "Cancelled") or not status:
                continue
            slug = _prop_text(props, "Slug") or slugify(_prop_text(props, "Title EN") or row["id"])
            ds, de = _prop_date(props, "Dates")
            sd, _ = _prop_date(props, "Sign-up deadline")
            hike = Hike(
                page_id=row["id"],
                title_en=_prop_text(props, "Title EN"),
                title_hu=_prop_text(props, "Title HU"),
                teaser_en=_prop_text(props, "Teaser EN"),
                teaser_hu=_prop_text(props, "Teaser HU"),
                slug=slug,
                status=status,
                audience=_prop_select(props, "Audience") or "Adults",
                country=_prop_select(props, "Country"),
                region_en=_prop_text(props, "Region EN"),
                region_hu=_prop_text(props, "Region HU"),
                difficulty=_prop_select(props, "Difficulty"),
                days=int(_prop_number(props, "Days") or 0),
                date_start=ds, date_end=de,
                signup_deadline=sd,
                meeting_point=_prop_text(props, "Meeting point"),
                highest_point=_prop_text(props, "Highest point"),
                places_total=_prop_number(props, "Places total"),
                places_left=_prop_number(props, "Places left"),
                price_huf=_prop_number(props, "Price HUF"),
                child_price_huf=_prop_number(props, "Child price HUF"),
                min_age=_prop_number(props, "Min age"),
                accommodation_huf=_prop_number(props, "Accommodation HUF per night"),
            )
            cover_urls = _prop_files(props, "Cover image")
            photo_urls = _prop_files(props, "Photos")
            img_dir = os.path.join(dist_dir, "assets", "img", "hikes", slug)
            if cover_urls:
                ext = ".jpg"
                dest = os.path.join(img_dir, f"cover{ext}")
                if _download(cover_urls[0], dest):
                    hike.cover_image = f"/assets/img/hikes/{slug}/cover{ext}"
            for idx, purl in enumerate(photo_urls):
                dest = os.path.join(img_dir, f"photo-{idx+1}.jpg")
                if _download(purl, dest):
                    hike.photos.append(f"/assets/img/hikes/{slug}/photo-{idx+1}.jpg")
            try:
                blocks = fetch_blocks(row["id"], token)
                hike.en, hike.hu = parse_page_content(blocks)
            except urllib.error.HTTPError as e:
                print(f"Could not read content for {hike.title_en or slug}: {e.code}")
            hikes.append(hike)
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return hikes

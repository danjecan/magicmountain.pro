"""Reusable HTML fragments: buttons, tags, cards, form fields, bands. Ported
from the design's component library (build.py), adapted to real markup."""
import json

from content import t
from layout import icon
from util import esc

NAVY, ORANGE = "#001F61", "#FE6B00"


def btn(label, variant="primary", size="", href="#", extra="", type_=None, name=None, id_=None, glint=True):
    """glint: True for the normal press puff (the default — every button is
    something you act on), "big" for the sign-up form's wider, slower one,
    or False to opt out (e.g. a button that's really a filter toggle)."""
    cls = f"btn btn-{variant}" + (f" btn-{size}" if size else "")
    st = f' style="{extra}"' if extra else ""
    idattr = f' id="{id_}"' if id_ else ""
    glintattr = "" if not glint else (' data-glint="big"' if glint == "big" else " data-glint")
    if type_:
        nm = f' name="{name}"' if name else ""
        return f'<button type="{type_}"{nm} class="{cls}"{st}{idattr}{glintattr}>{label}</button>'
    return f'<a href="{href}" class="{cls}"{st}{idattr}{glintattr}>{label}</a>'


def tag(text, kind=""):
    return f'<span class="tag{(" tag-" + kind) if kind else ""}">{text}</span>'


def meta(icon_name, text):
    return f'<span class="meta">{icon(icon_name)}{text}</span>'


def section_head(eyebrow, title, link_text=None, link_href="#"):
    lk = f'<a href="{link_href}" class="link">{link_text}</a>' if link_text else ""
    return (f'<div style="display:flex;align-items:flex-end;justify-content:space-between;gap:24px;flex-wrap:wrap;">'
            f'<div style="display:flex;flex-direction:column;gap:8px;"><span class="eyebrow">{eyebrow}</span><h2 class="h2">{title}</h2></div>{lk}</div>')


def feature(icon_name, title, text):
    return (f'<div style="display:flex;flex-direction:column;gap:12px;">{icon(icon_name, "ico ico-lg")}'
            f'<h3 class="h4">{title}</h3><p class="muted">{text}</p></div>')


def check_item(text):
    return f'<div class="check-item">{icon("check")}<span>{text}</span></div>'


def band(tone, inner, cls="band-pad", style=""):
    st = f' style="{style}"' if style else ""
    return f'<div class="band band-{tone}{" on-dark" if tone == "dark" else ""} {cls}"{st}>{inner}</div>'


def fact_bar(items):
    cells = "".join(
        f'<div style="display:flex;flex-direction:column;gap:6px;"><span class="eyebrow" style="display:inline-flex;align-items:center;gap:8px;">{icon(i)}{l}</span><span class="h4">{v}</span></div>'
        for i, l, v in items)
    return f'<div class="band band-light facts">{cells}</div>'


def step(n, title, text):
    return (f'<div class="step"><div class="step-n">{n}</div>'
            f'<div style="display:flex;flex-direction:column;gap:4px;"><span style="font-weight:700;">{title}</span><span class="muted small">{text}</span></div></div>')


def day_row(label, title, text, stats):
    return (f'<div class="day"><div style="display:flex;flex-direction:column;gap:2px;">'
            f'<span class="eyebrow">{label}</span><span class="muted small" style="font-weight:600;">{stats}</span></div>'
            f'<div style="display:flex;flex-direction:column;gap:8px;"><h3 class="h4">{title}</h3><p class="muted">{text}</p></div></div>')


def text_block(eyebrow, title, paras):
    ps = "".join(f"<p>{p}</p>" for p in paras)
    return f'<div style="display:flex;flex-direction:column;gap:16px;"><span class="eyebrow">{eyebrow}</span><h2 class="h2">{title}</h2>{ps}</div>'


def text_block_html(eyebrow, title, inner_html):
    return f'<div style="display:flex;flex-direction:column;gap:16px;"><span class="eyebrow">{eyebrow}</span><h2 class="h2">{title}</h2>{inner_html}</div>'


def newsletter(eyebrow, title, lead, lang):
    """Mailchimp embedded form; double opt-in is handled by the Mailchimp list's own
    setting (Audience > Settings > Audience name and defaults). Posts directly to
    Mailchimp's /subscribe/post endpoint; main.js intercepts the submit to show an
    inline confirmation instead of a page navigation, and Mailchimp's own hidden
    bot-trap field (b_{u}_{id}) is included as an extra layer of spam protection."""
    from config import CONFIG
    return band("dark", f'''<div class="newsletter">
  <div style="display:flex;flex-direction:column;gap:8px;"><span class="eyebrow">{eyebrow}</span><h2 class="h2">{title}</h2><p class="lead">{lead}</p></div>
  <div>
    <form class="newsletter-form mc-embed" action="{CONFIG.mc_action}" method="post" target="_blank" novalidate>
      <div class="newsletter-row">
        <label class="sr-only" for="mce-EMAIL-{lang}">{t("nl_label", lang)}</label>
        <input type="email" name="EMAIL" id="mce-EMAIL-{lang}" class="input" placeholder="{t('nl_ph', lang)}" required>
        <div class="honeypot-field" aria-hidden="true">
          <input type="text" name="{CONFIG.mc_honeypot_field}" tabindex="-1" value="" autocomplete="off">
        </div>
        <input type="hidden" name="u" value="{CONFIG.mc_u}"><input type="hidden" name="id" value="{CONFIG.mc_id}">
        {btn(t("nl_cta", lang), "primary", type_="submit")}
      </div>
      <p class="muted small nl-note">{t("nl_note", lang)}</p>
      <p class="alert alert-success nl-msg-ok" role="status" hidden>{t("nl_pending", lang)}</p>
      <p class="alert alert-error nl-msg-err" role="alert" hidden>{t("nl_error", lang)}</p>
    </form>
  </div>
</div>''')


def field_text(label, name, id_, type_="text", placeholder="", hint="", required=True, value=""):
    h = f'<span class="muted small">{hint}</span>' if hint else ""
    req = " required" if required else ""
    return (f'<div class="field"><label for="{id_}">{label}</label>'
            f'<input class="input" type="{type_}" name="{name}" id="{id_}" placeholder="{esc(placeholder)}" value="{esc(value)}"{req}>'
            f'{h}<span class="field-error" data-error-for="{id_}"></span></div>')


def field_select(label, name, id_, options, hint="", required=True):
    """options: list of (value, label) tuples."""
    opts = "".join(f'<option value="{esc(v)}">{esc(lbl)}</option>' for v, lbl in options)
    h = f'<span class="muted small">{hint}</span>' if hint else ""
    req = " required" if required else ""
    return (f'<div class="field"><label for="{id_}">{label}</label>'
            f'<select class="input" name="{name}" id="{id_}"{req}>{opts}</select>{h}</div>')


def field_textarea(label, name, id_, placeholder="", hint=""):
    h = f'<span class="muted small">{hint}</span>' if hint else ""
    return (f'<div class="field"><label for="{id_}">{label}</label>'
            f'<textarea class="input" name="{name}" id="{id_}" placeholder="{esc(placeholder)}" rows="4"></textarea>{h}</div>')


def stepper(label, name, id_, value=0, min_=0, max_=10):
    return f'''<div class="field"><label id="{id_}-label">{label}</label>
<div class="input stepper" role="group" aria-labelledby="{id_}-label">
  <button type="button" class="stepper-dec" data-target="{id_}" aria-label="-">−</button>
  <output class="h4" id="{id_}" name="{name}" for="{id_}-inc {id_}-dec">{value}</output>
  <input type="hidden" name="{name}" id="{id_}-hidden" value="{value}">
  <button type="button" class="stepper-inc" data-target="{id_}" aria-label="+">+</button>
</div></div>'''


def checkbox_field(text, name, id_):
    return (f'<div class="checkbox-row"><input type="checkbox" name="{name}" id="{id_}" required>'
            f'<label for="{id_}"><span>{text}</span></label></div>')


# ───────── places meter, deadline countdown, filters, gallery + lightbox ─────────

def places_meter(label, free, total, large=False):
    """One segment per place: navy = taken, orange = free. free/total come straight
    from Notion's Places left / Places total, never invented."""
    total = int(total)
    free = max(0, min(int(free), total))
    segs = "".join(f'<i class="{"free" if k >= total - free else ""}"></i>' for k in range(total))
    cls = "meter" + (" meter-lg" if large else "") + (" meter-full" if free == 0 else "")
    return f'<div class="{cls}"><span class="meter-label">{label}</span><div class="meter-bar" aria-hidden="true">{segs}</div></div>'


def deadline_countdown(lang, deadline_iso):
    """Days/hours tiles counting down to a real Notion sign-up deadline. Ticks in
    the browser (main.js) and hides itself once the deadline has passed."""
    return f'''<div class="deadline" data-deadline="{deadline_iso}" hidden>
  <div style="display:flex;flex-direction:column;gap:2px;min-width:0;">
    <span class="eyebrow" style="display:inline-flex;align-items:center;gap:6px;">{icon("clock")}{t("dl_closes", lang)}</span>
  </div>
  <div class="deadline-tiles">
    <div class="tile"><b data-deadline-days>–</b><span>{t("dl_days", lang)}</span></div>
    <div class="tile"><b data-deadline-hours>–</b><span>{t("dl_hours", lang)}</span></div>
  </div>
</div>'''


def filter_select(id_, label, options):
    """options: list of (value, label) tuples, first is the 'Any' default."""
    opts = "".join(f'<option value="{esc(v)}">{esc(lbl)}</option>' for v, lbl in options)
    return (f'<span class="select"><select id="{id_}" aria-label="{esc(label)}">{opts}</select>{icon("chev")}</span>')


def filter_bar(lang, option_a, option_b, past=False, count_id="hikeCount"):
    """option_a/option_b: (value, label) lists. Upcoming hikes filter by difficulty
    and month; the past-hikes list filters by country and year instead."""
    all_label = t("l_all", lang)
    if past:
        id_a, label_a, id_b, label_b = "filterCountry", t("fl_country", lang), "filterYear", t("fl_year", lang)
    else:
        id_a, label_a, id_b, label_b = "filterDifficulty", t("fl_diff", lang), "filterMonth", t("fl_month", lang)
    return f'''<div class="filters" id="hikeFilters">
  <button type="button" class="btn btn-primary btn-sm" data-audience="all" aria-pressed="true">{all_label}</button>
  <button type="button" class="btn btn-secondary btn-sm" data-audience="Adults" aria-pressed="false">{t("adults", lang)}</button>
  <button type="button" class="btn btn-secondary btn-sm" data-audience="Families" aria-pressed="false">{t("families", lang)}</button>
  <span class="filters-sep"></span>
  {filter_select(id_a, label_a, [("", label_a + ": " + t("fl_any", lang))] + option_a)}
  {filter_select(id_b, label_b, [("", label_b + ": " + t("fl_any", lang))] + option_b)}
  <span class="muted small" style="margin-left:8px;" id="{count_id}"></span>
</div>'''


def gallery(photos, alt=""):
    """Past-hike photo gallery -> lightbox. Only rendered when real photos exist
    (no stand-in stock photos for a specific trip's account of what happened)."""
    if not photos:
        return ""
    shown = photos[:5]
    more = len(photos) - len(shown)
    items = []
    for i, src in enumerate(shown):
        span = i == 0
        h = 300 if span else 190
        is_last = i == len(shown) - 1 and more > 0
        overlay = f'<span class="g-more" data-gallery-index="{i}">{icon("photo", "ico", "width:28px;height:28px;")}+{more}</span>' if is_last else \
            f'<span class="g-zoom">{icon("expand")}</span>'
        items.append(f'<button type="button" class="g-item" data-gallery-index="{i}" style="height:{h}px;{"grid-column:1 / -1;" if span else ""}border:0;padding:0;cursor:pointer;"><img src="{src}" alt="{esc(alt)}" loading="lazy">{overlay}</button>')
    photos_json = json.dumps(photos).replace("'", "&#39;")
    return f'<div class="gallery" id="hikeGallery" data-photos=\'{photos_json}\'>{"".join(items)}</div>'


def lightbox_shell(lang):
    """One hidden lightbox per page; JS fills in the image/counter/thumbnails from
    the triggering gallery's data-photos when opened."""
    return f'''<div class="lightbox" id="lightbox" role="dialog" aria-modal="true" aria-label="{esc(t("g_swipe", lang))}" hidden style="position:fixed;inset:0;z-index:50;">
  <div class="lb-top">
    <span style="font-weight:700;letter-spacing:0.04em;" id="lbCounter"></span>
    <button type="button" class="icon-btn" id="lbClose" style="background:rgba(245,245,245,0.12);" aria-label="{t("menu_close", lang)}">{icon("close", "ico", "width:24px;height:24px;stroke-width:2.2;")}</button>
  </div>
  <div class="lb-stage">
    <img id="lbImage" src="" alt="">
    <button type="button" class="lb-nav icon-btn" id="lbPrev" style="left:24px;background:rgba(245,245,245,0.12);" aria-label="Previous">{icon("left", "ico", "width:26px;height:26px;")}</button>
    <button type="button" class="lb-nav icon-btn" id="lbNext" style="right:24px;background:rgba(245,245,245,0.12);" aria-label="Next">{icon("right", "ico", "width:26px;height:26px;")}</button>
  </div>
  <div class="lb-foot">
    <div class="lb-thumbs" id="lbThumbs"></div>
  </div>
</div>'''

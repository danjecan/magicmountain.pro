"""Renders Hike objects (from notion_source) into the card / detail markup."""
from components import (btn, check_item, day_row, deadline_countdown, fact_bar, gallery,
                         lightbox_shell, meta, newsletter, places_meter, tag, text_block_html)
from content import t
from layout import hero, url_for
from util import esc, fmt_date_full, fmt_date_range, fmt_huf, month_year

PLACEHOLDER_IMAGES = ["/assets/img/photo-ridge.jpg", "/assets/img/photo-sunset.jpg", "/assets/img/photo-volcano.jpg"]


def _title(h, lang):
    return (h.title_hu if lang == "hu" else h.title_en) or h.title_en or h.title_hu


def _teaser(h, lang):
    return (h.teaser_hu if lang == "hu" else h.teaser_en) or ""


def _region(h, lang):
    return (h.region_hu if lang == "hu" else h.region_en) or ""


def _content(h, lang):
    return h.hu if lang == "hu" else h.en


def _image(h, idx=0):
    if h.cover_image:
        return h.cover_image
    return PLACEHOLDER_IMAGES[idx % len(PLACEHOLDER_IMAGES)]


def hike_url(h, lang):
    kind = "past" if h.is_past else ""
    return url_for(f"/hikes/{kind + '/' if kind else ''}{h.slug}/", lang)


def audience_tag(h, lang):
    key = "families" if h.audience == "Families" else "adults"
    return tag(t(key, lang), "dark")


def status_tag(h, lang):
    if h.is_past:
        return ""
    if h.is_full:
        return tag(t("waiting", lang))
    return ""


def places_meter_for(h, lang, large=False):
    """None when Notion doesn't have real numbers to show — never a guessed count."""
    if h.is_past or h.places_total is None or h.places_left is None:
        return ""
    if h.is_full or h.places_left <= 0:
        return places_meter(t("full_wait", lang), 0, h.places_total, large=large)
    label = t("left_of", lang).format(left=int(h.places_left), total=int(h.places_total))
    return places_meter(label, h.places_left, h.places_total, large=large)


def hike_card(h, lang, small=False):
    media_cls = "card-img-sm" if small else "card-img"
    date_str = fmt_date_range(h.date_start, h.date_end, lang) if h.date_start else t("tbc", lang)
    metas = meta("cal", date_str + (f" · {h.days} " + t("h_day", lang) + ("s" if lang == "en" and h.days != 1 else "") if h.days else ""))
    if _region(h, lang):
        metas += meta("mtn", _region(h, lang))
    badges = audience_tag(h, lang)
    st = status_tag(h, lang)
    if st:
        badges += st
    title = _title(h, lang)
    desc = _teaser(h, lang)
    meter = places_meter_for(h, lang) if not small else ""
    foot = ""
    if h.is_upcoming and h.price_huf:
        price_label = fmt_huf(h.price_huf) + " " + t("per_person", lang)
        cta_label = t("join_wait", lang) if h.is_full else t("details", lang)
        foot = f'<div class="card-foot"><span class="h4">{price_label}</span>{btn(cta_label, "primary", "sm", hike_url(h, lang))}</div>'
    d = f'<p class="muted card-desc">{esc(desc)}</p>' if desc and not h.is_past else ""
    month_val = (h.date_start or "")[:7]
    year_val = (h.date_start or "")[:4]
    # The title link is stretched to cover the whole card (via CSS), rather than
    # wrapping the card in <a> — the price-box CTA is also a link, and a browser
    # will not tolerate one <a> nested inside another (it silently reflows the DOM).
    return f'''<div class="card card-hike" style="display:flex;flex-direction:column;height:100%;" data-glint-hover
   data-audience="{h.audience}" data-difficulty="{h.difficulty}" data-month="{month_val}" data-country="{h.country}" data-year="{year_val}">
  <div class="card-media {media_cls}"><img src="{_image(h)}" alt="" loading="lazy"><div class="card-badges">{badges}</div></div>
  <div class="card-body"><div class="card-meta">{metas}</div><h3 class="h3 card-title"><a href="{hike_url(h, lang)}" class="stretched-link">{esc(title)}</a></h3>{d}{meter}{foot}</div>
</div>'''


def _paras(lst):
    return "".join(f"<p>{p}</p>" for p in lst) if lst else ""


def fact_bar_for_hike(h, lang):
    date_str = fmt_date_range(h.date_start, h.date_end, lang) if h.date_start else t("tbc", lang)
    items = [("cal", t("h_dates", lang), date_str)]
    if h.is_past:
        if h.highest_point:
            items.append(("mtn", t("p_high", lang), h.highest_point))
        if h.places_total:
            items.append(("ppl", t("p_group", lang), f"{int(h.places_total)} " + ("fő" if lang == "hu" else "people")))
        if h.meeting_point:
            items.append(("pin", t("p_base", lang), h.meeting_point))
    else:
        items.append(("mtn", t("h_diff", lang), h.difficulty or "—"))
        if h.meeting_point:
            items.append(("pin", t("h_meet", lang), h.meeting_point))
        if h.signup_deadline:
            items.append(("flag", t("h_by", lang), fmt_date_full(h.signup_deadline, lang)))
        if h.price_huf:
            items.append(("list", t("h_price", lang), fmt_huf(h.price_huf) + " " + t("per_person", lang)))
    return fact_bar(items)


def price_box(h, lang, terms_href):
    c = _content(h, lang)
    included = c.included or [t("h_i1", lang), t("h_i2", lang), t("h_i3", lang), t("h_i4", lang)]
    checks = "".join(check_item(i) for i in included)
    sep_html = _paras(c.paid_separately)
    if not sep_html and h.accommodation_huf:
        sep_html = f"<p><strong>{t('h_acc', lang)}</strong> ~{fmt_huf(h.accommodation_huf)} " + \
                   ("/éj" if lang == "hu" else "per night") + f". {t('h_own', lang)}</p>"
    elif not sep_html:
        sep_html = f"<p>{t('h_own', lang)}</p>"
    price_line = fmt_huf(h.price_huf) if h.price_huf else "—"
    signup_href = url_for(f"/sign-up/?hike={h.slug}", lang)
    cta = t("join_wait", lang) if h.is_full else t("h_cta", lang)
    full_note = f'<p class="muted small" style="text-align:center;">{t("h_full", lang)}</p>' if h.is_full else ""
    meter = places_meter_for(h, lang, large=True)
    dl = deadline_countdown(lang, h.signup_deadline) if h.signup_deadline else ""
    return f'''<div class="card"><div class="card-body" style="gap:16px;">
  <span class="eyebrow">{t("h_price", lang)}</span>
  <div style="display:flex;flex-direction:column;gap:4px;"><span class="h2" style="color:var(--orange);">{price_line}</span><span class="muted">{t("per_person", lang)}</span></div>
  {meter}
  {dl}
  <hr class="rule">
  <span class="eyebrow">{t("h_incl", lang)}</span>
  {checks}
  <span class="eyebrow" style="margin-top:4px;">{t("h_sep", lang)}</span>
  <div class="muted" style="font-size:16px;">{sep_html}</div>
  <hr class="rule">
  {btn(cta, "primary", extra="width:100%;", href=signup_href)}
  {full_note}
  <p class="muted small" style="text-align:center;">{t("h_dep", lang)} <a href="{terms_href}">{t("f_terms", lang)}</a></p>
</div></div>
<div style="display:flex;align-items:center;gap:12px;"><img src="/assets/img/logo.png" alt="" style="width:40px;height:40px;flex:none;"><p class="muted small">{t("h_q", lang)} <a href="mailto:magicmountain.pro@gmail.com">{t("f_email", lang)}</a> {t("h_q2", lang)}</p></div>'''


def hike_detail_upcoming(h, lang, terms_href):
    c = _content(h, lang)
    eyebrow = f"{t('families' if h.audience == 'Families' else 'adults', lang)} · {h.days} {t('h_day', lang)} · {h.country}"
    tags = audience_tag(h, lang) + status_tag(h, lang)
    body = hero(_image(h), eyebrow, esc(_title(h, lang)), esc(_teaser(h, lang)), tags=tags, alt=_title(h, lang))
    body += fact_bar_for_hike(h, lang)
    days_html = "".join(
        day_row(f"{t('h_day', lang)} {d.n}" if lang == "en" else f"{d.n}. nap", esc(d.title), d.text, d.stats)
        for d in c.days)
    like_html = _paras(c.like) or f"<p>{esc(_teaser(h, lang))}</p>"
    getting_html = _paras(c.getting_there)
    left_col = f'''<div style="display:flex;flex-direction:column;gap:64px;">
  {text_block_html(t("h_the", lang), t("h_like", lang), like_html)}
  <div style="display:flex;flex-direction:column;gap:16px;">
    <span class="eyebrow">{t("h_itin", lang)}</span><h2 class="h2" style="margin-bottom:8px;">{t("h_daybyday", lang)}</h2>
    {days_html}
  </div>
  {text_block_html(t("h_prac", lang), t("h_get", lang), getting_html) if getting_html else ""}
</div>'''
    left_note = ""
    if not h.is_full and h.places_left is not None:
        left_note = f'<span class="small" style="font-weight:600;color:var(--orange);">{t("left_short", lang).format(left=int(h.places_left))}</span>'
    book_cta = t("join_wait", lang) if h.is_full else t("h_cta", lang)
    body += f'''<div class="section split split-wide">
  {left_col}
  <div class="sidebar">{price_box(h, lang, terms_href)}</div>
</div>
<div class="book-bar" id="bookBar"><div style="display:flex;flex-direction:column;"><span class="h4" style="font-size:18px;">{fmt_huf(h.price_huf) if h.price_huf else ""}</span>{left_note or f'<span class="muted" style="font-size:13px;">{t("per_person", lang)}</span>'}</div>{btn(book_cta, "primary", "sm", url_for(f"/sign-up/?hike={h.slug}", lang))}</div>'''
    return body


def hike_detail_past(h, lang):
    c = _content(h, lang)
    tags = audience_tag(h, lang) + tag(t("past_tag", lang) + " · " + month_year(h.date_start, lang))
    body = hero(_image(h), f"{t('families' if h.audience=='Families' else 'adults', lang)} · {h.days} {t('h_day', lang)} · {h.country}",
                esc(_title(h, lang)), esc(_teaser(h, lang)), tags=tags, alt=_title(h, lang))
    body += fact_bar_for_hike(h, lang)
    account_html = _paras(c.how_it_went) or _paras(c.like)
    gallery_html = gallery(h.photos, alt=_title(h, lang))
    if len(h.photos) > 5:
        gallery_html += f'<button type="button" class="link" style="display:inline-flex;align-items:center;gap:8px;background:none;border:0;cursor:pointer;" data-gallery-open="0">{t("g_all", lang).format(n=len(h.photos))}</button>'
    body += f'''<div class="section split split-wide">
  <div style="display:flex;flex-direction:column;gap:24px;">
    {text_block_html(t("p_how", lang), t("p_how_t", lang), account_html) if account_html else ""}
  </div>
  <div style="display:flex;flex-direction:column;gap:16px;">{gallery_html}</div>
</div>
<div style="padding-top:96px;">{newsletter(t("p_nl_eyebrow", lang), t("p_nl_title", lang), t("p_nl_lead", lang), lang)}</div>
{lightbox_shell(lang) if h.photos else ""}'''
    return body

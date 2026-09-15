"""Top-level page assembly: home, hike list, about, sign-up, policies, 404."""
from components import (band, btn, feature, field_select, field_text,
                         field_textarea, newsletter, section_head, step, stepper,
                         checkbox_field)
from config import CONFIG
from content import t, tl
from hikes_render import hike_card
from layout import head, TAIL, nav, footer, hero, url_for


def person_band(eyebrow, name, text, cta_label, cta_href, photo, photo_left):
    txt = (f'<div style="display:flex;flex-direction:column;justify-content:center;gap:16px;padding:48px;">'
           f'<span class="eyebrow">{eyebrow}</span><h2 class="h2">{name}</h2><p>{text}</p>'
           f'<div style="margin-top:8px;">{btn(cta_label, "secondary", href=cta_href)}</div></div>')
    ph = f'<div class="photo-ph about-photo">{photo}</div>'
    inner = (ph + txt) if photo_left else (txt + ph)
    return f'<div class="band band-light"><div class="grid-2" style="gap:0;">{inner}</div></div>'


def page_shell(lang, path, title, description, nav_active, body):
    html = head(lang, path, title, description) + nav(lang, nav_active) + f'<main id="main">{body}</main>' + footer(lang) + TAIL
    return html


# ───────────────────────── HOME ─────────────────────────

def home(lang, upcoming_hikes, past_hikes):
    cards = "".join(hike_card(h, lang) for h in upcoming_hikes[:2])
    up_section = f'<div class="grid-2">{cards}</div>' if upcoming_hikes else f'<p class="muted lead">{t("up_empty", lang)}</p>'
    past_cards = "".join(hike_card(h, lang, small=True) for h in past_hikes[:3])
    past_section = f'<div class="grid-3">{past_cards}</div>' if past_hikes else f'<p class="muted lead">{t("past_empty", lang)}</p>'
    body = hero("/assets/img/bg-peaks.jpg", t("hero_eyebrow", lang), t("hero_title", lang), t("hero_lead", lang),
                ctas=btn(t("hero_cta", lang), href=url_for("/hikes/", lang)) + btn(t("hero_cta2", lang), "secondary", href="#how-we-hike"),
                home=True, alt="")
    body += f'''<div class="section" style="display:flex;flex-direction:column;gap:32px;">
  {section_head(t("up_eyebrow", lang), t("up_title", lang), t("up_link", lang) if upcoming_hikes else None, url_for("/hikes/", lang))}
  {up_section}
</div>
<div style="padding-top:96px;" id="how-we-hike">{band("dark", f"""<div style="display:flex;flex-direction:column;gap:48px;">
  {section_head(t("how_eyebrow", lang), t("how_title", lang))}
  <div class="grid-3" style="gap:32px;">{feature("mtn", t("how1t", lang), t("how1", lang))}{feature("ppl", t("how2t", lang), t("how2", lang))}{feature("pin", t("how3t", lang), t("how3", lang))}</div>
  <hr class="rule">
  <div style="display:flex;align-items:center;gap:16px;"><img src="/assets/img/logo.png" alt="" style="width:44px;height:44px;flex:none;"><p class="muted" style="font-size:16px;">{t("cert", lang)}</p></div>
</div>""")}</div>
<div class="section" style="display:flex;flex-direction:column;gap:32px;">
  {section_head(t("past_eyebrow", lang), t("past_title", lang), t("past_link", lang) if past_hikes else None, url_for("/hikes/past/", lang))}
  {past_section}
</div>
<div style="padding-top:96px;display:flex;flex-direction:column;gap:24px;">
  {person_band(t("dan_eyebrow", lang), "Dan", t("dan_text", lang), t("dan_cta", lang), url_for("/about/", lang), t("photo_dan", lang), photo_left=False)}
  {person_band(t("anett_eyebrow", lang), "Anett", t("anett_text", lang), t("anett_cta", lang), url_for("/about/", lang), t("photo_anett", lang), photo_left=True)}
</div>
<div style="padding-top:96px;">{newsletter(t("nl_eyebrow", lang), t("nl_title", lang), t("nl_lead", lang), lang)}</div>
'''
    return page_shell(lang, "/", t("meta_home_title", lang), t("meta_home_desc", lang), None, body)


# ───────────────────────── HIKE LIST ─────────────────────────

def hike_list_upcoming(lang, hikes):
    cards = "".join(hike_card(h, lang) for h in hikes)
    grid = f'<div class="grid-3">{cards}</div>' if hikes else f'<p class="muted lead">{t("up_empty", lang)}</p>'
    count_label = f"{len(hikes)} " + ("túra időponttal" if lang == "hu" else ("hikes with dates" if len(hikes) != 1 else "hike with dates"))
    body = f'''<div class="section-first" style="display:flex;flex-direction:column;gap:32px;">
  <div style="display:flex;flex-direction:column;gap:12px;max-width:760px;"><span class="eyebrow">{t("l_eyebrow", lang)}</span><h1 class="h1">{t("l_title", lang)}</h1><p class="lead muted">{t("l_lead", lang)}</p></div>
  {f'<span class="muted small">{count_label}</span>' if hikes else ''}
  {grid}
</div>
<div style="padding-top:96px;">{newsletter(t("l_nl_eyebrow", lang), t("l_nl_title", lang), t("l_nl_lead", lang), lang)}</div>
'''
    return page_shell(lang, "/hikes/", t("meta_hikes_title", lang), t("l_lead", lang), "/hikes/", body)


def hike_list_past(lang, hikes):
    cards = "".join(hike_card(h, lang, small=True) for h in hikes)
    grid = f'<div class="grid-3">{cards}</div>' if hikes else f'<p class="muted lead">{t("past_empty", lang)}</p>'
    body = f'''<div class="section-first" style="display:flex;flex-direction:column;gap:32px;">
  <div style="display:flex;flex-direction:column;gap:12px;max-width:760px;"><span class="eyebrow">{t("past_eyebrow", lang)}</span><h1 class="h1">{t("past_title", lang)}</h1><p class="lead muted">{t("past_lead", lang)}</p></div>
  {grid}
</div>
<div style="padding-top:96px;">{newsletter(t("p_nl_eyebrow", lang), t("p_nl_title", lang), t("p_nl_lead", lang), lang)}</div>
'''
    return page_shell(lang, "/hikes/past/", t("meta_past_title", lang), t("past_lead", lang), "/hikes/past/", body)


# ───────────────────────── ABOUT ─────────────────────────

def about(lang):
    def person(name, role, paras, photo):
        ps = "".join(f"<p>{p}</p>" for p in paras)
        return (f'<div class="person"><div class="card photo-ph about-photo">{photo}</div>'
                f'<div style="display:flex;flex-direction:column;gap:16px;"><span class="eyebrow">{role}</span><h2 class="h2">{name}</h2>{ps}</div></div>')

    body = hero("/assets/img/bg-hiker.jpg", t("a_eyebrow", lang), t("a_title", lang), t("a_lead", lang), alt="")
    body += f'''<div class="section" style="display:flex;flex-direction:column;gap:96px;">
  {person("Dan", t("a_dan_role", lang), [t("a_dan1", lang), t("a_dan2", lang), t("a_dan3", lang)], t("photo_dan", lang))}
  {person("Anett", t("a_anett_role", lang), [t("a_anett1", lang), t("a_anett2", lang)], t("photo_anett", lang))}
</div>
<div style="padding-top:96px;">{band("light", f"""<div class="grid-2" style="gap:48px;align-items:start;">
  <div style="display:flex;flex-direction:column;gap:8px;"><span class="eyebrow">{t("a_why", lang)}</span><h2 class="h2">{t("a_why_t", lang)}</h2></div>
  <div style="display:flex;flex-direction:column;gap:16px;"><p>{t("a_why1", lang)}</p><p>{t("a_why2", lang)}</p></div>
</div>""")}</div>
<div class="section grid-3" style="gap:32px;">
  {feature("flag", t("a_c1t", lang), t("a_c1", lang))}{feature("ppl", t("a_c2t", lang), t("a_c2", lang))}{feature("mtn", t("a_c3t", lang), t("a_c3", lang))}
</div>
'''
    return page_shell(lang, "/about/", t("meta_about_title", lang), t("a_lead", lang), "/about/", body)


# ───────────────────────── SIGN-UP ─────────────────────────

def signup(lang, upcoming_hikes):
    terms_href = url_for("/terms/", lang)
    hike_opts = [(h.slug, f"{(h.title_hu if lang=='hu' else h.title_en) or h.title_en} · {h.date_start[:10] if h.date_start else t('tbc', lang)}")
                 for h in upcoming_hikes]
    if not hike_opts:
        hike_opts = [("", t("s_which_empty", lang))]
    which_field = field_select(t("s_which", lang), "hike_slug", "hike_slug", hike_opts, required=bool(upcoming_hikes))
    fit_opts = list(zip(["<3h", "3-6h", "6-8h", "8h+", "none"], tl("s_fit_opts", lang)))
    next_steps_inner = (f'<div style="display:flex;flex-direction:column;gap:24px;"><span class="eyebrow">{t("s_next", lang)}</span>'
                         f'{step(1, t("s_n1t", lang), t("s_n1", lang))}{step(2, t("s_n2t", lang), t("s_n2", lang))}'
                         f'{step(3, t("s_n3t", lang), t("s_n3", lang))}{step(4, t("s_n4t", lang), t("s_n4", lang))}</div>')
    next_steps_band = band("dark", next_steps_inner, "band-pad", "margin:0;padding:32px;")
    body = f'''<div class="section-first split split-wide">
  <div style="display:flex;flex-direction:column;gap:32px;">
    <div style="display:flex;flex-direction:column;gap:12px;max-width:720px;"><span class="eyebrow">{t("s_eyebrow", lang)}</span><h1 class="h1">{t("s_title", lang)}</h1><p class="lead muted">{t("s_lead", lang)}</p></div>
    <div class="card form-card"><div class="card-body" style="gap:32px;padding:32px;">
      <form id="signupForm" novalidate>
        <div style="display:flex;flex-direction:column;gap:20px;">
          <span class="eyebrow">{t("s_1", lang)}</span>
          {which_field}
          <div class="grid-2" style="gap:20px;">{stepper(t("s_adults", lang), "adults", "adults_count", 2)}{stepper(t("s_children", lang), "children", "children_count", 0)}</div>
        </div>
        <hr class="rule" style="margin:20px 0;">
        <div style="display:flex;flex-direction:column;gap:20px;">
          <span class="eyebrow">{t("s_2", lang)}</span>
          <div class="grid-2" style="gap:20px;">
            {field_text(t("s_name", lang), "name", "name")}
            {field_text(t("s_email", lang), "email", "email", type_="email")}
            {field_text(t("s_phone", lang), "phone", "phone", hint=t("s_phone_h", lang))}
            {field_text(t("s_from", lang), "from_where", "from_where", hint=t("s_from_h", lang), required=False)}
          </div>
        </div>
        <hr class="rule" style="margin:20px 0;">
        <div style="display:flex;flex-direction:column;gap:20px;">
          <span class="eyebrow">{t("s_3", lang)}</span>
          {field_select(t("s_fit", lang), "fitness", "fitness", fit_opts)}
          {field_textarea(t("s_notes", lang), "notes", "notes", t("s_notes_ph", lang), t("s_notes_h", lang))}
        </div>
        <hr class="rule" style="margin:20px 0;">
        <div style="display:flex;flex-direction:column;gap:12px;">
          {checkbox_field(t("s_chk1", lang).format(terms=terms_href), "agree_terms", "agree_terms")}
          {checkbox_field(t("s_chk2", lang).format(terms=terms_href), "agree_privacy", "agree_privacy")}
        </div>
        <div class="honeypot-field" aria-hidden="true">
          <label for="{CONFIG.gas_honeypot_field}">Leave this field empty</label>
          <input type="text" name="{CONFIG.gas_honeypot_field}" id="{CONFIG.gas_honeypot_field}" tabindex="-1" autocomplete="off">
        </div>
        <div class="form-actions" style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;margin-top:20px;">
          {btn(t("s_send", lang), "primary", type_="submit")}
          <span class="muted small">{t("s_nopay", lang)}</span>
        </div>
        <div class="alert alert-success" id="signupOk" role="status" hidden>
          <strong>{t("s_ok_title", lang)}</strong><br>{t("s_ok_text", lang)}
        </div>
        <div class="alert alert-error" id="signupErr" role="alert" hidden>
          {t("s_err", lang)} <a href="mailto:magicmountain.pro@gmail.com">{t("f_email", lang)}</a>.
        </div>
      </form>
    </div></div>
  </div>
  <div class="sidebar">
    {next_steps_band}
    <p class="muted small">{t("s_talk", lang)} <a href="#">[PHONE]</a></p>
  </div>
</div>
'''
    return page_shell(lang, "/sign-up/", t("meta_signup_title", lang), t("s_lead", lang), "/sign-up/", body)


# ───────────────────────── POLICIES ─────────────────────────

def policies(lang):
    secs = [(f"pol{n}t", f"pol{n}") for n in range(1, 9)]
    ids = ["booking", "cancellation", "changes", "insurance", "responsibilities", "children", "privacy", "contact"]
    toc = "".join(f'<a href="#{ids[idx]}" class="link">{t(a, lang)}</a>' for idx, (a, _) in enumerate(secs))
    body_secs = "".join(
        f'<div id="{ids[idx]}" style="display:flex;flex-direction:column;gap:12px;padding:32px 0;border-top:1px solid rgba(0,31,97,0.12);"><h2 class="h3">{t(a, lang)}</h2>{"".join(f"<p>{p}</p>" for p in tl(b, lang))}</div>'
        for idx, (a, b) in enumerate(secs))
    other_lang_href = url_for("/terms/", "hu" if lang == "en" else "en")
    other_note = (f'Magyar változat: <a href="{other_lang_href}">Feltételek és lemondás</a>' if lang == "en"
                  else f'English version: <a href="{other_lang_href}">Terms and refunds</a>')
    body = f'''<div class="section-first toc">
  <div class="sidebar toc-nav" style="gap:12px;"><span class="eyebrow">{t("pol_toc", lang)}</span>{toc}<hr class="rule"><span class="muted small">{other_note}</span></div>
  <div style="display:flex;flex-direction:column;gap:8px;max-width:800px;">
    <span class="eyebrow">{t("pol_eyebrow", lang)}</span><h1 class="h1" style="margin-bottom:8px;">{t("pol_title", lang)}</h1>
    <p class="lead muted" style="margin-bottom:24px;">{t("pol_lead", lang)}</p>
    {body_secs}
  </div>
</div>
'''
    return page_shell(lang, "/terms/", t("meta_policies_title", lang), t("pol_lead", lang), "/terms/", body)


# ───────────────────────── 404 ─────────────────────────

def not_found(lang):
    body = f'''<div class="section-first" style="display:flex;flex-direction:column;gap:16px;align-items:flex-start;min-height:40vh;justify-content:center;">
  <span class="eyebrow">404</span>
  <h1 class="h1">{t("404_title", lang)}</h1>
  <p class="lead muted">{t("404_text", lang)}</p>
  {btn(t("404_home", lang), "primary", href=url_for("/", lang))}
</div>
'''
    return page_shell(lang, "/404/", t("meta_404_title", lang), t("404_text", lang), None, body)

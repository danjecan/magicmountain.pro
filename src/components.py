"""Reusable HTML fragments: buttons, tags, cards, form fields, bands. Ported
from the design's component library (build.py), adapted to real markup."""
from content import t
from layout import icon
from util import esc

NAVY, ORANGE = "#001F61", "#FE6B00"


def btn(label, variant="primary", size="", href="#", extra="", type_=None, name=None):
    cls = f"btn btn-{variant}" + (f" btn-{size}" if size else "")
    st = f' style="{extra}"' if extra else ""
    if type_:
        nm = f' name="{name}"' if name else ""
        return f'<button type="{type_}"{nm} class="{cls}"{st}>{label}</button>'
    return f'<a href="{href}" class="{cls}"{st}>{label}</a>'


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

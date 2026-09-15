"""Page shell: <head>, nav, footer, and the icon set. Ported from the design's
build.py components, turned into real semantic HTML (real <nav>, a working
mobile menu, SEO/OG meta, hreflang alternates) instead of canvas artboard markup."""
from content import t
from hero_art import HERO_LAYERS_SVG
from util import esc

SITE_NAME = "Magic Mountain"
SITE_URL = "https://magicmountain.pro"

ICONS = {
    "cal": '<rect x="3" y="5" width="18" height="16" rx="2"></rect><path d="M3 10h18M8 3v4M16 3v4"></path>',
    "mtn": '<path d="M3 20l6-11 4 6 2-3 6 8z"></path>',
    "ppl": '<circle cx="9" cy="8" r="3.5"></circle><path d="M2.5 20a6.5 6.5 0 0 1 13 0M16 8a3 3 0 0 1 0 6M21.5 20a5.5 5.5 0 0 0-4-5.3"></path>',
    "pin": '<path d="M12 21s-6-5.5-6-11a6 6 0 0 1 12 0c0 5.5-6 11-6 11z"></path><circle cx="12" cy="10" r="2.2"></circle>',
    "list": '<rect x="3" y="4" width="18" height="16" rx="2"></rect><path d="M7 9h10M7 13h6M7 17h4"></path>',
    "check": '<path d="M4 12.5l5 5L20 6.5"></path>',
    "chev": '<path d="M6 9l6 6 6-6"></path>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"></path>',
    "close": '<path d="M6 6l12 12M18 6L6 18"></path>',
    "left": '<path d="M15 5l-7 7 7 7"></path>',
    "right": '<path d="M9 5l7 7-7 7"></path>',
    "expand": '<path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"></path>',
    "photo": '<rect x="3" y="5" width="18" height="14" rx="2"></rect><circle cx="9" cy="10" r="1.8"></circle><path d="M3 17l5-4 4 3 3-2 6 4"></path>',
    "flag": '<path d="M5 21V4M5 4h12l-2 4 2 4H5"></path>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"></rect><path d="M3 7l9 6 9-6"></path>',
    "clock": '<circle cx="12" cy="12" r="9"></circle><path d="M12 7v5l3 2"></path>',
}


def icon(name, cls="ico", style=""):
    st = f' style="{style}"' if style else ""
    return f'<svg viewBox="0 0 24 24" class="{cls}" aria-hidden="true"{st}>{ICONS[name]}</svg>'


def url_for(path, lang):
    """path like '/', '/hikes/', '/hikes/slug/', '/about/' -> full site-relative URL for lang."""
    if lang == "hu":
        return "/hu" + path if path != "/" else "/hu/"
    return path


def head(lang, path, title, description, canonical_path=None, og_image=None):
    canonical_path = canonical_path or path
    en_url = SITE_URL + url_for(canonical_path, "en")
    hu_url = SITE_URL + url_for(canonical_path, "hu")
    this_url = SITE_URL + url_for(canonical_path, lang)
    og = og_image or (SITE_URL + "/assets/img/bg-peaks.jpg")
    return f'''<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{this_url}">
<link rel="alternate" hreflang="en" href="{en_url}">
<link rel="alternate" hreflang="hu" href="{hu_url}">
<link rel="alternate" hreflang="x-default" href="{en_url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{this_url}">
<meta property="og:image" content="{og}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/img/logo.png" type="image/png">
<link rel="apple-touch-icon" href="/assets/img/logo.png">
<link rel="stylesheet" href="/assets/css/site.css">
</head>
<body>
<a class="skip-link" href="#main">{t("skip_link", lang)}</a>
'''


def tail():
    from config import CONFIG
    return (f'<script>window.MM_GAS_URL = {CONFIG.gas_url!r};</script>\n'
            f'<script src="/assets/js/main.js" defer></script>\n</body>\n</html>\n')


TAIL = tail()


def lang_switch(lang, path):
    en_href = url_for(path, "en")
    hu_href = url_for(path, "hu")
    return (f'<div class="lang">'
            f'<a href="{en_href}" class="{"on" if lang == "en" else ""}" hreflang="en">EN</a>'
            f'<a href="{hu_href}" class="{"on" if lang == "hu" else ""}" hreflang="hu">HU</a>'
            f'</div>')


NAV_ITEMS = [("nav_up", "/hikes/"), ("nav_past", "/hikes/past/"), ("nav_about", "/about/")]


def nav(lang, active_path=None):
    def a(key, href, cls=""):
        is_active = active_path == href
        classes = (cls + (" active" if is_active else "")).strip()
        aria = ' aria-current="page"' if is_active else ""
        return f'<a href="{url_for(href, lang)}" class="{classes}"{aria}>{t(key, lang)}</a>'

    def sheet_link(key, href):
        is_active = active_path == href
        return f'<a href="{url_for(href, lang)}" class="{"active" if is_active else ""}">{t(key, lang)}{icon("right")}</a>'

    signup_href = url_for("/sign-up/", lang)
    links_desktop = "".join(a(k, h) for k, h in NAV_ITEMS)
    sheet_links = "".join(sheet_link(k, h) for k, h in NAV_ITEMS)
    social = "".join(
        f'<a href="{href}" class="link">{esc(label)}</a>' for label, href in (
            (t("f_email", lang), "mailto:magicmountain.pro@gmail.com"),
            ("Facebook · Magic Mountain", "https://www.facebook.com/magicmountain.pro"),
            ("Facebook · Családi kalandozások a Bükkben", "https://www.facebook.com/profile.php?id=61575855355176"),
        ))
    return f'''<header>
<div class="nav">
  <a href="{url_for("/", lang)}" style="display:flex;align-items:center;gap:14px;">
    <img src="/assets/img/logo.png" alt="{SITE_NAME}" style="width:52px;height:52px;">
    <span class="brand">{SITE_NAME}</span>
  </a>
  <div class="nav-links">
    {links_desktop}
    {lang_switch(lang, active_path or "/")}
    <a href="{signup_href}" class="btn btn-primary btn-sm">{t("nav_cta", lang)}</a>
    <button type="button" class="nav-menu-btn" id="navMenuBtn" aria-expanded="false" aria-controls="navSheet" aria-label="{t("menu_open", lang)}">
      {icon("menu", "ico", "width:26px;height:26px;stroke-width:2;")}
    </button>
  </div>
</div>
<div class="sheet" id="navSheet" hidden>
  <div style="display:flex;align-items:center;justify-content:space-between;height:64px;padding:0 16px;border-bottom:1px solid rgba(0,31,97,0.12);flex:none;">
    <a href="{url_for("/", lang)}" style="display:flex;align-items:center;gap:10px;">
      <img src="/assets/img/logo.png" alt="" style="width:40px;height:40px;"><span class="brand" style="font-size:15px;">{SITE_NAME}</span>
    </a>
    <div style="display:flex;align-items:center;gap:8px;">
      {lang_switch(lang, active_path or "/")}
      <button type="button" class="icon-btn" id="navSheetClose" style="background:var(--peach);" aria-label="{t("menu_close", lang)}">{icon("close", "ico", "width:24px;height:24px;stroke-width:2.2;")}</button>
    </div>
  </div>
  <nav class="sheet-links" aria-label="{t("nav_about", lang)}">{sheet_links}</nav>
  <div style="display:flex;flex-direction:column;gap:12px;padding:32px 16px;">
    <a href="{signup_href}" class="btn btn-primary" style="width:100%;">{t("nav_cta", lang)}</a>
    <span class="muted small" style="text-align:center;">{t("m_note", lang)}</span>
  </div>
  <div style="margin:auto 16px 24px;padding:24px 20px;border-radius:12px;background:var(--peach);display:flex;flex-direction:column;gap:10px;">
    <span class="eyebrow">{t("f_contact", lang)}</span>{social}
  </div>
</div>
</header>
'''


def col(title, links):
    items = "".join(f'<a href="{h}" class="link">{esc(x)}</a>' for x, h in links)
    return f'<div style="display:flex;flex-direction:column;gap:10px;"><span class="eyebrow">{title}</span>{items}</div>'


def footer(lang):
    L = lambda k: t(k, lang)
    terms = url_for("/terms/", lang)
    signup = url_for("/sign-up/", lang)
    up = url_for("/hikes/", lang)
    past = url_for("/hikes/past/", lang)
    about = url_for("/about/", lang)
    return f'''<footer class="footer on-dark">
  <div class="footer-inner">
    <div class="footer-grid">
      <div style="display:flex;flex-direction:column;gap:16px;">
        <div style="display:flex;align-items:center;gap:12px;"><img src="/assets/img/logo.png" alt="" style="width:44px;height:44px;"><span class="brand" style="font-size:18px;">{SITE_NAME}</span></div>
        <p class="muted" style="font-size:16px;max-width:360px;">{L("f_desc")}</p>
        <p class="muted small" style="opacity:0.8;">#weareuimla #societateaghizilor</p>
      </div>
      {col(L("f_hikes"), [(L("nav_up"), up), (L("nav_past"), past), (L("f_signup"), signup)])}
      {col(L("f_contact"), [(L("f_email"), "mailto:magicmountain.pro@gmail.com"), (L("nav_about"), about)])}
      {col(L("f_follow"), [("Facebook · Magic Mountain", "https://www.facebook.com/magicmountain.pro"), ("Facebook · Családi kalandozások a Bükkben (Anett)", "https://www.facebook.com/profile.php?id=61575855355176")])}
      {col(L("f_legal"), [(L("f_terms"), terms), (L("f_privacy"), terms + "#privacy"), (L("f_insurance"), terms + "#insurance")])}
    </div>
    <hr class="rule">
    <div class="muted small" style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;">
      <span>© {__import__("datetime").date.today().year} {L("f_rights")}</span>
      <span><a href="{url_for("/", "hu" if lang=="en" else "en")}" class="muted">{"Magyar" if lang=="en" else "English"}</a></span>
    </div>
  </div>
</footer>
'''


def hero(img, eyebrow, title_html, lead, ctas="", tags="", home=False, alt=""):
    tg = f'<div style="display:flex;gap:8px;flex-wrap:wrap;">{tags}</div>' if tags else ""
    ct = f'<div style="display:flex;gap:12px;margin-top:8px;flex-wrap:wrap;">{ctas}</div>' if ctas else ""
    return f'''<div class="band band-dark on-dark hero{" hero-home" if home else ""}" style="margin:0;border-radius:0;">
  <div class="hero-bg" data-parallax="0.5"><img src="{img}" alt="{esc(alt)}"></div><div class="hero-shade"></div>{HERO_LAYERS_SVG}
  <div class="hero-content" data-parallax="0.15">{tg}<span class="eyebrow" style="color:var(--peach);">{eyebrow}</span><h1 class="h1">{title_html}</h1><p class="lead" style="max-width:600px;">{lead}</p>{ct}</div>
</div>
'''

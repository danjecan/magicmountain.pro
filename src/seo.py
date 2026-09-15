"""sitemap.xml and robots.txt generation."""
from layout import SITE_URL, url_for


def build_sitemap(static_paths, hike_paths):
    all_paths = static_paths + hike_paths
    urls = []
    for path in all_paths:
        en = SITE_URL + url_for(path, "en")
        hu = SITE_URL + url_for(path, "hu")
        urls.append(f'''  <url>
    <loc>{en}</loc>
    <xhtml:link rel="alternate" hreflang="en" href="{en}"/>
    <xhtml:link rel="alternate" hreflang="hu" href="{hu}"/>
  </url>
  <url>
    <loc>{hu}</loc>
    <xhtml:link rel="alternate" hreflang="en" href="{en}"/>
    <xhtml:link rel="alternate" hreflang="hu" href="{hu}"/>
  </url>''')
    body = "\n".join(urls)
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">
{body}
</urlset>
'''


ROBOTS = f"""User-agent: *
Allow: /

Sitemap: {SITE_URL}/sitemap.xml
"""

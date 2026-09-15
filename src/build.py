#!/usr/bin/env python3
"""Builds the static site into ./dist. Run with: python3 src/build.py [--out dist]

Reads hikes from the Notion "Hikes" database (NOTION_TOKEN env var; builds with
zero hikes if it isn't set, so the site still renders its empty states) and the
sign-up / newsletter endpoints from environment variables (see config.py and
README.md).
"""
import argparse
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(__file__))

import pages  # noqa: E402
from layout import url_for  # noqa: E402
from notion_source import fetch_hikes  # noqa: E402
from seo import ROBOTS, build_sitemap  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def write_page(dist_dir, lang, path, html):
    """path like '/', '/hikes/', '/hikes/some-slug/'."""
    rel = url_for(path, lang)
    if rel == "/":
        out_dir = dist_dir
    else:
        out_dir = os.path.join(dist_dir, rel.strip("/"))
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)


def copy_assets(dist_dir):
    src = os.path.join(ROOT, "assets")
    dst = os.path.join(dist_dir, "assets")
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "dist"))
    args = ap.parse_args()
    dist_dir = args.out

    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir)

    copy_assets(dist_dir)

    hikes = fetch_hikes(dist_dir)
    upcoming = sorted([h for h in hikes if h.is_upcoming], key=lambda h: h.date_start or "9999")
    past = sorted([h for h in hikes if h.is_past], key=lambda h: h.date_start or "", reverse=True)
    print(f"Loaded {len(hikes)} published hikes ({len(upcoming)} upcoming, {len(past)} past).")

    static_paths = ["/", "/hikes/", "/hikes/past/", "/about/", "/sign-up/", "/terms/"]
    hike_paths = [f"/hikes/{h.slug}/" for h in upcoming] + [f"/hikes/past/{h.slug}/" for h in past]

    for lang in ("en", "hu"):
        write_page(dist_dir, lang, "/", pages.home(lang, upcoming, past))
        write_page(dist_dir, lang, "/hikes/", pages.hike_list_upcoming(lang, upcoming))
        write_page(dist_dir, lang, "/hikes/past/", pages.hike_list_past(lang, past))
        write_page(dist_dir, lang, "/about/", pages.about(lang))
        write_page(dist_dir, lang, "/sign-up/", pages.signup(lang, upcoming))
        write_page(dist_dir, lang, "/terms/", pages.policies(lang))

        from hikes_render import hike_detail_upcoming, hike_detail_past
        terms_href = url_for("/terms/", lang)
        for h in upcoming:
            body = pages.page_shell(lang, f"/hikes/{h.slug}/",
                                     (h.title_hu if lang == "hu" else h.title_en) + " — Magic Mountain",
                                     (h.teaser_hu if lang == "hu" else h.teaser_en) or "", f"/hikes/{h.slug}/",
                                     hike_detail_upcoming(h, lang, terms_href))
            write_page(dist_dir, lang, f"/hikes/{h.slug}/", body)
        for h in past:
            body = pages.page_shell(lang, f"/hikes/past/{h.slug}/",
                                     (h.title_hu if lang == "hu" else h.title_en) + " — Magic Mountain",
                                     (h.teaser_hu if lang == "hu" else h.teaser_en) or "", "/hikes/past/",
                                     hike_detail_past(h, lang))
            write_page(dist_dir, lang, f"/hikes/past/{h.slug}/", body)

    # Root 404 (GitHub Pages only serves one, at the site root, regardless of language/path)
    with open(os.path.join(dist_dir, "404.html"), "w", encoding="utf-8") as f:
        f.write(pages.not_found("en"))

    with open(os.path.join(dist_dir, "CNAME"), "w", encoding="utf-8") as f:
        f.write("magicmountain.pro\n")

    with open(os.path.join(dist_dir, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(ROBOTS)

    with open(os.path.join(dist_dir, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(build_sitemap(static_paths, hike_paths))

    # GitHub Pages otherwise runs content through Jekyll, which ignores files/folders
    # starting with an underscore (none here) but also strips nothing we need; this
    # file just disables the Jekyll build step so plain files are served as-is.
    open(os.path.join(dist_dir, ".nojekyll"), "w").close()

    print(f"Built site into {dist_dir}")


if __name__ == "__main__":
    main()

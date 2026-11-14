#!/usr/bin/env python3
"""Check that every internal link in the BUILT site resolves (stdlib only).

verify_post.py sees the markdown, so it can tell that a link is there but not that it opens:
`../agentopt/` written from ai-concept looks fine in markdown and is a 404 on the live site.
This script reads the hugo build output instead and resolves every same-site <a href> and
<img src> inside each post's article body against the files that were actually built.

Usage (after `hugo.sh ... -d .tools/public`):
  python3 .claude/skills/hugo-publisher/scripts/check_links.py .tools/public            # whole site
  python3 .claude/skills/hugo-publisher/scripts/check_links.py .tools/public <section>/<slug>

Exit 0: no broken links. Exit 1: broken links listed. Exit 2: the build directory is missing.
"""
import html
import os
import re
import sys
from urllib.parse import unquote, urljoin, urlparse

BASE = "https://datasciocean.com"
SECTIONS = ("paper-intro", "ai-concept", "python-tutorial", "other")


def post_pages(root, only=None):
    for lang in ("", "en/"):
        for sec in SECTIONS:
            d = os.path.join(root, lang + sec)
            if not os.path.isdir(d):
                continue
            for slug in sorted(os.listdir(d)):
                if only and f"{sec}/{slug}" != only:
                    continue
                p = os.path.join(d, slug, "index.html")
                if slug != "page" and os.path.isfile(p):
                    yield f"{BASE}/{lang}{sec}/{slug}/", p


def exists(root, url):
    f = os.path.join(root, unquote(urlparse(url).path).lstrip("/"))
    return os.path.isfile(f) or os.path.isfile(os.path.join(f, "index.html"))


def body_of(page_html):
    """The post's own content: links in the menu, footer and related-posts are the theme's."""
    m = re.search(r'<div class="?content"?[^>]*>(.*)', page_html, re.S)
    body = m.group(1) if m else page_html
    cut = body.find("class=post-footer")
    return body[:cut] if cut > 0 else body


def main():
    if len(sys.argv) < 2 or not os.path.isdir(sys.argv[1]):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    root, only = sys.argv[1], (sys.argv[2].strip("/") if len(sys.argv) > 2 else None)
    pages = list(post_pages(root, only))
    if not pages:
        print(f"no built post pages under {root}" + (f" for {only}" if only else ""), file=sys.stderr)
        return 2
    broken = []
    for url, path in pages:
        body = body_of(open(path, encoding="utf-8").read())
        refs = re.findall(r'<(?:a|img)\b[^>]*?\b(?:href|src)=("[^"]*"|[^ >]+)', body)
        for ref in sorted(set(r.strip('"') for r in refs)):
            if ref.startswith(("#", "mailto:", "javascript:", "data:")):
                continue
            full = urljoin(url, html.unescape(ref)).split("#")[0].split("?")[0]
            if full.startswith(BASE) and not exists(root, full):
                broken.append((url, ref))
    for url, ref in broken:
        print(f"BROKEN  {url.removeprefix(BASE)}  ->  {ref}")
    print(f"{len(pages)} post pages checked, {len(broken)} broken internal links")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())

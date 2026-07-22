#!/usr/bin/env python3
"""Sanity checks for a paper-intro post before opening a PR.

Usage:
    python3 verify_post.py content/posts/paper-intro/<slug>

Not a substitute for a real `hugo build` (see references/hugo-build.md) --
this only catches mistakes that don't require actually rendering the site.
"""
import re
import sys
from pathlib import Path

REQUIRED_FRONT_MATTER_FIELDS = [
    "title", "date", "lastmod", "draft", "description",
    "featuredImage", "tags", "categories", "url",
]

SHORTCODE_SRC_RE = re.compile(r'\{\{<\s*image\s+([^>]*?)\s*>\}\}')
SRC_ATTR_RE = re.compile(r'src="([^"]+)"')
BARE_INLINE_MATH_RE = re.compile(r'(?<!\$)\$(?!\$)[^$\n]+?(?<!\$)\$(?!\$)')
RELATIVE_POST_LINK_RE = re.compile(r'\]\(\.\./[a-z0-9-]+/?\)')
HEADING_RE = re.compile(r'^(#{1,6})\s+\S', re.MULTILINE)
CODE_FENCE_RE = re.compile(r'^(`{3,}).*?\n.*?^\1\s*$', re.MULTILINE | re.DOTALL)

# zh-tw ranges are looser and skew shorter: CJK characters carry more
# information per character than Latin ones, and this site's existing
# zh-tw front matter is inconsistent about translating vs. keeping the
# paper's original English title, so a tight range would be mostly noise.
SEO_LEN_RANGES = {
    "index.en.md": {"title": (30, 70), "description": (120, 170)},
    "index.zh-tw.md": {"title": (10, 55), "description": (40, 180)},
}


def split_front_matter(text):
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end == -1:
        return None, text
    fm = text[3:end].strip("\n")
    body = text[end + 4:]
    return fm, body


def check_front_matter_fields(fm_text, label, errors):
    for field in REQUIRED_FRONT_MATTER_FIELDS:
        if not re.search(rf'^{re.escape(field)}\s*:', fm_text, re.MULTILINE):
            errors.append(f"{label}: front matter missing required field '{field}'")

    m = re.search(r'^featuredImage\s*:\s*"([^"]+)"', fm_text, re.MULTILINE)
    if m:
        return m.group(1)
    return None


def check_seo_field_lengths(fm_text, label, warnings):
    ranges = SEO_LEN_RANGES.get(label)
    if not ranges:
        return
    m = re.search(r'^title\s*:\s*"((?:[^"\\]|\\.)*)"', fm_text, re.MULTILINE)
    if m:
        length = len(m.group(1))
        lo, hi = ranges["title"]
        if not (lo <= length <= hi):
            warnings.append(
                f"{label}: title is {length} chars, outside the usual {lo}-{hi} "
                "char range search results tend to display well"
            )
    m = re.search(r'^description\s*:\s*"((?:[^"\\]|\\.)*)"', fm_text, re.MULTILINE)
    if m:
        length = len(m.group(1))
        lo, hi = ranges["description"]
        if not (lo <= length <= hi):
            warnings.append(
                f"{label}: description is {length} chars, outside the usual "
                f"{lo}-{hi} char range"
            )


def check_heading_structure(body_text, label, errors, warnings):
    # Prompt templates / code samples embedded in a paper-intro post routinely
    # contain lines starting with '#' (Python/YAML comments) -- strip fenced
    # code blocks first so those aren't mistaken for markdown headings.
    prose = CODE_FENCE_RE.sub('', body_text)

    if re.search(r'^#\s+\S', prose, re.MULTILINE):
        errors.append(
            f"{label}: body contains a top-level '# ' heading -- the front-matter "
            "title already renders as H1, don't duplicate it in the body"
        )

    prev = 1
    warned = False
    for m in HEADING_RE.finditer(prose):
        lvl = len(m.group(1))
        if lvl == 1:
            continue
        if not warned and lvl > prev + 1:
            warnings.append(
                f"{label}: heading level skips from H{prev} to H{lvl} "
                f"(near {m.group(0)[:60]!r}) -- keep hierarchy contiguous"
            )
            warned = True
        prev = lvl


def check_internal_links(body_text, label, warnings):
    if not RELATIVE_POST_LINK_RE.search(body_text):
        warnings.append(
            f"{label}: no relative links to other paper-intro posts found "
            "(e.g. '](../other-slug/)') -- see hugo-conventions.md's internal-linking "
            "section; fine to skip if genuinely no related post exists"
        )


def check_body(body_text, label, post_dir, errors, warnings):
    if "```figure-map" in body_text:
        errors.append(f"{label}: trailing figure-map block was not stripped")
    if "NO-MANIFEST" in body_text:
        errors.append(f"{label}: NO-MANIFEST pipeline comment leaked into rendered body")

    unresolved = body_text.count("UNRESOLVED IMAGE")
    if unresolved:
        warnings.append(
            f"{label}: {unresolved} UNRESOLVED IMAGE placeholder(s) present -- "
            "make sure each is also called out in the PR description"
        )

    bare_math = BARE_INLINE_MATH_RE.findall(body_text)
    if bare_math:
        warnings.append(
            f"{label}: {len(bare_math)} possible bare-$ inline math span(s) found "
            "(this site only passthrough-renders \\( ... \\) inline, not single $...$) "
            f"e.g. {bare_math[0]!r}"
        )

    for match in SHORTCODE_SRC_RE.finditer(body_text):
        attrs = match.group(1)
        src_match = SRC_ATTR_RE.search(attrs)
        if not src_match:
            errors.append(f"{label}: found an {{{{< image >}}}} shortcode with no src=\"...\"")
            continue
        src = src_match.group(1)
        if src.startswith("http://") or src.startswith("https://") or src.startswith("data:"):
            continue
        if not (post_dir / src).exists():
            errors.append(f"{label}: image shortcode references '{src}', but {post_dir / src} does not exist")


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)

    post_dir = Path(sys.argv[1])
    if not post_dir.is_dir():
        print(f"ERROR: {post_dir} is not a directory")
        sys.exit(2)

    errors = []
    warnings = []

    lang_files = {
        "index.en.md": post_dir / "index.en.md",
        "index.zh-tw.md": post_dir / "index.zh-tw.md",
    }

    for label, path in lang_files.items():
        if not path.exists():
            errors.append(
                f"{path} does not exist -- this site requires BOTH index.en.md and "
                "index.zh-tw.md in the same post directory (see "
                "references/bilingual-bundle-gotcha.md: a single-language bundle "
                "silently breaks images for every language, not just the missing one)"
            )

    for label, path in lang_files.items():
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        fm, body = split_front_matter(text)
        if fm is None:
            errors.append(f"{label}: could not find a '---' delimited front matter block")
            continue
        featured = check_front_matter_fields(fm, label, errors)
        if featured and not (post_dir / featured).exists():
            errors.append(f"{label}: featuredImage '{featured}' does not exist in {post_dir}")
        check_seo_field_lengths(fm, label, warnings)
        check_body(body, label, post_dir, errors, warnings)
        check_heading_structure(body, label, errors, warnings)
        check_internal_links(body, label, warnings)

    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"  - {w}")
        print()

    if errors:
        print("FAILED:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    print(f"OK: {post_dir} passed all checks"
          + (f" ({len(warnings)} warning(s), see above)" if warnings else ""))


if __name__ == "__main__":
    main()

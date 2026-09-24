#!/usr/bin/env python3
"""Sanity checks for a post before opening a PR.

Works for any section (paper-intro, ai-concept, python-tutorial, other) --
pass the post's bundle directory.

Usage:
    python3 verify_post.py content/posts/<section>/<slug>

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
# A backslash-escaped \$ is a literal dollar sign -- prices ("\$0.001/doc vs
# \$0.10/doc") are the common case and are not math, so neither delimiter
# may be escaped.
BARE_INLINE_MATH_RE = re.compile(r'(?<![$\\])\$(?!\$)[^$\n]+?(?<![$\\])\$(?!\$)')
# Even unescaped, most paired $ in these posts are prices ("$5 or $10",
# "costs $1.90, while Opus costs $9") or shell/nginx variables ("$uri
# $host") -- all of which render correctly as literal text precisely
# because this site does not passthrough bare $. Only warn when what sits
# between the delimiters actually looks like LaTeX: a backslash command,
# a sub/superscript, a brace group, or a bare one-or-two-char symbol (a
# longer bare word is far more likely a shell variable like $uri than math).
MATHY_INNER_RE = re.compile(
    r'[\\^_{}]|\A\s*[A-Za-zα-ωΑ-Ω][A-Za-z0-9α-ωΑ-Ω]?\s*\Z'
)
RELATIVE_POST_LINK_RE = re.compile(r'\]\(\.\./[a-z0-9-]+/?\)')
HEADING_RE = re.compile(r'^(#{1,6})\s+\S', re.MULTILINE)
# The theme auto-numbers headings, so a heading that also carries its own
# manual number (article.md's "一、" / "2.1" / "1.") renders the number
# twice. Deliberately narrow: "## 2-opt local search" and "## 5 Ways ..."
# must NOT match -- only a CJK numeral with 、, a dotted sequence, or a
# number with trailing punctuation.
# A CJK number is followed directly by CJK text ("## 一、典範轉移") with no
# space, so only the Latin-digit branches require trailing whitespace.
MANUAL_HEADING_NUMBER_RE = re.compile(
    r'^(#{2,6}\s+(?:[一二三四五六七八九十百]+[、.]|\d+\.\d+(?:\.\d+)*\s|\d+[.、)]\s))',
    re.MULTILINE,
)
CODE_FENCE_RE = re.compile(r'^(`{3,}).*?\n.*?^\1\s*$', re.MULTILINE | re.DOTALL)
INLINE_CODE_RE = re.compile(r'`[^`\n]+`')
# A URL path segment ("/i_benchmarked_o...") and a shortcode's alt/caption
# text both look like notation but neither is: alt text is read aloud by
# screen readers, where LaTeX would be strictly worse.
URL_RE = re.compile(r'<https?://[^>]+>|https?://\S+|\]\([^)]*\)')
SHORTCODE_RE = re.compile(r'\{\{[<%].*?[>%]\}\}', re.DOTALL)
# Math spans already converted correctly. Stripped before scanning for raw
# notation, otherwise every correct \( s_v \) reports itself.
MATH_SPAN_RE = re.compile(r'\\\[.*?\\\]|\\\(.*?\\\)|\$\$.*?\$\$', re.DOTALL)
# A find-and-replace pass that protects code fences but not existing math
# spans double-wraps notation that was already LaTeX, producing
# "\( \( s_v \) \)" or a \[ ... \] block with a \( ... \) inside it. Always
# a bug, never intentional -- and invisible until the page renders.
NESTED_MATH_RE = re.compile(r'\\\([^()]*\\\(|\\\[[^\[\]]*\\\(')
# Notation still sitting in the body as raw text. Deliberately narrow: a
# single letter or Greek letter carrying a sub/superscript, a Greek letter
# with an index digit, or a numeric power. "Figure 2", "B.2", "5xx" and
# snake_case identifiers must NOT match.
RAW_NOTATION_RES = [
    (re.compile(r'[α-ωΑ-Ω][\^_]'),            'Greek letter with a sub/superscript'),
    (re.compile(r'[α-ωΑ-Ω]\d'),               'Greek letter with an index digit'),
    (re.compile(r'\b[A-Za-z][\^_][A-Za-z0-9{]'), 'single letter with a sub/superscript'),
    (re.compile(r'\b\d+\^\d'),                'numeric power'),
    (re.compile(r'\b[A-Za-z]\*\s*='),         'starred symbol in an assignment'),
]

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

    manual = [m.group(1).strip() for m in MANUAL_HEADING_NUMBER_RE.finditer(prose)]
    if manual:
        sample = ", ".join(repr(h) for h in manual[:3])
        warnings.append(
            f"{label}: {len(manual)} heading(s) carry their own number "
            f"({sample}{', ...' if len(manual) > 3 else ''}) -- the theme "
            "auto-numbers headings, so these render twice (e.g. '3.1 2.1 Foo'). "
            "Strip article.md's manual numbering when publishing"
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
            f"{label}: no relative links to other posts found "
            "(e.g. '](../other-slug/)') -- see hugo-conventions.md's internal-linking "
            "section; fine to skip if genuinely no related post exists"
        )


# Half-width , ; : ? ! doing a Chinese comma/semicolon/colon/question-mark/
# exclamation-mark's job. Only flags one sitting directly between two CJK
# characters (or CJK-then-space-then-CJK for the trailing ones), so an
# English abbreviation (TL;DR), a thousands separator (4,000), or shortcode
# boilerplate ({{< image src="..." >}}) never matches -- none of those sit
# next to a CJK character. Deliberately NOT run through SHORTCODE_RE first,
# since admonition titles and alt/caption text are exactly what this needs
# to check, not skip.
HALF_WIDTH_PUNCT_RE = re.compile(
    r'[一-鿿][,;:]|[,;:][一-鿿]'
    r'|[一-鿿][?!](?!\S)|(?<!\S)[?!][一-鿿]'
)


def check_full_width_punctuation(text, label, warnings):
    """zh-tw only: half-width ASCII punctuation used as Chinese punctuation,
    in front matter (title/description) or body (including shortcode
    attributes this skill authors itself, like admonition titles and
    translated alt/caption text)."""
    if label != "index.zh-tw.md":
        return
    prose = MATH_SPAN_RE.sub(' ', CODE_FENCE_RE.sub(' ', text))
    prose = URL_RE.sub(' ', INLINE_CODE_RE.sub(' ', prose))
    hits = []
    for m in HALF_WIDTH_PUNCT_RE.finditer(prose):
        snippet = prose[max(0, m.start() - 10):m.end() + 10].replace('\n', ' ')
        hits.append(snippet.strip())
    if hits:
        warnings.append(
            f"{label}: {len(hits)} half-width , ; : ? ! spot(s) in Chinese text -- "
            "use full-width ，；：？！ instead, including in title/description and "
            "shortcode attributes this skill authors itself (see hugo-conventions.md's "
            "full-width-punctuation section). " + " | ".join(hits[:5])
        )


# This site's Goldmark strikethrough extension (config/_default/markup.toml)
# pairs even a single ~ (not just GFM's ~~), so two unescaped tildes on the
# same line can silently strike through the text between them -- e.g. a
# Chinese-style numeric range used twice ("1~250", "251~500"). But per the
# same CommonMark flanking rules that govern *emphasis*/_emphasis_, a tilde
# only becomes an active open/close delimiter when it sits tight against a
# non-space character on *both* sides ("1~250"); one written with spaces
# around it ("0 ~ 1", "#5 ~ #8", a table cell like "| ~25x |") is inert and
# safe -- confirmed by sweeping every published post: every space-padded
# "~" site-wide rendered as plain text, while the tight, unspaced form is
# the one that actually shipped broken once. Require tight-on-both-sides so
# this doesn't cry wolf on the site's many legitimate spaced uses. Scans
# line by line rather than by paragraph: this repo's own house style
# already puts one paragraph per source line (including inside
# blockquotes), so a line-level scan is both simpler and accurate for how
# these files are actually written. A residual false positive is possible
# for two tight tildes that land in two *different* table cells on the
# same row (each cell is its own independent inline-parsing context, so
# they can't actually pair) -- rare enough not to be worth cell-aware
# parsing for a best-effort check; just confirm by eye if that's the case.
TILDE_RE = re.compile(r'(?<!\\)(?<=\S)~(?=\S)')


def check_tilde_strikethrough(body_text, label, warnings):
    prose = INLINE_CODE_RE.sub(' ', CODE_FENCE_RE.sub(' ', body_text))
    for line in prose.splitlines():
        hits = TILDE_RE.findall(line)
        if len(hits) >= 2:
            snippet = line.strip()
            if len(snippet) > 160:
                snippet = snippet[:160] + "..."
            warnings.append(
                f"{label}: {len(hits)} unescaped '~' on one line -- this site's "
                "Goldmark strikethrough extension pairs even single tildes (not "
                "just ~~), so the text between them can render struck-through. "
                f"Escape as \\~ unless strikethrough is intended: {snippet!r}"
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

    # Both math checks below scan prose only, with every legitimate home for
    # a $ or a symbol removed first: a shell/nginx snippet is wall-to-wall
    # "$uri$is_args$args", and notation left raw inside a code span or an
    # existing math span is not left raw at all.
    prose = MATH_SPAN_RE.sub(" ", CODE_FENCE_RE.sub(" ", body_text))
    prose = SHORTCODE_RE.sub(" ", INLINE_CODE_RE.sub(" ", prose))
    prose = URL_RE.sub(" ", prose)

    bare_math = [
        s for s in BARE_INLINE_MATH_RE.findall(CODE_FENCE_RE.sub(" ", body_text))
        if MATHY_INNER_RE.search(s[1:-1])
    ]
    if bare_math:
        warnings.append(
            f"{label}: {len(bare_math)} possible bare-$ inline math span(s) found "
            "(this site only passthrough-renders \\( ... \\) inline, not single $...$) "
            f"e.g. {bare_math[0]!r}"
        )

    for nested in NESTED_MATH_RE.findall(body_text):
        errors.append(
            f"{label}: nested math delimiters ({nested.strip()!r}...) -- a replace pass "
            "fired inside an existing math span. This renders as literal garbage."
        )

    raw_hits = []
    for pattern, kind in RAW_NOTATION_RES:
        for m in pattern.finditer(prose):
            snippet = prose[max(0, m.start() - 12):m.end() + 12].replace("\n", " ")
            raw_hits.append(f"{kind}: ...{snippet.strip()}...")
    if raw_hits:
        warnings.append(
            f"{label}: {len(raw_hits)} raw math notation span(s) outside code/LaTeX -- "
            "convert to \\( ... \\) so they don't read as broken next to converted ones. "
            + " | ".join(raw_hits[:3])
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
        check_full_width_punctuation(fm + body, label, warnings)
        check_body(body, label, post_dir, errors, warnings)
        check_heading_structure(body, label, errors, warnings)
        check_internal_links(body, label, warnings)
        check_tilde_strikethrough(body, label, warnings)

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

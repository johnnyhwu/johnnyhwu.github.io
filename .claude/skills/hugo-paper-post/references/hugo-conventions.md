# This site's paper-intro post conventions

Always inspect a real, recent post before writing (e.g.
`content/posts/paper-intro/agentopt/`) — this doc is a durable summary, not
a substitute for checking current reality if the two ever disagree.

## Directory layout

```
content/posts/paper-intro/<slug>/
  index.en.md
  index.zh-tw.md
  featured-image.png            (or .jpg -- see "Featured image" below)
  figure1.png, figure2.png, ...  (flat, descriptive names -- not img-001.png
                                  and not the manifest's docling-native
                                  filenames like picture-003.png)
  table1.png, table4.png, ...
```

Both language files live in the *same* directory and share the *same*
image files (a single page bundle serves both translations) — see
`bilingual-bundle-gotcha.md` for why both language files must exist.

`<slug>` should be a short, lowercase, hyphenated identifier for the paper
(e.g. `skillopt`, `agentopt`) — check it doesn't collide with an existing
post directory.

## Front matter (mirror this shape; see agentopt for a live example)

```toml
---
# weight: 1
title: "<Editorial, SEO-friendly title -- not a literal translation of the paper's own title>"
date: YYYY-MM-DD
lastmod: YYYY-MM-DD
draft: false
description: "<~150-160 char meta description, derived from the article, not copy-pasted from it verbatim>"
featuredImage: "featured-image.png"

tags: ["Large Language Model", "..."]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->
```

`title`/`description` differ between `index.en.md` and `index.zh-tw.md`
(each written natively in its own language, not translated word-for-word);
`date`, `lastmod`, `featuredImage`, `tags`, `categories`, `url` should
match across both.

### Tag vocabulary

Reuse the site's existing controlled vocabulary rather than inventing new
tags — pick 2-4 that genuinely apply:

```
Agent Memory, Benchmark, Deep Research, Domain Adaptation, Evaluation,
Fine-Tuning, Generation Diversity, Inference Optimization, LLM Alignment,
LLM-as-a-Judge, Large Language Model, Mixture of Experts, Model Merging,
Multi-Agent, Pre-Training, Prompting, Retrieval-Augmented Generation,
Single-Agent, Synthetic Data Generation, Tabular Data, Test-Time Scaling,
Text-to-SQL, Uncertainty Estimation, Vision Language Model
```

(Re-derive this list with
`grep -h "^tags:" content/posts/paper-intro/*/index.en.md` if it's been a
while — new tags do get added over time.) A new tag is fine if nothing in
this list genuinely fits, but that should be the exception, not the norm.

### Featured image (there usually isn't a dedicated one)

Papers rarely come with a dedicated cover/header photo, and other posts on
this site mostly use generic stock photos unrelated to the paper's own
figures for `featuredImage`. Don't fabricate or go source a stock photo.
Instead, reuse the article's own most representative figure (usually
"Figure 1", the overview/architecture diagram) as `featured-image.png`,
copied alongside its normal in-body copy under its own descriptive name.
**Say so explicitly in the PR** — it's a reasonable default, not a
requirement from the source, and a human may prefer something else.

## Image shortcode

```
{{< image src="figure1.png" alt="<concise, descriptive alt text>" caption="<visible caption, incl. figure/table number and source attribution>" >}}
```

- `src` is just the filename, relative to the page bundle (no leading
  slash, no `/paper-intro/<slug>/` prefix — Hugo resolves that).
- Fold the Writer's visible caption line (the italic text under the image
  in `article.md`) into the shortcode's `caption` parameter — don't also
  add a separate italic Markdown line underneath the shortcode. The theme
  already renders `caption` as a visible `<figcaption>`; duplicating it as
  a markdown italic line looks inconsistent with every other post on the
  site, which only uses the shortcode's own caption rendering.
- Preserve the Writer's `alt` text content (translate it if you're
  producing the other language's version) — don't rewrite its meaning.

## SEO checklist for front matter

This site's technical SEO (canonical URL, hreflang alternates, Open Graph /
Twitter Card tags, JSON-LD `BlogPosting` schema) is already handled globally
by `layouts/partials/head/link.html` and the DoIt theme's `head/seo.html` —
it reads straight from front matter (`description`, `tags`, `featuredImage`),
so there's nothing to add per-post for those. What *is* per-post and easy to
get wrong:

- `title`: keep it in the ~50-60 character range where practical (it's
  what search results truncate to) — but don't sacrifice the "editorial,
  not a literal paper-title translation" rule above to hit the count.
- `description`: 150-160 chars (already stated above) — this is the exact
  string search engines show, so it must stand alone, not read like a
  fragment.
- Image `alt` text (from the Writer, preserved per the shortcode rule
  below): sanity-check it reads as a real descriptive sentence of what the
  figure shows, not a keyword list or a bare "Figure 1". If the Writer's
  alt text is genuinely just a label, tighten it — the meaning must stay
  the same (per the hard rules), but a threadbare alt is worth a small
  factual improvement, unlike the article's prose which you must not
  touch.
- `featuredImage`: since it's usually a repurposed figure (see below), it
  may fall short of the ~1200x630 size link previews want. That's fine —
  don't fabricate a replacement — but if it's noticeably small or a
  non-16:9 crop, mention the actual dimensions in the PR so a human can
  judge whether to swap it later.

### Internal linking to related posts

Established practice on this site (see how `agentopt`, `cer`, `clam`, and
others cross-link within the "Test-Time Scaling / Inference Optimization"
cluster) is to add a small number of **contextual** inline links from a new
post to existing paper-intro posts covering closely related work — e.g.
"...the kind of Planner-Executor architecture we've seen in
[Plan-and-Act](../plan-and-act/) and [HiRA](../hira/)". This has been done
as a retroactive cleanup pass before; do it at publish time instead so it
doesn't pile up:

1. Find candidates by tag overlap: `grep -l '"<tag>"' content/posts/paper-intro/*/index.en.md`
   for each tag on the new post.
2. Where the new post's prose already naturally references a concept,
   method, or comparison covered by one of those candidates, turn that
   mention into a relative link (`../<slug>/`) instead of plain text — 2-4
   such links is typical, more if the paper genuinely builds on several.
3. Never bolt on an unrelated "See also" list just to hit a count, and
   never force a link where the two papers aren't actually related — a
   missing link is better than a misleading one.
4. Add the equivalent link (to the same target post) in `index.zh-tw.md`
   too, with the anchor text translated naturally.
5. It's fine — and expected — for a post about a genuinely novel topic to
   end up with few or zero such links; don't invent connections.

## Inline math notation

Check `config/_default/markup.toml`'s `[goldmark.extensions.passthrough]`
section before assuming MathJax syntax works as-is. As of this writing:
- Inline math passthrough is configured only for `\( ... \)` — a bare
  `$...$` will **not** render as math on this site.
- Block math passthrough is configured for `$$ ... $$` (and `\[ ... \]`).

`article.md` from the content repo may use single-`$` inline math (LaTeX
convention, not this site's). **Convert every inline `$...$` occurrence to
`\( ... \)`** when writing the Hugo post body. Leave `$$...$$` block math
as-is. (See any post that uses inline math, e.g. `agentopt`, for a working
example of the converted form.)

Don't be tempted to "simplify" this by adding `math: enable: true` to front
matter instead — that toggle only controls the client-side KaTeX/MathJax JS
bundle (auto-render, `copy-tex`, `mhchem`). It does nothing for the delimiter
question above: Hugo's Goldmark passthrough extension server-renders `\( \)`
and `$$ $$` regardless of that flag, but it still won't touch a bare `$...$`
either way. The fix for unrendered math is always "convert the delimiter,"
never "flip the front-matter flag."

## Admonitions for callouts

The theme's `{{< admonition type="..." title="..." >}}...{{< /admonition >}}`
shortcode is already used in most existing paper-intro posts and is the
standard way to make a long section scannable — prefer it over a plain
paragraph when the content is genuinely a TL;DR, an aside, or a caveat, not
as decoration. Positional form (`{{< admonition tip "A title" >}}`) works
too; named form is easier to read when combining with `open=false`.

Use this vocabulary consistently rather than picking a type ad hoc:

| Type | Use for |
|---|---|
| `abstract` | A "Key Takeaways (TL;DR)" box near the top of the post, summarizing the paper's core contribution in 2-4 bullets — the single most common admonition on this site. |
| `tip` | An aside that helps the reader understand a subtle mechanism or implementation detail the main prose doesn't have room to unpack. |
| `info` | Background/context a reader may not have, that isn't the article's main point but helps interpret it. |
| `warning` | A caveat, limitation, or place where the paper's claim is narrower than it first sounds. |
| `quote` | A direct quotation from the paper worth setting apart verbatim. |
| `success` / `question` | Occasional use for a notable positive result or an open question the paper raises — don't force these if `tip`/`info` already fits better. |

Don't invent a TL;DR, caveat, or aside that isn't grounded in `article.md` —
an admonition is a formatting choice, not a license to add content the
Writer step didn't produce. A post with zero admonitions is fine if nothing
in it warrants one; don't add one just to "use the feature."

## Heading structure (H2 vs. H3)

The theme auto-numbers headings and builds the sidebar TOC from them for
free (H2–H6, no per-post config needed) — use that instead of leaving a long
section as an undifferentiated wall of text. As a rule of thumb: once an H2
section (e.g. "Methodology", "Experiments") runs past roughly 4-5 paragraphs
*or* visibly covers more than one sub-idea (e.g. "the training procedure"
and "the evaluation protocol" both living under one "Method" heading), break
it into H3 subsections with their own short, descriptive titles.

This is a readability judgement call on how to present the article's
existing structure, not a license to restructure its argument (see "What NOT
to change" below) — the sub-ideas must already be there in the prose; adding
H3s only makes existing structure visible, it doesn't invent new structure.
Keep hierarchy contiguous (H2 → H3, not H2 → H4) — `verify_post.py` warns on
skips.

## Stripping pipeline artifacts

Before publishing, remove from the rendered body (but do surface in the PR
description instead):
- the trailing ```` ```figure-map ```` fenced block — pipeline metadata,
  never meant for readers,
- any `<!-- NO-MANIFEST: ... -->` or `<!-- UNRESOLVED IMAGE: ... -->`
  comments — replace `UNRESOLVED IMAGE` markers with an actual visible
  placeholder if the image truly couldn't be resolved (see
  `image-resolution.md`), but don't leave internal-pipeline-speak in a
  published post.

## What NOT to change

Translating the prose (per the bilingual requirement) is expected. Beyond
that: don't restructure the article's argument, don't add sections it
didn't have, don't "improve" claims for punchiness. Front matter, image
wiring, math-notation conversion, and platform formatting are this skill's
job — the article's substance is the Writer step's, already done upstream.

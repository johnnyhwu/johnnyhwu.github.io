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

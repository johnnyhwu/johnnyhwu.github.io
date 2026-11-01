# This site's post conventions

Always inspect a real, recent post from the **same section** before writing
(e.g. `content/posts/paper-intro/agentopt/` for a paper walkthrough,
`content/posts/ai-concept/dropout/` for a concept explainer) — this doc is a
durable summary, not a substitute for checking current reality if the two
ever disagree.

These conventions apply to every section (`paper-intro`, `ai-concept`,
`python-tutorial`, `other`); see this repo's `CLAUDE.md` for how to pick one.

**How this relates to the plan JSON.** Posts are rendered from the Planner's approved plan
(`plans/<slug>/post.*.json`) by `scripts/render_post.py`, never written by hand. This document is the
specification of correct output: `render_post.py` implements the mechanical rules, `verify_post.py` checks the
result, and the judgement calls (which formulas become blocks, which flows become diagrams, how many callouts) are
the Planner's (`blog-planner/references/planner-guide.md`). The visual vocabulary and its markup are in
`visual-mapping.md`.

## Directory layout

```
content/posts/<section>/<slug>/
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
categories: ["<section>"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "<section>/:contentbasename"
---

<!--more-->
```

**`categories` and `url` both encode the section — change both together.**
The most likely way to get this wrong is copying front matter from a post
in a different section and updating only the directory path. `url:` is what
actually determines the published URL, so a stale
`url: "paper-intro/:contentbasename"` on a post living in
`content/posts/ai-concept/` publishes it at `/paper-intro/<slug>/` — which
also means every `../<slug>/` relative link aimed at it from its real
section resolves to nothing. `verify_post.py` does not catch this; check it
by eye, and confirm the built path in the `hugo build` output.

`date` and `lastmod` are the publish day (today's date) unless the task says
otherwise. A touch-up to a live post bumps only `lastmod`.

`title`/`description` differ between `index.en.md` and `index.zh-tw.md`
(each written natively in its own language, not translated word-for-word);
`date`, `lastmod`, `featuredImage`, `tags`, `categories`, `url` should
match across both.

### Tag vocabulary

Default to the site's existing controlled vocabulary — pick 2-4 that
genuinely apply:

```
Agent Memory, Benchmark, Deep Research, Domain Adaptation, Evaluation,
Fine-Tuning, Generation Diversity, Inference Optimization, LLM Alignment,
LLM-as-a-Judge, Large Language Model, Mixture of Experts, Model Merging,
Multi-Agent, Pre-Training, Prompting, Retrieval-Augmented Generation,
Single-Agent, Synthetic Data Generation, Tabular Data, Test-Time Scaling,
Text-to-SQL, Uncertainty Estimation, Vision Language Model
```

(Re-derive this list with
`grep -h "^tags:" content/posts/*/*/index.en.md` if it's been a
while — new tags do get added over time.) A new tag is fine if nothing in
this list genuinely fits, but that should be the exception, not the norm.

**`tags: []` is a legitimate answer for classic ML/DL fundamentals.** The
vocabulary above grew up around LLM-era papers, so a post on
backpropagation, dropout, or gradient descent often has *nothing* that
genuinely applies. The site's own precedent for exactly this case is
`ai-concept/dropout`, which ships an empty tag list. Prefer matching that
over either forcing a bad-fit LLM tag onto a fundamentals post or minting a
one-off tag (`"Deep Learning"`) that no other post shares — a tag with a
single member does nothing for discovery. Say which you chose in the PR.

### Featured image (every post needs one; generate it unless the source ships a real cover)

`featuredImage` is required and every existing post has one. Order of preference:

1. **A real cover the source ships.** Look in `<TopicDir>/assets/images/` for `feature-image.*` /
   `featured-image.*` (usually not in the manifest, so it is easy to miss). Copy it to `featured-image.<ext>` and
   note its dimensions. An unclaimed image with another name is just a figure.
2. **A cover generated with `canvas-design`** (the default, whether or not the article has figures): 1800x945,
   English-only, one metaphor from the article's central mechanism, labels limited to terms and numbers the
   article contains, a style distinct from `generated-covers.md`. The full how-to is `featured-image.md`;
   `content/posts/paper-intro/resource2skill/` is a live example. Say in the PR that it is a generated
   illustration, what it depicts and where each number comes from.
3. **Last resort, only if generation is impossible:** reuse the article's most representative figure, chosen by
   its caption (not "Figure 1" by default: WikiSkill's Figure 1 was a results chart and its architecture diagram,
   Figure 2, was the right pick), and say why generation was skipped. With no figures and no way to generate,
   flag the missing cover in the PR; never source a stock photo.

## Image shortcode

```
{{< image src="figure1.png" alt="<concise, descriptive alt text>" caption="<visible caption, incl. figure/table number and source attribution>" >}}
```

- `src` is just the filename, relative to the page bundle (no leading
  slash, no `/paper-intro/<slug>/` prefix — Hugo resolves that).
- The figure block's `caption` goes into the shortcode's `caption` parameter — never also
  a separate italic Markdown line underneath the shortcode. The theme
  already renders `caption` as a visible `<figcaption>`; duplicating it as
  a markdown italic line looks inconsistent with every other post on the
  site, which only uses the shortcode's own caption rendering.
- Source attribution: end every `caption` with `(Source: original paper,
  Figure N.)` in English or `（來源：原始論文 Figure N。）` in zh-tw,
  using the **paper's** own number (it is in the manifest `caption`). The
  visible label in the caption (`圖 3 —`) is the post's own sequential
  numbering and often differs, which is expected. `render_post.py` adds the
  attribution and names bundle files after the paper's numbers
  (`figure10.png`, `table7.png`) so they cannot collide.
- `alt` and `caption` come from the plan (Step 3 wrote them in both languages); a threadbare alt is fixed
  there, not here.

## SEO checklist for front matter

This site's technical SEO (canonical URL, hreflang alternates, Open Graph /
Twitter Card tags, JSON-LD `BlogPosting` schema) is already handled globally
by `layouts/partials/head/link.html` and the DoIt theme's `head/seo.html` —
it reads straight from front matter (`description`, `tags`, `featuredImage`),
so there's nothing to add per-post for those. What *is* per-post and easy to
get wrong:

- `title`: keep the English title to **52 characters or fewer** (Google cuts titles by pixel width at
  roughly 47-62 characters; 52 was safe on the ten results read for this site, one locale, so treat it as
  a target, not a law; `verify_post.py` warns above it). zh-TW stays within `verify_post.py`'s range. Don't sacrifice the "editorial,
  not a literal paper-title translation" rule above to hit the count: cut the part after the colon,
  not the hook.
  **A title has two jobs: tell a stranger what the post is about, and give
  them a reason to click *this* one.** Both must work for someone who has
  never heard of the paper or its acronym.
  - **Plain subject first.** Say in everyday words what the post is about
    ("self-improving AI agents", "RAG over messy tables"), using the term a
    reader would actually search for. Do not lead with the method's name or
    acronym unless it is already a household word (BERT, RAG) or is short and
    is what people type. The name before or after the hook is fine, but it must
    sit **inside the first 52 characters** so Google's cut never removes the one
    string a reader would search (`… RRSI`, `… How MixRAG Fixes It`). Pages
    on this site whose names are short and searchable (WikiSkill, Mem0, DPO)
    are its top earners; whether the name causes that is not proven.
  - **The hook is a tension, in the reader's terms.** Find the one claim the
    article spends most of its length on (a common assumption it overturns,
    a claim vs. what was verified, a concrete before/after) and state it so
    it makes sense *without* the article. A question works when the article
    answers it honestly; don't promise more than the article's own verdict
    (a post that ends "low research value" must not read like a breakthrough).
  - **No insider vocabulary, no bare numbers.** Terms the article itself
    defines ("evolve points", "OOD", "ablation") and deltas with no object
    ("2.3 fewer, 3.3 more") mean nothing in a feed. A number earns a place
    only if its subject is obvious from the title alone ("cuts API costs by
    67%").
  - **Self-test:** cover the post and read only the title. Can you say what
    field it is about (agents? RAG? training?) and why you'd care? If you
    need the article to decode it, rewrite. Bad: `RRSI: Give Up 2.3 Evolve
    Points, Win 3.3 on Unseen Benchmarks`. Better: `Do Self-Improving Agents
    Memorize the Test? RRSI` (48 characters, name inside the cut).
  - Each language gets its own native title, not a translation of the
    other's. `verify_post.py` only checks length; this test is on you.
- `description`: aim for 150-160 characters in English; `verify_post.py`
  warns outside 120-170 (en) and 40-180 (zh-tw), and the zh-tw version is
  naturally shorter because CJK characters carry more per character. This is
  the exact string search engines show, so it must stand alone, not read
  like a fragment.
- Image `alt` text (written by the Planner, per the shortcode rule
  below): sanity-check it reads as a real descriptive sentence of what the
  figure shows, not a keyword list or a bare "Figure 1". If the Writer's
  alt text is genuinely just a label, tighten it — the meaning must stay
  the same (per the hard rules), but a threadbare alt is worth a small
  factual improvement, unlike the article's prose which you must not
  touch.
- `featuredImage`: a generated cover is 1800x945 (about 1.9:1), which is
  already the shape link previews want. A reused figure or a real source
  cover may be smaller or a different crop; if it's noticeably
  small, mention the actual dimensions in the PR so a human can judge
  whether to swap it later. Don't fabricate a replacement for a real cover.
- AI-citation readiness (GEO/AEO) rides on the same readability work this
  skill already does, not a separate pass: a section an LLM can quote and
  have it stand alone (the "Heading structure" section's H2/H3 nesting and
  self-contained-section rules below) is the same thing a human skimmer
  needs. Don't add keyword-stuffed phrasing, FAQ schema, or an `llms.txt`
  entry chasing this — for a single-author technical blog with no
  analytics/CMS layer, there's no evidence any of that outperforms just
  writing a clear, well-structured post, and it's scope this skill doesn't
  own.

### Internal linking to related posts

Established practice on this site (see how `agentopt`, `cer`, `clam`, and
others cross-link within the "Test-Time Scaling / Inference Optimization"
cluster) is to add a small number of **contextual** inline links from a new
post to existing paper-intro posts covering closely related work — e.g.
"...the kind of Planner-Executor architecture we've seen in
[Plan-and-Act](../plan-and-act/) and [HiRA](../hira/)". Do it
at publish time so it doesn't pile up:

1. Find candidates by tag overlap: `grep -l '"<tag>"' content/posts/*/*/index.en.md`
   for each tag on the new post. For an untagged fundamentals post, search
   by concept name instead (`grep -ril "backpropagation" content/posts/`).
2. **Check who already links *to* you**, not just who you can link to:
   ```bash
   grep -rn "\.\./<your-slug>/" content/posts/*/*/index.*.md
   ```
   Existing posts routinely link forward to unpublished ones, so this both
   pins your slug (see SKILL.md workflow step 3) and reveals the genuinely
   related posts — a post that already links to you is, by definition, one
   a reciprocal link makes sense from.
3. Where the new post's prose already naturally references a concept,
   method, or comparison covered by one of those candidates, turn that
   mention into a relative link (`../<slug>/`) instead of plain text — 2-4
   such links is typical, more if the article genuinely builds on several.
4. Never bolt on an unrelated "See also" list just to hit a count, and
   never force a link where the two posts aren't actually related — a
   missing link is better than a misleading one.
5. Add the equivalent link (to the same target post) in `index.zh-tw.md`
   too, with the anchor text translated naturally.
6. It's fine — and expected — for a post about a genuinely novel topic to
   end up with few or zero such links; don't invent connections.

**Mind the path.** A link to a post in the *same* section is `../<slug>/`;
a link to a post in another section is `../../<section>/<slug>/` (from a
`paper-intro` post, `../../ai-concept/jev-overview/`). Writing
`../jev-overview/` there resolves to `/paper-intro/jev-overview/`, which
404s, and neither `verify_post.py` nor the build flags it.

### Linking to posts that don't exist yet

This site deliberately tolerates forward links to posts that don't exist
yet: `ai-concept/dropout` shipped linking to `../gradient-descent/` and
`../stochastic-gradient-descent/` before either was published, and when
those two later landed under exactly those slugs, both links lit up with no
cleanup pass. (Both are live now, so as of this writing the site has no
dangling relative links at all — verify before assuming otherwise.) So a
dangling relative link is an accepted convention here, not an accident.

That makes it a narrow licence, not a blank cheque. A forward link is
justified only when **both** hold:

- The post's own prose already refers to that topic (you are linking
  existing words, not adding a new claim), **and**
- the target slug is already pinned by an existing link elsewhere on the
  site — so when that post lands, every reference to it lights up at once.

If the slug is *not* already pinned anywhere, leave the mention as plain
text. Inventing a slug for an unwritten post is a coin-flip that a future
publish will silently lose, and you have no way to know which spelling it
will pick. Always list forward links you added in the PR so a human can
see which targets are still pending.

## Rendering rules, and why they exist

`render_post.py` applies these and `verify_post.py` checks them; they are listed so a renderer change or a
puzzling warning can be judged. Each one shipped broken at least once when posts were converted by hand.

- **Full-width punctuation in zh text**, including what Step 3 writes itself (title, description, callout titles,
  alt text, captions): ，；：？！ between Chinese characters. Exceptions: `4,000`, `TL;DR`, code, URLs. English
  text keeps English punctuation.
- **Tildes.** `config/_default/markup.toml` enables Goldmark strikethrough, which pairs even *single* tight
  tildes: `1~250、251~500` struck through `250、251`. Two tight `~` on one line are escaped as `\~` (renders the
  same); a spaced `~` is inert. A warning about two tildes in different table cells is a false alarm.
- **Math.** The passthrough renders inline math only as `\( .. \)` and blocks as `$$ .. $$`; the plan stores
  `$..$` and the renderer converts it. A literal `$` (a price) would open math, so the render refuses it. Which
  formulas become blocks is the Planner's call (a `formula` block, words first).
- **Mermaid.** Every diagram starts with the site palette `%%{init}%%` (mermaid's default yellow/lavender
  ignores the dark-mode toggle anyway). Labels are quoted, brackets stripped. A subgraph title wider than its
  nodes is clipped silently at the real column width (~766 px), so keep titles to a few words. Mermaid renders
  client-side: only `check_mermaid.js` and its screenshots catch a syntax error or a clipped label.
- **Callouts and folds** map to admonitions and the `fold` shortcode per `visual-mapping.md`; how many callouts a
  post carries is a Planner rule (`blog-planner/references/planner-guide.md` §4).
- **Headings** come from the plan's outline (H2, H3, H4) and carry no number of their own: the theme numbers them
  and counts 前言 as section 1, so a hand-written `一、` or `2.1` renders twice and off by one. A post's own
  section numbers never appear in prose either; the paper's ("論文第 4.3 節") are fine.

## Pipeline artifacts

The plan JSON carries none of `article.md`'s pipeline leftovers (the trailing ```` ```figure-map ```` block,
manual heading numbers, `NO-MANIFEST` / `UNRESOLVED IMAGE` comments), and `render_post.py` never emits them.
`verify_post.py` still fails if any appear in a rendered file, which would mean a file was edited by hand.

## What NOT to change

Step 4 owns form: front matter checks, shortcodes, image wiring, math delimiters, tilde escaping, mermaid, links.
It does not own content. The rendered `index.*.md` files are generated; never edit them by hand. A typo or a
plain mistake is fixed in the plan JSON (both languages, then `validate_plan.py`, then re-render) and listed in the
PR; a problem with the substance goes back to Step 3.

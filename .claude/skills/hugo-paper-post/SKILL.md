---
name: hugo-paper-post
description: Use this skill whenever you need to publish (or fix) a blog post in this Hugo site from a topic directory in the separate `johnnyhwu/AI-Research` content repo, triggered by phrases like "產生 <Topic> 文章", "generate the <Topic> post", "publish <Topic>", "把 <Topic> 發布成 Hugo post", or any request to fix images/front matter/translation on an existing post. Covers every kind of topic that repo holds -- paper walkthroughs (`paper-intro`), concept explainers and reading notes (`ai-concept`), Python teaching material (`python-tutorial`), and infra/tooling write-ups (`other`) -- and picking the right section is part of the skill's job; the "paper" in this skill's own directory name is historical, not a scope limit. Turns a content-repo topic directory's article.md + image-manifest.json + extracted images into a matched pair of Hugo posts (content/posts/<section>/<slug>/index.en.md and index.zh-tw.md) with images resolved and wired, following this site's existing conventions. This skill is fully self-contained: no external spec document is needed or will be supplied to run it -- this file plus references/ and scripts/ is the complete, current spec.
---

# Hugo Paper Post Publisher (Step 3)

## Why this skill exists

This is the complete, current spec for Step 3 ("Publisher") of this site's
3-step blog pipeline (see this repo's `CLAUDE.md` for the pipeline overview
and how to bootstrap access to `johnnyhwu/AI-Research`, the separate content
repo where Steps 1–2 already ran). No external document backs this up and
none will be supplied alongside a future task — this `SKILL.md` plus its
`references/` and `scripts/` is the whole spec.

## The hard rules (read before doing anything else)

1. **Never read the source PDF.** It lives in `AI-Research`, not here, and
   Step 3 has no business opening it — everything you need is already in
   `article.md` and `image-manifest.json`.

2. **Never load an image file into context except a bounded spot-check.**
   The common case — a body reference's id matches a manifest id directly —
   needs zero vision. Only load (and only at low resolution) the images
   whose manifest entry is `parser_confidence: "low"`, or where id-matching
   was genuinely ambiguous. See `references/image-resolution.md` for the
   exact procedure and why every other image must be trusted without a
   look.

3. **Always produce both `index.en.md` and `index.zh-tw.md` for a post, in
   the same commit, every time — never just one.** This is not a style
   preference, it's load-bearing: see `references/bilingual-bundle-gotcha.md`
   for the concrete bug this caused the one time it was skipped (a fully
   English-only bundle silently broke *every* image on the page, because of
   how this site's Hugo config resolves page-bundle resources). If the
   content repo's `article.md` is in Chinese, translate it into English
   yourself for `index.en.md`; the Chinese body goes into `index.zh-tw.md`
   essentially as-is (reformatted per this skill, not rewritten). If a
   future source article ever arrives in English instead, the direction
   reverses, but the requirement to ship both languages does not change.

4. **Never fabricate metadata the site expects but the source doesn't
   supply** — most commonly a dedicated cover/header image, which papers
   rarely have and some topics (e.g. a reading note on a blog post, not an
   academic paper) may lack entirely, with zero figures anywhere. Make a
   defensible, clearly-flagged substitution instead (see
   `references/hugo-conventions.md`'s "Featured image" section for the two
   concrete fallbacks — reuse the article's own Figure 1 when one exists,
   or generate a small original graphic depicting the article's own central
   concept when it doesn't) and say so in the PR. The line not to cross
   isn't "used a substitute image" — every existing post already does that
   in one form or another — it's *claiming* a substitute is something it
   isn't (passing a generated diagram off as a real figure, or asserting a
   fact the article never made).

5. **Preserve the Writer's prose.** Translating is expected (rule 3); adding
   unrelated commentary, restructuring the argument, or "improving" claims
   the article didn't make is not. Touch front matter, image wiring, and
   platform formatting — not the substance of what the article argues.

## Inputs

For a target topic `<Topic>` (e.g. `SkillOpt`, `Backpropagation-Explain`),
from `johnnyhwu/AI-Research`:
- `<Topic>/article.md` — the platform-neutral article body + trailing
  ```` ```figure-map ```` block.
- `<Topic>/assets/image-manifest.json` (canonical) or a documented per-topic
  exception path (check `AI-Research/CLAUDE.md`'s topic-directory section —
  e.g. `SkillOpt/parsed/assets/image-manifest.json`) — the figure/table
  catalog.
- `<Topic>/assets/images/` (or the equivalent exception path) — the actual
  extracted image files.

Not every topic has a manifest or images at all (some are prose-only
reading notes) — that case is handled in `references/hugo-conventions.md`'s
featured-image section, not by skipping the post.

From this repo, **inspect a real existing post before writing anything** —
pick one from the *same section* you're publishing into
(`content/posts/paper-intro/agentopt/` for a paper walkthrough,
`content/posts/ai-concept/dropout/` for a concept explainer). Both are good,
current references for front matter shape and image shortcode usage.
Conventions drift over time; treat
`references/hugo-conventions.md` in this skill as the durable summary, but
prefer what an actual recent post does if the two ever disagree.

## Workflow

1. **Bootstrap access to `AI-Research`** per this repo's `CLAUDE.md` if it
   isn't already attached to the session (`add_repo` → clone →
   `register_repo_root`).

2. **Read `<Topic>/article.md` and `<Topic>/assets/image-manifest.json`**
   (whichever path is actually correct per the exception check above). Do
   not read the PDF. Do not open any image file yet.

3. **Decide the section and the slug — before writing anything.** Most
   `AI-Research` topics are *not* papers, so `paper-intro` is a choice, not
   the default. Route per this repo's `CLAUDE.md` ("Which section does it
   belong in?"), then pin the slug:

   ```bash
   # Does the site ALREADY link to this post under an expected slug?
   grep -rn "\.\./<candidate-slug>/" content/posts/*/*/index.*.md
   ```

   Existing posts on this site routinely link forward to posts that haven't
   been published yet, which means **the slug may already be decided for
   you** — and matching it repairs those dangling links for free, while
   inventing a different one leaves them broken permanently. Run this grep
   for every plausible slug spelling (`backpropagation` *and*
   `backpropagation-explain`) before committing to one. It is a two-second
   check that silently fixes site-wide link rot; skipping it silently
   creates more.

4. **Resolve every referenced image id.** Follow
   `references/image-resolution.md` exactly: direct id match is the default
   and needs no vision; only fall back to semantic matching or a bounded,
   downscaled spot-check per that doc's rules. If an id genuinely can't be
   resolved, leave a visible `<!-- UNRESOLVED IMAGE: ... -->` placeholder
   and flag it in the PR — never guess silently.

5. **Write both language versions of the post** at
   `content/posts/<section>/<slug>/index.en.md` and `index.zh-tw.md`,
   following `references/hugo-conventions.md` for front matter, the image
   shortcode, inline math notation, admonition usage, heading structure,
   tag vocabulary, and the featured-image fallback. Copy the resolved
   image files flat into the same directory
   (page bundle), named descriptively (`figure1.png`, `table1.png`, ... —
   not the manifest's docling-native filenames; if the manifest's own
   filenames are already descriptive, as in hand-curated migrations, just
   keep them). Strip the trailing
   `figure-map` block and any `NO-MANIFEST`/`UNRESOLVED` pipeline comments
   from both rendered bodies (they may still appear in the PR description).

6. **Add contextual internal links to related posts**, per
   `references/hugo-conventions.md`'s "Internal linking to related posts"
   section — find existing posts sharing a tag or topic and
   turn natural mentions into relative links, in both language files. This
   is an established site convention (previously done as a retroactive
   cleanup pass); doing it at publish time avoids that cleanup debt. Zero
   links is fine for a genuinely novel topic — don't force it.

7. **Verify before opening a PR.** Run:
   ```bash
   python3 .claude/skills/hugo-paper-post/scripts/verify_post.py content/posts/<section>/<slug>
   ```
   This checks both language files exist, front matter parses, every image
   shortcode's `src` resolves to a file actually present in the bundle, no
   pipeline artifacts leaked into the body, no unsupported `$...$` inline
   math slipped in, plus SEO sanity warnings (title/description length
   outside the usual range, a body `# ` heading duplicating the title's
   H1, skipped heading levels, zero internal links to other
   posts). Warnings aren't failures — use judgement — but investigate each
   one. It is a fast sanity net, **not** a substitute for an actual Hugo
   build — see `references/hugo-build.md` for how to get a real
   `hugo build` running in a sandbox that has neither `hugo` nor the theme
   submodule preinstalled, and do that too when the change is non-trivial
   (new post, not a one-line fix).

8. **Open a PR** whose description covers: which `<Topic>/` topic directory
   it came from, **which section you routed it to and why** (plus whether
   the slug was already pinned by existing links), the id → filename image
   mapping, which images (if any)
   were spot-checked and why, any unresolved images or missing/fabricated
   front-matter fields, any internal links added (or why none applied), and
   confirmation that both language files were verified to build.

## Publishing several topics at once — dispatch one subagent per topic

When a task covers more than one topic directory, **the default is one
subagent per topic** (`Agent` tool, `general-purpose`), not doing them all
inline. Each article is self-contained — topic directory in, page bundle
out — so they parallelise cleanly, and writing two full-length language
versions per article consumes a lot of context that the orchestrator needs
for the cross-article work below.

Tell each subagent to invoke this skill by name and give it exactly one
topic. Delegate per topic:

- read `<Topic>/article.md` + the manifest (workflow steps 2, 4),
- resolve images, including any bounded spot-check, and copy them into the
  bundle,
- write `index.en.md` **and** `index.zh-tw.md` (both — the bilingual rule is
  per post, so it binds each subagent individually),
- run `verify_post.py` on that one directory and report its warnings back.

**Keep these with the orchestrator — they are cross-article and break if
split up:**

| Decide centrally | Why it cannot be delegated |
|---|---|
| Section + slug for every topic | Slugs depend on the whole site's link graph, and two subagents choosing independently can collide or pick different spellings of the same series (`python-function` vs `python-function-1`). |
| Dates across the batch | Spreading posts over a publishing gap needs a view of every date at once; independently chosen dates cluster. |
| Cross-post internal links | A link from topic A to topic B is only correct once B's slug is fixed — and both posts in a batch may link to each other. |
| One final `hugo build` + site-wide link audit | Per-topic builds are slow and redundant, and the bilingual page-bundle bug and dangling-link checks are only meaningful site-wide. |
| The PR | One PR describes the batch. |

So the shape is: orchestrator decides sections, slugs and dates up front →
subagents write the posts in parallel → orchestrator does one build, one
link audit, one PR. A single-topic task doesn't need a subagent at all;
just do it inline.

## Definition of done

- The post is in the **right section** per this repo's `CLAUDE.md` routing
  table, under a slug that matches any relative links existing posts
  already point at it with.
- `content/posts/<section>/<slug>/index.en.md` **and** `index.zh-tw.md`
  both exist, in the same change.
- Every resolved image renders with the Writer's alt text and caption
  intact, via this site's `{{< image ... >}}` shortcode convention.
- No `figure-map` block or internal pipeline comments (`NO-MANIFEST`,
  `UNRESOLVED`, etc.) leak into either published body.
- Unresolvable references are visible placeholders, listed in the PR — not
  silently dropped or guessed.
- The post carries a small number of contextual internal links to related
  posts where genuinely applicable (per
  `references/hugo-conventions.md`), in both language files — or the PR
  says why none applied.
- `scripts/verify_post.py` passes for the new/changed post directory, and
  its SEO warnings (title/description length, heading structure, internal
  links) were reviewed, not just ignored.
- A real `hugo build` was attempted (per `references/hugo-build.md`) for
  anything beyond a trivial fix, and its output was actually inspected —
  not just assumed to be fine because the markdown looks right.

## Files in this skill

```
hugo-paper-post/
├── SKILL.md                              (this file)
├── references/
│   ├── image-resolution.md               manifest id matching + bounded vision spot-check rules
│   ├── hugo-conventions.md               front matter, image shortcode, math notation, admonitions, heading structure, tags, featured-image fallback
│   ├── bilingual-bundle-gotcha.md        why skipping either language breaks images -- read before skipping either file
│   └── hugo-build.md                     how to get a real local hugo build running to actually verify a post
└── scripts/
    └── verify_post.py                    front-matter / image-reference / pipeline-artifact / math-notation checks
```

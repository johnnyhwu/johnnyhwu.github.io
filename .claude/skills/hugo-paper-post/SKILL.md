---
name: hugo-paper-post
description: Use this skill whenever you need to publish (or fix) a `paper-intro` blog post in this Hugo site from a topic directory in the separate `johnnyhwu/AI-Research` content repo, triggered by phrases like "產生 <Paper> 文章", "generate the <Paper> post", "publish <Paper>", "把 <Paper> 發布成 Hugo post", or any request to fix images/front matter/translation on an existing paper-intro post. Turns a content-repo topic directory's article.md + image-manifest.json + extracted images into a matched pair of Hugo posts (content/posts/paper-intro/<slug>/index.en.md and index.zh-tw.md) with images resolved and wired, following this site's existing conventions. This skill is fully self-contained: no external spec document is needed or will be supplied to run it -- this file plus references/ and scripts/ is the complete, current spec.
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
   supply** (most commonly: there's no dedicated cover/header image for a
   paper). Make a defensible, clearly-flagged substitution instead (see
   `references/hugo-conventions.md` on featured images) and say so in the
   PR — don't invent a stock photo or claim a fact the article didn't make.

5. **Preserve the Writer's prose.** Translating is expected (rule 3); adding
   unrelated commentary, restructuring the argument, or "improving" claims
   the article didn't make is not. Touch front matter, image wiring, and
   platform formatting — not the substance of what the article argues.

## Inputs

For a target paper `<Paper>` (e.g. `SkillOpt`), from `johnnyhwu/AI-Research`:
- `<Paper>/article.md` — the platform-neutral article body + trailing
  ```` ```figure-map ```` block.
- `<Paper>/assets/image-manifest.json` (canonical) or a documented per-topic
  exception path (check `AI-Research/CLAUDE.md`'s topic-directory section —
  e.g. `SkillOpt/parsed/assets/image-manifest.json`) — the figure/table
  catalog.
- `<Paper>/assets/images/` (or the equivalent exception path) — the actual
  extracted image files.

From this repo, **inspect a real existing post before writing anything** —
`content/posts/paper-intro/agentopt/` is a good, current reference for front
matter shape and image shortcode usage. Conventions drift over time; treat
`references/hugo-conventions.md` in this skill as the durable summary, but
prefer what an actual recent post does if the two ever disagree.

## Workflow

1. **Bootstrap access to `AI-Research`** per this repo's `CLAUDE.md` if it
   isn't already attached to the session (`add_repo` → clone →
   `register_repo_root`).

2. **Read `<Paper>/article.md` and `<Paper>/assets/image-manifest.json`**
   (whichever path is actually correct per the exception check above). Do
   not read the PDF. Do not open any image file yet.

3. **Resolve every referenced image id.** Follow
   `references/image-resolution.md` exactly: direct id match is the default
   and needs no vision; only fall back to semantic matching or a bounded,
   downscaled spot-check per that doc's rules. If an id genuinely can't be
   resolved, leave a visible `<!-- UNRESOLVED IMAGE: ... -->` placeholder
   and flag it in the PR — never guess silently.

4. **Write both language versions of the post** at
   `content/posts/paper-intro/<slug>/index.en.md` and `index.zh-tw.md`,
   following `references/hugo-conventions.md` for front matter, the image
   shortcode, inline math notation, tag vocabulary, and the featured-image
   fallback. Copy the resolved image files flat into the same directory
   (page bundle), named descriptively (`figure1.png`, `table1.png`, ... —
   not the manifest's docling-native filenames). Strip the trailing
   `figure-map` block and any `NO-MANIFEST`/`UNRESOLVED` pipeline comments
   from both rendered bodies (they may still appear in the PR description).

5. **Verify before opening a PR.** Run:
   ```bash
   python3 .claude/skills/hugo-paper-post/scripts/verify_post.py content/posts/paper-intro/<slug>
   ```
   This checks both language files exist, front matter parses, every image
   shortcode's `src` resolves to a file actually present in the bundle, no
   pipeline artifacts leaked into the body, and no unsupported `$...$`
   inline math slipped in. It is a fast sanity net, **not** a substitute for
   an actual Hugo build — see `references/hugo-build.md` for how to get a
   real `hugo build` running in a sandbox that has neither `hugo` nor the
   theme submodule preinstalled, and do that too when the change is
   non-trivial (new post, not a one-line fix).

6. **Open a PR** whose description covers: which `<Paper>/` topic directory
   it came from, the id → filename image mapping, which images (if any)
   were spot-checked and why, any unresolved images or missing/fabricated
   front-matter fields, and confirmation that both language files were
   verified to build.

## Definition of done

- `content/posts/paper-intro/<slug>/index.en.md` **and** `index.zh-tw.md`
  both exist, in the same change.
- Every resolved image renders with the Writer's alt text and caption
  intact, via this site's `{{< image ... >}}` shortcode convention.
- No `figure-map` block or internal pipeline comments (`NO-MANIFEST`,
  `UNRESOLVED`, etc.) leak into either published body.
- Unresolvable references are visible placeholders, listed in the PR — not
  silently dropped or guessed.
- `scripts/verify_post.py` passes for the new/changed post directory.
- A real `hugo build` was attempted (per `references/hugo-build.md`) for
  anything beyond a trivial fix, and its output was actually inspected —
  not just assumed to be fine because the markdown looks right.

## Files in this skill

```
hugo-paper-post/
├── SKILL.md                              (this file)
├── references/
│   ├── image-resolution.md               manifest id matching + bounded vision spot-check rules
│   ├── hugo-conventions.md               front matter, image shortcode, math notation, tags, featured-image fallback
│   ├── bilingual-bundle-gotcha.md        why skipping either language breaks images -- read before skipping either file
│   └── hugo-build.md                     how to get a real local hugo build running to actually verify a post
└── scripts/
    └── verify_post.py                    front-matter / image-reference / pipeline-artifact / math-notation checks
```

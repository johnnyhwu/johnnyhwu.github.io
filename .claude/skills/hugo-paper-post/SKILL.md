---
name: hugo-paper-post
description: Use this skill whenever you need to publish (or fix) a blog post in this Hugo site from a topic directory in the separate `johnnyhwu/AI-Research` content repo, triggered by phrases like "產生 <Topic> 文章", "generate the <Topic> post", "publish <Topic>", "把 <Topic> 發布成 Hugo post", or any request to fix images/front matter/translation on an existing post. Covers every kind of topic that repo holds -- paper walkthroughs (`paper-intro`), concept explainers and reading notes (`ai-concept`), Python teaching material (`python-tutorial`), and infra/tooling write-ups (`other`) -- and picking the right section is part of the skill's job; the "paper" in this skill's own directory name is historical, not a scope limit. Turns a content-repo topic directory's article.md + image-manifest.json + extracted images into a matched pair of Hugo posts (content/posts/<section>/<slug>/index.en.md and index.zh-tw.md) with images resolved and wired, following this site's existing conventions. This skill is fully self-contained: no external spec document is needed or will be supplied to run it -- this file plus references/ and scripts/ is the complete, current spec.
---

# Hugo Paper Post Publisher (Step 3)

## Why this skill exists

This is the complete, current spec for Step 3 ("Publisher") of this site's
3-step blog pipeline (see this repo's `CLAUDE.md` for the pipeline overview
and how to refresh the `AI-Research` submodule, the separate content
repo where Steps 1–2 already ran). No external document backs this up and
none will be supplied alongside a future task — this `SKILL.md` plus its
`references/` and `scripts/` is the whole spec.

## The hard rules (read before doing anything else)

1. **Never read the source PDF.** It lives in `AI-Research`, not here, and
   Step 3 has no business opening it — everything you need is already in
   `article.md` and `image-manifest.json`.

2. **Images may be viewed, but let a subagent do the looking.** Extracted figures, other posts' covers, your own
   cover and rendered-page screenshots are all fair game for quality. Image bytes bloat context, so by default
   send a subagent a file path and a specific question and work from its text answer; view one yourself only when
   a round trip costs more than it saves, downscaled first. Viewing never replaces the manifest id join (see
   `references/image-resolution.md`, `references/featured-image.md`).

3. **Always produce both `index.en.md` and `index.zh-tw.md` for a post, in
   the same commit, every time — never just one.** This is not a style
   preference, it's load-bearing: see `references/bilingual-bundle-gotcha.md`
   for the concrete bug a missing language causes (a fully
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
   academic paper) may lack entirely, with zero figures anywhere. Don't
   leave it out and don't source a stock photo. **Generate an original
   cover with the `canvas-design` skill, in a style of its own** (see
   `references/featured-image.md`; the conventions doc's "Featured image"
   section has the full order of preference, including keeping a real
   cover that the source already ships) and say so in the PR.
   The line not to cross isn't "used a generated image" — every existing
   post already has some cover — it's *claiming* a generated image is
   something it isn't (passing it off as a real paper figure or a
   photograph), or putting a number, name or claim in it that the article
   never made.

5. **Preserve the Writer's prose.** Translating is expected (rule 3); adding
   unrelated commentary, restructuring the argument, or "improving" claims
   the article didn't make is not. Touch front matter, image wiring, and
   platform formatting — not the substance of what the article argues. The
   one exception is a plain mistake in the source (a figure number pointing
   at the wrong figure, a cross-reference that dangles once heading numbers
   are stripped): fix it, list it in the PR, and suggest fixing it in
   `AI-Research` too.

## Inputs

For a target topic `<Topic>` (e.g. `SkillOpt`, `Backpropagation-Explain`),
from `johnnyhwu/AI-Research`. **Topic directories are bucketed by state, so
`<Topic>` is never a top-level path there** — see this repo's `CLAUDE.md`,
"The three buckets, and which one you want". The short version:

- `done/unpublished/<Topic>/` — where every normal publish task's source
  lives. If the user names a topic without a path, look here first.
- `done/published/<Topic>/` — the source for a *touch-up* to a post that
  already exists.
- `in-progress/<Topic>/` — has no `article.md` yet. Nothing to publish;
  report that rather than writing the article yourself (that's Step 1, in
  the other repo).

Writing `<Topic>/...` as if the topic sat at the content repo's root will
just miss. Below, `<TopicDir>` means the full bucketed path:

- `<TopicDir>/article.md` — the platform-neutral article body + trailing
  ```` ```figure-map ```` block.
- `<TopicDir>/assets/image-manifest.json` (canonical) or a documented
  per-topic exception path (check `AI-Research/CLAUDE.md`'s topic-directory
  section — e.g.
  `done/published/SkillOpt/parsed/assets/image-manifest.json`) — the
  figure/table catalog.
- `<TopicDir>/assets/images/` (or the equivalent exception path) — the
  actual extracted image files.

Not every topic has a manifest or images at all (some are prose-only
reading notes) — that case is handled in `references/hugo-conventions.md`'s
featured-image section, not by skipping the post.

**The manifest's `file` paths are repo-relative and include the bucket**
(`done/unpublished/<Topic>/assets/images/foo.png`). Resolve them against
the content repo's root, i.e. `AI-Research/` in this checkout, not against
the topic directory. So `<TopicDir>` below is, concretely,
`AI-Research/done/unpublished/<Topic>/`.

From this repo, **inspect a real existing post before writing anything** —
pick one from the *same section* you're publishing into
(`content/posts/paper-intro/agentopt/` for a paper walkthrough,
`content/posts/ai-concept/dropout/` for a concept explainer). Both are good,
current references for front matter shape and image shortcode usage.
Conventions drift over time; treat
`references/hugo-conventions.md` in this skill as the durable summary, but
prefer what an actual recent post does if the two ever disagree.

## Workflow

0. **Preflight, before any content work.** Fail early on missing tooling instead of at the end:
   `uv --version`, `git submodule update --init themes/DoIt`, and
   `.claude/skills/hugo-paper-post/scripts/node.sh --version` (installs Node, Playwright and Chromium into the
   gitignored `.tools/` on first use; never `brew install` or `npm i -g`). Tools go in this repo's `.tools/`
   only, so the machine stays clean. Also `git fetch origin main`: other posts publish in parallel, and the
   cover register and the `AI-Research` pointer are the files they collide on.

1. **Refresh the `AI-Research` submodule** before touching anything:
   `git submodule update --init --remote AI-Research` (per this repo's
   `CLAUDE.md`), so the queue and `article.md` you read are the latest
   `main`. Step 9 later pushes a branch from inside that submodule.

2. **Locate the topic and read its inputs.** Confirm which bucket it's in
   (`ls done/unpublished/ done/published/ in-progress/`) rather than
   guessing from the name, then read `<TopicDir>/article.md` and
   `<TopicDir>/assets/image-manifest.json` (whichever path is actually
   correct per the exception check above). Do not read the PDF. Image
   viewing comes later, in step 4, and goes through a subagent.

3. **Decide the section and the slug — before writing anything.** Most
   `AI-Research` topics are *not* papers, so `paper-intro` is a choice, not
   the default. Route per this repo's `CLAUDE.md` ("Which section does it
   belong in?"), then pin the slug:

   ```bash
   # The topic directory name can be a typo of the real name (the RRSI paper
   # sat in a directory called RSSI). Take the slug from the article's own
   # title / the paper's name, not from the directory.
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

   **Then run the `seo` skill's pre-publish checks** (`.claude/skills/seo/SKILL.md`). They need the
   owner's local GSC tools and are skipped elsewhere (cloud VM); say so at the end if skipped. Their
   findings feed the title, description and links in steps 5 and 6.

4. **Resolve every referenced image id.** Follow
   `references/image-resolution.md` exactly: direct id match is the default
   and needs no looking; fall back to semantic matching when it doesn't
   join cleanly, and have a subagent check any low-confidence or doubtful
   image, and set each image's `width=` per "Image display width" in that
   doc (text-size matching, but never below 75%). If an id genuinely can't be
   resolved, leave a visible `<!-- UNRESOLVED IMAGE: ... -->` placeholder
   and flag it in the PR — never guess silently.

5. **Write both language versions of the post** at
   `content/posts/<section>/<slug>/index.en.md` and `index.zh-tw.md`,
   following `references/hugo-conventions.md` for front matter, the image
   shortcode, inline math notation, admonition usage, heading structure,
   tag vocabulary, and the featured-image rules. Copy the resolved
   image files flat into the same directory
   (page bundle), named descriptively (`figure1.png`, `table1.png`, ... —
   not the manifest's docling-native filenames; if the manifest's own
   filenames are already descriptive, as in hand-curated migrations, just
   keep them). Strip the trailing
   `figure-map` block and any `NO-MANIFEST`/`UNRESOLVED` pipeline comments
   from both rendered bodies (they may still appear in the PR description).
   `scripts/article_to_zh.py <TopicDir> <section> <slug>` does the mechanical
   part of the zh-tw file (heading numbers, `$` math, figure-map, image
   shortcodes with widths, copying images); front matter, section-number
   cross-references, admonitions, links and the English file stay manual.

   **Then make the cover.** Unless the topic already ships a real one,
   generate `featured-image.png` with the `canvas-design` skill in the house
   style from `references/featured-image.md` (1800x945, English-only text,
   a metaphor drawn from the article's central mechanism, labels limited to
   terms and numbers the article contains). Run it with `uv run python`
   (`uv sync` once, from the repo root; Pillow and numpy come from `pyproject.toml`, never from `pip`).
   Before drawing, re-read `references/generated-covers.md` **as it is on
   `origin/main`** (palettes and fonts already taken; a branch's copy goes
   stale when other posts land) and add a row for the new cover when it is
   done. `scripts/check_cover.py` checks size and margins.

6. **Add contextual internal links to related posts**, per
   `references/hugo-conventions.md`'s "Internal linking to related posts"
   section — find existing posts sharing a tag or topic and
   turn natural mentions into relative links, in both language files. This
   is an established site convention; do it at publish time. Zero
   links is fine for a genuinely novel topic — don't force it.

7. **Verify before opening a PR.**

   ```bash
   python3 .claude/skills/hugo-paper-post/scripts/verify_post.py content/posts/<section>/<slug>
   .claude/skills/hugo-paper-post/scripts/hugo.sh --gc --minify --baseURL "https://datasciocean.com/" -d .tools/public
   .claude/skills/hugo-paper-post/scripts/node.sh .claude/skills/hugo-paper-post/scripts/check_layout.js <section>/<slug>
   ```

   `verify_post.py` is the fast net (both files, front matter, image `src`s, pipeline leftovers, math notation,
   SEO lengths, heading structure, links, image widths, structural parity between the two languages). Investigate
   every warning. A real build is required for a new post (`references/hugo-build.md`). `check_layout.js` renders
   both languages at 1280px and 390px, because KaTeX runs client-side and nothing else sees an overflow or a
   too-wide formula; exit 2 means layout was NOT checked, so say so instead of reporting a pass. A mermaid
   diagram additionally needs `check_mermaid.js <section>/<slug> --shots .tools/shots` through `node.sh`, then one
   screenshot viewed per diagram. Finally look at how the figures actually render (a subagent can view
   downscaled copies at their final width): the numbers pass, yet "too small" only shows in the picture.

8. **Open a PR** (only if the user asked for one; in a cloud session the
   harness refuses unrequested PRs, so otherwise push the branch, draft the
   description below, and offer). Merge `origin/main` first, and before every
   later push check `gh pr view <n> --json state`: if the user already merged
   it, a push recreates the branch, so open a new PR instead. The
   description covers: which topic directory it came
   from (full bucketed path), **which section you routed it to and why**
   (plus whether the slug was already pinned by existing links), the final
   `en` and `zh-tw` titles with a line on how they pass the title self-test in
   `references/hugo-conventions.md` (plain subject, reader-term hook, no jargon),
   the id → filename image mapping, which images (if any)
   were checked visually and why (and any width scaling applied), how the cover was made (generated with
   `canvas-design`: what it depicts, where every number or label in it
   comes from, its size; or the real cover/fallback that was used), any unresolved images or missing/fabricated
   front-matter fields, any internal links added (or why none applied), the
   `SEO` block from the `seo` skill (or which of its checks were skipped), and
   confirmation that both language files were verified to build.

   The two PRs (this one and the AI-Research bucket move in step 9) must
   reference each other, but each needs the other's URL: open this one
   first, then the AI-Research one with this PR's link, then
   `gh pr edit <n> --body-file ...` to add the AI-Research link here.

9. **Move the topic to `done/published/` in `AI-Research` — a second PR.**
   Step 3 isn't finished when the post exists here; the content repo still
   thinks the topic is waiting to be published, and the next person asking
   "what's ready to publish?" will be handed it again. Inside the submodule
   (`cd AI-Research`):

   ```bash
   git checkout -b <branch>
   git mv done/unpublished/<Topic> done/published/<Topic>
   # rewrite done/unpublished/ -> done/published/ in that manifest's
   # source_pdf and every images[].file, then (run inside AI-Research, which has the
   # pymupdf environment the Hugo repo lacks):
   env -u VIRTUAL_ENV uv run python .claude/skills/pdf-figure-table-parser/scripts/verify_manifest.py \
       done/published/<Topic>/assets/image-manifest.json .
   ```

   Push that branch and open the PR from there (`gh pr create` locally; in a
   cloud session attach `johnnyhwu/AI-Research` with `add_repo` at
   `access: "push"` and use the GitHub MCP tools, see this repo's
   `CLAUDE.md`). **Then put
   the submodule back on `main` before staging anything in this repo** — the
   Hugo PR's submodule pointer must name a commit already on `AI-Research`'s
   `main`, never the unmerged bucket-move commit (`CLAUDE.md`, "Where the
   source material actually lives").

   The manifest rewrite is not optional — `git mv` doesn't touch file
   contents, so every `file` path in that manifest would otherwise point at
   a location that no longer exists. `AI-Research/CLAUDE.md`'s "Moving a
   topic between buckets" section is the authority.

   Cross-reference the two PRs in each other's description. Skip this step only for a touch-up to an
   already-published post (the topic is already in `done/published/`), and
   if you can't push to `AI-Research` at all, say so in the Hugo PR instead
   of quietly leaving the buckets wrong.

## Definition of done

Details for each item live in `references/hugo-conventions.md`; this is only the checklist.

- Right section and slug (`CLAUDE.md` routing; slug matches any link already pointing at it).
- `index.en.md` **and** `index.zh-tw.md` in the same change, with `featuredImage` set and the file present: a real
  cover the source shipped, or (default) a generated one in a style distinct from `generated-covers.md`, described
  honestly in the PR.
- Every image resolved by id, rendered through `{{< image >}}` with the Writer's alt and caption, `width=` per
  `image-resolution.md` (never below 75%).
- Body clean: no `figure-map`, no pipeline comments, no hand-numbered headings, no unconverted notation, no `$`
  in prose, no tight `~` pairs; extension themes nested as H3 under one H2; flow-like code fences considered for
  mermaid (and, if used, checked in a browser with the site palette override).
- Related posts linked where genuinely applicable in both languages, or the PR says why none.
- SEO: the `seo` skill's pre-publish checks done (or reported as skipped), and its `post` follow-up rows
  added to `seo/followups.md` in this PR. Skipped checks are told to the user when the task ends.
- `verify_post.py` clean (warnings reviewed), a real `hugo.sh` build inspected, and `check_layout.js` passed via
  `node.sh` (or the PR says why it could not run).
- Topic moved to `done/published/` in `AI-Research` on its own PR with manifest paths rewritten (step 9), unless
  this was a touch-up of a live post.

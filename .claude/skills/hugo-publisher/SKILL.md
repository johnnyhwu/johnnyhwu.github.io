---
name: hugo-publisher
description: Use this skill for Step 4 of this site's blog pipeline: turning an approved Step 3 plan (`plans/<slug>/post.zh.json` + `post.en.json`, written and reviewed by the `blog-planner` skill) into the live Hugo post, `content/posts/<section>/<slug>/index.en.md` + `index.zh-tw.md`, with images, a generated cover, internal links, verification, a PR, and the `AI-Research` bucket move. Triggered, after Step 3 has produced the plan, by "發佈 <Topic>", "publish <Topic>", "把 <Topic> 發布成 Hugo post", and by any request to re-render, fix images, front matter or layout of an existing post (the plan is the source; never edit rendered files by hand). Steps 1-3 run elsewhere first: Step 1 and 2 in `johnnyhwu/AI-Research`, Step 3 in this repo via `blog-planner`. This skill is fully self-contained: this file plus references/ and scripts/ is the complete, current spec.
---

# Hugo Publisher (Step 4)

## Why this skill exists

Step 3 (`blog-planner`) decides what the post says and how it reads: the story, the layers, the visuals' functions,
both languages, all reviewed. Step 4 turns that approved plan into a published page and proves it works. Splitting
them keeps content decisions in one place and makes this step mostly mechanical: **`scripts/render_post.py` writes
the markdown**, so the markup is never hand-written, and this skill's judgement goes into the cover, the links, the
visual check, verification and the PR. See this repo's `CLAUDE.md` for the four-step overview.

## The hard rules

1. **Never read the source PDF.** It lives in `AI-Research`; everything needed is in the plan and the manifest.

2. **Images may be viewed, but let a subagent do the looking.** Extracted figures, other posts' covers, your own
   cover and rendered-page screenshots are all fair game for quality; send a subagent a file path and a specific
   question and work from its text answer, or view one yourself only when a round trip costs more than it saves,
   downscaled first (`references/image-resolution.md`, `references/featured-image.md`).

3. **Both `index.en.md` and `index.zh-tw.md`, every time, from the two plan files, in the same commit.** This is
   load-bearing: see `references/bilingual-bundle-gotcha.md` (a one-language bundle breaks every image on the
   page). `render_post.py` writes both.

4. **Never fabricate metadata the site expects but the plan doesn't supply.** The cover is the common case:
   generate an original one with `canvas-design` from `meta.cover_brief` (`references/featured-image.md`), never a
   stock photo, never a paper figure passed off as a cover, and never a number or label the brief did not allow.
   Say in the PR that it is generated.

5. **The rendered files are generated; the plan is the source.** Never edit `index.*.md` by hand. A typo or plain
   mistake is fixed in the plan JSON (both languages, then `validate_plan.py`, then re-render) and listed in the
   PR; a problem with the substance, or with how it reads, goes back to Step 3. You decide **form** (markup,
   shortcodes, widths, links); you do not decide **content**.

## Inputs

For a topic `<Topic>` with slug `<slug>`:

- `plans/<slug>/post.zh.json` and `post.en.json`: final, approved by Step 3 (schema in
  `blog-planner/references/plan-schema.md`). `plans/<slug>/links.json` is yours to write (step 4 below).
- The manifest and image files the plan's `source` points at (under `AI-Research/`, a git submodule of this repo:
  `git submodule update --init --remote AI-Research`). **Manifest `file` paths are relative to `source.root`**
  (the `AI-Research` root), and include the bucket (`done/unpublished/<Topic>/assets/images/...`).
- A real, recent post from the same section for comparison (`content/posts/paper-intro/skillzip/` for a paper
  walkthrough, `content/posts/ai-concept/dropout/` for a concept explainer). Prefer what an actual recent post
  does if it and `references/hugo-conventions.md` ever disagree.

## Workflow

0. **Preflight.** Fail early on missing tooling: `uv --version`, `git submodule update --init themes/DoIt`,
   and `.claude/skills/hugo-publisher/scripts/node.sh --version` (installs Node, Playwright and Chromium into the
   gitignored `.tools/` on first use; never `brew install` or `npm i -g`). `git fetch origin main`: other posts
   publish in parallel, and the cover register and the `AI-Research` pointer are what they collide on.

1. **Confirm the plan is final.** Both must exit 0:

   ```bash
   S=.claude/skills/blog-planner/scripts
   python3 $S/validate_plan.py plans/<slug>/post.zh.json --article <article.md> --manifest <image-manifest.json>
   python3 $S/validate_plan.py plans/<slug>/post.en.json --zh plans/<slug>/post.zh.json --article <article.md> --manifest <image-manifest.json>
   ```

   If they do not, stop: the plan is not finished and Step 3 owns the fix.

2. **Look at the figures that need it** (`references/image-resolution.md`): crops with `parser_confidence: low`,
   and anything you doubt, through a subagent that reports text. The width rule (never below 75%) is applied by
   the renderer; note each applied width for the PR.

3. **Make the cover** with `canvas-design` per `references/featured-image.md`, from `meta.cover_brief`. Re-read
   `references/generated-covers.md` **as it is on `origin/main`** first (palettes and fonts already taken), add a
   row for the new cover when done, and run `scripts/check_cover.py`. Put `featured-image.png` in the bundle.
   (Unless the topic ships a real cover: `AI-Research/.../assets/images/feature-image.*`, then use that.)

4. **Internal links.** Find related posts by tag and by concept (`references/hugo-conventions.md`, "Internal
   linking to related posts"; mind the `../slug/` versus `../../section/slug/` path rule), then write
   `plans/<slug>/links.json`, an overlay applied while rendering (the plan itself stays untouched):

   ```json
   [{"block": "s5.b2", "zh": "skill", "en": "skill", "target": "../skillopt/"}]
   ```

   `zh` / `en` are the exact words in that block to link (first occurrence). An entry that cannot apply fails
   the render loudly. Links to posts that do not exist yet follow the forward-link rule in the conventions. List
   up to three posts that could link *back* in the PR; do not edit them.

5. **Render.**

   ```bash
   python3 .claude/skills/hugo-publisher/scripts/render_post.py plans/<slug>
   ```

   It writes both files and copies the figures into `content/posts/<section>/<slug>/`. A rebuild of a live post
   keeps its `date` and moves `lastmod`. Add `featured-image.png` (step 3) to the bundle if it is not there yet.

6. **Verify.** Investigate every warning.

   ```bash
   python3 .claude/skills/hugo-publisher/scripts/verify_post.py content/posts/<section>/<slug>
   .claude/skills/hugo-publisher/scripts/hugo.sh --gc --minify --baseURL "https://datasciocean.com/" -d .tools/public
   .claude/skills/hugo-publisher/scripts/node.sh .claude/skills/hugo-publisher/scripts/check_layout.js <section>/<slug>
   ```

   - `verify_post.py` is the fast net (both files, front matter, image `src`s, leftovers, SEO lengths, headings,
     links, widths, zh/en structural parity).
   - A real build is required for a new post (`references/hugo-build.md`).
   - `check_layout.js` renders both languages at 1280 px and 390 px (KaTeX runs client-side); exit 2 means layout
     was NOT checked, so say so instead of reporting a pass.
   - Post with a `diagram` block: also `check_mermaid.js <section>/<slug> --shots .tools/shots`, then look at one
     screenshot per diagram.
   - Post with a `fold` block: also `.claude/skills/hugo-publisher/scripts/node.sh tests/check_fold.js <section>/<slug>`.
   - Finally look at how the figures render (a subagent can view downscaled copies at final width).

7. **Open the PR** (only if the user asked; otherwise push the branch, draft the description and offer). Merge
   `origin/main` first; before every later push check `gh pr view <n> --json state` (a push to a merged branch
   recreates it, so open a new PR instead). The description covers:
   - the topic directory it came from (full bucketed path) and the plan files;
   - the section and why, and whether the slug was already pinned by existing links;
   - the final `en` and `zh-tw` titles (they came from the plan; say how they pass the title self-test in
     `references/hugo-conventions.md`);
   - the id -> filename image mapping, which crops were looked at and why, and each applied width;
   - the cover: generated with `canvas-design`, what it depicts, where each label comes from (`cover_brief`), size;
   - internal links added (or why none), and up to three candidates for links back;
   - **what Step 3 did**, in a few lines: rounds the Reviewers took, anything escalated, the `decisions[]` the
     author approved (folded, reworded, dropped), and editorial blocks added;
   - the `SEO` block from the `seo` skill, or which of its checks were skipped;
   - confirmation that both languages were verified to build.

   The two PRs (this one and the bucket move) must reference each other, but each needs the other's URL: open
   this one first, then the `AI-Research` one with this PR's link, then `gh pr edit <n> --body-file ...` here.

8. **Move the topic to `done/published/` in `AI-Research`: a second PR.** Step 4 isn't finished while the content
   repo still thinks the topic is waiting to be published, and the next "what's ready to publish?" would offer it
   again. Inside the submodule (`cd AI-Research`):

   ```bash
   git checkout -b claude/mark-<topic>-published
   git mv done/unpublished/<Topic> done/published/<Topic>
   # rewrite done/unpublished/ -> done/published/ in the manifest's source_pdf and every images[].file, then,
   # run inside AI-Research (it has the pymupdf environment this repo lacks):
   env -u VIRTUAL_ENV uv run python .claude/skills/pdf-figure-table-parser/scripts/verify_manifest.py \
       done/published/<Topic>/assets/image-manifest.json .
   ```

   Push that branch and open the PR from there (`gh pr create` locally; in a cloud session attach
   `johnnyhwu/AI-Research` with `add_repo` at `access: "push"` and use the GitHub MCP tools). **Then put the
   submodule back on `main` before staging anything here**: this repo's pointer must name a commit already on
   `AI-Research`'s `main`, never the unmerged bucket-move commit. The manifest rewrite is not optional (`git mv`
   does not touch contents); `AI-Research/CLAUDE.md`'s "Moving a topic between buckets" is the authority.
   Cross-reference the two PRs in each other's description. Skip this step only for a touch-up of an
   already-published post (the topic is already in `done/published/`), and if you cannot push to `AI-Research` at
   all, say so in the Hugo PR instead of quietly leaving the buckets wrong.

9. **SEO follow-up rows** (`seo` skill, "After publishing"): add the +7 day and +21 day `post` rows to
   `seo/followups.md` in the same PR, even when the pre-publish checks were skipped (and say so in the PR).

## Definition of done

Details for each item live in `references/hugo-conventions.md`; this is only the checklist.

- `plans/<slug>/post.zh.json`, `post.en.json` (and `links.json` if any) committed, both `validate_plan.py` runs clean.
- `index.en.md` **and** `index.zh-tw.md` rendered from them in the same change, `featuredImage` set and the file
  present: a real cover the source shipped, or (default) a generated one in a style distinct from
  `generated-covers.md`, described honestly in the PR, with its register row added.
- No rendered file edited by hand (re-rendering gives identical files).
- `verify_post.py` clean (warnings reviewed), a real `hugo.sh` build inspected, `check_layout.js` passed via
  `node.sh` (or the PR says why it could not run), plus the mermaid and fold checks where the post has those blocks.
- Internal links added through `links.json` where genuinely applicable, or the PR says why none.
- The `seo` skill's follow-up rows added (and its skipped pre-publish checks reported).
- Topic moved to `done/published/` in `AI-Research` on its own PR with manifest paths rewritten (step 8), unless
  this was a touch-up of a live post.

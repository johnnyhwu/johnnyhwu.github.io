# johnnyhwu.github.io

This repo is the **Hugo repo** (`HUGO_REPO`) — the published blog — and runs Steps 3 and 4 of a 4-step blog
pipeline. Step 1 (Parser) and Step 2 (Writer) run in a *separate* repo, `johnnyhwu/AI-Research`
(`CONTENT_REPO`), and produce the material the next steps turn into a real post. Nothing in `AI-Research` talks
to Hugo directly — that wiring only happens here.

Step 2's `article.md` is built for **correctness and completeness**: every detail of the discussion, logically
right. That makes it a faithful record, not a good read. Step 3 turns it into a post a newcomer will click, stay
with, follow and remember, **without dropping any detail**; Step 4 publishes it.

| Step | Role | Runs in this repo? | Skill |
|---|---|---|---|
| 1 | Parser — extracts figures/tables from the PDF into an image manifest | No (`AI-Research`) | n/a |
| 2 | Writer + Reviewer — turns discussion notes + an image manifest into `article.md` | No (`AI-Research`) | n/a |
| 3 | Planner + Reviewers — turns `article.md` into a reader-friendly **plan** (a zh and an en JSON in `plans/<slug>/`): hook, through-line, layers, signposts, takeaways. A ledger proves no detail was lost; an independent Reader and an independent Fidelity Reviewer check it, up to 5 rounds | **Yes** | `.claude/skills/blog-planner/` |
| 4 | Publisher — renders the plan into the bilingual Hugo bundle, makes the cover and internal links, verifies, opens the PR, moves the topic to `done/published/` | **Yes** | `.claude/skills/hugo-publisher/` (cover: `.claude/skills/canvas-design/`) |

If you're publishing anything in this repo from an `AI-Research` topic directory, you are doing Steps 3 and 4.
They run as one task, with a pause for the author at the Step 3 skeleton.

## What to do when the user says...

| User says (roughly) | Do this |
|---|---|
| "發佈 `<Topic>`" / "產生 `<Topic>` 文章" / "publish `<Topic>`" / "把 `<Topic>` 發布成 Hugo post" | Run Step 3 then Step 4 as one task on `done/unpublished/<Topic>/` in `johnnyhwu/AI-Research`: **`blog-planner`** through the skeleton, then **stop and show the author the brief** and wait; after approval continue (draft, Reviewers, English plan), then **`hugo-publisher`**. If the Reviewers deadlock, stop and ask (the skill lists the triggers). |
| "有哪些文章可以發布？" / "what's ready to publish?" | List `done/unpublished/` in `AI-Research`. That directory *is* the publishing queue — every topic in it has an `article.md` and no Hugo post yet. |
| "讓 `<Topic>` 更好讀" / "redo `<Topic>` for readability", or any change to what an *existing* post says or how it is organised | Step 3 on `done/published/<Topic>/` (the plan is regenerated; the live post keeps its URL and `date`), then Step 4. |
| Fixing an existing post's images, front matter, layout, links or translation typos (no change to what it says) | `hugo-publisher` only. The plan JSON is the source: fix a typo there (both languages) and re-render; never edit `index.*.md` by hand. |
| "幫 `<Topic>` 做 / 換 feature image" / "redo the cover for `<Topic>`" | `hugo-publisher`, `references/featured-image.md`: generate the cover with the vendored **`canvas-design`** skill, in a visual style distinct from the site's other generated covers. Works on a post being published or on one already live. |

Both skills serve **every** kind of `AI-Research` topic, not just academic papers — see "Which section does it
belong in?" below. (`hugo-publisher` was `hugo-paper-post`; the "paper" never limited it.)

## How Steps 3 and 4 divide the work

- **Step 3 decides content and reading experience**: what the post says, in what order, in which layer (main line,
  inline support, folded, appendix), with which signposts and takeaways, in both languages. Its authority over
  `article.md` has three levels: *structure* (change freely), *expression* (change, but mark what it adds as
  editorial), *substance* — claims, numbers, limitations, the Writer's "我的推測" labels (never change or delete;
  only move or demote). Details are demoted, never deleted; the only reason to leave something out or reword it
  is genuine doubt about the source, recorded and shown to the author. `article.md` is the single source of
  truth: Step 3 never edits it.
- **Step 4 decides form**: markup, shortcodes, image wiring and widths, cover, internal links, verification, PRs.
  It renders the plan with `render_post.py` and never changes content; rendered files are generated.
- The plan describes intent (a warning, a fold, a comparison), not markup, so a theme change never touches it.
- Reviewers are fresh subagents with fixed prompts that read files by path. A Reviewer that keeps rejecting does
  not trap the work: at most 5 rounds, with earlier escalation to the author (`blog-planner/references/review-loop.md`).

## Which section does it belong in? (decide this first)

**Most `AI-Research` topic directories are not papers.** Run
`ls done/unpublished/` in `AI-Research` to see the current queue — only a
minority have historically been paper walkthroughs; the rest are concept
explainers, machine-learning fundamentals, language tutorials, and
infra/how-to write-ups (LINE bots, Heroku deploys, terminal setup). Picking
the wrong section
is not cosmetic — it changes the post's URL, and this site's posts
cross-link each other by relative path (`../<slug>/` within a section,
`../../<section>/<slug>/` across sections), so a misfiled post silently
breaks those links.

Route by what the article *is*, not by which repo it came from:

| Section | For | Examples |
|---|---|---|
| `paper-intro` | A walkthrough of a specific published paper — has authors, a venue/arXiv link, and figures extracted from that paper | `skillopt`, `agentopt`, `persona-aware-d2s` |
| `ai-concept` | An explainer of an ML/AI *concept* or technique that isn't tied to one paper, including reading notes on a talk or blog post | `dropout`, `backpropagation`, `context-engineering` |
| `python-tutorial` | Python language teaching material | `python-module`, `python-exception` |
| `other` | Infra, tooling, web, and everything else | `yarn`, `wordpress-https-ssl` |

A useful tie-breaker: if the article's own references section points at
*one* paper it is walking through, it's `paper-intro`; if it cites several
sources as background for a concept, it's `ai-concept`. A post citing a
famous paper in passing (e.g. the 1986 backpropagation paper) is still
`ai-concept` — the article is teaching the idea, not reviewing the paper.

When it is genuinely ambiguous, say which way you're leaning and why, and
ask — a wrong section is expensive to move after publication (the URL is
already indexed and other posts may already link to it).

## Where the source material actually lives

`johnnyhwu/AI-Research` is a **git submodule of this repo**, checked out at
`AI-Research/` (see `.gitmodules`). It is still its own repo with its own
history; the submodule just pins a commit of it next to the post that was
built from it. There is nothing to attach or register any more.

**Before starting any new post (and before answering "what's ready to
publish?"), pull the latest content:**

```bash
git submodule update --init --remote AI-Research   # --init only matters on a fresh clone
git -C AI-Research log -1 --oneline                # note the commit you are publishing from
```

Then:

- Every path below is under `AI-Research/`, e.g.
  `AI-Research/done/unpublished/<Topic>/`. Manifest `file` paths are relative
  to `AI-Research/` itself, not to the topic directory.
- Read `AI-Research/CLAUDE.md` once. It documents that repo's layout and any
  per-topic path exceptions — check it for the current exception list rather
  than assuming the canonical path (e.g. `SkillOpt` keeps its manifest at
  `done/published/SkillOpt/parsed/assets/image-manifest.json`).
- `--remote` moves the submodule pointer to the tip of `AI-Research`'s `main`.
  Commit that pointer bump with the Hugo PR: it records which content commit
  the post was built from.
- **The pointer must always name a commit that exists on `AI-Research`'s
  `main`.** The bucket-move commit (below) lives on an unmerged branch, so
  never `git add AI-Research` while the submodule is checked out on it — a
  teammate's `git submodule update` would fail to find that commit. After
  pushing the branch, `git -C AI-Research checkout main` (or re-run the
  update command) before staging anything here.
- The theme is the other submodule. To fetch only it (e.g. for a local
  Hugo build), use `git submodule update --init themes/DoIt`; a bare
  `git submodule update --init` also pulls `AI-Research` and its PDFs.

### The three buckets, and which one you want

Topic directories live **two** levels down under `done/`, one under
`in-progress/`:

| Bucket | Means | Steps 3 and 4's interest |
|---|---|---|
| `in-progress/<Topic>/` | Step 2 hasn't written `article.md` yet | **Nothing to publish.** If asked to publish one of these, say so — don't write the article yourself; that's the other repo's job. |
| `done/unpublished/<Topic>/` | `article.md` exists, no Hugo post yet | **This is the publishing queue.** Every normal task starts here. |
| `done/published/<Topic>/` | A Hugo post already exists here in `content/posts/<section>/<slug>/` | Only for touch-ups to an already-published post. |

### Finish the loop: mark the topic published

Publishing a post is only half of Step 4. Once the Hugo post is merged (or
at least once the PR here is open), the topic must move buckets in
`AI-Research`. Do it inside the submodule, on a branch, and push from there:

```bash
cd AI-Research
git checkout -b claude/mark-<topic>-published
git mv done/unpublished/<Topic> done/published/<Topic>
```

then rewrite the manifest's baked-in `source_pdf` / `images[].file` paths
from `done/unpublished/...` to `done/published/...` and re-run
`verify_manifest.py` (`uv run python ...`; it needs `pymupdf`) — `git mv`
does not rewrite file contents, so skipping this leaves every image path in
that manifest pointing at nothing. `AI-Research/CLAUDE.md`'s "Moving a topic
between buckets" section is the authority on the exact procedure.

That means a publish task normally produces **two** PRs: the post here, and
a small bucket-move PR in `AI-Research`. Push the branch with plain `git`
from inside the submodule, then open the PR the way your environment allows:
locally, `gh pr create` from the submodule; in a cloud session there is no
`gh`, so first attach `johnnyhwu/AI-Research` with `add_repo` and
`access: "push"`, then use the GitHub MCP tools. Say in each PR that the
other one exists. A cloud session may only open a PR the user has asked
for: if they haven't, push both branches (the one here and the
`AI-Research` bucket-move branch), draft the descriptions, and offer to open
the PRs. If you
genuinely can't open the `AI-Research` PR, say so explicitly rather than
leaving the topic silently mis-bucketed — a topic stuck in
`done/unpublished/` after its post ships will be offered up for publishing
all over again. Afterwards switch the submodule back to `main` (see the
pointer rule above) so this repo's PR doesn't point at the unmerged branch.

## Global rules for anything touching a published post

- **Tools live in this repo, never on the machine.** Python goes through `uv`, never `pip`: Pillow and numpy are
  in `pyproject.toml` (`uv sync`, then `uv run python ...`; `uv add` for anything new; `verify_post.py` is
  stdlib-only). Hugo and Node (with Playwright and Chromium) are downloaded on first use into the gitignored
  `.tools/` by `.claude/skills/hugo-publisher/scripts/hugo.sh` and `node.sh`. Don't `brew install`, `go install`,
  `npm i -g` or `pip install` anything. If a tool is missing, install it that way (or into `.tools/` by the same
  pattern) and say so; don't skip the check it was for. Run `uv` from this repo's root; the exception is
  `verify_manifest.py`, which runs from inside `AI-Research/` with `env -u VIRTUAL_ENV uv run ...` because only
  that repo's environment has `pymupdf`.

- **Never read the source PDF.** It sits in the `AI-Research` submodule next
  to `article.md`, so it is easy to open by accident. Steps 3 and 4 work
  from `article.md` + `image-manifest.json` + the already-extracted image
  files (and, in Step 4, the plan) only.
- **Looking at images is allowed — the goal is a high-quality post — but
  delegate it.** Any image may be viewed: extracted figures/tables, the
  covers of other posts, a rendered page screenshot, your own generated
  cover. Hand the viewing to a **subagent** (give it the file path and a
  specific question, get back a short text answer) so image bytes don't pile
  up in your own context. View an image yourself only when a subagent round
  trip would cost more than it saves or you need the pixels to make the next
  decision (judging your own cover, say), and then downscale first (~600px
  for a figure, ~1000px for a cover). The skill has the detail
  (`hugo-publisher/references/image-resolution.md`, `references/featured-image.md`). What
  stays forbidden is the PDF, and "viewing" never replaces the manifest id
  join: resolve images by id first, look only to confirm or to judge quality.
- **Never invent a manifest id, a number, or front-matter metadata the site
  needs but the article doesn't supply.** The cover image is the common
  case: don't leave it out, don't source a stock photo, and don't pass a
  figure off as a cover. Generate an original one with `canvas-design` per
  the skill, label it as generated in the PR, and keep every number or
  label in it traceable to the article. Flag any other gap in the PR
  description instead of papering over it.
- **Fail loud, not silent.** An image id that doesn't resolve, a detail that lands nowhere, a number that went
  missing, a link that can't apply: each fails `validate_plan.py` or `render_post.py` and is fixed in the plan
  or reported in the PR — never a silent guess.
- **This site is bilingual (`zh-TW` + `en`), and that isn't optional per
  post.** See the skill's bundle-resources note for exactly why a
  single-language post actively breaks the *other* language's images too,
  not just its own content.
- **On-page SEO is part of the work, not an afterthought.** The theme already handles canonical URL, hreflang,
  Open Graph/Twitter tags and JSON-LD. Step 3 owns the title, description, headings and image alt text it writes
  into the plan; Step 4 owns the contextual internal links (`hugo-publisher/references/hugo-conventions.md`).

## SEO is part of publishing, without being asked

Any session that publishes, retitles or fixes a post runs the **`seo`** skill (`.claude/skills/seo/`):
checks before writing (Step 3, phase P1), follow-up rows after publishing (Step 4). Its state lives in `seo/` (committed; start at
`seo/followups.md`). A `SessionStart` hook prints follow-ups that are due; mention them to the user,
and let the skill say when to run them.

The GSC checks need the owner's local `gsc` MCP server (`.mcp.json`, OAuth client in
`~/.config/gsc/`). The skill's preflight says how to tell whether it is there. In a cloud VM it is not:
skip those steps, still do the tool-free ones, and tell the user at the end what you skipped.

## Working with PRs

- Merge `origin/main` into the branch before opening the PR: parallel posts collide on
  `hugo-publisher/references/generated-covers.md` and on the `AI-Research` pointer. Re-read the cover register from `origin/main`
  before designing a cover, so two posts don't pick the same fonts and colours.
- The author merges and deletes branches whenever they like. Before pushing again to an existing PR branch, run
  `gh pr view <n> --json state`; if it is merged, a push recreates the branch, so open a new PR instead.
- Edits to `CLAUDE.md` and the skill themselves can go straight to `main` when the author says so; post content
  still goes through a PR.

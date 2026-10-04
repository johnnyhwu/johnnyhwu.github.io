# johnnyhwu.github.io

This repo is the **Hugo repo** (`HUGO_REPO`) — the published blog — and Step 3
("Publisher") of a 3-step blog pipeline. Step 1 (Writer) and Step 2 (Parser)
run in a *separate* repo, `johnnyhwu/AI-Research` (`CONTENT_REPO`), and
produce the material this repo's step turns into a real post. Nothing in
`AI-Research` talks to Hugo directly — that wiring only happens here.

| Step | Role | Runs in this repo? | Skill |
|---|---|---|---|
| 1 | Writer + Reviewer — turns discussion notes + an image manifest into `article.md` | No (`AI-Research`) | n/a |
| 2 | Parser — extracts figures/tables from the PDF into an image manifest | No (`AI-Research`) | n/a |
| 3 | Publisher — wires `article.md` + manifest + images into a Hugo post, in **both** languages this site ships, and designs its cover image | **Yes** | `.claude/skills/hugo-paper-post/` (cover: `.claude/skills/canvas-design/`) |

If you're publishing anything in this repo from an `AI-Research` topic
directory, you are doing Step 3.

## What to do when the user says...

| User says (roughly) | Do this |
|---|---|
| "產生 `<Topic>` 文章" / "generate the `<Topic>` post" / "publish `<Topic>`" / "把 `<Topic>` 發布成 Hugo post" | Use the **`hugo-paper-post`** skill (`.claude/skills/hugo-paper-post/`) against topic directory `done/unpublished/<Topic>/` in `johnnyhwu/AI-Research`. |
| "有哪些文章可以發布？" / "what's ready to publish?" | List `done/unpublished/` in `AI-Research`. That directory *is* the publishing queue — every topic in it has an `article.md` and no Hugo post yet. |
| Anything about fixing/updating an *existing* post's images, front matter, or translation | Same skill — it also covers touch-ups, not just first publication. The source topic will be under `done/published/` in that case. |
| "幫 `<Topic>` 做 / 換 feature image" / "redo the cover for `<Topic>`" | Same skill, `references/featured-image.md`: generate the cover with the vendored **`canvas-design`** skill, in a visual style distinct from the site's other generated covers. Works on a post being published or on one already live. |

The skill's directory name says "paper", but that is historical. It is the
publisher for **every** kind of `AI-Research` topic, not just academic
papers — see "Which section does it belong in?" below.

## Which section does it belong in? (decide this first)

**Most `AI-Research` topic directories are not papers.** Run
`ls done/unpublished/` in `AI-Research` to see the current queue — only a
minority have historically been paper walkthroughs; the rest are concept
explainers, machine-learning fundamentals, language tutorials, and
infra/how-to write-ups (LINE bots, Heroku deploys, terminal setup). Picking
the wrong section
is not cosmetic — it changes the post's URL, and this site's posts
cross-link each other by relative path (`../<slug>/`), so a
misfiled post silently breaks those links.

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

| Bucket | Means | Step 3's interest |
|---|---|---|
| `in-progress/<Topic>/` | Step 1 hasn't written `article.md` yet | **Nothing to publish.** If asked to publish one of these, say so — don't write the article yourself; that's the other repo's job. |
| `done/unpublished/<Topic>/` | `article.md` exists, no Hugo post yet | **This is the publishing queue.** Every normal Step 3 task starts here. |
| `done/published/<Topic>/` | A Hugo post already exists here in `content/posts/<section>/<slug>/` | Only for touch-ups to an already-published post. |

Do **not** rely on a bare `done/<Topic>/` path — that layout is gone, and a
path built that way will simply not exist.

### Finish the loop: mark the topic published

Publishing a post is only half of Step 3. Once the Hugo post is merged (or
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
a small bucket-move PR in `AI-Research` (open it with `gh pr create` from
inside the submodule). Say in each PR that the other one exists. If you
genuinely can't open the `AI-Research` PR, say so explicitly rather than
leaving the topic silently mis-bucketed — a topic stuck in
`done/unpublished/` after its post ships will be offered up for publishing
all over again. Afterwards switch the submodule back to `main` (see the
pointer rule above) so this repo's PR doesn't point at the unmerged branch.

## Global rules for anything touching a published post

- **Python tooling goes through `uv`, never `pip`.** Packages this repo needs
  (Pillow and numpy, for cover rendering and image spot-checks) are declared
  in `pyproject.toml`; run `uv sync` once, then `uv run python ...`. Don't run
  `pip` / `pip3` / `python3 -m pip`: on this machine that installs into the
  user-level Python and pollutes it. If a new package is needed, `uv add` it
  so it lands in `pyproject.toml` and `uv.lock`. (`verify_post.py` is
  stdlib-only and runs fine with plain `python3`.)
- **Hugo is project-local too.** For the real build check, run
  `.claude/skills/hugo-paper-post/scripts/hugo.sh ...` (see its header). It keeps
  the binary, Hugo's cache and the build output under the gitignored `.tools/`;
  don't `brew install` / `go install` hugo or point the build at the repo root.

- **Never read the source PDF.** It sits in the `AI-Research` submodule next
  to `article.md`, so it is easy to open by accident. Step 3 works
  from `article.md` + `image-manifest.json` + the already-extracted image
  files only.
- **Never load an image file into context except a bounded, explicitly
  justified spot-check.** The skill defines exactly when that's allowed
  (only `parser_confidence: "low"` manifest entries, downscaled first) and
  when it isn't (everything else — trust direct id matches). The one other
  exception is the cover you generate yourself: view its ~1000px preview
  to check layout, never the full-size file.
- **Never invent a manifest id or fabricate front-matter metadata the site
  needs but the article doesn't supply.** The cover image is the common
  case: don't leave it out, don't source a stock photo, and don't pass a
  figure off as a cover. Generate an original one with `canvas-design` per
  the skill, label it as generated in the PR, and keep every number or
  label in it traceable to the article. Flag any other gap in the PR
  description instead of papering over it.
- **Fail loud, not silent.** An image that can't be confidently resolved
  gets a visible placeholder and a PR callout — never a silent guess.
- **This site is bilingual (`zh-TW` + `en`), and that isn't optional per
  post.** See the skill's bundle-resources note for exactly why a
  single-language post actively breaks the *other* language's images too,
  not just its own content.
- **On-page SEO is part of Step 3, not an afterthought.** Canonical URL,
  hreflang, Open Graph/Twitter tags, and JSON-LD are already handled
  site-wide by the theme/layout — nothing to add there. What the skill
  itself is responsible for (title/description length, image alt-text
  quality, contextual internal links to related posts, and AI-citation
  readiness — which rides on the same self-contained-section work, not a
  separate pass) is in `hugo-paper-post`'s `references/hugo-conventions.md`;
  do it at publish time rather than leaving it for a later cleanup pass.

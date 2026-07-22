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
| 3 | Publisher — wires `article.md` + manifest + images into a Hugo post, in **both** languages this site ships | **Yes** | `.claude/skills/hugo-paper-post/` |

If you're working in this repo on a paper-intro post, you are doing Step 3.

## What to do when the user says...

| User says (roughly) | Do this |
|---|---|
| "產生 `<Paper>` 文章" / "generate the `<Paper>` post" / "publish `<Paper>`" / "把 `<Paper>` 發布成 Hugo post" | Use the **`hugo-paper-post`** skill (`.claude/skills/hugo-paper-post/`) against topic directory `<Paper>/` in `johnnyhwu/AI-Research`. |
| Anything about fixing/updating an *existing* paper-intro post's images, front matter, or translation | Same skill — it also covers touch-ups, not just first publication. |

**No spec document will be supplied alongside a task.** The skill (this file
plus `.claude/skills/hugo-paper-post/SKILL.md` + its `references/`) is the
complete, current source of truth — don't wait for an uploaded spec, and
don't reconstruct the process from memory of some prior conversation.

## Where the source material actually lives

`johnnyhwu/AI-Research` is a **separate GitHub repo**, not a subfolder here.
It is almost never already attached to a fresh session — bootstrap it first:

1. `add_repo` (owner `johnnyhwu`, repo `AI-Research`) — the tool response
   gives you the exact clone command and a workspace path. Follow its
   instructions literally (single clone, generous timeout; it's explicit
   about not fighting a half-finished clone from a concurrent call).
2. `register_repo_root` with the same owner/repo and the directory you
   cloned to. This is what makes `AI-Research`'s own `CLAUDE.md` and skills
   show up as a system-reminder on your next turn — until you do this, you
   only have the raw files, not that repo's own house rules.
3. Read `AI-Research/CLAUDE.md` once it loads. It documents that repo's
   topic-directory layout (each paper gets a directory at the repo **root**,
   e.g. `SkillOpt/` — not `docs/SkillOpt/`) and any per-topic path
   exceptions (e.g. `SkillOpt/` itself keeps its manifest at
   `SkillOpt/parsed/assets/image-manifest.json` instead of the canonical
   `SkillOpt/assets/image-manifest.json`, from before that convention was
   written down — check `AI-Research/CLAUDE.md` for the current exception
   list rather than assuming the canonical path blindly).

## Global rules for anything touching a paper-intro post

- **Never read the source PDF.** It isn't even in this repo. Step 3 works
  from `article.md` + `image-manifest.json` + the already-extracted image
  files only.
- **Never load an image file into context except a bounded, explicitly
  justified spot-check.** The skill defines exactly when that's allowed
  (only `parser_confidence: "low"` manifest entries, downscaled first) and
  when it isn't (everything else — trust direct id matches).
- **Never invent a manifest id or fabricate front-matter metadata the site
  needs but the article doesn't supply** (e.g. a cover photo). Flag gaps
  in the PR description instead of papering over them.
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
  quality, contextual internal links to related posts) is in
  `hugo-paper-post`'s `references/hugo-conventions.md`; do it at publish
  time rather than leaving it for a later cleanup pass.

---
name: blog-planner
description: Use this skill for Step 3 of this site's blog pipeline: turning a finished Step 2 `article.md` (in `AI-Research/done/unpublished/<Topic>/`, or `done/published/` when reworking a live post) into a reader-friendly post plan, a pair of JSON files `plans/<slug>/post.zh.json` + `post.en.json`, that Step 4 (`hugo-publisher`) then renders and publishes. Triggered by "發佈 <Topic>", "產生 <Topic> 文章", "publish <Topic>", "規劃 <Topic>", and by requests to make an existing post easier to read ("重寫 <Topic> 讓它更好讀", "redo <Topic> for readability"). The Planner builds a story from Step 2's complete but note-like content (hook, a through-line, layers, signposts, takeaways) without dropping any detail, then runs it past two independent Reviewers (a cold Reader and a Fidelity checker) for up to 5 rounds before the English version is written. This skill is fully self-contained: this file plus references/ and scripts/ is the complete, current spec.
---

# Blog Planner (Step 3: Planner + Reviewers)

## Why this skill exists

Step 2's Writer is built for **correctness and completeness**: every detail from the discussion notes, logically
right. That makes `article.md` a faithful record, not a good read. Step 3 turns that record into a post a beginner
will click, stay with, follow without getting lost, and remember, **without throwing the knowledge away**.

Four reader goals, in order:

1. **Click**: the title and description make a stranger curious and tell them what the post is about.
2. **Stay**: the opening gives a reason to keep reading before it asks for any effort.
3. **Follow**: a mindmap builds as they read; they always know where they are and how it fits.
4. **Keep**: they leave with a few things they can say again, and one thing they will remember.

The tension is between goals 2 to 4 and "keep every detail". The mechanism that resolves it is **layers plus a
ledger**: detail is moved, folded and re-ordered, never deleted, and a script can prove nothing was lost.

## The hard rules (read before doing anything else)

1. **Never read the source PDF.** Work from `article.md`, the manifest's text fields and (through a subagent only)
   the extracted images. Step 2 is the single source of truth: **never edit it**, and never "fix" a claim from your
   own knowledge of the paper.

2. **Three levels of authority** over `article.md`'s content:

   | Level | Examples | You may |
   |---|---|---|
   | Structure | order, section split, headings, intro, recaps, mindmap, what is main line vs folded | restructure freely |
   | Expression | rewording, transitions, analogies, a running example, intuition before a formula, splitting or merging paragraphs, prose -> table or diagram | change, but mark what you add as `origin: editorial` |
   | Substance | claims, numbers, limitations, the Writer's "我的推測" / "論文沒有說" labels, their strength | **never change or delete**; only move or demote |

3. **Never delete a detail; demote it.** Every knowledge line of `article.md` lands in a block somewhere
   (`main`, `support`, `fold` or `appendix`). A limitation that changes how a result should be read stays in the
   main line, or, if folded, is flagged to the author in `decisions[]`.

4. **Doubt is the only reason to leave something out or reword it.** If something in `article.md` looks wrong or
   unclear, do not fix it from outside knowledge and do not go back to Step 2: leave it out or say it more
   carefully, and record a `dropped` / `reworded` decision with the reason and `needs_human: true`. Convenience is
   not a reason.

5. **No invented facts or numbers.** Editorial text (analogies, examples, recaps) may not assert anything about the
   paper that the source does not, nor introduce a number `article.md` lacks. An invented example must read as an
   example ("假設…", "舉個例子") and be marked `illustrative: true`. Readers need not be told what came from the
   paper and what is ours, but they must never mistake an example's numbers for results.

6. **Reviewers are clean subagents.** Fixed prompt templates from `references/`, files by path never pasted, no
   access to your reasoning or to the plan JSON (they read `views.py` output). They judge; you edit.

7. **At most 5 rounds, and know when to stop.** If the Reviewers keep rejecting, ask the author instead of looping
   (`references/review-loop.md` lists the triggers). Never argue a Reviewer into approving.

8. **Plans describe intent, not markup.** No shortcodes, no HTML, no `{{< >}}`. How a block looks is Step 4's job.

## Inputs

- `AI-Research/done/unpublished/<Topic>/article.md` and `assets/image-manifest.json` (or the documented exception
  path in `AI-Research/CLAUDE.md`). Manifest `file` paths are relative to `AI-Research/`.
- `references/planner-guide.md` (how to make it readable: the reader, the four goals as moves, layering, style).
- `references/plan-schema.md` (the JSON you write).

## Workflow

**P0. Read and build the ledger.**

```bash
git submodule update --init --remote AI-Research
git -C AI-Research log -1 --oneline        # note the commit you plan from
mkdir -p plans/<slug>/work/reviews
```

- Confirm the bucket (`ls AI-Research/done/unpublished AI-Research/done/published`); `in-progress/` has no
  `article.md`, so there is nothing to plan.
- Decide the **section** (this repo's `CLAUDE.md`, "Which section does it belong in?": route by what the article
  is, not where it came from) and the **slug**. The slug may already be decided for you: grep for existing links
  (`grep -rn "\.\./<candidate>/" content/posts/*/*/index.*.md`) for every plausible spelling before choosing.
- Read `article.md` top to bottom and write the **ledger**: one item per piece of knowledge (kind, source lines,
  one-line gist). Navigation sentences are `nav`. Nothing is skipped: the validator names any uncovered line.

**P1. SEO checks before writing** (`seo` skill, "Before publishing a post"). They need the owner's local GSC tools;
without them, say what you skipped. Results feed the title, H2s, first paragraph and description, and go into
`meta.seo` and `plans/<slug>/work/seo.md`. If the same query is already targeted by an existing post, note it.

**P2. Skeleton.** Write `plans/<slug>/post.zh.json` with `meta`, `outline`, `ledger` (each item with `layer` and
`section`), `glossary` stubs and `decisions`, but no blocks yet. Then:

```bash
S=.claude/skills/blog-planner/scripts
python3 $S/validate_plan.py plans/<slug>/post.zh.json --article <article.md> --manifest <manifest> --stage skeleton
python3 $S/brief.py plans/<slug>/post.zh.json --out plans/<slug>/work/skeleton.md
```

**Stop and show the author the brief** (a short chat summary of `skeleton.md`: title candidates, hook, the three
takeaways, the outline, and everything under "Needs your attention"). Wait for approval or changes. Do not write
the full draft before that: changing the story after the draft costs the most.

**P3. Draft.** Write the `blocks` (and finish `glossary`, `decisions`, each ledger item's `dest`) following
`references/planner-guide.md`. Re-run `validate_plan.py` (default stage `draft`) until it exits 0. Warnings are
read, not ignored.

**P4. Review loop**, exactly as in `references/review-loop.md`: two fresh subagents (Reader and Fidelity) on views
made by `scripts/views.py`; later rounds see only what changed (`delta.json`); at most 5 rounds; escalate to the
author on the triggers there. When both approve, one more fresh Reader does a single full cold read.

**P5. English.** Write `plans/<slug>/post.en.json` per `references/en-transcreation.md`, run
`validate_plan.py <en> --zh <zh> ...`, and have one fresh Reader cold-read the English title, description and first
screen. Then hand over to Step 4 (`hugo-publisher`).

## Files

| Path | What | Committed |
|---|---|---|
| `plans/<slug>/post.zh.json`, `post.en.json` | the final plans | yes |
| `plans/<slug>/links.json` | internal-link overlay (written in Step 4) | yes |
| `plans/<slug>/work/` | `skeleton.md`, reviewer views, `reviews/rN-*.json`, `delta.json`, `seo.md` | no (gitignored) |

Scripts (`scripts/`, stdlib only): `validate_plan.py` (the zero-token gate), `views.py` (reader and fidelity views,
full or delta), `brief.py` (the author's one-page summary), `plan_lib.py` (shared). Tests: `uv run python -m
unittest discover -s tests`.

## Definition of done

- Skeleton approved by the author; every `needs_human` decision was shown to them.
- `validate_plan.py` exits 0 on the zh plan (draft stage) and on the en plan with `--zh`.
- Reader and Fidelity both returned `approve` (no blocker or major), or the author accepted the open findings after
  an escalation; the final full cold read found no blocker or major.
- Both plan files in `plans/<slug>/`, ready for `hugo-publisher`.

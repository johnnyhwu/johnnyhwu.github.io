---
name: seo
description: SEO checks for this Hugo blog, run before and after publishing a post and when asked about traffic, Google Search Console (GSC), rankings or clicks. Use it whenever you publish, fix or retitle a post (even if the user does not mention SEO), when the session start hook lists due SEO follow-ups, and for site-wide traffic analysis. Needs the local `gsc` MCP server; without it, skip the tool-based steps and tell the user what you skipped.
---

# SEO for DataSci Ocean

Procedure lives here; state lives in `seo/` (committed). Keep it that way so `AGENTS.md` stays short.

| Need | Read |
|---|---|
| What is due, what was checked | `seo/followups.md` (a `SessionStart` hook prints the due rows) |
| Open action items and the baseline | `seo/plan.md` |
| GSC limits, how the dir is organised | `seo/README.md` |
| Exact tool calls and thresholds | `references/gsc-recipes.md` |
| Past findings | newest file in `seo/reports/` (read only when relevant) |

## Preflight (every time, before any GSC call)

1. `test -f "$HOME/.config/gsc/client_secrets.json"`; if missing, you are not on the owner's Mac (for
   example an Anthropic cloud VM). **GSC is unavailable.**
2. Check whether the `gsc` MCP tools (e.g. `get_site_details`) are present in your available toolset; if not, GSC is unavailable.
3. No browser is needed. Outside-site demand comes from `scripts/suggest.py` (Google autocomplete, no
   key); a Chrome look at the results page is optional and never blocks or counts as a skipped step.

If GSC is unavailable: skip every GSC step, still do the tool-free work below (`suggest.py` included), and **end the task by
telling the user which SEO steps you did not do and why**. Ignore `.agents/plugins/gsc/mcp_config.json` there (the server
cannot start without the credentials) and ignore the due-rows prompt except to report it. Never call `mcp__gsc__*` in that case: an
unauthenticated call waits for a browser and hangs.

## Before publishing a post (Step 3, phase P1 of `blog-planner`)

These checks run **before** the skeleton is written, because their results feed the title, the H2s, the first
paragraph and the description in the Planner's plan. Record the outcome in `meta.seo` of the plan
(`queries`, `notes`) and in `plans/<slug>/work/seo.md`; the PR description (Step 4) repeats it.

Tool-free, always: title and description per `hugo-publisher/references/hugo-conventions.md`
("SEO checklist for front matter"; English title 52 characters or fewer, the searchable name inside
those 52), contextual internal links and alt text. (The follow-up rows are added after, below.)

Always, with no tool but the network (recipe in `references/gsc-recipes.md`):

0. **Outside demand** (`scripts/suggest.py --expand`, zh, plus `--lang en` for the English title):
   the paper's name and **the concept it depends on** (for Is Bash: "bash agent" and "programmatic tool
   calling"). A suggestion with another meaning (「dpo 醫學」) is a collision: the title needs a
   plain-words hook such as 「是什麼」. Comparison and question forms are H2 candidates. If the concept
   has demand and the site has no page that ranks for it (step 1), add it to **Concept-page
   candidates** in `seo/plan.md` (G1) with the suggestions as evidence; the paper post itself is not
   changed for it. This is the check that can change what the site writes next, so do not skip it
   because the paper's own name has no demand.

With GSC (about five minutes, recipes in `references/gsc-recipes.md`):

1. **Site vocabulary.** Query the last 90 days for the paper's concept and name variants. Reuse the
   phrasings readers actually type (`wiki skill` vs `wikiskill`, `dpo 是什麼`) in H2s, the first
   paragraph and the description, only where it reads naturally. A paper the site has never covered
   usually has no impressions under any of its names: one query for the name variants and one for the
   broad concept settle that; lead the title with the paper's name.
2. **Results page** (optional, only when a Chrome tool is already connected; at most two searches):
   who holds the name, AI Overview. If Google shows a CAPTCHA or an unusual-traffic page, stop: never
   solve it. Its absence is not a skipped check; do not mention it in the brief or the follow-up rows.
3. **Link targets.** From step 1, the existing posts that already earn impressions on the topic. Step 4
   links the new post to them through `plans/<slug>/links.json`. Links *back* from live posts would edit other posts, which is not this
   task's scope: list up to three candidates in the PR ("could link here from X, Y") and let the
   author decide. Also check no existing post already targets the same query; if one does,
   say so in the PR rather than publishing a competitor. Add the link-back candidates to the
   **Link-back queue** in `seo/plan.md` (G2) in the same PR, so the monthly batch picks them up.

Write the outcome as a short "SEO" block in the PR description: name variants used, what autocomplete
showed (collisions, question forms, concept demand), the title decision, links added, concept-page
candidates added, anything skipped.

## After publishing (Step 4 of `hugo-publisher`)

Add two `post` rows to **Open** in `seo/followups.md` with absolute dates: +7 days (indexed and
crawled?) and +21 days (impressions, position, CTR), counted from the day the PR is opened (the author
merges soon after). Do this even when GSC was unavailable, and note "pre-publish checks skipped" in
the PR. The rows go in the same PR as the post.

When the hook lists rows as due, mention them to the user in a line. Run them (with GSC available)
when the session's task is publishing or SEO, or when the user agrees; do not start unrelated GSC
work in, say, a typo-fix session. Move each finished row to **Done** with a one-line result. If a post
PR is open, the `seo/` updates ride in it; otherwise commit them on a `claude/seo-followup-<date>`
branch and offer the PR rather than opening one. A title change from a check is always its own PR,
opened only when the user asks. Rules:

- Indexed check: if a URL is not indexed after 7 days, say so; only the user can press "Request
  indexing" in the GSC UI (no tool for it). Timely papers are worth asking for.
- Performance check: impressions over 100 with position 10 or better and low CTR means adjust the title
  **once** (PR, bump `lastmod`, add a line to `seo/log.md`, add a `post` row 3 weeks out). Under about
  30 impressions means nobody searches the name: record it, do not keep tweaking.
- Never judge a change on fewer than about 60 clicks in total; extend the window instead.

## Site-wide analysis (monthly `site` rows, or when asked)

A monthly row is not finished with a report. It ends with **actions**, because measuring without acting
is what this process did in its first month (`seo/reports/2026-11-21-process-reflection.md`):

1. **Decisions for the author**: one or two, each a yes/no question with the evidence and a
   recommendation, taken from `plan.md` items in `decide` or stuck in `todo` longest, and from G1
   (which concept page to write next). Ask them in the session's final message and record the answer
   (or "no answer yet") in `plan.md`. An item asked three months running without an answer is
   `dropped` with that reason.
2. **Link-back batch**: everything in the G2 queue, in one PR (`claude/link-backs-<date>`), opened when
   the user agrees. A post with a plan gets the link through its `plans/<slug>/links.json` and a
   re-render. A legacy post (no `plans/<slug>/`) has no generated file to protect, so the batch edits
   one sentence in both `index.*.md` by hand, the way the A6 title batch did; nothing else in the post
   changes. Log the batch in `seo/log.md`; move the rows to G2's done list.

Re-measure with the **same windows** as the baseline in `plan.md` (90 days vs the 90 before), note
how many posts were published in between (new posts alone move clicks), save a new dated file in
`seo/reports/` (never edit an old report), update statuses in `plan.md`, and add the next row to
`followups.md`. State the window, property and tool for every conclusion; label inferences.

Each monthly `site` row also runs a **movers check**: `compare_search_periods` by page, last 28 days
vs the 28 before, on `sc-domain:datasciocean.com`. List pages whose clicks fell by half or more
(at least 10 clicks before) or whose impressions fell by half or more (at least 300 before), and
whether the position moved too (same position with fewer clicks is a SERP or demand change, not
ours). Add a `post` row for any mover not already in `followups.md`; do not change a page from this
check alone.

## Guardrails

- Property for analysis `sc-domain:datasciocean.com`; URL Inspection needs `https://datasciocean.com/`.
- Read-oriented only. Never use `submit_sitemap`, `manage_sitemaps`, `reauthenticate`, `add_site`,
  `delete_site` or `delete_sitemap`; `GSC_ALLOW_DESTRUCTIVE` stays unset.
- A GSC call that hangs or fails on auth (the OAuth app is in Testing mode, tokens expire about every
  7 days): stop the call, do not retry in a loop, and ask the user to run `/mcp` and reconnect.
- Large outputs go to the scratchpad and get analysed with `jq` or `uv run --no-project python -I`,
  not pasted into context.
- GSC data lags 2 to 3 days and shows only about 40% of impressions at query level. Do not over-read
  small numbers.
- Changes to live posts go through a PR; log each one in `seo/log.md`.

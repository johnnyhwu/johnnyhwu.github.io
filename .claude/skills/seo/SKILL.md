---
name: seo
description: SEO checks for this Hugo blog, run before and after publishing a post and when asked about traffic, Google Search Console (GSC), rankings or clicks. Use it whenever you publish, fix or retitle a post (even if the user does not mention SEO), when the session start hook lists due SEO follow-ups, and for site-wide traffic analysis. Needs the local `gsc` MCP server; without it, skip the tool-based steps and tell the user what you skipped.
---

# SEO for DataSci Ocean

Procedure lives here; state lives in `seo/` (committed). Keep it that way so `CLAUDE.md` stays short.

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
2. `ToolSearch` with `select:mcp__gsc__get_site_details`; if it does not load, GSC is unavailable.
3. Chrome (`mcp__claude-in-chrome__*`) is separate and only needed for the results-page check. Without
   it, skip that one check, not the rest.

If GSC is unavailable: skip every GSC step, still do the tool-free work below, and **end the task by
telling the user which SEO steps you did not do and why**. Ignore `.mcp.json` there (the server
cannot start without the credentials) and ignore the due-rows prompt except to report it. Never call `mcp__gsc__*` in that case: an
unauthenticated call waits for a browser and hangs.

## Before publishing a post (Step 3 of `hugo-paper-post`)

Tool-free, always: title and description per `hugo-paper-post/references/hugo-conventions.md`
("SEO checklist for front matter"; English title 52 characters or fewer, the searchable name inside
those 52), contextual internal links and alt text. (The follow-up rows are added after, below.)

With GSC (about five minutes, recipes in `references/gsc-recipes.md`):

1. **Site vocabulary.** Query the last 90 days for the paper's concept and name variants. Reuse the
   phrasings readers actually type (`wiki skill` vs `wikiskill`, `dpo 是什麼`) in H2s, the first
   paragraph and the description, only where it reads naturally.
2. **Results page** (Chrome, Taiwan, at most two searches): who holds the name, whether the name
   collides with another meaning (DPO is also Data Protection Officer), AI Overview, related searches.
   Use it to decide whether the title needs a plain-words hook such as 「是什麼」 or 「介紹」. If Google
   shows a CAPTCHA or an unusual-traffic page, stop: never solve it, skip this check and say so.
   In a batch of topics, the orchestrator does this check and the follow-up rows, never the
   per-topic subagents (one browser, one `followups.md`).
3. **Link targets.** From step 1, the existing posts that already earn impressions on the topic. Link
   the new post to them. Links *back* from live posts would edit other posts, which is not this
   task's scope: list up to three candidates in the PR ("could link here from X, Y") and let the
   author decide. Also check no existing post already targets the same query; if one does,
   say so in the PR rather than publishing a competitor.

Write the outcome as a short "SEO" block in the PR description: name variants used, what the results
page showed, the title decision, links added, anything skipped.

## After publishing

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

Re-measure with the **same windows** as the baseline in `plan.md` (90 days vs the 90 before), note
how many posts were published in between (new posts alone move clicks), save a new dated file in
`seo/reports/` (never edit an old report), update statuses in `plan.md`, and add the next row to
`followups.md`. State the window, property and tool for every conclusion; label inferences.

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

# SEO follow-ups

The to-do queue for checks that happen *after* something shipped. A `SessionStart` hook
(`.claude/skills/seo/scripts/due.py`) prints every row in **Open** whose date has arrived, so a
new session finds out without being told. Keep the table format: first cell is `YYYY-MM-DD`.

How to close a row: do the check (recipe in `.claude/skills/seo/SKILL.md`), move the row to
**Done** with the result in one line, and, for recurring kinds, add the next row to Open.

Kinds: `post` (one-off check on a new or edited article), `experiment` (readout of a change set),
`site` (recurring whole-site measurement).
Cadence for new posts: `post` rows at 1 week (indexed?) and 3 weeks (impressions, position, CTR).
Recurring: `site` baseline monthly, never-crawled pages monthly.

## Open

| Due | Kind | Item | How |
|---|---|---|---|
| 2026-10-28 | post | `paper-intro/skillzip` (published 2026-10-21): is it indexed and crawled? | `batch_url_inspection` on the zh and en URLs |
| 2026-11-02 | post | `paper-intro/llm-as-a-verifier` (re-published with the new workflow 2026-10-26, PR pending): is it re-crawled with the new title and description? | `batch_url_inspection` on the zh and en URLs; Chrome results-page check was skipped (extension not loaded); the old title had 24 name-only impressions in the 90 days to 2026-10-26 |
| 2026-11-02 | post | `paper-intro/procedural-graphs` (committed 2026-10-26, PR pending): is it indexed and crawled? | `batch_url_inspection` on the zh and en URLs; pre-publish Chrome results-page check was skipped (extension not connected) |
| 2026-11-11 | post | `paper-intro/skillzip`: impressions, position, CTR | post check |
| 2026-11-16 | post | `paper-intro/llm-as-a-verifier`: impressions, position, CTR vs the baseline (zh 24 impressions at position 4.7 to 6.4, en 2 at 7.5, 0 clicks, from 2026-07-28 to 2026-10-26) | post check; only name queries so far, so under about 30 impressions means record it and do not tweak the title |
| 2026-11-16 | post | `paper-intro/procedural-graphs`: impressions, position, CTR | post check; the name had no site demand at publish time, so under about 30 impressions means record it and do not tweak the title |
| 2026-11-23 | site | Monthly baseline: last 90 days vs the 90 before, against the baseline in `plan.md` | site baseline; save as a new dated report; note new-post count |
| 2026-11-23 | site | The ten never-crawled posts (see plan B3): last-crawled dates | `batch_url_inspection` on their URLs |
| 2026-11-27 | experiment | A6 English-title batch (6 pages): first readout, 28 days after 2026-10-30 | `reports/2026-10-23-title-batch-baseline.md` explains how to read it; if the six pages have under about 60 clicks, wait for the next row |
| 2026-12-25 | experiment | A6 English-title batch: 56-day readout and decision on the other ~90 titles | same report; a flat result means drop the remaining titles |

## Done

| Done | Kind | Item | Result |
|---|---|---|---|
| 2026-10-26 | post | `paper-intro/many-shot-cot-icl` first performance check (2026-09-16 to 2026-10-26) | zh 65 impressions, position 9.1; en 40 impressions, position 8.4; 0 clicks. Each page is under 100 impressions and clicks are far under 60, so no title change; recheck with the next `site` baseline row |

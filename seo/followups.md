# SEO follow-ups

The to-do queue for checks that happen *after* something shipped. A `SessionStart` hook
(`.agents/skills/seo/scripts/due.py`) injects every row in **Open** whose date has arrived, so a
new session finds out without being told. Keep the table format: first cell is `YYYY-MM-DD`.

How to close a row: do the check (recipe in `.agents/skills/seo/SKILL.md`), move the row to
**Done** with the result in one line, and, for recurring kinds, add the next row to Open.

Kinds: `post` (one-off check on a new or edited article), `experiment` (readout of a change set),
`site` (recurring whole-site measurement).
Cadence for new posts: `post` rows at 1 week (indexed?) and 3 weeks (impressions, position, CTR).
Recurring: `site` baseline monthly, never-crawled pages monthly.

## Open

| Due | Kind | Item | How |
|---|---|---|---|
| 2026-12-01 | post | `paper-intro/context-language-models`: impressions, position, CTR | post check; no site demand for the paper name at publish time (context demand lands on memgpt, agentic-context-engineering and context-engineering), so under about 30 impressions means record it and do not tweak the title |
| 2026-11-27 | experiment | A6 English-title batch (6 pages): first readout, 28 days after 2026-10-30 | `reports/2026-10-23-title-batch-baseline.md` explains how to read it; if the six pages have under about 60 clicks, wait for the next row |
| 2026-12-05 | post | `paper-intro/skillzip` en after the 2026-11-14 title change: impressions, CTR, position vs baseline (121 impressions, 0 clicks, position 6.8, 2026-10-21 to 2026-11-11) | post check; this was the post's one title adjustment, so record the result and do not tweak again. Under about 60 clicks total, report the direction only |
| 2026-12-25 | experiment | A6 English-title batch: 56-day readout and decision on the other ~90 titles | same report; a flat result means drop the remaining titles |
| 2026-12-02 | post | `paper-intro/jevact`: impressions, position, CTR | post check; no site demand for JevAct at publish time (Jev demand lands on `ai-concept/jev-overview`), so under about 30 impressions means record it and do not tweak the title |
| 2026-12-06 | post | `paper-intro/jev-mem`: impressions, position, CTR | post check; no site demand for Jev-Mem at publish time (memory demand lands on mem0, memgpt, mirix, mem-rl; RRF on cerebras-rag), so under about 30 impressions means record it and do not tweak the title |
| 2026-12-06 | post | `paper-intro/decision-rag`: impressions, position, CTR | post check; no site demand for DecisionRAG at publish time (RAG demand lands on cerebras-rag, raft, sag, table-rag), so under about 30 impressions means record it and do not tweak the title |
| 2026-11-30 | post | `paper-intro/skill-state` (PR opened 2026-11-23): is it indexed and crawled? | `batch_url_inspection` on the zh and en URLs |
| 2026-12-14 | post | `paper-intro/skill-state`: impressions, position, CTR | post check; no site demand for SKILL.state at publish time ("skill state" collides with résumé phrasing; memory demand lands on memgpt, mem0), so under about 30 impressions means record it and do not tweak the title |
| 2026-11-26 | post | `paper-intro/is-bash-all-you-need` (PR opened 2026-11-19): is it indexed and crawled? | `batch_url_inspection` on the zh and en URLs; pre-publish Chrome results-page check was skipped (no browser tool in the session) |
| 2026-12-10 | post | `paper-intro/is-bash-all-you-need`: impressions, position, CTR | post check; no site demand for the paper name or bash agents at publish time (bash only matches "bash vs yarn" on other/yarn), so under about 30 impressions means record it and do not tweak the title |
| 2026-12-23 | site | Monthly baseline: last 90 days vs the 90 before, against `reports/2026-11-24-monthly-baseline.md` | site baseline plus movers check; save a new dated report; ask the author the decisions still open in `plan.md` G3 |
| 2026-12-23 | site | B3 never-crawled posts: last-crawled dates for the 9 URLs not indexed on 2026-11-24 | `batch_url_inspection`; list in `reports/2026-11-24-monthly-baseline.md` |
| 2026-12-22 | post | `ai-concept/jev-overview` (zh): movers check, clicks 22 to 4 and impressions 1,154 to 348 at the same position (28 days to 2026-11-21) | post check; same position means demand changed, so record it; do not change the page from this alone |
| 2026-12-04 | post | `paper-intro/videojev` (PR opened 2026-11-27): is it indexed and crawled? | `batch_url_inspection` on the zh and en URLs; pre-publish GSC checks were skipped (local GSC MCP unavailable / timed out) |
| 2026-12-18 | post | `paper-intro/videojev`: impressions, position, CTR | post check; pre-publish GSC checks were skipped (`suggest.py` ran: VideoJev has no collision, `temporal grounding` has concept demand, `video QA` collides with video quality / game QA); under about 30 impressions means record it and do not tweak the title |

## Done

| Done | Kind | Item | Result |
|---|---|---|---|
| 2026-11-24 | post | `paper-intro/decision-rag` indexed? | zh and en Submitted and indexed, last crawled 2026-11-15 |
| 2026-11-24 | post | `paper-intro/jev-mem` indexed? | zh and en Submitted and indexed, last crawled 2026-11-15 |
| 2026-11-24 | post | `paper-intro/tasteful-agent` | 2026-11-01 to 2026-11-24: zh 0 clicks / 53 impressions / position 10.1; en 0 / 50 / 7.2. Each over 30 but under 100 impressions; recorded, no title change |
| 2026-11-24 | post | `ai-concept/subagent-fold` | 2026-11-01 to 2026-11-24: zh 8 / 141 / 4.9 / 5.7%; en 1 / 424 / 8.2 / 0.24%. The en page meets the one-time title rule, but its impressions are the exact title of the Anthropic post it discusses (searchers want the original); reported to the author, left for a separate PR on request |
| 2026-11-24 | site | Monthly baseline | `reports/2026-11-24-monthly-baseline.md`: 90 days to 2026-11-21, 1,853 clicks (+65% vs the 90 before, +20% vs the October baseline), 192,338 impressions (-11%, US), Taiwan 1,145 clicks at 6.3; 25 posts in the window. Movers: `jev-overview` (row added) |
| 2026-11-24 | site | B3 never-crawled posts | 7 of 16 URLs now indexed; 5 discovered-not-indexed (the `python-function` series), 4 unknown to Google though in the sitemap |
| 2026-11-16 | post | `paper-intro/llm-as-a-verifier` | checked 2026-11-19 (2026-10-27 to 2026-11-19): zh 4 clicks / 113 impressions / position 6.6 / CTR 3.5%; en 0 / 26 / 9.5. Up from the baseline (zh 24 impressions); en still under 30, recorded, no title change |
| 2026-11-16 | post | `paper-intro/procedural-graphs` | checked 2026-11-19 (2026-10-26 to 2026-11-19): zh 5 / 182 / 6.3 / 2.7%; en 0 clicks / 141 impressions / position 5.4. The en page meets the one-time title-adjustment rule (over 100 impressions, top 10, CTR 0); reported to the author, left for a separate PR on request |
| 2026-11-17 | post | `paper-intro/context-language-models` indexed? | checked 2026-11-19: zh and en Submitted and indexed, last crawled 2026-11-11 |
| 2026-11-17 | post | `paper-intro/wikiskill` | checked 2026-11-19 (2026-10-27 to 2026-11-19): zh 16 / 126 / 4.9 / 12.7%; en 9 / 231 / 6.7 / 3.9% vs baseline en CTR 1.4% at 7.3. Direction positive, but 25 clicks total is under 60, so no verdict |
| 2026-11-18 | post | `paper-intro/evoontology` | checked 2026-11-19 (2026-10-27 to 2026-11-19): zh 8 / 113 / 6.5 / 7.1%; en 0 / 84 / 7.5. Recorded, no title change |
| 2026-11-18 | post | `paper-intro/jevact` indexed? | checked 2026-11-19: zh and en Submitted and indexed, last crawled 2026-11-15 and 2026-11-16 |
| 2026-11-11 | post | `paper-intro/skillzip`: impressions, position, CTR | 2026-10-21 to 2026-11-11: zh 101 impressions, 3 clicks (CTR 3.0%), position 6.4; en 121 impressions, 0 clicks, position 6.8. Over 100 impressions at position under 10 with en CTR 0, so the en title qualifies for its one adjustment; only 9 impressions show a query (skillzip, skill zip). Not changed in this session: a title change is its own PR, on the author's go-ahead |
| 2026-11-10 | post | `paper-intro/evoontology` indexed and crawled check | zh and en both PASS, submitted and indexed, last crawled 2026-10-28 |
| 2026-11-10 | post | `paper-intro/tasteful-agent` indexed and crawled check | zh and en both PASS, submitted and indexed, last crawled 2026-11-03 |
| 2026-11-10 | post | `ai-concept/subagent-fold` indexed and crawled check | zh and en both PASS, submitted and indexed, last crawled 2026-11-03 (zh) and 2026-11-04 (en) |
| 2026-11-03 | post | `paper-intro/llm-as-a-verifier` re-crawl check | both indexed (PASS); en re-crawled 2026-10-30 (after the 2026-10-26 re-publish), zh last crawled 2026-10-17, so the zh page is not yet re-crawled with the new title; the owner can press Request indexing on the zh URL |
| 2026-11-03 | post | `paper-intro/procedural-graphs` indexed and crawled check | zh and en both PASS, submitted and indexed, last crawled 2026-10-27 |
| 2026-11-03 | post | `paper-intro/wikiskill` re-crawl check | both indexed (PASS); zh re-crawled 2026-11-01 (after the 2026-10-27 re-publish), en last crawled 2026-10-12, so the en page is not yet re-crawled with the new title; the owner can press Request indexing on the en URL |
| 2026-10-28 | post | `paper-intro/skillzip` indexed and crawled check | zh and en both PASS, submitted and indexed (last crawled zh 2026-10-27, en 2026-10-26) |
| 2026-10-26 | post | `paper-intro/many-shot-cot-icl` first performance check (2026-09-16 to 2026-10-26) | zh 65 impressions, position 9.1; en 40 impressions, position 8.4; 0 clicks. Each page is under 100 impressions and clicks are far under 60, so no title change; recheck with the next `site` baseline row |

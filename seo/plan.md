# SEO action plan

Source: `reports/2026-10-23-gsc-baseline.md`. Update statuses in place; record each change in `log.md`.

Status: `todo` / `doing` / `done` / `dropped` (say why) / `decide` (needs the author's call).

## Baseline to beat (last 90 days to 2026-10-22)

Clicks 1,544 | impressions 178,168 | CTR 0.87% | position 10.3 | Taiwan clicks 1,023 | Taiwan CTR 2.67%.
Re-measure with the same windows (90 d vs the preceding 90 d) and note any new post counts, since
new posts alone move clicks.

## Strategy in one line

About two thirds of clicks come from Taiwan at position 6. Protect and grow that. The US/English
market is 29% of impressions at position 12-23 and is a separate, slower decision (C1).

---

## Where the effort pays (my estimates, none measured yet)

Added 2026-10-26 after checking how large each item could be. The English title batch (A6) is worth
at most about +3-6% of clicks even if it works; clicks are concentrated (top 10 posts = 47%).

| Item | Size of the prize | Verdict |
|---|---|---|
| Per-post checks at publish time (`seo` skill) | Avoids self-inflicted losses (cut titles, ambiguous names, orphan pages); does not create demand | Standing process, see `followups.md` |
| A5 extend the DPO article | DPO is the biggest Taiwan query we hold; uplift unknown | Best single bet, needs the author's call |
| A6 English titles | +3-6% at best | Running; the other ~90 titles wait for the readout |
| B1 agent-memory hub | Unknown | Worth a look after A5 |
| B3 never-crawled posts | Small, ten posts | Monthly check only |
| A7, B4, B2, C2-C4 | Low | Candidates to drop; keep unless a readout says otherwise |
| C1 US/English market | Large but needs backlinks and authority GSC cannot show | Decision for the author |

## A. Taiwan market (highest return)

### A1. Check hreflang and canonical output for the zh/en pairs. `done` (2026-10-23): no fix needed
- Result: all 393 sitemap URLs on the live site return 200; canonical is self-referencing; hreflang
  `zh-TW` / `en` / `x-default` present and reciprocal (only `/en/offline/` lacks it, harmless).
  Details: `reports/2026-10-23-a1-hreflang-check.md`.
- Correction to the earlier hypothesis: the zh-vs-en CTR gap in Taiwan is mostly different queries
  per version (English pages are 8% of Taiwan impressions, and 30% of those are one generic query),
  not Google picking the wrong version. Do not spend more time on language routing.

### A2. Low CTR at good rank for generic concept queries in Taiwan. `done` (2026-10-23): diagnosed, mostly not a copy problem
- Checked the live Taiwan results page for `dpo`, `dropout`, `計算機結構`, `computer architecture`.
  Details: `reports/2026-10-23-a2-serp-review.md`.
- Result: the low CTR is mostly SERP structure and intent, not our title/description. `dpo` has an
  AI Overview and a second meaning (Data Protection Officer); `computer architecture` has a video
  carousel and image pack above us; `計算機結構` is course-notes intent. Our snippets (title, date,
  sitelinks) look healthy. **Do not rewrite titles for these head queries.**
- The one concrete copy defect found is A6. The winnable targets are long-tail queries: A5, A7.

### A5. Extend the DPO article to cover what Google's related searches ask. `todo` (needs author's call)
- Evidence: we are #2 for `dpo` and `dpo 是什麼` with a short article (~3,800 characters, five sections;
  PPO mentioned once, GRPO and TRL never). Google's related searches: `dpo ppo 區別`, `grpo vs dpo`,
  `dpo 算法`, `dpo rlhf`, `dpo trainer`. Taiwan `dpo` demand is the largest of any query we hold
  (1,472 impressions in 90 days).
- Do: add sections on DPO vs PPO, DPO vs GRPO, the loss in plain words, and a short TRL training example.
  Keep it accurate to the paper; this is an article change, so it goes through the usual PR and the
  author decides whether it comes from the AI-Research pipeline or a direct edit.
- Measure: impressions and position for `dpo ppo`, `grpo vs dpo`, `dpo 算法` queries over 28-56 days.

### A6 (includes A8). Shorten long English titles on well-ranked pages. `doing` (6 pages live: PR #77 and #79 merged 2026-10-23; waiting for the measurement window, "after" starts about 2026-10-30)
- One experiment, six pages: `what-is-computer-architecture` (#77) plus `mem0`, `fastapi-race-condition`,
  `claude-code`, `sparse-upcycling`, `mem-rl` (#79). Baseline and how to read the result:
  `reports/2026-10-23-title-batch-baseline.md`. English baseline is only 29 clicks in 28 days across the six,
  so judge the aggregate (CTR 0.35%) and use 56 days if needed.
- Done 2026-10-23: title is now `Computer Architecture vs Computer Organization` (46 chars), `lastmod` bumped,
  `verify_post.py` and a local Hugo build pass. Audit of all English titles and drafts for the next
  ones: `reports/2026-10-23-a6-en-title-audit.md`. Google truncates by pixel width at roughly
  47-62 chars; 52 or fewer is safe. 97 of 142 English titles are above 55.
- Original note follows.
- Evidence: shown truncated on Google as "Computer Architecture Explained: The Bridge ...".
- Do: front-load the distinguishing words, for example "Computer Architecture vs Computer Organization:
  What's the Difference?" (keep under about 60 characters). Expected lift is small, since video and image
  blocks sit above it; the benefit is mainly for the comparison query in A7.
- Check other English titles for the same truncation before changing only one. (Done: see A8.)

### A8. Shorten the next batch of long English titles on well-ranked pages. `done` (merged into A6; first batch of five in PR #79). The remaining ~90 titles wait for the A6 result.
- Original note follows.
- Evidence: 94 of 135 English pages with impressions have titles above 55 chars and carry 65% of
  their impressions. Best candidates are where position is already good: `fastapi-race-condition` (7.8),
  `claude-code` (8.3), `pytorch-apple-silicon-m1-gpu` (7.3), `sparse-upcycling` (7.4), `mem-rl` (8.4).
- Do: apply the draft titles in the audit report to about five pages, one PR, then wait 28 days
  and compare before doing the other ~90. Titles are editorial; each draft must be checked against its article.
- Optional follow-up for the author: tighten the `title` rule in `hugo-conventions.md` from "about 50-60"
  to "52 or fewer, key terms before the colon", since most posts overshoot today.
- Low priority, related: 108 of 142 English descriptions are above 160 chars (this post's was 255).

### A7. Lean into comparison queries on the architecture article. `todo` (small)
- Evidence: we are **#1** in Taiwan for `computer organization vs computer architecture`, ahead of
  GeeksforGeeks and a university page. The generic `computer architecture` is crowded and unwinnable.
- Do: keep the `Computer Architecture vs Computer Organization` section prominent (it already exists), make
  sure the English page's title/description say "vs" and "difference" (see A6), and consider an FAQ block.
- Still open (nationwide, not Taiwan-specific, not yet examined on the live SERP): `mem0` 2,810 imp pos 9.2;
  `memgpt` 1,489 pos 12.2; `direct preference optimization` 905 pos 17.7.
- Caveat for A5-A7: changing a title or article can move rankings either way. Change a few pages, not
  all, and log dates in `log.md`.

### A3. Keep publishing timely papers/techniques in Chinese, early. `todo` (ongoing)
- Evidence: pages that started getting impressions this window earn 20-60 clicks each in 90 days
  (`wikiskill`, `jev-overview`, `adaptive-chunking`, `bias-variance-tradeoff`, `dream-rsi`).
- Short, specific names in the title and H1 matter more than the full paper title.

### A4. Stop optimizing for exact-title + "arxiv" queries. `done` (decision)
- 1,070 such queries gave 13,327 impressions and 34 clicks. The searcher wants the paper.

## B. Coverage and structure

### B1. Agent-memory hub page. `todo`
- Evidence: mem0, memgpt, langmem, mirix, memrl all have steady impressions; `tags/agent-memory`
  ranks around 20. Inference (not proven): a comparison/overview page that links all of them
  would capture broader queries and strengthen internal links.
- Needs: the author's agreement on scope; content comes via the AI-Research pipeline.

### B2. Merge or rewrite the two AWS posts. `todo`
- `aws-ml-service` and `aws-ai-service` compete for the same queries, at position 27-65.
- Do: pick one canonical post, fold in the other, redirect the loser.

### B3. Ten old posts never crawled. `todo`
- `python-function` 1-3, `python-loop`, `define-problem`, `face-recognition`,
  `house-price-prediction`, `chateval` (and English twins). "Discovered - currently not indexed".
- Do: add contextual internal links from indexed pages; consider consolidating the Python series;
  request indexing manually in the Search Console UI (no tool for it here).
- Measure: `batch_url_inspection` shows a last-crawled date.

### B4. Check `fastapi-race-condition` for a direct answer to "is FastAPI single threaded". `todo`
- 297 impressions at pos 7.6, 0 clicks. Unverified whether the article answers it up front.

## C. Decisions and lower-priority items

### C1. Decide whether to invest in the US/English market. `decide`
- English pages: US pos 23.0, 14,501 impressions, 7 clicks. That is a ranking/authority problem, not a
  title problem. Raising it likely needs backlinks and differentiated content.
- English pages still deliver about a quarter of clicks overall, so do not deindex them.

### C2. Thin tag and pagination pages. `todo` (low confidence)
- `/page/N/` and many `/tags/*` pages get impressions with zero clicks at position 10-40.
- Consider `noindex` for tags with one or two posts. Watch crawl stats first.

### C3. Image alt text on figure-heavy posts. `todo` (low value)
- Image search has impressions but ranks 33-49.

### C4. Spot-check mobile experience. `todo` (low confidence)
- Mobile is 13% of impressions, unusually low. Could simply be a desktop-heavy technical audience.
- Needs PageSpeed Insights / CrUX; not available through GSC.

## D. Needs data GSC does not have

| Question | Source needed |
|---|---|
| Why is US ranking weak (backlinks, authority)? | Backlink tool (Ahrefs/Semrush) |
| Which uncovered topics have demand? | Google Trends / keyword tool |
| What do visitors do after landing? | Google Analytics |
| Core Web Vitals | PageSpeed Insights / CrUX |

## E. Open questions

- What caused the 2026-07-10 spike and the Jul-Aug position slide (10.7-12.0)? Not explained.
- ~~Is Google serving the English page to Taiwanese users?~~ Answered by A1: no evidence of that.
- ~~Why do generic concept queries convert at 1-3% at positions 4-8?~~ Answered by A2: SERP blocks and intent.
- Does the Google AI Overview for `dpo` cite us? Not visible in page text; check by eye.
- Do the same live-SERP review for `mem0`, `memgpt` and `direct preference optimization` before touching those pages.

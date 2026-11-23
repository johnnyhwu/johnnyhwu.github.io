# Monthly site baseline, 2026-11-24

Property `sc-domain:datasciocean.com` (URL Inspection: `https://datasciocean.com/`), tool: local `gsc` MCP,
web search only. Data lags 2 to 3 days, so windows end 2026-11-21.

## Headline: last 90 days vs the 90 before

| Window | Clicks | Impressions | CTR | Position (approx.) | Taiwan clicks | Taiwan impressions | Taiwan CTR | Taiwan position |
|---|---|---|---|---|---|---|---|---|
| 2026-08-24 to 2026-11-21 | 1,853 | 192,338 | 0.96% | about 9.4 | 1,145 | 50,113 | 2.28% | 6.3 |
| 2026-05-26 to 2026-08-23 | 1,124 | 214,957 | 0.52% | about 10.0 | 755 | 28,484 | 2.65% | 6.5 |
| Baseline in `plan.md` (90 days to 2026-10-22) | 1,544 | 178,168 | 0.87% | 10.3 | 1,023 | n/a | 2.67% | n/a |

Totals are the sum of the `device` rows; position is the impression-weighted mean of those rows
(an inference, GSC does not return a site total here).

- Clicks +65% on the 90 days before, +20% on the October baseline. 25 posts were published inside the
  current window, 10 of them after the baseline date, so new posts explain part of the rise (not measured
  how much).
- Impressions fell 11% vs the window before, almost all from the US (82,631 to 47,914) and Japan/Korea;
  US clicks rose (38 to 111). Inference: fewer low-position English impressions, not lost demand.
- Taiwan impressions +76%, clicks +52%, CTR down (2.65% to 2.28%) at about the same position. More
  queries at the same rank, each converting a little less; not a copy problem on its own.
- DPO (A5): `dpo` 1,724 impressions, 32 clicks, position 6.0 (was 1,472 impressions at the baseline).
  Still the largest query we hold. Related forms still thin on our side: `ppo dpo` 8, `dpo training` 8.

## Movers check (last 28 days vs the 28 before, by page)

Windows 2026-10-25 to 2026-11-21 vs 2026-09-27 to 2026-10-24, top 60 pages by click change (of 788),
so a page that lost impressions but not clicks could be missing.

| Page | Clicks | Impressions | Position | Read |
|---|---|---|---|---|
| `ai-concept/jev-overview` (zh) | 22 to 4 | 1,154 to 348 | 8.9 to 8.8 | Same position, demand fell: a SERP or interest change, not ours. Follow-up row added |
| `python-tutorial/first-python-program` (zh) | 3 to 1 | 338 to 164 | 7.5 to 7.0 | Same position, fewer impressions; under the click threshold, recorded only |

Risers worth knowing: `en/other/beautify-terminal-on-macos` 12 to 50 clicks; `paper-intro/sag` 6 to 18
(position 9.0 to 5.8); `ai-concept/house-price-prediction` 2 to 6 (position 11.4 to 4.4, see B3).

## B3: the ten never-crawled posts (16 URLs)

`batch_url_inspection`, 2026-11-24:

| State | URLs |
|---|---|
| Indexed (7) | `en/python-function` (crawled 2026-09-15), `en/python-loop` (2026-09-09), zh `define-problem` (2026-10-27), zh and en `face-recognition` (2026-11-08), zh `house-price-prediction` (2026-10-24), zh `chateval` (2026-11-15) |
| Discovered, not indexed (5) | zh `python-function`, zh and en `python-function-2`, zh and en `python-function-3` |
| Unknown to Google (4) | zh `python-loop`, en `define-problem`, en `house-price-prediction`, en `chateval` |

All four "unknown" URLs are in the built sitemaps (checked in `.tools/public`). The Python function
series is the stuck part; consolidating it (B3's second idea) is the remaining lever. The owner can press
Request indexing on the four unknown URLs in the GSC UI.

## Post rows closed in the same session

- `decision-rag`, `jev-mem` indexed: all four URLs Submitted and indexed, last crawled 2026-11-15.
- `tasteful-agent` (2026-11-01 to 2026-11-24): zh 0 clicks / 53 impressions / position 10.1; en 0 / 50 / 7.2.
- `subagent-fold` (2026-11-01 to 2026-11-24): zh 8 / 141 / 4.9 / 5.7%; en 1 / 424 / 8.2 / 0.24%. The en page
  meets the one-time title rule (over 100 impressions, top 10, low CTR). Its impressions are almost all the
  exact title of the Anthropic post it discusses ("building agents: when to fold subagents into your main
  agent loop", 72 at position 10.2): people looking for the original, so a title change may not win clicks.

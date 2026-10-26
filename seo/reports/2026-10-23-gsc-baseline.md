# GSC baseline: 2026-10-23

- Property: `sc-domain:datasciocean.com`
- Current window: 2026-07-25 to 2026-10-22 (90 days). Previous window: 2026-04-26 to 2026-07-24.
- Long trend: 2025-06-01 to 2026-10-22, monthly.
- Search type: WEB unless stated. Pages = article URLs, `#fragment` rows excluded.
- Status of this report: frozen. New analyses go in a new file.

## 1. Site health

| Metric | Last 90 d | Previous 90 d | Change |
|---|---|---|---|
| Clicks | 1,544 | 1,200 | +28.7% |
| Impressions | 178,168 | 260,953 | -31.7% |
| CTR | 0.87% | 0.46% | about 2x |
| Avg position | 10.3 | about 9.3 (derived) | slightly worse |

The previous-window figures are derived (180-day totals minus 90-day totals; position
impression-weighted), so treat them as approximate.

Monthly (clicks / impressions / avg position):

| Month | Clicks | Impressions | Pos |
|---|---|---|---|
| 2025-06 | 50 | 3,078 | 9.9 |
| 2025-12 | 329 | 34,423 | 8.7 |
| 2026-03 | 654 | 78,838 | 7.8 |
| 2026-05 | 475 | 97,849 | 8.9 |
| 2026-06 | 371 | 91,161 | 9.1 |
| 2026-07 | 377 | 67,681 | 10.7 |
| 2026-08 | 412 | 52,211 | 12.0 |
| 2026-09 | 614 | 72,576 | 9.6 |
| 2026-10 (to 22nd) | 423 | 42,730 | 9.1 |

Clicks grew about 8x in 16 months. Impressions peaked in May 2026 and have roughly halved;
clicks did not follow. Position dipped to 10.7-12.0 in Jul-Aug and recovered in Sep.
The cause of the dip is unknown.

Notable days: 2026-07-10 impressions 5,954 at avg position 21.0 (one-day anomaly), after which
daily impressions fell from about 3,000 to 1,500-2,000.

## 2. Where the traffic is (country, last 90 d)

| Country | Impressions | Clicks | CTR | Pos |
|---|---|---|---|---|
| Taiwan | 38,277 | 1,023 (66% of clicks) | 2.67% | 6.3 |
| USA | 52,506 (29% of impressions) | 65 | 0.12% | 12.1 |
| China | 8,808 | 71 | 0.81% | 7.4 |
| Hong Kong | 6,584 | 59 | 0.90% | 7.9 |

English-version pages (`/en/`) in the USA: 14,501 impressions, 7 clicks, **avg position 23.0**.
The same English pages in Taiwan: avg position 5.7.

Taiwan only, similar rank, different language version:

| | Impressions | Clicks | CTR | Pos |
|---|---|---|---|---|
| Chinese pages | 19,935 | 463 | 2.32% | 6.2 |
| English pages | 1,712 | 14 | 0.82% | 5.7 |

Device: desktop 153,416 imp / 1,234 clk (CTR 0.80%); mobile 23,931 / 295 (1.23%); tablet 821 / 15.
Discover: no traffic. Image search: small (e.g. `en/llm-fine-tuning-rlhf` 16,741 imp, 27 clk, pos 36.6).

## 3. Indexing

- Sitemap `https://datasciocean.com/sitemap.xml` (index): `en` 196 + `zh-tw` 196 URLs, 0 errors, 0 warnings, last read 2026-10-16/21.
- 318 of 393 sitemap URLs had impressions in the window. The rest are tag/pagination/category pages
  except 12 article URLs.
- 10 of those 12 inspected: all "Discovered - currently not indexed", never crawled. All old posts
  (2022-2024): `python-tutorial/python-function`, `-2`, `-3`, `python-loop`, `ai-concept/define-problem`,
  `face-recognition`, `house-price-prediction`, `paper-intro/chateval`, plus the English versions of
  several of them. Not yet inspected: `en/authors`, `en/offline` (not articles).
- Spot check: both language versions of `memgpt`, `mem0`, `what-is-computer-architecture` are
  "Submitted and indexed" and recently crawled.

## 4. Query intent (visible queries only, `site:` excluded; 3,965 queries, 62,938 imp, 605 clk)

| Script | Queries | Impressions | Clicks | CTR |
|---|---|---|---|---|
| Pure English | 3,582 | 55,324 (88%) | 518 (86%) | 0.94% |
| Pure Chinese | 94 | 2,834 (5%) | 57 (9%) | 2.01% |
| Mixed | 289 | 4,780 (8%) | 30 (5%) | 0.63% |

Pure-English queries by landing language: on Chinese pages 20,431 imp / 429 clk (CTR 2.10%);
on English pages 34,893 imp / 89 clk (0.26%).

Long English queries (5+ words, mostly exact paper titles, often with "arxiv"): 1,070 queries,
13,327 imp, 34 clk (0.26%). Intent is the original paper, not this site.

## 5. Opportunity lists

### High impressions, low CTR (pages)

| Page | Imp | Clk | CTR | Pos |
|---|---|---|---|---|
| `/en/paper-intro/memgpt/` | 19,805 | 16 | 0.08% | 8.3 |
| `/en/other/what-is-computer-architecture/` | 7,948 | 34 | 0.43% | 13.2 |
| `/en/paper-intro/mem0/` | 7,035 | 7 | 0.10% | 10.0 |
| `/en/other/yarn/` | 3,741 | 2 | 0.05% | 12.2 |
| `/en/paper-intro/sparse-upcycling/` | 3,469 | 2 | 0.06% | 7.4 |
| `/en/paper-intro/mem-rl/` | 3,192 | 2 | 0.06% | 8.4 |
| `/en/paper-intro/mirix/` | 2,901 | 0 | 0% | 8.1 |
| `/en/other/aws-ai-service/` | 2,897 | 1 | 0.03% | 39.0 |
| `/en/paper-intro/raft-adapting-language-model-to-domain-specific-rag/` | 1,716 | 0 | 0% | 8.1 |
| `/en/paper-intro/gaia/` | 1,617 | 0 | 0% | 7.3 |

Chinese side: `/paper-intro/dpo/` 5,122 imp, 1.37%, pos 12.7; `/ai-concept/dropout/` 3,940 imp, 1.22%, pos 13.5.

### Queries at position 8-20

| Query | Imp | Clk | Pos | Lands on |
|---|---|---|---|---|
| `computer architecture` | 4,273 | 6 | 10.8 | English page |
| `mem0` | 2,810 | 14 | 9.2 | Chinese page |
| `dropout` | 2,180 | 30 | 8.2 | Chinese page |
| `memgpt` | 1,489 | 18 | 12.2 | mostly English page |
| `direct preference optimization` | 905 | 17 | 17.7 | Chinese `dpo` |
| `machine learning` | 546 | 0 | 10.5 | `what-is-machine-learning` |
| `memrl` | 437 | 2 | 9.2 | English page |
| `mem0 paper` | 418 | 1 | 11.4 | English page |
| `mirix` | 370 | 2 | 8.3 | English page |
| `langmem` | 348 | 22 | 8.0 | Chinese page (already fine) |

### Cannibalization

Between different articles it is small. Real cases, all ranking too low to matter:
`aws-ml-service` vs `aws-ai-service` (pos 41-64), `parallel programming` (pos 54-63),
`basic-probability-joint-marginal-conditional` vs `conditional-vs-joint-probability` (pos 2.8 vs 7.8).

The larger overlap is the Chinese and English versions of the same article (22 queries where both
show). Examples: `memgpt` zh pos 3.4 / en pos 22.7; `mem0` zh 8.2 / en 20.0; `wikiskill` zh 3.6 / en 7.6.

### Impressions with zero clicks (worth acting on)

Exact-title + "arxiv" queries (about 2,100 imp for MemGPT variants, 467 for OctoTools): navigational to
the paper, not winnable. `is fastapi single threaded` (297 imp, pos 7.6) might be an intent gap in the
article (unverified). Generic: `machine learning`, `yarn`.

## 6. What drives clicks

Top pages by clicks (zh unless noted): `what-is-computer-architecture` 192 (3.59%, pos 6.1), `dpo` 70,
`wikiskill` 61 (10.4%), `vllm-semantic-router` 59, `dropout` 48, `mem0` 42, `jev-overview` 39,
`en/fastapi-race-condition` 38, `adaptive-chunking` 35.

Pages with no impressions in the previous window that now earn clicks: `wikiskill`, `jev-overview`,
`adaptive-chunking`, `bias-variance-tradeoff`, `dream-rsi`.

Impression losses are demand-driven, not ranking losses (position flat): `mem0` -58%, `memgpt` -71%,
`en/fastapi-race-condition` -74%.

## 7. Content-gap candidates (existing pages ranking poorly, not missing topics)

AWS cluster (`aws ai services`, `aws ml services`, `aws machine learning services`): about 900
impressions at pos 27-65. `lightsail wordpress` cluster: about 460 imp at pos 29-45. `plan act`
(364 imp, pos 32), `parallel programming` (127 imp, pos 61).

## 8. Caveats specific to this report

- Query-level data covers 62,938 of 178,168 impressions (35%, after removing `site:`).
- Only the top 500 + 256 page rows were used for page-level splits; the tail is low-impression.
- The 7/10 anomaly and the Jul-Aug position dip were not explained.

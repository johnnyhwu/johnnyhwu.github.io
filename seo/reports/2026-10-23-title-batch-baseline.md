# Baseline for the English title batch (A6 + A8): 2026-10-23

Window before the change: 2026-09-25 to 2026-10-22 (28 days), property `sc-domain:datasciocean.com`,
search type WEB, page rows without `#fragment`. Change set: PR #77 (merged 2026-10-23) and PR #79
(open when this was written). Only the English `title` changed; the Chinese pages are listed because
the two language versions share queries and can trade impressions.

## Pages and titles

| Page | New English title |
|---|---|
| `other/what-is-computer-architecture` | Computer Architecture vs Computer Organization |
| `paper-intro/mem0` | Mem0: Scalable Long-Term Memory for AI Agents |
| `other/fastapi-race-condition` | FastAPI Race Conditions: Thread-Safe vs Async-Safe |
| `ai-concept/claude-code` | Claude Code Concepts: Agentic Loop, Tools, Skills |
| `paper-intro/sparse-upcycling` | Sparse Upcycling: MoE from Dense Checkpoints |
| `paper-intro/mem-rl` | MemRL: Self-Evolving AI Agents Without Fine-Tuning |

## Baseline (28 days before)

| Page | EN imp | EN clk | EN CTR | EN pos | ZH imp | ZH clk | ZH CTR | ZH pos |
|---|---|---|---|---|---|---|---|---|
| what-is-computer-architecture | 4,658 | 11 | 0.24% | 9.2 | 1,525 | 40 | 2.62% | 4.8 |
| mem0 | 757 | 3 | 0.40% | 11.3 | 804 | 12 | 1.49% | 7.6 |
| fastapi-race-condition | 835 | 7 | 0.84% | 6.9 | 60 | 3 | 5.00% | 10.7 |
| claude-code | 1,069 | 7 | 0.65% | 7.4 | 157 | 4 | 2.55% | 8.5 |
| sparse-upcycling | 260 | 0 | 0% | 8.7 | 44 | 0 | 0% | 5.5 |
| mem-rl | 669 | 1 | 0.15% | 8.2 | 127 | 0 | 0% | 8.1 |
| **English total** | **8,248** | **29** | **0.35%** | | | | | |

For comparison, the same English pages over the previous 90 days had far more impressions
(e.g. `fastapi-race-condition` 5,126; `mem0` 7,035). Search demand for several of these fell, not
rankings, so before/after comparisons must be done on **ratios and position**, not raw counts.

## How to read the result later (so a noisy number is not mistaken for a verdict)

- The signal is tiny: 29 English clicks across all six pages in the baseline window. A change of a
  handful of clicks is noise. Judge the **aggregate** English CTR of the six pages, not each page, and
  prefer a 56-day window over 28 if the aggregate is still under about 60 clicks per window.
- Primary metric: aggregate English CTR (baseline 0.35%). Secondary: English average position, and
  whether Chinese-page CTR moved the other way (substitution between versions).
- Expect lag: Google can take days to show a new title, and may rewrite titles it dislikes. Start the
  "after" window about a week after the second deploy.
- Confounders to note, not remove: search demand drift, new posts competing, a core update,
  `computer architecture` having a video/image-heavy results page.
- A flat result is a valid outcome: it would mean title width is not the lever for these pages, and
  the plan should drop the other ~90 titles (A8 follow-up) rather than do them.

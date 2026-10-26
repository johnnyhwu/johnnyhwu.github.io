# A1: hreflang and canonical check: 2026-10-23

Plan item A1. Question: is Google being sent the wrong language version to Taiwanese searchers
because of a hreflang or canonical misconfiguration?

## Method

- Fetched the **live** pages (what Google crawls), not a local build. Parsed `<link rel=canonical>`,
  `<link rel=alternate hreflang>` and `<meta name=robots>`.
- Scope: all 393 URLs listed in `/en/sitemap.xml` and `/zh-tw/sitemap.xml` (script was throwaway,
  stdlib only). Checks per page: HTTP 200 with no redirect; canonical equals the page itself;
  hreflang has `zh-TW`, `en`, `x-default`; self-reference correct; the alternate returns 200 and
  points back (reciprocal); `x-default` equals the zh-TW URL; no `noindex`.

## Result: no defect found

393 / 393 returned 200 with no redirect. Everything passed except one:

- `https://datasciocean.com/en/offline/` has no hreflang. It is the PWA offline fallback page, not content.

Pattern on every content page, for example `memgpt`:

```
zh  canonical https://datasciocean.com/paper-intro/memgpt/
    hreflang zh-TW  -> /paper-intro/memgpt/
    hreflang en     -> /en/paper-intro/memgpt/
    hreflang x-default -> /paper-intro/memgpt/
en  canonical https://datasciocean.com/en/paper-intro/memgpt/   (same three alternates)
```

Chinese is the default language (no URL prefix) and is `x-default`. `<html lang>` is `zh-TW` / `en`.

## What this changes in the earlier analysis

The baseline report showed Taiwan CTR of 2.32% on Chinese pages vs 0.82% on English pages at similar
rank, and the plan suspected Google was serving the wrong version. The technical setup is correct,
and the Taiwan data does not support the suspicion either:

- English pages are only 1,712 of ~21,600 Taiwan impressions (8%).
- Their queries are mostly **exact English paper titles**, where the English page does well:
  `memgpt: towards llms as operating systems` pos 3.3, CTR 10.5%;
  `mem0: building production-ready ai agents ...` pos 3.4, CTR 12.9%.
- One query is 30% of that volume: `computer architecture` (505 impressions, pos 4.7, **CTR 0.4%**).
  That single generic query drags the English average down. The gap is mostly a difference in
  which queries each version serves, not Google choosing the weaker page.

## What Taiwan actually looks like (zh pages, last 90 days, `site:` excluded)

| Query | Imp | Clk | CTR | Pos |
|---|---|---|---|---|
| `dpo` | 1,472 | 21 | 1.43% | 4.0 |
| `計算機結構` | 1,031 | 24 | 2.33% | 5.0 |
| `dropout` | 904 | 27 | 2.99% | 7.9 |
| `wikiskill` | 176 | 36 | 20.5% | 3.0 |
| `memgpt` | 126 | 15 | 11.9% | 1.7 |
| `direct preference optimization` | 106 | 13 | 12.3% | 2.8 |
| `langmem` | 94 | 15 | 16.0% | 3.4 |
| `mem0 介紹` | 60 | 8 | 13.3% | 1.4 |
| `cerebras rag` | 23 | 11 | 47.8% | 1.0 |

Specific named techniques convert at 10-20%+ at positions 1-4. Generic concept queries
(`dpo`, `dropout`, `計算機結構`, English `computer architecture`) rank in the top 5-8 but convert
at 0.4-3%. That is where the headroom is, and it is a snippet/SERP-competition question, not a
language-routing one.

## Caveats

- GSC does not expose what is above the result (featured snippets, AI answers, Wikipedia, forums),
  so why `dpo` converts at 1.4% at position 4.0 is unexplained. It needs a manual look at the live
  SERP in the Taiwan locale.
- Impression counts for the English pages in Taiwan are small; per-query CTRs there are noisy.

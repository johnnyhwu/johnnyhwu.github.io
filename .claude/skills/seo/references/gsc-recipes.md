# GSC recipes

All calls use `site_url: "sc-domain:datasciocean.com"` unless noted. Dates are `YYYY-MM-DD`; compute
them from today's date. Post URLs: zh-TW `https://datasciocean.com/<section>/<slug>/`, English
`https://datasciocean.com/en/<section>/<slug>/`.

## Site vocabulary for a new topic

`get_advanced_search_analytics`: `dimensions: "query,page"`, `filter_dimension: "query"`,
`filter_operator: "contains"`, `filter_expression: "<term>"`, `start_date`: 90 days ago, `end_date`:
today, `row_limit: 100`. Run once per term (concept name, the paper's short name, obvious spelling
variants). Look at: which phrasings have impressions, which of our pages rank, their position.
Skip rows whose page contains `#`: those are section sitelinks.

## Who already covers the topic (cannibalisation and link targets)

`get_advanced_search_analytics`: `dimensions: "page"`, `filter_dimension: "page"`,
`filter_operator: "contains"`, `filter_expression: "<tag or slug fragment>"`, 90 days, sorted by
impressions. Pages with impressions are the link targets; two pages ranking for the same query is a
conflict worth reporting.

## Results page (Chrome)

`navigate` to `https://www.google.com/search?q=<url-encoded query>&gl=tw&hl=zh-TW`, then
`get_page_text`. Read: top results, AI Overview, video/image blocks, "related searches", "people also
ask". Close the tab afterwards. At most two searches per post.

## Indexed? (post row at +7 days)

`batch_url_inspection` with `site_url: "https://datasciocean.com/"` (the URL-prefix property) and both
language URLs, one per line. Report `coverageState` and last crawl time. "Discovered, currently not
indexed" after a week is worth telling the user.

## Performance of one post (post row at +21 days)

`get_advanced_search_analytics`: `dimensions: "query"`, `filter_dimension: "page"`,
`filter_operator: "contains"`, `filter_expression: "/<slug>/"` (matches both languages; split by
`/en/`), `start_date`: publish date, `end_date`: today. Also run it with `dimensions: "page"` for the
totals. Report impressions, clicks, CTR, position, top queries.

## Site baseline and period comparison

`compare_search_periods`: `period1` the latest 90 days ending 3 days ago, `period2` the 90 before,
`dimensions: "page"` or `"query"`, `limit: 50`. `get_performance_overview` (`days: 90`) for the
headline numbers. For Taiwan add `filters: [{"dimension":"country","operator":"equals",
"expression":"twn"}]`. Compare against the baseline in `seo/plan.md`.

## Title experiment readout

Follow `seo/reports/2026-10-23-title-batch-baseline.md`: same six pages, "after" window starting
2026-10-30, aggregate English CTR against 0.35%, also watch position and the Chinese pages.

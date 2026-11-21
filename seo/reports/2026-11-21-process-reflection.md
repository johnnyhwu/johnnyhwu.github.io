# Did the SEO process move traffic? (2026-11-21)

Written at the author's request after the Is Bash re-publish. Property `sc-domain:datasciocean.com`,
tool `compare_search_periods` (gsc MCP), windows 2026-10-23..2026-11-18 vs 2026-09-26..2026-10-22
(28 days each; the process started 2026-10-23). A short window: the 90-day `site` row on 2026-11-23
is the proper measurement.

## Numbers

| | Before | After |
|---|---|---|
| Taiwan clicks | 333 | 346 (+3.9%) |
| Taiwan impressions | | +16.1% |
| Taiwan CTR | 2.21% | 1.98% |
| Taiwan position | 6.2 | 6.2 |
| US clicks | 22 | 50 |

- Largest page gains are old evergreen pages no SEO action touched: en `beautify-terminal-on-macos`
  +32 clicks, `pytorch-apple-silicon-m1-gpu` +11, `sag` +12, en `memgpt` +9.
- New posts add about 5 to 9 clicks each in their first weeks (`evoontology` 9, `skillzip` 8,
  `subagent-fold` 6, `procedural-graphs` 6); the re-published `wikiskill` +8.
- Drops: `jev-overview` -19, `dream-rsi` -8, `mem0` -6, `dropout` -6.

## Reading (inference, labelled)

No site-level lift can be attributed to the process. Reasons:

1. The levers pulled are small by our own estimate (`plan.md`: A6 titles +3-6% at best).
2. The largest bet, A5 (extend DPO, the biggest Taiwan query we hold), has waited on the author's call
   since 2026-10-23.
3. Almost every new post is on a paper nobody searches for yet, so the pre-publish check nearly always
   concluded "no demand, lead with the name": correct, but it changed little.
4. Follow-ups recorded results and ended "do not tweak"; link-back candidates were listed in 12 PRs
   and none was added.
5. The insight that traffic comes from evergreen concept and how-to pages did not reach what the site
   writes next.

## Changes made (this PR)

- The results-page check no longer needs Chrome: `seo/scripts/suggest.py` (Google autocomplete, no
  key) is the default, run on the paper name **and the concept it depends on**.
- Concept demand found that way goes to `plan.md` G1 (concept-page candidates).
- Link-back candidates go to `plan.md` G2 and ship monthly in one batch PR.
- Each monthly `site` row ends with one or two yes/no decisions for the author, not only a report.

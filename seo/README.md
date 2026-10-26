# SEO workspace

Research notes and the action plan for DataSci Ocean's organic search traffic. Written
by Claude from Google Search Console (GSC) data; edited by whoever acts on it.

This directory is **not published**: it sits outside `content/`, `static/` and `assets/`,
so Hugo ignores it.

## Layout: read only what the task needs

The procedure is in the `seo` skill (`.claude/skills/seo/`); this directory holds state.

| Task | Read |
|---|---|
| Publishing or fixing a post | `followups.md` only (the skill says the rest) |
| Something is due (the session hook lists it) | `followups.md`, then the skill's recipe for that kind |
| Site analysis, choosing what to work on | `plan.md`, then the newest `reports/` file |
| Judging a change made earlier | `log.md` (what changed, when), then the matching report |

| Path | What it is |
|---|---|
| `followups.md` | Dated queue of checks to run later (`Open`) and their results (`Done`). The session hook reads it. |
| `plan.md` | The live action list: evidence, status, how to tell if it worked. |
| `reports/YYYY-MM-DD-<topic>.md` | Dated, immutable analysis snapshots. Never edit an old report; write a new one. |
| `log.md` | One line per change made *because of* this plan. Needed to attribute later movement. |
| `raw/` | Bulk exports. Gitignored: large and regenerable. |

## Rules for whoever edits this directory

1. Do not re-derive findings already recorded here. Re-run analyses only against a **new date window**
   and save the result as a new report.
2. When a `plan.md` item changes status, update it in place and add a line to `log.md`.
3. When a `followups.md` row is done, move it to `Done` with a one-line result; add the next row for
   recurring kinds.
4. Say which window, property and tool a conclusion came from. Mark inferences as inferences.
5. This repository is public. Traffic numbers are fine; credentials, tokens and personal data are not.

## Data source

GSC through the `gsc` MCP server (configured in `/.mcp.json`, OAuth, read-oriented use only;
`GSC_ALLOW_DESTRUCTIVE` stays unset).

- Property used for analysis: `sc-domain:datasciocean.com` (whole site).
  `https://datasciocean.com/` is the URL-prefix twin, used for URL Inspection.
- Raw exports are **not** committed (large, and regenerable). Reports carry the numbers
  that matter.

## Known limits of GSC (so nobody over-reads a report)

- Query-level rows cover only part of the impressions (about 40% in the first report);
  Google withholds anonymized queries. Page- and country-level totals are complete.
- `#fragment` rows are "jump to section" sitelinks counted separately; exclude them from CTR work.
- `site:...` queries are the owner checking indexing, not demand.
- The URL Inspection API does not return the Google-selected canonical or an "indexed pages"
  total, and there is no tool here to request indexing.
- GSC cannot show: backlinks, demand for topics with no page yet, on-site behaviour,
  Core Web Vitals.

# Change log

One line per change made because of `plan.md`. Newest first. Format:
`YYYY-MM-DD | plan item | what changed | URLs/files | PR`

2026-10-26 | publish | Re-published `paper-intro/llm-as-a-verifier` from a new plan (new zh and en title and description, restructured body, regenerated cover); date unchanged, lastmod moved | content/posts/paper-intro/llm-as-a-verifier/, plans/llm-as-a-verifier/ | this PR
2026-10-26 | process | SEO workflow: `seo` skill, `followups.md` queue + SessionStart hook, short rules in CLAUDE.md and hugo-paper-post; en title cap 52 in verify_post.py and hugo-conventions; seo/ and .mcp.json now committed | .claude/skills/seo/, .claude/settings.json, CLAUDE.md, .github/workflows/hugo.yaml, .gitignore | this PR
2026-10-23 | A8 (into A6) | Shortened en titles + lastmod on 5 more posts (44-50 chars): mem0, fastapi-race-condition, claude-code, sparse-upcycling, mem-rl. Baseline saved in reports/2026-10-23-title-batch-baseline.md | content/posts/{paper-intro/mem0,other/fastapi-race-condition,ai-concept/claude-code,paper-intro/sparse-upcycling,paper-intro/mem-rl}/index.en.md | PR #79, merged 2026-10-23 03:36 UTC; all six new titles confirmed live on the site shortly after. "After" window for the whole batch starts about 2026-10-30. Measure with the A6 batch: aggregate EN CTR vs 0.35% baseline, start "after" about a week after the deploy
2026-10-23 | A6 | Edited en title + lastmod of what-is-computer-architecture (73 -> 46 chars); audited all 142 en titles | content/posts/other/what-is-computer-architecture/index.en.md | PR #77, merged 2026-10-23 03:21 UTC (merge commit 1bdccfa); deploy run started 03:22 UTC. Measure: 28 days after it is live and recrawled (about 2026-11-21 to 2026-12-18) vs the 28 days before (2026-09-25 to 2026-10-22). Google can take days to show the new title, so start the window a few days late if needed
2026-10-23 | A2 | Reviewed live Taiwan SERPs (dpo, dropout, 計算機結構, computer architecture + 2 long-tail); no site change. Added A5-A7 | none | n/a
2026-10-23 | A1 | Audited live hreflang/canonical for all 393 sitemap URLs: no defect, no site change | none | n/a
2026-10-23 | setup | Connected GSC via MCP (`.mcp.json`) and created `seo/` with baseline report and plan | `.mcp.json`, `seo/` | not yet pushed

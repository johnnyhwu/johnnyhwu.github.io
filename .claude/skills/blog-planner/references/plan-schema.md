# The plan JSON (schema `post-plan/1`)

One file per language: `plans/<slug>/post.zh.json` (the source of truth) and `post.en.json` (a native-voice twin
with the same ids). The Planner writes them, `scripts/validate_plan.py` checks them, `scripts/views.py` and
`scripts/brief.py` make the files Reviewers and the author read, and `hugo-publisher/scripts/render_post.py` turns
them into Hugo markdown. `tests/fixtures/mini/post.zh.json` is a small, valid example of everything below.

The plan is the bridge between `article.md` (complete and correct, not built for reading) and the post (built for
reading, nothing lost). Three ideas carry it:

- **Ledger**: every piece of knowledge in `article.md` gets an id and a place to land, so "nothing was lost" can
  be checked by a script instead of promised.
- **Blocks**: the post is a list of small blocks (a paragraph, a table, a figure...), each citing the ledger items
  it carries. A block either carries source knowledge (`origin: source`) or is something the Planner added to help
  the reader (`origin: editorial`).
- **Intent, not markup**: blocks say *what a thing is for* (a warning, a fold, a comparison); the Publisher decides
  how it looks (`hugo-publisher/references/visual-mapping.md`).

## Top level

| Key | Meaning |
|---|---|
| `schema` | `"post-plan/1"` |
| `source` | `article` (path to article.md), `manifest` (path to image-manifest.json), `root` (what the manifest's `file` paths are relative to, normally `AI-Research`). Paths are relative to the repo root |
| `meta` | the post's identity and promise (below) |
| `outline` | the section tree |
| `glossary` | terms the reader must meet defined before they are used |
| `ledger` | one entry per piece of knowledge in `article.md` (zh plan only) |
| `blocks` | the post, in blocks |
| `decisions` | everything the author should know was moved, folded, reworded or dropped |

## `meta`

`section` (one of paper-intro, ai-concept, python-tutorial, other), `slug`, `tags` (the site vocabulary in
`hugo-publisher/references/hugo-conventions.md`), `title`, `description`, `title_alts` (zh only; the candidates
you considered), `reader{persona, promise, assumes[]}` (`assumes` lists extra terms this post does not explain, on
top of the site-wide list in `planner-guide.md`), `takeaways[{id, text, memory_hook}]` (aim for 3, 2 to 5 allowed),
`hook{kind: tension|scenario|question, text}`, `running_example{id, desc}` (optional), `cover_brief{metaphor,
labels[{text, ledger}]}` (every label tied to a ledger item), `seo{queries[], notes}` (optional; from phase P1),
`date` (optional; a rebuild keeps the live post's date anyway).

Length targets, warned by the validator: zh title 10 to 55 characters and description 40 to 180; en title 30 to 52
(the searchable name inside the first 52) and description 120 to 170.

## `outline`

A tree of `{id, title, role, goal, serves[], recap, children[]}`. `role` is one of `hook`, `context`, `mechanism`,
`evidence`, `caveat`, `takeaway`, `deep-dive`. `goal` is what the reader can do or say after the section.
`serves` lists takeaway ids. Depth 1 renders as H2, depth 2 as H3, depth 3 as H4 (no deeper). **Titles carry no
numbers**: the theme numbers headings. A section's heading is generated from the outline; it is not a block.

## `glossary`

`{term, defined_in, first_used_in?}`. `defined_in` is a block id. The validator fails if the term shows up in an
earlier block than its definition. Terms on the reader's "no need to explain" list are exempt.

## `ledger` (zh plan)

`{id, kind, src{lines:[a,b]}, gist, layer, section, dest[]}`.

- `kind`: claim, number, caveat, inference (the Writer's "我的推測" and the like), definition, table, figure,
  formula, example, or `nav` (a signposting sentence such as 「接下來看實驗」, which carries no knowledge).
- `src.lines`: 1-based inclusive lines of `article.md` (above the `figure-map` block). Every line that is not a
  heading, a rule, a fence marker, a table separator or an image/caption line must be covered by some item, or the
  validator names it.
- `layer`: `main` (the reading line), `support` (inline detail that backs the main line), `fold` (collapsed block,
  the reader clicks to open), `appendix` (a deep-dive section after the conclusion). `none` is allowed only for `nav`.
- `section`: the outline id it lands in (required at the skeleton stage, so the author can see the placement).
- `dest`: block ids carrying it, filled at the draft stage. A non-`nav` item with no `dest` needs a `dropped`
  decision.

## `blocks`

Common fields: `id` (unique; `s3.b2` style), `section` (an outline id), `type`, `layer`, `origin`, `ledger[]`
(ledger ids it carries), optional `illustrative: true` and `purpose` (`recap`, `signpost`, `bridge`, `hook`).
A `source` block must cite at least one ledger item. Reading order is the outline order, then the list order.

| `type` | Fields |
|---|---|
| `paragraph` | `text` (markdown; inline math as `$..$`; never a literal `$` for prices) |
| `list` | `items[]` (strings), `ordered` (bool) |
| `table` | `headers[]`, `rows[][]` (cells are inline markdown) |
| `formula` | `latex` (no delimiters), `intuition` (id of the block that explains it in words; must come earlier) |
| `figure` | `manifest_id`, `alt`, `caption` (visible label such as 「圖 2 — ...」 without the source note), `paper_label` (optional), `role` |
| `callout` | `tone` (note, abstract, info, tip, success, question, warning, example, quote), `title`, `text` |
| `fold` | `title`, `tone` (optional), `children[]` (blocks; layer `fold` or `appendix`; no callout or fold inside) |
| `diagram` | `kind` flow (`direction`, `nodes[{id,label}]`, `edges[{from,to,label?}]`), tree or mindmap (`tree{label, children[]}`) |
| `code` | `lang`, `code` |

Rules the validator enforces beyond field presence: a `layer: fold` block must sit inside a fold; a figure block
exists for every image `article.md` references; ledger and block ids cite each other both ways; every number in
`article.md` is still in the post (or its line is waived by a `dropped`/`reworded` decision); an `editorial` block
introduces no number that `article.md` lacks (except single digits, or when marked `illustrative`).

## `decisions`

`{id, kind: moved|folded|reworded|dropped, ledger, why, needs_human}`.

- A `caveat` or `inference` whose layer is `fold` or `appendix` needs a `folded` decision with `needs_human: true`:
  the author must be told a limitation was tucked away.
- A `dropped` decision is allowed only for content the Planner doubts (see `SKILL.md`, rule 4) and must have
  `needs_human: true`.
- `moved` and `reworded` are informational; list the ones the author would want to know about.

## The English plan

Same `meta` (written natively: title, description, hook, takeaways, cover labels), same `outline` ids and depths,
same block ids, order, types, layers, origins, ledger citations, figure ids and fold nesting; no `ledger` array (it
lives in the zh plan). Per block, the multiset of numbers must equal the zh block's. `validate_plan.py <en> --zh
<zh>` checks all of this. See `en-transcreation.md`.

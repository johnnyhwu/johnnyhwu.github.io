# Resolving article.md image references to real files

For every image reference in `<Paper>/article.md`'s body — Markdown syntax
`![alt](img-00N)` where the "src" is a manifest id, not a path — resolve it
to an actual file in `<Paper>/assets/images/` (or the topic's documented
exception path), then decide how wide it should display.

Images may be looked at (the goal is a high-quality post), but the join
itself is text: ids and captions first, pixels only to confirm or to judge.

## Step 1: direct id match (the default)

Look up the id in the article's trailing `figure-map` block to get
`references_manifest_caption` and `agent_match_hint`, then find that same
id directly in `image-manifest.json`. In practice this is nearly always a
clean match — the Writer step reuses the manifest's own ids on purpose so
this join is trivial. If the id and caption line up, you're done with
resolution; no image needs opening to confirm it.

## Step 2: semantic fallback (only if step 1 doesn't cleanly match)

Only if the id has no manifest entry, or the caption in `figure-map`
clearly doesn't match the manifest entry at that id: compare
`references_manifest_caption` / `agent_match_hint` against every manifest
entry's `caption` / `nearby_text` and pick the best textual match.

## Step 3: look at the images that need it — through a subagent

Have an image looked at when:
- the matched manifest entry has `"parser_confidence": "low"`, **or**
- step 2's semantic match was ambiguous (two plausible candidates), **or**
- the id had no confident match at all and you're about to guess, **or**
- you want to judge quality (is the crop cut off? is the text legible at
  the width it will display?).

**Default: delegate.** Image bytes stay in context for the rest of the
session, so send a subagent (`Agent`, `general-purpose`) with the file
paths and a precise question, and work from its text answer. Batch every
image that needs checking into one subagent call. A good prompt:

> Downscale each of these images to 600px wide with `uv run python` (Pillow;
> save the JPEGs in the scratchpad, never in the repo), look at them, and for
> each say whether it shows what its caption says, and flag any crop that is
> cut off, blank, or illegible. Caption per file: ... Answer in one line per
> image; do not paste image content back.

**View one yourself** only when a round trip costs more than it saves (one
image, a quick judgement call) or you need the pixels for your next decision.
Downscale first (below) — don't load a 1500px PNG at full size without a
reason.

```python
from PIL import Image
im = Image.open(src_path).convert("RGB")
w, h = im.size
im.resize((600, int(h * 600 / w))).save(out_path, "JPEG", quality=65, optimize=True)
```

(Run it with `uv run python` from the repo root; Pillow is in this repo's
`pyproject.toml`. Don't `pip install` it.) 600px is enough to confirm
"a results table vs. a line chart vs. a pipeline diagram"; it is not enough
to read exact numbers, so if the check is about specific values, ask for a
higher resolution or a crop of the relevant region.

Note in the PR description which ids were checked and why.

## Image display width: match text size, but never shrink below 75%

The parser crops each figure to its own region, so one post's images come in different pixel widths (say a 1592px
full-text-width crop and 794px single-column crops). The theme stretches every image to the content column
(about 766px), so a narrow crop is enlarged and its text renders bigger than in a wide crop. A `width=` equalises
that, but shrinking too far makes the figure unreadable: SkillZip shipped four 794px crops at 50% (about 380px
rendered, and a 794x258 chart only ~125px tall) and the author had to ask for them to be enlarged.

Read each image's pixel width (`file`, or `Image.open(...).size`) and set, in both language files:

```
width = max(75%, round(image_px_width / widest_image_px_width_in_this_post * 100)%)
```

The widest image gets no `width`; neither does any within about 10% of it. Flat figures (aspect ratio above 2.5)
rarely need shrinking at all. Say each width in the PR so the author can adjust. `verify_post.py` warns on a
narrow image with no `width=` and on any `width=` below 75%. `scripts/article_to_zh.py` applies this rule.

## When a reference truly can't be resolved

Don't silently drop or guess. Leave a visible placeholder in the rendered
body:
```
<!-- UNRESOLVED IMAGE: img-004 -- no confident match; needs manual review -->
```
and list it explicitly in the PR description. A loud gap beats a
confidently-wrong figure shipped to the blog.

## Tables specifically

If a manifest entry carries a `table_markdown` field and the article
references that table as an image, you *may* emit the Markdown table
inline instead of the screenshot — but only if the site renders tables
cleanly (it does; `goldmark.extensions.table = true` in
`config/_default/markup.toml`) and the surrounding prose reads naturally
with a table there instead of an image. When unsure, keep the image — it's
always the safer default.

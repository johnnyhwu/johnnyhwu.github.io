# Resolving figure blocks to real files

Every figure in the post is a `figure` block in the plan JSON (`plans/<slug>/post.*.json`) with a `manifest_id`
(`img-00N`). The Planner (Step 3) decided which figure goes where and wrote its alt and caption;
`validate_plan.py` has already checked that every `manifest_id` exists in `image-manifest.json` and that every
image `article.md` references is used. `render_post.py` then resolves each id to its file (paths in the
manifest are relative to `source.root`, i.e. `AI-Research/`), names it after the paper's own number
(`figure5.png`, `table11.png`), copies it into the bundle and sets `width=` (below).

Images may be looked at (the goal is a high-quality post), but the join itself is text: ids and captions first,
pixels only to confirm or to judge.

## What can still go wrong, and who fixes it

- **An id that does not exist or does not match its caption**: `validate_plan.py` fails. That is a Step 3 fix
  (edit the figure block), never a guess here.
- **A crop that is cut off, blank or illegible**: found by looking (next section). Report it in the PR; a re-crop
  is a Step 1 job in `AI-Research`.

## Look at the images that need it — through a subagent

Have an image looked at when:
- the matched manifest entry has `"parser_confidence": "low"`, **or**
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

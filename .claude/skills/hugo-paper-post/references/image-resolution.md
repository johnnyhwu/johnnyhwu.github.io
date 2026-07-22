# Resolving article.md image references to real files

For every image reference in `<Paper>/article.md`'s body — Markdown syntax
`![alt](img-00N)` where the "src" is a manifest id, not a path — resolve it
to an actual file in `<Paper>/assets/images/` (or the topic's documented
exception path) before ever touching pixels.

## Step 1: direct id match (the default, needs zero vision)

Look up the id in the article's trailing `figure-map` block to get
`references_manifest_caption` and `agent_match_hint`, then find that same
id directly in `image-manifest.json`. In practice this is nearly always a
clean match — the Writer step reuses the manifest's own ids on purpose so
this join is trivial. If the id and caption line up, you're done; move to
the next reference. **Do not open the image file just to be extra sure** —
that defeats the entire point of a separate parsing step.

## Step 2: semantic fallback (only if step 1 doesn't cleanly match)

Only if the id has no manifest entry, or the caption in `figure-map`
clearly doesn't match the manifest entry at that id: compare
`references_manifest_caption` / `agent_match_hint` against every manifest
entry's `caption` / `nearby_text` and pick the best textual match. This is
still text-only — no image bytes involved.

## Step 3: bounded visual spot-check (the *only* place vision is allowed)

Load an image file into context, and only at reduced resolution/size, in
exactly these cases:
- the manifest entry you matched has `"parser_confidence": "low"`, **or**
- step 2's semantic match was ambiguous (two plausible candidates), **or**
- the id had no confident match at all and you're about to guess.

Everything else — every high-confidence direct id match — is trusted
without a look. This keeps vision cost bounded to a small minority of
images on any given post.

### How to do the spot-check cheaply

The source PNGs from the parser are typically large (1000–2000px wide,
hundreds of KB). Don't load them at full size. Downscale first:

```python
from PIL import Image
im = Image.open(src_path).convert("RGB")
w, h = im.size
scale = 600 / w
im.resize((600, int(h * scale))).save(out_path, "JPEG", quality=65, optimize=True)
```

(`pip install pillow` first if it isn't already available in the sandbox.)
Then read only the downscaled copy. This typically cuts a spot-check image
from several hundred KB to under 100 KB with no loss of legibility for the
purpose of "does this picture match the caption/hint" — you're confirming
gestalt (a results table vs. a line chart vs. a pipeline diagram), not
transcribing exact numbers.

For each spot-checked image, confirm the picture's actual content (a
results matrix, a 3-part transfer table, a line chart with N series, etc.)
matches what the caption and `agent_match_hint` describe. Note in the PR
description which ids were spot-checked and why (which of the three
conditions above triggered it).

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
always the safer default, and every table in the SkillOpt post was kept as
an image for exactly this reason (no `table_markdown` field was present in
that manifest at all).

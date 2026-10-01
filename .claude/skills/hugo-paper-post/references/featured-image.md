# Featured images: generate one per post with `canvas-design`

Every post needs a `featuredImage`, and the default way to get one is to **design an original cover with the
`canvas-design` skill** (`.claude/skills/canvas-design/`, vendored verbatim from
`ComposioHQ/awesome-claude-skills`). Don't reuse a paper figure as the cover and don't go looking for stock
photos. The order of preference is in `hugo-conventions.md`, "Featured image"; this file is the how-to for
the generated case.

`canvas-design` is a generic "make art" skill: it asks for a written design philosophy, then an expression of
it on a canvas. Used bare, every post would come out in a different palette and typeface. The house style
below pins down what stays constant across posts, so covers read as one series, and leaves the **metaphor**
free, since that is the part that depends on the paper.

The worked example is `featured-image-example/` (`render.py` + `design-philosophy.md`). It reproduces
`content/posts/paper-intro/resource2skill/featured-image.png` byte for byte. Read it before drawing your
first one, then write a new script for the new topic. It is a skeleton to learn from, not a template to fill
in: copying its picture onto a different topic is exactly the failure to avoid.

## What is fixed (house style)

| | |
|---|---|
| Canvas | Design on a **1200x630 logical** canvas, draw at **3x** and downsample (LANCZOS) to a **1800x945** PNG. Link previews want about 1.9:1, and 1.5x keeps lines crisp on high-DPI screens. |
| Output | `featured-image.png` in the post's page bundle. Never put the philosophy `.md` in the bundle: Hugo would treat it as a content file. |
| Palette | Midnight ink background `(8,15,30)` with a faint radial lift. Ember `(244,176,72)` / `(255,226,170)` for the living, temporal or hero element. Ice blue `(122,176,255)` / `(206,228,255)` for structure that has been resolved. Slate `(98,114,140)` for everything that accompanies but doesn't lead. Brightness, not extra hues, carries emphasis. Don't add a fourth hue. |
| Type | Title and subtitle in the **same family, Instrument Sans**: title about 62px with +1.2px tracking, subtitle about 19px with +0.5px. Annotations in **DM Mono** (10 to 12px). Both are in `canvas-design/canvas-fonts/`. An earlier cover set the title in Instrument Serif and read as cramped and mismatched with the subtitle, so don't mix a serif title back in. |
| Text language | **English only.** One image serves both `index.en.md` and `index.zh-tw.md`, and the bundled fonts have no CJK glyphs. |
| Margins | 60px text margin. Corner registration marks at 34px. Nothing touches or crosses anything else, and nothing leaves the canvas. |
| Layout skeleton | Title block top-left; the drawing owns the rest; a measured-values line at bottom-left. Keep the title block clear of the drawing, and keep the leftmost 40% free of fine detail near the top, since list pages crop covers. |

## What varies (the part you design)

1. **Find the one mechanism.** Read the finished `article.md`, not the PDF, and pick the single idea the post
   spends most of its length on. Express it as a *flow* or a *structure*: a stream converging on a point, a
   tree branching, layers stacking, a loop closing, a gate splitting traffic. Resource2Skill is "a dense
   stream of video distilled through one aperture into a hierarchical skill tree".
2. **Write the design philosophy** (4 to 6 paragraphs, per `canvas-design`) and keep it in the scratchpad.
   Keep it generic, as the skill says, with no mention of the post's topic. Reusing the example's movement
   name is fine only if the picture is genuinely the same kind of thing.
3. **Embed one subtle reference.** The skill's "deduce the subtle reference" step is where the post's real
   finding goes: in Resource2Skill the three non-video sources are drawn as thin dashed lines, so "video beats
   the other three combined" is visible without a caption.
4. **Annotations are data, not decoration.** Column headers, labels and the bottom values line may only use
   terms and numbers that appear in the article (Resource2Skill's 66.8 / 59.4 come from its Table 3, and
   11.9 pp from its intro). If the post has no number worth showing, leave the line out. Never invent a
   statistic, a logo or a venue.
5. **Title text** is the method or concept name as the post uses it, short enough to sit in the top-left block
   (roughly 18 characters at 62px; scale the size down for longer names rather than wrapping, and keep it clear of the first column header of the drawing).

## Workflow

```bash
pip install pillow numpy          # neither is guaranteed in a fresh session
python3 render.py /tmp/<scratch>  # writes featured-image.png and a 1000px preview.jpg
```

1. Draw it. Use supersampled `PIL.ImageDraw` as the example does. It is dependency-light and runs in the
   sandbox.
2. **View `preview.jpg` only** (1000px wide, about 40KB), never the 1800px original. This is the one place the
   site's "don't load images" rule has an exception; see `SKILL.md` hard rule 2. Check, in this order: no
   overlap, nothing past the margins, the title isn't cramped, the one lit element is obvious, and every
   label is legible.
3. Refine instead of adding. If it feels unfinished, make what is already there crisper (spacing, opacity,
   alignment) rather than adding shapes. `canvas-design`'s own final step says the same.
4. Copy the PNG into the bundle as `featured-image.png`, set `featuredImage: "featured-image.png"` in both
   language files, and re-run `verify_post.py`.

## What to say in the PR

Say it is a **generated original illustration**, not a sourced photo and not a figure from the paper. State
what it depicts in a sentence, list every number or label that appears in it with where in the article it
comes from, and give the output size. A human may swap it later; the PR note makes that easy.

## Fallbacks

- **Source ships a real cover** (hand-migrated topics): use it and skip generation; see `hugo-conventions.md`.
- **Pillow cannot be installed** (no network, blocked index): reuse the article's most representative
  figure as `featured-image.png`, as the old convention did, and say in the PR that generation was
  skipped and why. Don't hand-edit a figure.
- **No honest metaphor comes to mind** (a pure how-to with no mechanism): draw the abstract skeleton of the
  steps (a simple pipeline of nodes) rather than decorating. Say so in the PR.

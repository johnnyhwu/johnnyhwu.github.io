# Featured images: generate one per post with `canvas-design`

Every post needs a `featuredImage`, and the default way to get one is to **design an original cover with the
`canvas-design` skill** (`.claude/skills/canvas-design/`, vendored verbatim from
`ComposioHQ/awesome-claude-skills`). Don't reuse a paper figure as the cover and don't go looking for stock
photos. The order of preference is in `hugo-conventions.md`, "Featured image"; this file is the how-to for
the generated case.

`canvas-design` is a generic "make art" skill: it asks for a written design philosophy, then an expression of
it on a canvas. **Each post's cover gets its own visual style.** Two covers that share a palette, typeface and
layout read as one template, which is the opposite of what a cover is for (RRSI's first cover reused
Resource2Skill's look and had to be redone). So only the technical contract
is fixed; the look is not.

Two worked examples live in `featured-image-example/`: `render.py` (Resource2Skill: dark ink background,
ember and ice-blue line work, a stream converging on an aperture) and `render-rrsi.py` (RRSI: light paper
background, flat vermilion and ink, a condensed poster title, a plot). They are deliberately unlike each other.
Read both for mechanics (supersampling, margins, text helpers, preview), then write a new script. Never reuse
either one's palette, type pairing or composition for a third post.

## What is fixed (the technical contract)

| | |
|---|---|
| Canvas | Design on a **1200x630 logical** canvas, draw at **3x** and downsample (LANCZOS) to a **1800x945** PNG. Link previews want about 1.9:1, and 1.5x keeps lines crisp on high-DPI screens. |
| Output | `featured-image.png` in the post's page bundle. Never put the philosophy `.md` in the bundle: Hugo would treat it as a content file. |
| Text language | **English only.** One image serves both `index.en.md` and `index.zh-tw.md`, and the bundled fonts have no CJK glyphs. |
| Legibility | 60px text margin; nothing touches, overlaps or leaves the canvas. The title is readable at list-page thumbnail size, and the leftmost 40% stays calm near the top because list pages crop covers. |
| Fonts | Only the files in `canvas-design/canvas-fonts/`. |
| Honesty | Labels use only terms and numbers the article contains. Anything drawn that is not paper data (a schematic scatter, say) says so on the image ("ILLUSTRATIVE"). |

## What must differ from existing covers (the part you design)

Before drawing, look at the covers already in `content/posts/*/*/featured-image.png` that were generated
(start with `paper-intro/resource2skill` and `paper-intro/rrsi`). Then choose, on purpose, a combination none of
them uses:

- **Palette family.** Dark and luminous, light paper with flat spot colour, blueprint, two-colour risograph,
  warm earth tones, monochrome with one accent... Pick a different background tone *and* a different accent hue
  than the previous generated covers.
- **Type pairing.** A different display face and annotation face (e.g. a condensed grotesque with a mono, a
  serif with a sans, a geometric sans alone). Don't default to the last cover's pair.
- **Composition.** Centred, grid/poster, diagonal, tall column, split panels, a single large object... and a
  different drawing technique (line work, flat shapes, dot fields, halftone, stacked bars).
- **Metaphor.** Drawn from this article's one central mechanism, as below.

## How to find the idea

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
4. **Annotations are data, not decoration.** Headers, labels and any values line may only use
   terms and numbers that appear in the article (Resource2Skill's 66.8 / 59.4 come from its Table 3, and
   11.9 pp from its intro). If the post has no number worth showing, leave the line out. Never invent a
   statistic, a logo or a venue.
5. **Title text** is the method or concept name as the post uses it. Size it to the layout you chose (scale
   down rather than wrap if it is long) and keep it clear of the drawing.

## Workflow

```bash
uv sync                                  # once: creates .venv/ from pyproject.toml (Pillow, numpy)
uv run python render.py <scratch dir>    # writes featured-image.png and a 1000px preview.jpg
```

1. Draw it. Use supersampled `PIL.ImageDraw` as the examples do. It is dependency-light and runs in the
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

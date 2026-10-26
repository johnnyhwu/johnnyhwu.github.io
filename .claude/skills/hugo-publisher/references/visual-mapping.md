# Visual mapping: plan intent -> site markup

The Planner (Step 3) decides *function* ("this is a warning", "this detail can be folded away", "this is a
comparison"); this file is where Step 4 decides *form*. `scripts/render_post.py` implements the table, so a
new visual means a new row here, a new branch there and a golden-file test in `tests/`.

| Block (type, intent) | Markup written | Notes |
|---|---|---|
| `paragraph`, `list` | markdown | inline math as `\( \)` (the plan stores `$..$`); two tight `~` on a line are escaped |
| `callout` + `tone` | `{{< admonition <tone> "Title" >}}` | positional form, the site's convention. Tones: note, abstract, info, tip, success, question, warning, example, quote. Markdown inside is rendered, and it never appears in the TOC |
| `fold` | `{{< fold title=".." tone=".." >}}` | **collapsed by default**, click the title to open, auto-opens for print. `layouts/_shortcodes/fold.html`. Do not use `admonition ... open=false`: the theme turns it back into `open` (`default true`) |
| `table` | pipe table | the theme wraps it so it scrolls sideways on a phone; `\|` in a cell is escaped |
| `formula` | `$$ .. $$` block | its `intuition` block must come first (validated) |
| `figure` | `{{< image src alt caption [width] >}}` | file named after the paper's number; width 75% floor; attribution appended per language |
| `diagram` kind `flow` / `tree` | ```` ```mermaid ```` `graph TD/LR` | site palette `%%{init}%%` first line |
| `diagram` kind `mindmap` | ```` ```mermaid ```` `mindmap` | renders on mermaid@10 (checked with `check_mermaid.js`); branch colours come from mermaid, not the site palette |
| `code` | fenced code | |

## Not used (yet)

`tabs`, `echarts`, `typeit`, `mark`, `style` and the other theme shortcodes exist but no post uses them, so none
are in the plan vocabulary. Add one only after a real post proves it renders cleanly on desktop and phone.

## House rules that apply to the form

- Never two admonitions of the same tone back to back; fold minor ones into prose (see "Don't let admonitions
  become their own repeated pattern" in `hugo-conventions.md`).
- Headings are generated from the plan's outline (H2 for depth 1, H3 for depth 2, H4 for depth 3); the theme numbers
  them, so the outline carries no numbers.
- Never a literal `$` in prose; `render_post.py` refuses to write a file in which one survives.
- After a render, run `check_layout.js` (always), `check_mermaid.js` (if the post has a diagram) and
  `tests/check_fold.js` (if it has a fold). `hugo-build.md` has the commands.

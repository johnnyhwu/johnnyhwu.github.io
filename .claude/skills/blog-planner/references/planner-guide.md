# Planner guide: from a complete note to a post people read

`article.md` is organised the way the *discussion* went and the way a careful note is: setup, then details, then
results, with every caveat attached where it was discussed. A reader does not read like that. This guide is how to
re-shape it. It changes structure and expression; it never changes substance (`SKILL.md`, rule 2).

## 1. The reader

This site's readers are **newcomers to AI**. Explain concepts in detail, with plain words before symbols and a
concrete example for every abstract mechanism. Do **not** explain what a general audience already knows. The
site-wide "no need to explain" list starts as: **AI, LLM, RL, ML, GPU, API**. Everything else is explained on
first use, in the main line, in a sentence or two (a longer explanation goes in a `callout` of tone `info`, or a
fold if it is optional). A post can add terms to its own list in `meta.reader.assumes`. The Reader Reviewer uses the
same profile, so an unexplained term outside the list will be flagged.

Write the persona and promise in `meta.reader`: who this is for, and what they will be able to say or do afterwards.
Every later decision is checked against that promise.

## 2. The four goals, as concrete moves

### Click (title and description)

- **Plain subject first**, in the words a reader would search; the paper's or method's name inside the first 52
  characters of the English title (`hugo-publisher/references/hugo-conventions.md`, "SEO checklist for front
  matter", has the title self-test: cover the post, read only the title; can you say what it is about and why you'd
  care?). Each language gets its own native title and description.
- **The hook is a tension in the reader's terms**: the one claim the post spends most of its length on, a common
  assumption it overturns, a concrete before/after. Do not promise more than the article's own verdict. A question
  works only if the article answers it honestly.
- Write 3 candidates into `title_alts`; the skeleton brief shows them to the author.
- Use the vocabulary readers actually type (from the GSC check) where it reads naturally.

### Stay (the opening)

- The first screen gives a **reason to read before it asks for effort**: a scenario, a tension, or the verdict plus
  what is surprising about it. No definitions, symbols or setup before that reason exists.
- If `article.md` opens with the conclusion, keep it, but dress it: say why it matters, then promise the route.
- One short paragraph that tells the reader the route ("先看…，再看…，最後…") is welcome; a table of contents is not.

### Follow (the mindmap)

- **Pick one through-line** and let every section serve it. Common spines: problem -> idea -> mechanism ->
  evidence -> where it breaks -> what to take away; or claim -> why you might doubt it -> what the evidence says.
- **Thread one running example** (a concrete task, one worked case) through the mechanism sections instead of
  introducing a new toy each time. If the paper has one, use it; otherwise make one and mark it `editorial`.
- **Signposts**: a one-line "where we are" opening each major section, and a one-line recap (`purpose: recap`)
  closing it, in the reader's words. A `mindmap` or `flow` diagram near the top is worth it only when the post has
  a real structure to show (three parts, a loop); do not draw a diagram of a list.
- **Informative headings** that state the point ("整張圖會傷害，局部子圖才有效") rather than label it ("實驗二").
  No numbers (the theme numbers headings). Keep hierarchy contiguous; a section past about five paragraphs or two
  sub-ideas gets H3s.
- **Define a term right before it is first needed**, and list it in `glossary` so the validator can check order.
  When a term returns after a long gap, re-anchor it in a few words.
- **Intuition before formula.** Every `formula` block has an `intuition` block before it: what the formula says
  in words, with the symbols named. The symbol list can follow as a short `list`.

### Keep (the takeaways)

- Decide **three takeaways** in the skeleton (`meta.takeaways`), each in a form a reader could repeat to a
  colleague, and at least one **memory hook**: a named idea, a one-line analogy, or one number.
- Every section declares which takeaway it serves (`outline[].serves`); the validator warns on an orphan.
- The closing section repeats the three in new words and ends with what the reader can do with them (try it, watch
  for it, doubt it). It is not a rerun of the introduction.

## 3. Layers: how to keep every detail and still have a clear line

Give every ledger item a layer.

| Layer | Put here | Rendered as |
|---|---|---|
| `main` | the conclusion, the key mechanism, the numbers that carry the argument, any limitation that changes how a result should be read | the reading line |
| `support` | detail that backs the main line and is cheap to read: an example, a definition, a setup row | inline, kept short |
| `fold` | worth having, not needed to follow: derivations, exact prompt details, alternative readings, a full config table, the "how exactly does X work" asides | a `fold` block the reader can open |
| `appendix` | standalone deep-dives that stand on their own | a `deep-dive` section after the conclusion, with its own heading (folds inside are fine) |

Rules of thumb:

- **When in doubt, `support`, not `fold`.** Folded content is read much less often. Fold what a reader loses
  nothing by skipping.
- **Never fold the answer to the post's own question.** A caveat that qualifies the headline result stays in the
  main line.
- A caveat or inference you fold needs a `folded` decision with `needs_human: true`; the author is told.
- Move, don't summarise: the folded text is the Writer's content (reworded for flow), not a gist of it.
- Put the conclusion **before** the deep-dives, so a reader who stops there still has the whole argument.
- The Writer's "我的推測" paragraphs are substance. Gather related ones into one clearly labelled callout rather than
  scattering blockquotes through the argument, but keep the label and the strength of each.

## 4. Expression: what you may do to the sentences

- Rewrite for flow and plain words; split long paragraphs (one idea each, point first); merge duplicates (one home
  per explanation); add transitions. Keep the Taiwan Traditional Chinese voice, full-width punctuation and the
  Writer's house style (`AI-Research/.claude/skills/blog-writer/references/writing-style.md`).
- Turn a before/after or A/B comparison in prose into a `table`; a loop or a flow in prose into a `diagram`
  (flow / tree / mindmap); a sequence of steps into an ordered `list`.
- Add **analogies and examples** where an abstract mechanism has none; mark them `editorial`. An example with
  invented numbers is `illustrative: true` and reads as an example.
- Do not change what is claimed, how strongly, or any number. "可能" stays "可能"; "論文沒有說" stays.
- Callouts are for a genuine TL;DR, caveat, aside or example; not decoration. Never two of the same tone back to
  back; most posts need only a handful.
- No filler transitions, em-dash glue, "首先…其次…" ladders or tour-guide narration; avoid repeating one sentence
  shape three times.

## 5. Figures and tables

Every image `article.md` references gets a `figure` block (the validator fails otherwise). Place it **right after
the sentence that makes the reader want it**, say what to look at in the text before it, and write alt text that
describes what the figure shows. A figure that carries only data may be shortened to a `table` block if the numbers
are all in the Writer's text; if not, keep the figure. Figure captions use the post's own numbering ("圖 2 —").

## 6. Decisions to record

Record in `decisions[]`: anything folded that is a caveat or inference; anything dropped or reworded because the
source looked doubtful (with the reason); a Writer claim you could not reconcile with another (do not choose
between them from outside knowledge: keep both, flag it). Everything with `needs_human: true` is shown to the author
in the skeleton brief and again in the PR.

## 7. Cover brief

`meta.cover_brief`: the single mechanism the post spends most of its length on, as a flow or a structure (a stream
converging, a loop closing, a gate splitting traffic); the labels it may use, each tied to a ledger item (a term or
number the article contains). Step 4 draws it (`hugo-publisher/references/featured-image.md`).

## 8. Self-check before the first Reviewer

- Cover the body: do the title, description and first paragraph make you want to read on?
- Read only the headings: can you tell the route?
- Is there any symbol, term or acronym used before it is explained?
- Does every formula have its words first? Every abstract mechanism an example?
- Is any limitation that changes the headline hidden in a fold?
- Could the main line be read in one sitting without the folds, and still be true?

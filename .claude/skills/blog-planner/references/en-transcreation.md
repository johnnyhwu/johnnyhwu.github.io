# English plan: write it natively, on the approved structure (phase P5)

When the zh plan has passed review, write `plans/<slug>/post.en.json`. This is **transcreation, not translation**:
the same post, rebuilt in the voice an English-speaking newcomer expects. English pages also earn a large share of
this site's search impressions, and English readers search and skim differently, so a word-for-word rendering of the
Chinese leaves value on the table.

## What stays identical to the zh plan (the validator enforces it)

- `outline`: same ids, depths and order (the titles are yours).
- `blocks`: same ids, order, `type`, `section`, `layer`, `origin`, `ledger` citations, `manifest_id`, `tone`,
  `kind`, fold nesting. No block added, none dropped, none moved.
- **Numbers**: each block carries exactly the numbers its zh twin carries.
- Substance: every claim, its strength and its caveats. A hedge stays a hedge ("probably", "the paper does not
  say"); the Writer's "my guess" paragraphs stay labelled as guesses.

## What you rewrite natively

- **Title, description, hook, takeaways, recaps, headings**: written for an English reader, not carried over. The
  title follows the same self-test as zh (plain subject first, the searchable name inside the first 52 characters,
  a tension in the reader's terms, 52 characters or fewer); the description is about 150 to 160 characters. Use the
  vocabulary the GSC check found (`meta.seo`) where it reads naturally.
- **Sentences**: idiomatic English, point first, short paragraphs; no calques of Chinese structure.
- **Editorial material**: analogies, examples and the running example may be replaced by ones that land better in
  English, as long as they stay `editorial`, assert nothing about the paper that the source does not, and keep any
  invented numbers marked `illustrative` (and, for parity, with the same numbers as the zh block).
- **Terms**: the same beginner profile. Explain on first use anything outside the "no need to explain" list (AI, LLM,
  RL, ML, GPU, API). Keep the paper's own English terms exactly (method and benchmark names).

## What does not change

Math (`$..$` and `latex`), code, figure `manifest_id`, `paper_label`. Figure `alt` and `caption` are rewritten in
English. No Chinese characters anywhere in the English plan (the validator warns).

## Check

```bash
python3 .claude/skills/blog-planner/scripts/validate_plan.py plans/<slug>/post.en.json \
  --zh plans/<slug>/post.zh.json --article <article.md> --manifest <manifest>
```

Then one **fresh Reader** (`reviewer-reader.md`, the same fixed prompt) reads the English title, description and
first screen only (make a short view yourself: the title, description and first three blocks) and answers questions
1 and 2. A "no" on clicking, or a stall in the first screen, is fixed before handing over. The English body does not
get a second full review: the zh plan was reviewed, parity is mechanical, and the validator catches drift in numbers
and structure.

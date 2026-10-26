# Reader Reviewer: the fixed prompt

The Reader Reviewer is a **fresh subagent** (`Agent`, `general-purpose`) that experiences the post as a newcomer
would. It sees **only** the reader view of the post: no `article.md`, no plan JSON, no ledger, no Planner reasoning,
no manifest. That blindness is the point: it cannot hand-wave a gap by "knowing what was meant".

Do not rewrite this prompt per post and do not add hints about what the post is trying to do (that would let the
Planner steer the verdict). Only the three paths and the round number change.

## How to launch

1. Make the view: `python3 .claude/skills/blog-planner/scripts/views.py reader plans/<slug>/post.zh.json
   --out plans/<slug>/work/r<N>-reader-view.md` (round 1, and the final cold read). For rounds 2 to 5 add
   `--delta plans/<slug>/work/delta.json`.
2. Launch (round 1 and the final cold read: a new agent; rounds 2 to 5: `SendMessage` to the same agent, telling it the
   new view path, so it keeps its own memory of what it already told you):

```
You are an independent reviewer. You are NOT the author and you have not seen any source material.

Persona: a curious newcomer to AI. You know what AI, LLM, RL, ML, GPU and API mean in everyday terms. You know
nothing else about this topic. You are reading a blog post to learn something, on your phone, with limited patience.

Read the file at this exact path and review it as that reader: <VIEW_PATH>
Do not read any other file. (This round: <ROUND>. If it says "changed blocks only", the outline shows the whole post
and only the blocks marked CHANGED, with one neighbour each side, need review; judge the changes in context and
re-check only the findings you raised earlier.)

Tags like ⟦s3.b2⟧ are block ids so you can point at text; otherwise ignore them. "[COLLAPSED section ...]" is
content the reader must click to open; judge whether skipping it would lose anything the reader needs.

Judge ONLY reading experience, not whether the claims are true. For round 1 and for a full read, answer in this
order:
1. Before reading the body: from the title and description alone, what do you think this post is about, and would
   you click? (one or two sentences)
2. Read the first screen (about the first 150 words). Do you want to continue, and why or why not?
3. Headings only: write the route you expect, one line per heading. Then say where the body surprised you.
4. Read it all. Note every place you got lost, stalled, or would stop reading.
5. Write the 3 things you would tell a friend you learned, in your own words, and the 1 thing you will remember.

Check for these problems and report each one you find with a quote:
- a term, symbol or acronym used before it is explained (outside the list above), or reintroduced late with no reminder
- an abstract claim or mechanism with no concrete example
- a formula or symbol-heavy passage with no plain-words explanation first
- a section whose role in the whole post you cannot tell, or that does not move the argument
- a wall of text; a point buried at the end of a paragraph; the same idea explained twice
- a table, list or diagram that would be clearer than the prose around it (or one that adds noise)
- an opening that asks for effort before giving a reason to care
- a missing or empty recap or ending; takeaways that do not match what the post spent its time on
- callouts or folds overused or in the wrong place; something collapsed that you needed
- awkward or translated-sounding Chinese, half-width punctuation in Chinese text

Severity:
- blocker: you could not follow, or you would stop reading, or you would walk away with a wrong idea
- major: a real stumble that costs a reader a minute or loses them (an unexplained key term, a missing example)
- minor: polish. Minor findings never block approval.
Do not manufacture nitpicks; if something is fine, say nothing. Report at most 12 findings, most severe first.

Write your result as JSON to <RESULT_PATH> with exactly this shape:
{
  "round": <ROUND>,
  "verdict": "approve" | "revise",
  "title_guess": "...", "click": "yes|maybe|no", "first_screen": "...",
  "route_guess": ["..."], "learned": ["...","...","..."], "remember": "...",
  "findings": [
    {"id": "R<round>-1", "severity": "blocker|major|minor", "category": "term|example|formula|structure|flow|opening|ending|visual|language",
     "block_ids": ["s3.b2"], "quote": "<the exact words>", "problem": "...", "suggestion": "..."}
  ]
}
"verdict" is "approve" only when there is no blocker and no major finding. Later rounds may omit the answers to
questions 1 to 5 (keep "findings" and "verdict"); the final cold read must include all of them.
Reply to me with one line: the verdict and the finding counts by severity.
```

`<RESULT_PATH>` is `plans/<slug>/work/reviews/r<N>-reader.json`.

## What the Planner does with it

Read the JSON, not the agent's chat. Compare `learned` and `remember` with `meta.takeaways`: if they do not match
what the post meant to teach, that is a structural finding even when the reviewer raised no complaint. Handle
findings as in `review-loop.md`.

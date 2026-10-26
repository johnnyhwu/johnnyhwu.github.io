# The review loop (phase P4)

Two independent Reviewers, up to five rounds, and a clear way out if they do not converge. The design goals: the
Reviewers stay clean (no shared context with the Planner), tokens are spent once per piece of text, and a too-strict
Reviewer cannot trap the Planner in a loop.

## Setup, every round

```
plans/<slug>/work/r<N>-reader-view.md      from views.py reader      (round 1 and the final cold read: full)
plans/<slug>/work/r<N>-fidelity-view.md    from views.py fidelity    (round 1: full)
plans/<slug>/work/delta.json               {"round": N, "changed": ["s3.b2", ...], "resolved": ["R1-2", "F1-1"]}
plans/<slug>/work/reviews/r<N>-reader.json, r<N>-fidelity.json       written by the Reviewers
plans/<slug>/work/reviews/r<N>-rebuttals.json                        yours; shown to the author only
```

Run `validate_plan.py` first: a draft that fails the zero-token gate does not go to a Reviewer.

## Round 1: everything, in parallel

Launch both Reviewers in the same message (`reviewer-reader.md`, `reviewer-fidelity.md`), each on its full view.
Read the two result JSONs (not the agents' chat replies).

## Handling findings

For every `blocker` and `major` finding, do exactly one of:

- **Fix** it in the plan. Fidelity findings are always fixes: the source is the authority.
- **Rebut** it, only if the Reviewer is mistaken (misread the source, or asked for something the persona rules
  out). Write the reason in `r<N>-rebuttals.json`. A rebuttal of a blocker or major is an escalation trigger (below).
- **Escalate** it, if fixing would break something else or you cannot tell what is right.

`minor` findings: fix the cheap ones in the same pass; ignore the rest. Minor never blocks.

Edit the plan with small, targeted edits keyed by block id (or a short script), not by rewriting the file. List every
block you touched in `delta.json`, then re-run `validate_plan.py`.

## Rounds 2 to 5: only what changed

Build the delta views with `--delta delta.json`: the outline of the whole post plus each changed block with one
neighbour each side (the fidelity view also shows the verbatim source lines of each shown block). **Resume the same
two Reviewers** with `SendMessage`, giving the new view path: they keep their own memory of what they raised, and
you pay for the full text only once.

Widen the review when a fix is bigger than a sentence:

- you moved, split or merged blocks: send the whole affected section in the delta (list every block in it);
- you touched a block that carries a ledger item: it is in the fidelity delta automatically;
- you changed the outline or the takeaways: restart with a full Reader view (a new round-1 style read).

## Passing

Both result JSONs say `"verdict": "approve"` (no blocker, no major). Then:

**One final full cold read**: a *new* Reader agent (not the resumed one: it has anchored on your earlier drafts)
on the full reader view, answering all five questions. Local fixes can break the flow or duplicate an explanation,
and only a whole-post read sees that. Its blocker and major findings go through the same handling; the final read
counts as a round toward the cap.

## Severity is calibrated, so strictness cannot trap you

Only `blocker` and `major` block approval. Reviewers are told not to manufacture nitpicks and to cap their findings
(12 Reader, 15 Fidelity). If a Reviewer is repeatedly raising polish as `major`, that is a reason to escalate, not to
keep rewriting.

## Escalate to the author instead of looping

Stop and write `plans/<slug>/work/escalation.md`, then tell the author in chat, when **any** of these holds:

1. **Round 5 ended** without approval from both Reviewers (including the final cold read).
2. **The same finding stays open for two consecutive rounds** (same block and category), after you have tried a
   fix.
3. **No progress**: the number of open blockers plus majors is not lower than the previous round's for two rounds
   in a row, or the findings oscillate (a fix for one reintroduces another).
4. **You rebut a blocker or major.**
5. A Reviewer's demand would cross a hard rule (delete a detail, change a claim, invent a number).

Do not wait for round 5 if 2, 3, 4 or 5 already holds.

`escalation.md` is short: the open findings (quote, severity, which Reviewer), what you tried, what you think is
right and why, and two or three concrete options with your recommendation. The author decides; record the decision
(and any accepted open finding) in the plan's `decisions[]`, then continue or finish.

## Efficiency rules

- Reviewers never receive the plan JSON; they read `views.py` output.
- Reviewers write their JSON to disk and reply with one line.
- Do not paste any post text into a prompt; paths only.
- Do not run a round for a change the zero-token validator can judge (a number, a missing id, an undefined term).

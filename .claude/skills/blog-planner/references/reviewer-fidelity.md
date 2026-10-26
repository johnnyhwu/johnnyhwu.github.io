# Fidelity Reviewer: the fixed prompt

The Fidelity Reviewer checks that the readable post still says exactly what `article.md` says. It is a **fresh
subagent** (`Agent`, `general-purpose`), independent of the Reader Reviewer and of the Planner's reasoning. It sees
the **fidelity view**: every block next to the verbatim `article.md` lines of the ledger items it cites, so it does
not need to hold the whole article in mind, plus the Planner's decisions and any ledger item that lands nowhere.

`validate_plan.py` has already checked, with zero tokens, that every line is covered, every number survives and no
editorial block invents one. This reviewer does what a script cannot: **meaning**.

Do not rewrite the prompt per post; only paths and the round number change.

## How to launch

1. `python3 .claude/skills/blog-planner/scripts/views.py fidelity plans/<slug>/post.zh.json --article <article.md>
   --out plans/<slug>/work/r<N>-fidelity-view.md` (add `--delta plans/<slug>/work/delta.json` for rounds 2 to 5).
2. Round 1: a new agent. Rounds 2 to 5: `SendMessage` to the same agent with the new view path.

```
You are an independent fidelity reviewer for a blog post. You are NOT the author.

The post was rewritten from a source note (article.md) to be easier to read. Your only job is to catch places where
the rewrite changed what the source says. You are not judging style or readability.

Read the file at this exact path: <VIEW_PATH>
It lists each block of the post (tagged ⟦id⟧) with the ledger items it cites and, under each, the verbatim source
lines ("| ..."). If it says "changed blocks only", review the blocks marked CHANGED (neighbours are context) and
re-check only the findings you raised earlier. The article itself is at <ARTICLE_PATH>; open it only if a block
needs wider context than the view gives. Do not read any other file (no PDF, no images).

For every block with source lines, compare the block against those lines and look for:
- distortion: a claim, cause, comparison, condition or number that now means something else
- strength change: a hedge dropped or added ("may", "probably", "論文沒有說", "我的推測" turned into fact, or a fact
  turned into a guess); a scope qualifier lost ("on this benchmark", "in this setting")
- merging or splitting that changes meaning: two different claims fused; a condition detached from its claim
- wrong figures: a wrong table/figure caption or a number attached to the wrong thing
- a limitation or inference that was moved to a collapsed section but changes how a main-line result should be read
For every block marked origin=editorial (analogies, examples, recaps, intuition):
- it must assert nothing about the paper that the source does not (no new claim, mechanism, result or number)
- an example with invented numbers must read as an example
- an analogy must not change the meaning of the thing it explains
For the DECISIONS and the "LEDGER ITEMS THAT LAND IN NO BLOCK" lists:
- is each dropped or reworded item justified by genuine doubt about the source, not convenience? Say if not.

Severity:
- blocker: any distortion of a claim, strength or number; an editorial block asserting something unsupported
- major: a qualifier lost or a caveat misplaced in a way a careful reader could misjudge a result
- minor: wording drift that does not change meaning. Minor never blocks approval.
Do not manufacture nitpicks. Report at most 15 findings, most severe first. Quote both the block text and the source.

Write your result as JSON to <RESULT_PATH>:
{
  "round": <ROUND>,
  "verdict": "approve" | "revise",
  "findings": [
    {"id": "F<round>-1", "severity": "blocker|major|minor",
     "category": "distortion|strength|merge|wrong-figure|misplaced-caveat|unsupported-editorial|unjustified-decision",
     "block_ids": ["s3.b3"], "ledger": ["L4"], "block_text": "...", "source_text": "...", "problem": "...", "suggestion": "..."}
  ]
}
"verdict" is "approve" only when there is no blocker and no major finding.
Reply to me with one line: the verdict and the finding counts by severity.
```

`<RESULT_PATH>` is `plans/<slug>/work/reviews/r<N>-fidelity.json`.

## What the Planner does with it

A fidelity finding is a **fix, not a negotiation**: the source is the authority. Restore the source's meaning (you
may keep the new wording if it says the same thing). A rebuttal is allowed only when the Reviewer misread the
source, and then it goes to the author as an escalation, never back to the Reviewer (`review-loop.md`).

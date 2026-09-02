---
# weight: 1
title: "WikiSkill: A Skill Memory That Never Gets Rolled Back"
date: 2026-09-02
lastmod: 2026-09-02
draft: false
description: "WikiSkill adds a wiki layer that never gets rolled back between raw agent traces and skill files, so each skill edit builds on accumulated cross-iteration evidence."
featuredImage: "featured-image.png"

tags: ["Large Language Model", "Agent Memory", "Prompting", "Single-Agent"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## Introduction

If you've ever built an agent-skill auto-evolution system — packaging a domain's operating procedures into a `SKILL.md` that an agent reads and applies — you've probably hit the same wall: every iteration re-crawls the raw execution logs from scratch to figure out why things failed, and whatever was learned in earlier rounds never really sticks. At best it ends up as a "proposal history list" bolted onto the skill's change log, not a knowledge base that anyone actually maintains.

That's exactly the problem this *WikiSkill* paper (arXiv:2608.27454, August 2026, from Google Research and Virginia Tech) sets out to solve: inserting, between "raw execution traces" and "the final skill file," a **persistent knowledge layer that never gets rolled back just because one proposal got rejected** — so every round of skill editing can reason from accumulated evidence instead of starting the analysis from zero each time. The idea itself isn't original — the authors say up front they were inspired by a gist from Andrej Karpathy on the idea of an "LLM wiki" — but this paper turns it into a real, systematic implementation and validates it rigorously across 5 models and 5 tasks.

This article follows the paper's own order: first how the three-layer architecture works, then what the experiments actually prove (and what gaps they leave unproven), and finally a concrete case study showing step by step how one skill gets shaped by this mechanism.

{{< admonition abstract "Key Takeaways (TL;DR)" >}}
1. **A persistent, never-rolled-back middle layer**: WikiSkill inserts a Wiki Layer between raw execution traces and the final skill files. Evidence accumulates across iterations and is never wiped out just because a proposal gets rejected.
2. **The single strongest piece of evidence**: in an ablation on Gemini-3.5-Flash, simply giving the Skill Proposer access to this wiki layer jumps the average score from 48.7% to 63.7% (+15.0 points) — the largest single-variable effect in the whole paper.
3. **The bigger the model, the bigger the payoff from skill evolution**: across the Qwen family, WikiSkill's average gain increases with scale (4B: +12.3 points, 9B: +17.5 points, 27B: +23.9 points) — skill evolution and model scaling turn out to be complementary.
4. **The biggest gap left open**: the paper's central claim — that structured knowledge beats a flat history list — is never directly tested by its own ablation study. That's the weakest link in the whole argument.
{{< /admonition >}}

## The problem this paper is trying to solve

An agent skill is a lightweight way of packaging knowledge: the operating procedures for a specific domain get bundled into a self-contained directory, centered on a `SKILL.md` file that an agent reads and applies at task time — no retraining of model weights required. Hand-writing these skills takes a lot of human effort, so a recent line of research lets agents evolve skills automatically instead: run a batch of training tasks, analyze the successful and failed trajectories, and edit the skill accordingly, repeated over and over.

The three representative methods the paper compares against — EvoSkill, Trace2Skill, and [SkillOpt](../skillopt/) — all follow the same loop: run tasks, analyze traces, edit the skill, validate, and decide whether to keep the edit. They also each carry some form of "memory" — EvoSkill, for instance, keeps a running list of proposals and evaluation scores that never gets cleared across iterations. But the paper points out a shared weakness: all of that memory is just a **flat list** riding along on top of the skill's own edit history, never maintained as an independent, continuously curated, ever-thickening knowledge representation in its own right.

## Method: how the three-layer architecture works

WikiSkill splits an agent's workspace into three layers:

| Layer | Properties | Contents |
|---|---|---|
| Skill Layer (`skills/`) | Reversible, conditionally updated | The actual skill files injected into the prompt |
| Wiki Layer (`wiki/`) | Continuously accumulating, never reset | Curated, structured knowledge |
| Raw Layer (`raw/`) | Permanently kept, append-only | Raw execution traces |

The Wiki Layer is the new middle layer this paper introduces, and it holds three kinds of files: a set of markdown files under `patterns/`, each one covering a specific failure mode or successful strategy; `logs.md`, a chronological record of what happened in each iteration; and `skill-impact.md`, which records the content of every proposal, its validation score, and whether it was accepted or rejected. Each Skill Layer folder, in turn, has two files: `SKILL.md`, the skill content itself, and `PURPOSE.md`, which records which wiki patterns inspired this skill and why it was edited.

The three-layer split is just the static structure. What actually drives it are four roles that interact in sequence, once per iteration:

1. **Inference Agent** runs the training tasks using the previous round's skill set, and writes the results into the Raw Layer (append-only — it cannot access the wiki at all).
2. **Wiki Maintainer** makes a single LLM call, samples a small number of traces, does root-cause analysis, and updates the wiki's patterns, index, and log.
3. **Skill Proposer** runs as a multi-turn ReAct agent (alternating reasoning and tool calls), sequentially reading the wiki index, `skill-impact.md`, relevant patterns, and raw traces, and proposes either creating or editing a single skill (one change per round).
4. **Gating & Rollback** tests the candidate skill set on a validation split — if the score improves, the edit is kept; if not, the entire skill set is rolled back to the previous version. Either way, the proposal content, diff, and score get written into `skill-impact.md` before moving to the next round.

{{< image src="figure2.png" alt="Diagram of the WikiSkill framework: an immutable raw execution-trace layer at the bottom, a continuously accumulating Wiki knowledge layer in the middle, and a Skill layer at the top that actually gets injected into the prompt, with four roles interacting in sequence across one iteration." caption="Figure 2 — Overview of the WikiSkill framework: the Raw / Wiki / Skill three-layer architecture, and how the four roles interact within one iteration. (Source: original paper, Figure 2.)" >}}

There's a key design choice buried here: **the Inference Agent has zero access to the wiki while running training tasks**. The later ablation study confirms this restriction is necessary — letting it peek at the wiki actually makes the final skill quality worse, for reasons explained further down.

### The easiest part of this design to get wrong

The part of a layered design like this that's easiest to misunderstand is exactly which layer can delete, which can edit, and which can only append. The actual rules aren't quite what intuition suggests:

- **The Skill Layer has no "delete" operation at all.** The Skill Proposer's output format only supports three things: create new, edit existing, or take no action — never delete. What looks like a "deletion" is actually a full version rollback triggered by Gating & Rollback: when a new proposal fails validation, the system reverts the *entire* skill set to the previous round's version, rather than deleting any single skill.
- **The Wiki Layer isn't append-only either.** The Wiki Maintainer has three ways to modify an existing pattern page: append to the end of the file, find-and-replace specific text, or insert text after a given anchor. So existing content absolutely can be corrected or overwritten. "Never reset" refers to the wiki's overall state never rolling back just because a proposal was rejected — it doesn't mean "each file can only grow, never change."
- **The Raw Layer's read-only status is about how it's used, not what happens to it.** This layer gains a new batch of execution records every iteration and keeps growing continuously; "immutable" means records already written are never modified or overwritten. The Wiki Maintainer and Skill Proposer do only read from it, but the layer itself is constantly expanding underneath them.

Worth adding a gap the paper itself admits to in its Limitations section: the wiki currently has no automatic cleanup mechanism, so it keeps growing as iterations pile up — the paper explicitly flags this as a problem left for future work.

### How the Wiki Maintainer is actually prompted

The paper's appendix provides the Wiki Maintainer's full system prompt. Its role definition requires deep root-cause analysis of execution traces rather than surface-level symptom matching; its input is this round's raw traces plus the current wiki context; and its output is a fixed JSON schema containing new patterns to create, edits to existing patterns, the full updated content of the index (not a diff), and a summary of this round's iteration.

One instruction, flagged as CRITICAL, is particularly worth noting: the entries in `index.md` are the single most important part of the wiki, because they determine whether the inference agent ever bothers to read the full pattern page at all — the descriptions must be specific enough that an agent can judge relevance without opening the full page, while still covering the problem, root cause, and solution. That reveals an engineering detail worth internalizing: no matter how well a pattern page is written, if the index summary is weak, downstream agents simply never click through to read it — which is why index quality gets elevated to the same importance as the pattern content itself.

### Why training runs the full dataset every round, but analysis only reads a small slice closely

The `batch size` parameter defined in the paper's appendix is easy to get confused about — what exactly does it control? It has to be split into two separate layers to make sense of it: the Inference Agent always runs a rollout over the *entire* training set every iteration, regardless of batch size; what batch size actually controls is how many separate passes the "analyze and propose" step gets split into. If the batch size is smaller than the training set (the approach used by EvoSkill and SkillOpt), the training set gets sliced into multiple mini-batches, each triggering its own full analysis pass. WikiSkill instead sets batch size equal to the full training set size, so each iteration does exactly one analysis pass.

This is effectively splitting "breadth" and "depth" into two independent knobs. Breadth comes from the full-batch rollout plus the complete pass/fail summary of every task that the Skill Proposer gets up front, which avoids misjudging how common a given error pattern is from only seeing part of the data. Depth is controlled through bounded sampling to keep costs in check — the Wiki Maintainer samples a fixed maximum of 8 traces per round (5 failures, 3 successes), each truncated to 15,000 characters, while the Skill Proposer isn't bound by that cap at all: it can dynamically pick which traces from the entire training set to read closely, with the only rule being it must read at least 4. Both mechanisms exist to work around context-window limits — they just solve it differently: one is a single call with fixed sampling, the other is a multi-turn ReAct loop with dynamic, on-demand reading.

## Experimental results: consistently ahead, but by wildly different margins

The experiments span 5 models (Qwen-3.5-4B, Qwen-3.5-9B, Qwen-3.6-27B, Gemma-4-31B, Gemini-3.5-Flash) crossed with 5 tasks (math reasoning LiveMath, web-search-dependent factual QA SealQA, spreadsheet manipulation SpreadSheet, long-document QA OfficeQA, and the embodied-interaction task ALFWorld), with each combination averaged over three full evolution runs.

{{< image src="figure1.png" alt="Bar chart showing five models' average accuracy under no skill, EvoSkill, SkillOpt, and WikiSkill evolution methods; WikiSkill leads across the board, and its lead widens as models get bigger." caption="Figure 1 — Average performance across five models: WikiSkill leads on every model, with its advantage growing as model capability increases. (Source: original paper, Figure 1.)" >}}

The headline number: WikiSkill has the highest average score across all 5 models, beating each model's best-performing competitor by 3.3, 5.1, 10.0, 5.8, and 12.0 percentage points respectively (in order: 4B, 9B, 27B, Gemma-4-31B, Gemini-3.5-Flash). A few standout single points: Gemini-3.5-Flash goes from 33.0% to 72.6% on LiveMath, and from 50.5% to 76.6% on SpreadSheet; Qwen-3.6-27B goes from 52.8% to 77.6% on ALFWorld.

{{< image src="table1.png" alt="Table comparing accuracy on five tasks across five models, each under no skill and under EvoSkill, Trace2Skill, SkillOpt, and WikiSkill." caption="Table 1 — Main results comparison across models and tasks. WikiSkill has the highest average score in every model's block. (Source: original paper, Table 1.)" >}}

What the paper particularly emphasizes is **stability**, not just peak performance. Other methods regress noticeably in some settings — not just gaining less, but actually going backward. EvoSkill, for example, produces a huge gain for Qwen-3.5-9B on LiveMath (28.2%→58.1%) while making Gemma-4-31B *worse* on the exact same task (33.9%→29.8%); SkillOpt makes Gemini-3.5-Flash worse on SealQA (29.4%→28.2%). WikiSkill never shows this kind of inconsistent, hit-or-miss behavior.

One data-cleaning detail worth noting: Gemini-3.5-Flash scores exactly 85.9% on ALFWorld under *every* method, including no-skill. That's because it already hit 100% on the validation set before evolution even started, triggering early termination — the evolution loop never actually ran. This isn't WikiSkill failing on this task; the task was simply already too easy for this model.

### The bigger the model, the bigger the payoff from skill evolution

The paper describes this finding as skill evolution and model scaling being **complementary**. It shows up most cleanly within the Qwen family, where parameter count is the only thing that varies (making it a clean comparison): WikiSkill's average gain increases with scale — +12.3 points at 4B, +17.5 points at 9B, +23.9 points at 27B. This is especially pronounced on SpreadSheet, where the three models gain +6.5, +9.3, and +40.9 points respectively.

A more intuitive way to put it: a small model with a good skill can beat a large model with no skill at all. Qwen-3.5-9B with WikiSkill reaches an average accuracy of 47.4%, ahead of Qwen-3.6-27B's 39.4% with no skill whatsoever. The paper's interpretation: model capability and evolved procedural knowledge are complementary sources of performance — stronger models are better at developing and executing more sophisticated skills and so benefit more from them, while an effective skill can let a smaller model close the capability gap with a larger one.

That said, the benefit isn't uniform across datasets either. Qwen-3.6-27B gains only 11.6 points on OfficeQA (a long-document retrieval task), compared to +40.9 points on SpreadSheet. The paper doesn't dig into why this particular model shows such an internal gap, but it does make a related observation about tasks like OfficeQA: larger models can effectively use an evolved search procedure to navigate a long document, while smaller models (like Qwen-3.5-4B) can't execute this kind of multi-step search procedure at all and fall back to default reading behavior instead, causing a slight regression. This ties directly into the cross-model transfer results in the next section.

### Cross-model skill transfer: whether it transfers depends on what's actually packed inside the skill

This set of experiments asks: can a skill evolved by model A be handed directly to model B and just work?

{{< image src="table2.png" alt="Table comparing accuracy when using no skill versus skills evolved by Qwen-3.5-4B, Qwen-3.6-27B, and Gemini-3.5-Flash as source models, each applied to various inference models." caption="Table 2 — Cross-model skill transfer results. Shaded rows indicate the model evolving and using its own skill. (Source: original paper, Table 2.)" >}}

Three findings are worth pulling apart:

| Finding | Concrete example |
|---|---|
| A transferred skill is often *better* than a self-evolved one | Qwen-3.6-27B's skill, handed to Qwen-3.5-9B on SpreadSheet, scores 50.5% — higher than the 33.6% Qwen-3.5-9B gets with its own self-evolved skill |
| Whether transfer works depends on whether the skill encodes a general procedure or a model-specific workaround | LiveMath skills transfer especially well (33.0%→67-74%); but on SpreadSheet, Qwen-3.5-4B's skill given to Gemini-3.5-Flash drops the score from 50.5% to 18.1%, while the same scenario with Qwen-3.6-27B's skill instead lifts it to 63.4% |
| Even with the same source skill, different receiving models "digest" it differently | Qwen-3.5-4B's own self-evolved skill actually makes it worse when applied to itself (30.2%→28.5%), yet the exact same skill improves Qwen-3.6-27B (42.1%→52.9%) |

The paper does provide a root-cause analysis for the second finding's negative-transfer case: skills evolved by smaller models tend to be packed with low-level workarounds (single-line Python commands, string-conversion rules) that help the small model avoid execution failures, but end up constraining a stronger model that could otherwise use a more complete, end-to-end script. The fragmented diagnostic steps also generate redundant tool calls, which can drain a stronger model's interaction budget before the task even completes.

What the paper does **not** explain is an even more counterintuitive phenomenon: the skill evolved by the smaller Qwen-3.5-4B, when handed to Gemma-4-31B, actually improves it on both LiveMath and ALFWorld (up to 73.1% and 66.9% respectively) — the paper only reports these numbers without any further root-cause analysis. Overall, the paper offers a lot of descriptive observations about which transfer directions work and which don't, but the only case that gets an actual causal explanation is SpreadSheet, and even that is just qualitative error analysis, not systematic verification.

Putting these three findings together, the paper makes a framing argument worth remembering: self-evolution actually mixes two genuinely distinct capabilities — "discovering useful procedural knowledge from experience" and "effectively executing that knowledge at inference time" — and these should be treated as separate, independent capabilities, not the same thing. This framing is more broadly useful than the paper itself: when evaluating any self-improving agent system, it's worth first asking whether the system got better because it learned something better, or because it simply got better at following instructions.

## Ablation study: where exactly does the wiki do the work

This is the most cleanly designed experiment in the whole paper — run on a single model, Gemini-3.5-Flash, independently toggling whether the Inference Agent and the Skill Proposer each have wiki access.

{{< image src="table3.png" alt="Table showing average scores across five benchmarks under four ablation settings, varying whether the Inference Agent and the Skill Proposer have wiki access." caption="Table 3 — Ablation study results: independently removing wiki access from the Inference Agent and the Skill Proposer, and observing the change in average score. (Source: original paper, Table 3.)" >}}

One thing to note: whenever the Skill Proposer has no wiki access, the Wiki Maintainer role is removed entirely too — there's no point maintaining a wiki nobody reads. Below are the four ablation settings, plus the no-skill-evolution baseline, for five numbers total:

| Inference Agent has Wiki? | Skill Proposer has Wiki? | Average score | Note |
|---|---|---|---|
| — | — | 40.4% | No-skill baseline |
| Yes | No | 45.3% | Wiki Maintainer removed |
| No | No | 48.7% | Wiki Maintainer removed |
| Yes | Yes | 60.9% | Full configuration |
| No | Yes | 63.7% | **WikiSkill's default configuration** |

Two conclusions stand out clearly. First, giving the Skill Proposer access to the persistent wiki has a very significant effect: holding the Inference Agent's wiki access off, simply turning on the Skill Proposer's wiki access lifts the average score from 48.7% to 63.7% — a full +15.0 percentage points, the single largest effect from any one variable in the entire paper. Breaking it down, LiveMath goes from 51.3% to 72.6%, and SpreadSheet from 49.9% to 76.6%. The paper's explanation: without knowledge accumulated across iterations, the Skill Proposer struggles to handle complex failure patterns that only converge after multiple rounds.

Second, letting the Inference Agent also access the wiki during training actually makes the final skill quality *worse*: with the Skill Proposer's wiki access already on, if the Inference Agent is also allowed to see the wiki during training, the average score drops from 63.7% to 60.9%, with LiveMath dropping the most (72.6%→64.8%). The paper's explanation is explicitly flagged as a hypothesis, not something it verified further: when the Inference Agent can see both the skill and the wiki during training, it may end up finding answers directly from the wiki instead of solving tasks using the skill itself — which distorts the resulting training traces. The agent performs well not because the skill is good, but because the wiki bailed it out, and that makes the training signal the Skill Proposer receives unrepresentative. This is exactly why the architecture deliberately forbids the Inference Agent from seeing the wiki during training.

### What this paper actually defines as the problem — and what the ablation study doesn't prove

On the surface, EvoSkill also maintains a proposal history that never gets cleared across iterations, so what does WikiSkill actually add on top of that? The answer isn't "whether there's memory" — it's **the form that memory takes**:

| | EvoSkill's history list | WikiSkill's wiki |
|---|---|---|
| Storage form | A flat list: individual entries of proposal content, validation score, accept/reject | Structured, topic-organized knowledge pages, each covering one specific failure mode or successful strategy |
| Dedicated curation step? | None — the proposer reads the history list plus this round's raw trace and digests it on the fly | Yes — a dedicated Wiki Maintainer whose job is root-cause analysis, distilling raw traces into existing pattern pages |
| How evidence accumulates | Each failure case largely exists independently | The same pattern page keeps accumulating evidence across iterations |
| Can relevant knowledge be looked up? | No indexing mechanism — the entire history has to be read from scratch | Yes — an `index.md` with a one-line summary per pattern (problem, root cause, solution), letting the proposer quickly judge relevance |

Boiled down to one sentence: knowledge needs to be actively curated, digested, and built up as accumulating evidence — not just passively stacked in chronological order.

{{< admonition warning "The biggest gap the ablation study leaves open" >}}
The "no wiki" configuration in Table 3 removes the Wiki Maintainer entirely — it tests "having structured knowledge" against "having no cross-iteration knowledge at all." It never sets up a control comparing "a structured wiki" directly against "a flat history list, like EvoSkill's." In other words, Table 3 proves "structured knowledge > no knowledge" (+15%), but it never directly proves the paper's actual central claim — that "structured knowledge > flat-list knowledge." Table 1 does compare overall scores against EvoSkill, but that comparison confounds a second variable: WikiSkill's Skill Proposer is a multi-turn ReAct agent that can dynamically explore for 10 to 20 rounds, a mechanism EvoSkill doesn't have — so it's impossible to cleanly attribute the difference to "how structured the wiki is" alone. This is the single biggest gap in the paper's argument.
{{< /admonition >}}

## Case study: how one skill gets shaped by the wiki, step by step

This case study gives a concrete look at what the "backtracking mechanism" described above actually looks like in practice — the scenario is Qwen-3.6-27B on ALFWorld, walking through the full process of evolving a skill called `break-repetition-loop`.

{{< image src="figure3.png" alt="Timeline diagram: at Iteration 0 the Wiki Maintainer creates a pattern page and the Skill Proposer's proposal is rejected; at Iteration 1 a more focused new proposal is accepted based on the rejection record; new evidence keeps accumulating into the same pattern page over subsequent rounds, and the skill is edited at Iteration 4 based on that evidence." caption="Figure 3 — Case study of wiki-guided skill evolution (ALFWorld, Qwen-3.6-27B). (Source: original paper, Figure 3.)" >}}

At Iteration 0, the Wiki Maintainer creates a pattern page, `take-examine-move-loop.md`, describing an agent that picks up an item, examines it, puts it back, and repeats this loop indefinitely — backed by evidence from two training samples. In the same round, the Skill Proposer proposes creating a new skill called `goal-directed-action`, but it scores 0.72 on validation, doesn't beat the baseline, and gets rejected — `skill-impact.md` fully records this diff and its rejection.

At Iteration 1, the Wiki Maintainer finds the same error recurring, this time with a new variant, and appends the new evidence to the existing pattern page. The Skill Proposer, having now read the Iteration 0 rejection record, instead proposes a new, more specific skill focused on this exact action pattern — `break-repetition-loop` — which scores 0.78 and is accepted. Across Iterations 2-3 (simplified and not expanded in the paper), the Wiki Maintainer creates another new pattern, `multi-operation-loop.md`, describing an agent that repeats operations on the same object without ever checking whether the task is already complete. By Iteration 4, the Skill Proposer reads this new evidence and proposes an edit (not a rebuild) of `break-repetition-loop`, which is accepted again.

The final skill's `PURPOSE.md` sums up its entire history in a single line: "Created as break-repetition-loop. The prior attempt, goal-directed-action, was rejected for being too abstract. This version is leaner and uses a concrete action pattern." No need to go back and re-crawl the raw traces to guess why — that one line tells you exactly why this version of the skill looks the way it does. And the rule that got added at Iteration 4 — "only ever perform each operation type once" — was only possible because the corresponding pattern page kept accumulating cross-iteration evidence. This is a concrete instance of exactly the "+15 points from giving the Skill Proposer wiki access" effect from the ablation study above.

## Engineering cost: fewer calls doesn't mean lower total cost

This section counts "how many LLM API calls the analyze-and-propose step itself makes per iteration," excluding the calls the Inference Agent itself makes to run training tasks.

{{< image src="table7.png" alt="Table listing the optimizer API call-count formula and complexity class for WikiSkill, EvoSkill, SkillOpt, and Trace2Skill, per evolution iteration." caption="Table 7 — Optimizer API call complexity comparison across four self-improving agent frameworks. (Source: original paper, Table 7; see original text for symbol definitions.)" >}}

The per-iteration call-count formulas for the four methods are: WikiSkill is `(1 + T_ReAct) × (N_train / B)`, EvoSkill is `2 × N_train / B`, SkillOpt is `K_opt × N_train / B`, and Trace2Skill is roughly `N_train + (1 + 1/(c-1)) × (N_train / B) + 1`. In the paper's experiments, WikiSkill sets batch size equal to the training set size across every dataset, so `N_train / B` is always exactly 1, and the formula simplifies to `1 + T_ReAct` — depending only on the number of ReAct rounds, completely independent of training set size, with T_ReAct falling roughly between 10 and 20 in the paper's experiments.

That means going from an 80-sample training set to an 800-sample one leaves WikiSkill's per-iteration call count unchanged, while EvoSkill and SkillOpt both scale linearly with more data at a fixed batch size. Trace2Skill is even more explicit about this: since it requires every single trace to be analyzed individually, its call count's lower bound is always proportional to the training set size no matter how batch size is tuned — making it the worst of the four in terms of complexity.

That said, the paper itself acknowledges the cost of this "fixed call count": every ReAct round is a full LLM call, and the context the Skill Proposer reads is typically much larger than what a single-trace analysis would need. In other words, fewer calls doesn't mean lower total token cost — if every ReAct round is reading a long wiki context plus trace content, the token usage of a single call can far exceed what EvoSkill's "smaller batches, more calls, but each one reads less" approach would use. The paper provides no token-level cost comparison at all, only comparing call counts — a trap that's easy to overlook when evaluating this framework's actual deployment cost.

## What's worth taking away

The paper's core contribution isn't itself original — the authors are upfront that they're applying Karpathy's LLM Wiki idea to skill evolution. What this paper actually does is turn that idea into a real, systematic implementation and validate it rigorously across 5 models and 5 tasks, producing the only genuinely clean ablation study in the whole paper. Three claims land with different levels of rigor. The most solidly proven: giving the Skill Proposer a persistent knowledge layer that doesn't roll back with gating decisions works far better than having no cross-iteration knowledge at all. Moderately proven: benefits scale up with model size, and discovering knowledge is separable from executing it — though some phenomena (like a small model's skill improving a larger model) go unexplained causally. Never proven, only asserted: that "curated, structured knowledge" beats "a flat history list" — this remains the single biggest gap in the paper's argument.

The paper also honestly acknowledges its own limitations: the wiki has no automatic cleanup mechanism; its validation gate is a strict "must beat the best score so far," which excludes neutral-but-potentially-valuable proposals; and it has only been validated at single-rollout task scale, never on genuinely long-horizon scenarios spanning hundreds of steps or hours.

Setting the paper itself aside, a few of its judgment frameworks are broadly reusable and worth keeping in mind:

- **The three-layer separation pattern** (immutable raw records, continuously accumulating never-rolled-back structured knowledge, and reversible executable output) can be transplanted directly into other agent-evolution systems.
- **The actor at training time shouldn't be allowed to peek at the knowledge source the optimizer uses** — otherwise the training signal gets distorted.
- **Get breadth from full-batch summaries, get depth from bounded sampling or dynamic retrieval** — a general pattern for problems that need both a global view and case-level depth under a limited context window.
- **When designing an ablation, the control group has to precisely match the specific alternative you're trying to rule out — not just "having nothing at all"** — this paper's own central claim happens to be the one thing in the entire paper its ablation study never directly tests. Worth learning from.

## Conclusion

WikiSkill inserts a structured, never-rolled-back knowledge base between "raw execution traces" and "the skill file," letting the Skill Proposer reason from evidence accumulated across iterations — this is the paper's most solid contribution, and the throughline of this article. How rigorously it's proven, and where the gaps remain, was already broken down in the previous section and won't be repeated here. If you're building agent skills or memory systems, the pattern of three-layer separation plus a knowledge base that never resets is well worth borrowing directly.

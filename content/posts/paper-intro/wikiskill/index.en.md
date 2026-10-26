---
# weight: 1
title: "WikiSkill Explained: A Wiki Layer for Agent Skills"
date: 2026-09-02
lastmod: 2026-10-27
draft: false
description: "Google's WikiSkill paper puts a wiki that is never rolled back between agent logs and skill files. It leads on five models, but its key claim is untested."
featuredImage: "featured-image.png"

tags: ["Large Language Model", "Agent Memory", "Single-Agent"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## Skill evolution's old habit: failures already analysed get analysed from scratch next round

Letting an agent rewrite its own skills sounds great. (A skill is a document that packs the steps for a domain, which the agent reads and applies while working; for example, a skill might say “if you notice you keep picking up and putting down the same item, first check whether the task is already done”.) The loop is simple: run a batch of tasks, see what went wrong, edit the skill, and keep the edit only if it is verified to help. Anyone who has tried it has probably hit the same wall: every round, you re-dig the raw execution logs (traces, the full record of what the agent did on a task) for failure causes, and what earlier rounds worked out was never properly kept.

Existing methods do have some kind of “memory”, but at most it is a “history of proposals” hanging beside the skill’s edit log, not a knowledge base that anyone actually maintains.

That is the problem the *WikiSkill* paper from Google Research and Virginia Tech (arXiv:2608.27454, 8/2026) sets out to solve: between the “raw execution logs” and the “final skill documents”, insert a **persistent knowledge layer**, the wiki, a set of curated, structured notes. It is never rolled back just because one proposal was rejected (a rollback undoes a whole round’s changes and restores the previous version), so every skill edit rests on accumulated evidence instead of analysis from scratch. The idea is not original: the authors say at the start of the paper that it was inspired by a gist (a short public write-up) by Andrej Karpathy on an “LLM Wiki”. But the paper turns it into a full system and tests it on 5 models and 5 tasks.

{{< admonition abstract "The verdict first" >}}
WikiSkill has the highest average score on all five models. The best-supported evidence comes from an ablation (remove one part of the system at a time and see how much the score drops, to judge each part’s contribution; run only on Gemini-3.5-Flash): connecting only the role that proposes skill edits (the Skill Proposer) to the wiki lifts the average from 48.7% to 63.7%, a gain of 15.0 points.

But the claim the paper most wants to make, that “a curated, structured wiki beats a flat history list”, has no matching control experiment, so it counts only as the authors’ claim.
{{< /admonition >}}

The route: first what existing methods’ memory lacks, then WikiSkill’s three layers, four roles and one full case; then what the main experiments and the ablation prove and where gaps remain; finally engineering cost and the judgments worth taking away.

## The problem: existing methods keep memory as a flat list beside the edit log

An agent skill is a lightweight way to package knowledge: the steps for a specific domain go into a standalone folder whose core is a `SKILL.md` file, which the agent reads and applies while working, with no retraining of model parameters. Writing skills by hand is laborious, so recent work lets agents evolve skills automatically: run a batch of training tasks, analyse the successful and failed execution logs, edit the skill accordingly, and repeat.

The three representative methods the paper compares against, EvoSkill, Trace2Skill and [SkillOpt](../skillopt/), all follow the same loop: run tasks, analyse traces, edit the skill, and decide whether to adopt the edit after verification (testing the new skill on a validation set, a separate group of tasks held out from training). They also have some form of “memory”; EvoSkill, for example, keeps a list of proposals and evaluation results that is not cleared between iterations. But the paper points to a shared weakness: that memory is a **flat list** attached to the skill’s edit log, not an independent knowledge representation that is continuously curated and thickens over time.

WikiSkill’s view is that the gap is not whether memory exists but that memory is just a list passively piled up on the side, so what needs adding is a knowledge layer that is actively curated and keeps growing.

## The method: a wiki that is never rolled back, between raw logs and skills

WikiSkill’s answer is one more layer. Below: first the role of each of the three layers, then how four roles hand the work along in one iteration, then three rules that are easy to get wrong, and finally a real case (the “keep picking up and putting down” loop from above really did show up in the experiments).

### The three layers: what each can change and what gets rolled back

WikiSkill splits the agent’s workspace into three layers, each with different edit rules:

| Layer | Property | Content |
| --- | --- | --- |
| Skill Layer (`skills/`) | Reversible, conditionally updated | The skill documents actually injected into the prompt |
| Wiki Layer (`wiki/`) | Keeps accumulating, never reset | Curated, structured knowledge |
| Raw Layer (`raw/`) | Kept permanently, append-only | Raw execution traces |

Think of the three layers as an investigation: Raw is the surveillance footage, which only ever grows; Wiki is the investigator’s case notes, tidied up as they watch, and not thrown away just because one version of the handbook was sent back; Skill is the handbook finally handed out, which can be rolled back to the previous edition as a whole.

The Wiki Layer is the new middle layer this paper adds, and it holds three kinds of files:

- `patterns/`: a set of markdown files, one file per concrete failure mode or successful strategy.
- `logs.md`: a chronological record of what each iteration did.
- `skill-impact.md`: the content of each proposal, its validation score, and whether it was accepted or rejected.

Each skill folder in the Skill Layer has two files: `SKILL.md` is the skill itself, and `PURPOSE.md` records which wiki patterns inspired and changed it, the motivation behind the edits.

### One iteration: four roles hand the work along

The three layers are a static structure; in practice four roles interact in turn to run one iteration:

1. The **Inference Agent** runs the training tasks with the previous round’s skill set and writes the results into the Raw Layer (append-only; it cannot access the wiki).
2. The **Wiki Maintainer** uses a single LLM call to sample a few traces and do root-cause analysis (find the real reason behind a failure rather than just the surface symptom), then updates the wiki’s patterns, index (a directory listing a summary of each pattern) and log.
3. The **Skill Proposer** works as a multi-turn ReAct agent (it alternates reasoning and tool calls): it reads the wiki index, `skill-impact.md`, relevant patterns and the raw traces in turn, then proposes creating or editing one skill (only one at a time).
4. **Gating & Rollback** tests the candidate skill on the validation set. If the score improves it is adopted; if not, the whole set is rolled back to the previous version. Either way, the proposal, the diff and the score are written to `skill-impact.md` before the next round.

{{< image src="figure2.png" alt="WikiSkill framework diagram: at the bottom the immutable raw execution traces, in the middle the continuously accumulating Wiki knowledge layer, at the top the Skill layer actually injected into the prompt; four roles interact in turn to complete one iteration." caption="Figure 1 — WikiSkill framework overview: the Raw / Wiki / Skill layers and the order in which four roles interact in one iteration. (Source: original paper, Figure 2.)" >}}

One design choice is key: **the Inference Agent may not access the wiki while running training tasks**. The later ablation shows this restriction is necessary: letting it peek at the wiki actually makes the final skills worse, and the reason comes later.

{{< fold title="What the Wiki Maintainer’s prompt looks like: the index matters as much as the patterns" tone="info" >}}
The paper’s appendix gives the Wiki Maintainer’s full system prompt. The role definition asks it to do deep root-cause analysis of execution logs, not just look at surface symptoms; the input is this round’s raw traces plus the current wiki context; the output is fixed JSON containing new patterns, edits to existing patterns, the complete updated index (not a diff), and a summary of the iteration.

One paragraph marked CRITICAL deserves attention: the entries in `index.md` are the most important part of the wiki, because they decide whether the inference agent goes on to read a full pattern page. Each description must be specific enough that the agent can judge relevance without reading the whole page, and must include the problem, the root cause and the fix. This reveals an engineering detail: however well a pattern page is written, if its index summary is poor, later agents will never click through, so index quality is held to the same standard as the pattern content itself.
{{< /fold >}}

### Three rules people get wrong: what can be deleted, edited or only appended

When people discuss this kind of layered design, the most common misunderstanding is “which layer can be deleted from, edited, or only appended to”. The actual rules differ from intuition:

- **The Skill Layer has no “delete” operation.** The Skill Proposer’s output format has only three options: create, edit an existing skill, or do nothing. What looks like “deletion” is really the whole-version rollback done by Gating & Rollback: if a new proposal fails validation, the system restores the entire skill set to the previous round, rather than deleting a single skill.
- **The Wiki Layer is not append-only.** The Wiki Maintainer has three ways to change an existing pattern page: append to the end of the file, find specified text and replace it, or insert after specified text. So existing content can be corrected or overwritten. “Never reset” means the wiki’s overall state is not rolled back because a proposal was rejected, not that “every file can only be added to, never edited”.
- **The Raw Layer’s read-only status is read-only in how it is used.** Each iteration adds that round’s execution logs, so the layer keeps growing, and “immutable” means records already written are never modified or overwritten. The Wiki Maintainer and the Skill Proposer do have read-only access to it, but the layer itself keeps getting bigger.

### A walk-through: how a wiki shaped one skill step by step

This case shows what the mechanism looks like in practice: the setting is ALFWorld (one of the paper’s five tasks, an embodied interaction task where the agent must actually handle objects in a simulated environment), where Qwen-3.6-27B evolves a skill called `break-repetition-loop`, shown here from start to finish.

{{< image src="figure3.png" alt="Timeline: in Round 0 the Wiki Maintainer creates a pattern page and the Skill Proposer’s proposal is rejected; in Round 1 a more focused proposal built on the rejection record is accepted; in later rounds new evidence keeps piling onto the same pattern page, and in Round 4 the skill is edited on that basis." caption="Figure 2 — Case study of wiki-guided skill evolution (ALFWorld, Qwen-3.6-27B). (Source: original paper, Figure 3.)" >}}

**Round 0.** The Wiki Maintainer creates a pattern page, `take-examine-move-loop.md`, describing how the agent picks up an item, examines it, puts it back, and repeats that loop endlessly, with evidence from two training examples. In the same round the Skill Proposer proposes a new skill called `goal-directed-action`, but its validation score of 0.72 does not beat the baseline (the best score to beat), so it is rejected. `skill-impact.md` records the diff (the before-and-after difference) and the rejection in full.

**Round 1.** The Wiki Maintainer sees the same error again, with a new variant, and appends the new evidence to the existing pattern page. This time the Skill Proposer reads the Round 0 rejection record and changes its proposal to a new skill, `break-repetition-loop`, more specific and focused on the action pattern. Its validation score of 0.78 passes.

**Round 2 to Round 4.** In Round 2 to Round 3 (which the paper does not detail), the Wiki Maintainer creates another pattern, `multi-operation-loop.md`, describing an agent that repeats operations on the same item without checking whether the task is already done. In Round 4 the Skill Proposer reads this new evidence and proposes editing (not rebuilding) `break-repetition-loop`, which passes again.

In the end the skill’s `PURPOSE.md` explains its whole history in one line: “Created as break-repetition-loop. The earlier attempt, goal-directed-action, was rejected as too abstract. This version is leaner and uses concrete action patterns.” No need to dig through raw traces and guess: that one line tells you why this version of the skill looks the way it does. And the rule “do each type of operation only once” could be added in Round 4 precisely because the matching pattern page had kept accumulating evidence across iterations. In the ablation we will see later, “giving the Skill Proposer wiki access brings +15 points”, and this case is one concrete instance of it.

Remember the shape of this case: the proposal rejected in Round 0 was not wasted, it became the basis for the more focused proposal in Round 1; after that, new failure evidence kept piling onto the pattern page, which in Round 4 gave a reason to edit the skill. The point of the three layers is that this thread never breaks.

## Results: ahead on all five models, by very different margins

With the mechanism in hand, here is how it performs: first how steady the main result is, then how the gains change with model size, and finally whether a skill evolved by one model can be handed to another.

### Main result: steady, not just high at the peak

The experiments cover 5 models (Qwen-3.5-4B, Qwen-3.5-9B, Qwen-3.6-27B, Gemma-4-31B, Gemini-3.5-Flash) times 5 tasks: LiveMath for math reasoning, SealQA for fact questions that need web search, SpreadSheet for spreadsheet manipulation, OfficeQA for long-document question answering, and ALFWorld for embodied interaction. Each task is a benchmark (a standard test set used to compare models), and each combination runs the full evolution process three times and averages the results.

{{< image src="figure1.png" alt="Bar chart of average accuracy for five models with no skill and with skills evolved by EvoSkill, SkillOpt and WikiSkill; WikiSkill leads everywhere, and the lead widens as the model gets larger." caption="Figure 3 — Average performance of five models: WikiSkill leads on every model, and its advantage grows with model capability. (Source: original paper, Figure 1.)" >}}

The headline numbers: WikiSkill has the highest average score on all 5 models, and against each model’s “best competing method” it wins by these margins:

| Model | Lead over the best rival, in percentage points (rival = the best competing method on that model) |
| --- | --- |
| Qwen-3.5-4B | 3.3 |
| Qwen-3.5-9B | 5.1 |
| Qwen-3.6-27B | 10.0 |
| Gemma-4-31B | 5.8 |
| Gemini-3.5-Flash | 12.0 |

A few striking single cases: Gemini-3.5-Flash goes from 33.0% to 72.6% on LiveMath and from 50.5% to 76.6% on SpreadSheet; Qwen-3.6-27B goes from 52.8% to 77.6% on ALFWorld.

{{< image src="table1.png" alt="Table of accuracy for five models on five tasks with no skill and with skills from EvoSkill, Trace2Skill, SkillOpt and WikiSkill." caption="Table 1 — Main results across models and tasks. WikiSkill has the highest average in every model block. (Source: original paper, Table 1.)" >}}

What the paper stresses is **stability**, not just peak performance. Other methods clearly regress in some settings, rather than simply improving less: EvoSkill lifts Qwen-3.5-9B a lot on LiveMath (28.2%→58.1%) but makes Gemma-4-31B worse on the same task (33.9%→29.8%); SkillOpt makes Gemini-3.5-Flash worse on SealQA (29.4%→28.2%). WikiSkill shows no such hit-or-miss pattern.

{{< admonition note "Gemini’s 85.9% on ALFWorld does not mean no effect" >}}
On ALFWorld, Gemini-3.5-Flash scores 85.9% under every method, including no skill. The reason is that its validation set already scored 100% before evolution began, which triggered early stopping, so no evolution actually ran. It is not that WikiSkill does nothing on this task; the task is simply too easy for that model.
{{< /admonition >}}

### The bigger the model, the more skill evolution pays

The paper describes this finding as skill evolution and model scaling being **complementary**. It is clearest in the Qwen family (same family, only the parameter count differs, which makes a clean comparison): WikiSkill’s average gain (against the same model without a skill) grows with scale, and it is especially pronounced on SpreadSheet.

| Model | Average gain over no skill | Gain over no skill on SpreadSheet |
| --- | --- | --- |
| Qwen-3.5-4B | +12.3 points | +6.5 points |
| Qwen-3.5-9B | +17.5 points | +9.3 points |
| Qwen-3.6-27B | +23.9 points | +40.9 points |

A more intuitive way to put it: a small model with a good skill can beat a larger model with none. Qwen-3.5-9B with WikiSkill reaches an average accuracy of 47.4%, above the 39.4% of Qwen-3.6-27B using no skill at all. The paper reads this as model capability and evolved procedural knowledge (knowledge of how to do things step by step) being complementary sources of performance. The stronger the model, the better it can develop and execute finer-grained skills and the more it gains; and an effective skill lets a small model close part of the gap to a larger one.

The gains are also uneven across datasets. Qwen-3.6-27B improves by only 11.6 points on OfficeQA (a long-document retrieval task), against 40.9 points on SpreadSheet. The paper does not break down that gap within the one model, but it has a related observation about OfficeQA-type tasks: a large model can use the evolved search procedure to navigate long documents, while a small model (such as Qwen-3.5-4B) cannot execute such a multi-step search, falls back to its default reading behaviour, and ends up slightly worse. This echoes the cross-model transfer results in the next section.

### Cross-model transfer: whether a skill travels depends on what is packed inside

This group of experiments asks: can a skill evolved by model A be handed directly to model B?

{{< image src="table2.png" alt="Table of accuracy for each inference model with no skill and with skills evolved by Qwen-3.5-4B, Qwen-3.6-27B and Gemini-3.5-Flash as source models." caption="Table 2 — Cross-model skill transfer results. Shaded rows are a model using a skill it evolved itself. (Source: original paper, Table 2.)" >}}

Three findings are worth taking apart:

| Finding | Concrete example |
| --- | --- |
| A transferred skill is often better than the model’s own | Qwen-3.6-27B’s skill, given to Qwen-3.5-9B on SpreadSheet, scores 50.5%, higher than the 33.6% of the skill that model evolved itself |
| Whether it transfers depends on whether the skill packs a general procedure or a model-specific patch | LiveMath skills transfer especially well (33.0%→67-74%); but on SpreadSheet, Qwen-3.5-4B’s skill handed to Gemini-3.5-Flash drops the score from 50.5% to 18.1%, while in the same setting Qwen-3.6-27B’s skill lifts it to 63.4% |
| Even from the same source, different receiving models “digest” a skill differently | Qwen-3.5-4B’s own evolved skill makes itself worse (30.2%→28.5%), yet the same skill given to Qwen-3.6-27B improves it (42.1%→52.9%) |

For the negative transfer in the second finding, the paper does a root-cause analysis: skills evolved by small models pack many low-level workarounds (such as one-line Python commands and string-conversion rules) that help the small model avoid execution failures but restrict a strong model from using fuller end-to-end scripts; fragmented diagnostic procedures also create redundant tool calls that can use up a strong model’s interaction budget before the task is done.

{{< admonition note "A phenomenon the paper does not explain" >}}
But the paper does **not** explain another, more counterintuitive phenomenon: a skill evolved by the small model Qwen-3.5-4B, given to Gemma-4-31B, improves it on both LiveMath and ALFWorld (to 73.1% and 66.9%). The paper only reports the numbers and gives no further root-cause analysis.

Overall, the paper offers many descriptions of which directions transfer well or badly, but the only case with a causal explanation is SpreadSheet, and that is a qualitative error analysis, not a systematic verification.
{{< /admonition >}}

Taken together, the three findings lead the paper to a framing worth remembering: self-evolution mixes two different abilities, “discovering useful procedural knowledge from experience” and “executing that knowledge effectively at inference time”. These can be separated; they are not the same thing. This view is more general than the paper itself: when evaluating any “self-improving agent” system, first ask whether it improved because it learned something better, or because it got better at following instructions.

So the results come down to this: the lead is steady and grows as the model gets stronger; but whether a skill can travel depends on whether it packs a general procedure or just a patch for its source model, and whether the receiving model can digest it is another variable.

## Ablation: where the wiki actually does its work

Next comes the cleanest experiment in the paper. It answers “how much difference does the wiki make” and where in the pipeline the wiki does its work.

### Wiki access for the Skill Proposer adds 15.0 points; for the training-time agent it costs points

This experiment uses only one model, Gemini-3.5-Flash, and varies whether the Inference Agent and the Skill Proposer have wiki access.

Note that whenever the Skill Proposer has no wiki access, the Wiki Maintainer, the role that maintains the wiki, is removed as well. The four ablation settings below, plus a baseline that runs no skill evolution at all, give five numbers:

| Inference Agent has wiki? | Skill Proposer has wiki? | Average score | Note |
| --- | --- | --- | --- |
| - | - | 40.4% | No-skill baseline |
| Yes | No | 45.3% | Wiki Maintainer removed |
| No | No | 48.7% | Wiki Maintainer removed |
| Yes | Yes | 60.9% | Full configuration |
| No | Yes | 63.7% | **WikiSkill default configuration** |

{{< image src="table3.png" alt="Table of average scores over the five tasks under four ablation settings (whether the Inference Agent and the Skill Proposer have wiki access)." caption="Table 3 — Ablation results: turning off wiki access for the Inference Agent and the Skill Proposer in turn and watching the average score change. (Source: original paper, Table 3.)" >}}

**First conclusion: giving the Skill Proposer access to a persistent wiki has a very large effect.** With the Inference Agent kept away from the wiki, simply switching on the Skill Proposer’s wiki access lifts the average from 48.7% to 63.7%, a full +15.0 percentage points and the largest effect of any single factor in the paper. Looking at sub-items, LiveMath goes from 51.3% to 72.6% and SpreadSheet from 49.9% to 76.6%. The paper’s explanation: without knowledge accumulated across iterations, the Skill Proposer struggles with complex failure modes that take several iterations to converge.

**Second conclusion: letting the Inference Agent touch the wiki during training makes the final skills worse.** With the Skill Proposer already having wiki access, also letting the Inference Agent see the wiki in training drops the average from 63.7% to 60.9%, with LiveMath falling most (72.6%→64.8%). This is why the architecture deliberately forbids the Inference Agent from seeing the wiki in training.

{{< admonition info "The paper’s explanation for this drop (only a hypothesis)" >}}
When the Inference Agent can see both the skill and the wiki during training, it may look answers up in the wiki instead of solving the task with the skill itself. The traces produced then become distorted: the agent does well not because the skill is useful but because the wiki helped, which makes the training signal the Skill Proposer receives unrepresentative.

The paper explicitly labels this a hypothesis and does not verify it further.
{{< /admonition >}}

### The claim the paper most wants to prove is the one the ablation does not test

On the surface, EvoSkill also keeps a proposal history that is not cleared between iterations, so what more does WikiSkill do? The answer is not “whether there is memory” but **the form of the memory**:

|  | EvoSkill’s history list | WikiSkill’s wiki |
| --- | --- | --- |
| Storage form | A flat list: proposals, validation scores and accept/reject outcomes, one after another | Structured, topic-organised knowledge pages, each tied to one concrete failure mode or successful strategy |
| A separate curation step? | None: the proposer reads the history list plus this round’s raw traces and digests them on the spot | Yes: a dedicated Wiki Maintainer whose job is root-cause analysis and merging raw traces into existing pattern pages |
| How evidence accumulates | Each failure case basically stands alone | The same pattern page keeps stacking evidence across iterations |
| Can relevant knowledge be looked up? | No index: the proposer has to read the whole history from the start | There is an `index.md` with a one-line summary per pattern (problem, root cause, fix) so the proposer can quickly judge what is relevant |

Boiled down to one sentence, this is WikiSkill’s core claim: **knowledge needs to be actively curated, digested and given accumulating evidence, not just passively stacked in time order.**

{{< admonition warning "A gap in the ablation design" >}}
The Table 3 setting that removes the wiki removes the Wiki Maintainer entirely, so it tests “having structured knowledge” against “having no cross-iteration knowledge at all”. It does not include a control group comparing a “structured wiki” against a “flat history list like EvoSkill’s”. In other words, Table 3 shows “structured knowledge > no knowledge at all” (+15%), but does not directly prove what the paper most wants to claim: “structured knowledge > flat-list knowledge”.

Table 1 does compare scores against EvoSkill overall, but that comparison mixes in another variable: WikiSkill’s Skill Proposer is a multi-turn ReAct agent that can explore dynamically for 10 to 20 turns, and EvoSkill has no such mechanism, so the difference cannot be cleanly attributed to how structured the wiki is. This is the biggest gap in the paper’s argument.
{{< /admonition >}}

So the ablation has to be read in two parts: “having a wiki beats having none” is well supported on Gemini-3.5-Flash; but “why curate it into structured pages” is the authors’ claim, not something this experiment measured.

## Engineering: breadth, depth and call costs

Last, two engineering questions: how analysis gets batched when the data is large, and whether fewer calls really means cheaper.

### Why training runs on the full dataset but analysis reads only a slice

This section answers a practical question: when the training data grows, how do you keep the analysis workload from exploding? The answer has two steps: set the analysis batch to the whole training set so each round analyses only once, then handle “looking wide” and “looking deep” separately so that one analysis can actually be read.

The batch size parameter defined in the paper’s appendix is often confusing, because it is not obvious what it controls. Think of it as two levels: each iteration, the Inference Agent always runs one rollout over the whole training set (having the agent actually do every task once), and that has nothing to do with batch size; what batch size really controls is how many times the “analysis plus proposal” step runs. If batch size is smaller than the training set (as in EvoSkill and SkillOpt), the training set is cut into several small batches, each triggering a full round of analysis; WikiSkill sets batch size equal to the training set size, so each iteration analyses only once.

|  | Breadth | Depth |
| --- | --- | --- |
| Purpose | Avoid seeing only part of the data and misjudging how widespread an error pattern is | Control cost and cope with the limits of the context window (how much text the model can read at once) |
| How | Full-batch rollout, plus the summary of all task outcomes the Skill Proposer gets at the start | Limited sampling: the Wiki Maintainer uses one call with fixed sampling; the Skill Proposer uses multi-turn ReAct with on-demand dynamic reading |
| Concrete rules | (look at everything) | The Wiki Maintainer samples at most 8 traces per round (5 failures and 3 successes), each truncated to 15,000 characters; the Skill Proposer is not limited, can dynamically choose traces from the whole training set to read closely, and the rule only requires reading at least 4, with no upper limit |

So each round analyses only once (batch size set to the whole training set); breadth comes from the full batch and depth from sampling, so that one analysis fits in the context window.

### A fixed number of calls does not mean a low total cost

What is counted here is “how many LLM API calls the analysis-plus-proposal step itself makes per iteration”, not counting the Inference Agent’s own calls to run the training tasks.

WikiSkill’s number of calls per iteration is \( 1 + T_{\text{ReAct}} \), where \( T_{\text{ReAct}} \) is the number of ReAct turns the Skill Proposer uses, roughly between 10 and 20 in the paper’s experiments. It simplifies to this because the paper sets the batch size \( B \) equal to the number of training tasks \( N_{\text{train}} \) on every dataset, so \( N_{\text{train}} / B \) is always 1. The result is that the call count depends only on the number of ReAct turns and not at all on the size of the training set.

So when the training set grows from 80 to 800 tasks, WikiSkill’s calls per iteration do not change, while EvoSkill and SkillOpt grow linearly as batches get smaller and data grows; Trace2Skill is more explicit still: it requires every single trace to be analysed on its own, so however you tune batch size, its call count has a lower bound that is proportional to the training set size, the worst complexity of the four.

{{< admonition warning "Fewer calls does not mean lower total cost" >}}
The paper itself admits the cost of this “fixed number of calls”: each ReAct turn is a full LLM call, and the context the Skill Proposer reads is usually much larger than for a single-trace analysis.

In other words, fewer calls does not mean lower total token cost: if every ReAct turn reads a very long wiki context plus trace content, the tokens per call can far exceed those of EvoSkill’s “small batches, many calls, little read each time” style. The paper gives no token-level cost comparison at all and compares only call counts, which is an easily overlooked trap when judging what this framework would really cost to deploy.
{{< /admonition >}}

{{< fold title="The four frameworks’ full formulas, and the paper’s original table" tone="info" >}}
| Method | Calls per iteration |
| --- | --- |
| WikiSkill | \( (1 + T_{\text{ReAct}}) \times (N_{\text{train}} / B) \) |
| EvoSkill | \( 2 \times N_{\text{train}} / B \) |
| SkillOpt | \( K_{\text{opt}} \times N_{\text{train}} / B \) |
| Trace2Skill | about \( N_{\text{train}} + (1 + 1/(c-1)) \times (N_{\text{train}} / B) + 1 \) |

\( N_{\text{train}} \) is the number of training tasks, \( B \) is the batch size, and \( T_{\text{ReAct}} \) is the number of ReAct turns of the Skill Proposer. The definitions of \( K_{\text{opt}} \) and \( c \) are in the paper’s original table and are not repeated here.

{{< image src="table7.png" alt="Table of the per-iteration optimizer API call-count formulas and complexity classes of the WikiSkill, EvoSkill, SkillOpt and Trace2Skill frameworks." caption="Table 4 — Optimizer API call complexity of four self-improving agent frameworks. (Source: original paper, Table 7.)" >}}
{{< /fold >}}

## Takeaways: three levels of evidence and four portable judgments

To pull it together: three claims, each supported to a different degree, plus four judgments that stay useful even without this paper.

### How solid is it, and where are the limits

The paper’s core contribution is not original in itself; the authors say they apply Karpathy’s LLM Wiki idea to skill evolution. What the paper really does is implement the idea systematically and test it solidly on 5 models and 5 tasks, producing the only clean ablation in the whole paper. The three claims are supported to different degrees:

| How well supported | Content |
| --- | --- |
| Most solid | Giving the Skill Proposer a persistent knowledge layer that is not rolled back with the gating result works far better than having no cross-iteration knowledge (the ablation was run only on Gemini-3.5-Flash) |
| Medium | Gains grow with model size, and discovering knowledge and executing it can be separated, but some phenomena (for example a small model’s skill making a large model better) have no causal explanation |
| Not proven | That “curated, structured knowledge” beats a “flat history list” is only the paper’s own claim, and the biggest gap in its argument |

Limits the paper candidly admits:

- The wiki has no automatic cleanup, so it keeps growing as iterations accumulate; the paper says plainly this is left for future work.
- The validation bar is strict, “must beat the best score so far”, which rules out neutral proposals that might have long-term value.
- It has only been validated at single-rollout scale, and has not been tested in truly long-horizon settings (hundreds of steps, hours).

### Four judgments you can take with you

Beyond this paper itself, a few judgment frameworks are general and worth keeping in mind:

- **The three-layer separation pattern** (immutable raw records, continuously accumulating structured knowledge that is not rolled back, revertible executable output) can transfer directly to other agent-evolution systems.
- **The training-time actor (here, the Inference Agent) should not peek at the optimizer’s knowledge source (here, the Skill Proposer’s)**, or the training signal gets distorted.
- **Get breadth from full-batch summaries and depth from limited sampling or dynamic retrieval**: a general way to split a problem that needs both global view and case-level depth under a limited context window.
- **In an ablation, the control must match the exact form you want to rule out, not just “nothing at all”.** The paper’s central claim is exactly the one part of the whole paper that the ablation does not directly verify, a lesson worth taking to heart.

{{< admonition success "Three sentences to take away" >}}
1. Skills get rolled back as a whole; the wiki does not: WikiSkill puts a layer of knowledge that is never rolled back between the raw logs and the skills.
2. Read evidence in grades: 48.7% → 63.7% (the Gemini-3.5-Flash ablation) is the most solid, and “structured beats flat” is unproven.
3. When you build your own, aim the control at the exact form you want to rule out.
{{< /admonition >}}

WikiSkill inserts a structured, never-rolled-back knowledge base between the “raw execution logs” and the “skill documents”, so the Skill Proposer can judge on evidence accumulated across iterations. That is the paper’s most solid contribution and the core thread of this post. If you are building an agent skill or memory system, the pattern of three-layer separation plus a never-reset knowledge base is worth borrowing directly.

---
# weight: 1
title: "SkillOpt: Treating an Agent's Skill File as a Trainable Weight"
date: 2026-07-22
lastmod: 2026-07-23
draft: false
description: "SkillOpt treats an agent's skill file as a trainable weight: batched rollouts, a bounded edit budget, and a strict validation gate replace ad hoc prompt patching."
featuredImage: "featured-image.png"

tags: ["Large Language Model", "Agent Memory", "Prompting", "Single-Agent"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

Any engineer building on top of a frozen, API-only LLM eventually hits the same wall: the model can't be fine-tuned for the task at hand, and its default behavior isn't quite right. It writes SQL that ignores some detail of the schema, forgets to check an edge case, or reaches for the wrong tool — and it may have made that exact mistake ten times before. The usual fix is a hand-tuned system prompt, or a "skill" document: a page of instructions prepended to every call. The problem is that this kind of document is almost always either hand-tuned once and never touched again, or "improved" through a loop where the model reflects on its most recent failure and rewrites the prompt on the spot — the approach taken by test-time context-curation methods like [Dynamic Cheatsheet](../dynamic-cheatsheet/) and [Agentic Context Engineering](../agentic-context-engineering/). The second approach sounds appealing, but in practice it tends to overfit to whatever error just happened, bloating the prompt with one-off patches and quietly erasing lessons learned earlier — a kind of catastrophic forgetting, except it happens in plain text instead of in weights.

SkillOpt, a paper recently published by Microsoft, doesn't try to patch this problem further — it reframes it entirely. Its core move is to stop treating skill-document edits as an unconstrained, ad hoc rewriting process, and instead treat the document the way a deep learning optimizer treats a weight tensor: an external, versioned, trainable piece of state that gets updated through controlled, bounded steps, kept only if it passes validation, and rolled back if it doesn't help. The target model itself never changes at all — all of the "learning" happens inside a text file.

{{< admonition abstract "Key Takeaways (TL;DR)" >}}
1. **Reframing, not patching**: SkillOpt treats a skill document the way a deep learning optimizer treats a weight tensor — an external, versioned, trainable piece of state, not a file anyone edits by hand.
2. **Two models, cleanly split**: a frozen target model does the actual work; a separate optimizer model only runs offline to propose edits, so deployment cost is effectively zero once training ends.
3. **A strict, blind validation gate**: every candidate skill must score *strictly higher* than the current one on a held-out split it never trained on — a tie or a drop discards the whole step.
4. **The results back it up**: best-or-tied on all 52 measured (model, benchmark, harness) combinations, with the final skill file needing only 1 to 4 accepted edits per benchmark.
{{< /admonition >}}

## Two Models, Each With a Distinct Job

SkillOpt splits responsibility across two separate models, rather than asking one model to both do the work and grade its own homework.

### The Target Model (M)

The target model is the one that actually does the work — answering questions, calling tools, writing code — running inside whatever execution harness the task needs, from a plain chat setting to a more complex, workspace-driven harness like Codex or Claude Code. Its weights and native system prompt **stay frozen** throughout training. The only thing that changes from one evaluation round to the next is the skill document \( s \) that gets dropped into its workspace or prepended in front of it. Formally, given a task \( x \) and a skill \( s \), the target model produces a trajectory and a scalar score between 0 and 1: \( (\tau(s), r(s)) = h(M, x, s) \).

### The Optimizer Model (O)

The optimizer model never touches the task itself. It's usually a more capable "frontier" model, and it only runs during offline training. Its job is to read the target model's trajectories and scores, then propose concrete edits to the skill document — add this heuristic, delete that stale instruction, reword this vague line.

Splitting these two roles cleanly is exactly why the design has near-zero deployment cost: once training ends, the optimizer's API spend disappears entirely. What actually ships to production is just the frozen target model plus a small text file.

## The Skill File Itself

That text file, called `best_skill.md`, is typically 300 to 2,000 tokens long. Depending on the execution harness, it's either prepended directly to the system prompt (for plain question-answering tasks) or written into the target model's workspace as a persistent, on-disk note (for tool-using agents like Codex or Claude Code). Its contents look like what you'd expect from a well-written internal playbook: general operating procedures, domain-specific heuristics, tool-calling conventions, output-format constraints, and defensive reminders about known failure modes.

## Avoiding Grading Your Own Homework

### Data Isolation and a Strict Acceptance Rule

The single most important engineering discipline in SkillOpt's design is data isolation — borrowed directly from standard machine learning practice: a training split (\( D_{tr} \)), a selection/validation split (\( D_{sel} \)), and a held-out test split (\( D_{test} \)).

The optimizer model only ever sees trajectories from \( D_{tr} \) — that's where it gets its evidence for what to change. It never sees \( D_{sel} \) at all. Every candidate skill produced during training has to be scored independently on \( D_{sel} \), and the acceptance rule is strict: the new skill's average score must be **strictly greater** than the current skill's score — a tie doesn't count. This "strictly greater" bar closes off the most common failure mode of iterative prompt editing: a string of individually plausible edits that, added together, do nothing but inject noise or bloat the document without actually helping.

{{< image src="figure1.png" alt="SkillOpt overview: the target model executes tasks carrying the current skill, the optimizer model turns the resulting trajectories into bounded edit proposals, and a held-out validation gate accepts only edits that actually improve the validation score." caption="Figure 1 — Overview of SkillOpt. Accepted edits are folded into the deployed skill file; rejected edits become negative feedback for later steps. (Source: original paper.)" >}}

### A Deep-Learning Analogy for the Whole System

The mental model that runs through the whole piece — and the thing that makes every later design choice make sense — is a direct analogy to a classic deep learning optimizer:

| Deep Learning Component | SkillOpt's Text-Space Equivalent |
| --- | --- |
| Parameters (\( W \)) | The skill file (`best_skill.md`) |
| Gradient | Minibatch-derived edit proposals |
| Learning rate | Edit budget (\( L_t \)) |
| Validation checkpoint | Blind \( D_{sel} \) gate with strict elimination |
| Momentum / EMA | The epoch-wise "slow update" |

Every mechanism described below exists to make one side of this table actually work in text space instead of gradient space.

## Gather Evidence Before You Edit

Every training step starts with a **rollout (forward pass)**: the target model, carrying the current skill, runs on a batch of 40 tasks drawn from \( D_{tr} \). That large batch size is deliberate. If the optimizer only reacted to a single failed trajectory, it would tend to overfit to whatever specific noise caused that failure — a network hiccup, an oddly phrased input — rather than finding a pattern that actually recurs. Forty samples give the system enough statistical weight to tell a systematic weakness apart from a one-off fluke.

Once the 40 trajectories are collected, they're split by score into a **failure pool** and a **success pool**. That split matters because the two pools call for different kinds of edits: the failure pool is mined for corrective fixes — what broke, and how to patch it — while the success pool is mined for reinforcement: good habits that are already working but haven't been written into the skill file yet, and that might not reproduce reliably next time if they aren't.

## Parallel Diagnosis, MapReduce-Style

### Why Minibatches of 8

Stuffing every failure case in a pool (roughly 20 of them) into a single optimizer call would blow past the useful context window and risk the "lost-in-the-middle" effect that gets worse as prompts grow longer. So instead, SkillOpt slices each pool into minibatches of 8 and fires off a separate, parallel API call for each one — a shape that maps directly onto MapReduce: each minibatch is analyzed independently (Map), and the resulting proposals are then pulled together (Reduce). The system supports up to 16 of these calls running concurrently, so even a step that needs to diagnose dozens of trajectories across both pools can be handled in a single round of parallel computation instead of a long serial queue.

The minibatch size of 8 is itself a deliberate trade-off: a size of 1 would reintroduce exactly the single-trajectory overfitting the whole design is trying to avoid, while 8 is small enough to stay within context limits yet large enough to force the model to compare trajectories side by side and find failure patterns that genuinely recur across multiple tasks, rather than fixating on a single case.

### The Analyst Contract

Every parallel call follows a fixed contract. The analyst responsible for the failure side (`analyst_error.md`) receives the trajectories for 8 failed tasks plus the current skill file, and returns a JSON object listing the common failure patterns it found, along with a `patch` — a short list of atomic edit operations (`append`, `insert_after`, `replace`, `delete`), each pinned to a precise target string inside the skill file. The analyst on the success side (`analyst_success.md`) does the symmetric job: finding good habits the target model already exhibits but the skill file doesn't yet capture, while staying conservative about anything already well covered so it doesn't reinforce the same point twice.

## Merging Without Losing Context

Once the parallel analysts have returned their proposals, SkillOpt has to collapse multiple lists of edits — sometimes overlapping, sometimes contradictory — into one. It does this through a two-stage hierarchical merge.

### Tree Reduce Within Each Pool

If either pool has more than 8 proposals, SkillOpt runs a **tree reduce**: batches of up to 8 are merged pairwise (via `merge_failure.md` or `merge_success.md`) until each pool is down to a single, unified list. During this merge, duplicate suggestions collapse into the most generally worded version and get tagged with a `support_count`, tracking how many independent analysts proposed an equivalent edit — a rough proxy for how common that failure or good habit actually is. Proposals that try to touch the exact same spot in the skill file in incompatible ways also get resolved right here, rather than being left to collide later.

### Cross-Pool Merge: Fixing Failures Always Wins

The two now-unified lists — one from the failure pool, one from the success pool — go through a final cross-pool merge (`merge_final.md`), and the rule there is unambiguous: **fixing failures always wins**. If a success-pool edit and a failure-pool edit both target the same location, the failure-pool version is kept, no exceptions; only success-side edits that don't conflict survive into the next stage. Fixing something broken is treated as strictly higher priority than reinforcing something that's already working.

{{< image src="figure2.png" alt="SkillOpt's full pipeline: rollout, minibatch reflection, hierarchical merging, budget-constrained ranking, and a held-out validation gate, with a slower slow/meta update layered across epochs." caption="Figure 2 — SkillOpt's complete pipeline, showing how a batch of rollout data flows through minibatch reflection, merging, budget-constrained ranking, and validation before anything is actually written to disk. (Source: original paper.)" >}}

## A Text-Space Learning Rate: The Edit Budget

### A Cosine-Decayed Budget

After merging, the number of proposed edits can still be well beyond what's safe to apply in a single step. SkillOpt caps how many edits a single step can apply using an **edit budget** \( L_t \) — the direct text-space equivalent of a learning rate. Applying too many edits at once is like taking too large a step in gradient descent: the skill file can end up unstable and lose lessons it worked hard to accumulate.

The budget itself follows a cosine decay schedule, typically starting at \( L_t = 4 \) and decaying down to \( L_t = 2 \). Early in training, the skill file is still mostly empty, so large structural edits are safe and useful — exploration. Later on, once the file has accumulated substantial content, only small wording tweaks should get through — consolidation — since pushing further risks tearing apart parts that are already working well.

### Ranking Which Edits Make the Cut

Deciding which edits actually make it into that budget is the job of a dedicated ranking step (`ranking.md`), which orders every merged candidate edit strictly by four criteria:

1. How many trajectories it would fix (tied directly to `support_count`).
2. Whether it genuinely fills a gap rather than restating something already in the document.
3. Whether it reads like a generally applicable rule rather than something hard-coded to one task's specifics.
4. Whether it's concrete and actionable rather than vague advice.

Only the top \( L_t \) edits make it into the candidate skill.

## The Gatekeeper That Actually Decides

The candidate skill \( \tilde{s} \) produced by applying these edits isn't trusted just because it looks reasonable — it has to earn its way in by being blind-scored on \( D_{sel} \), the split the optimizer has never seen. Only when \( \text{score}(\tilde{s}) \) is **strictly greater** than the current skill's score does the candidate get written to disk and become the new current skill. A tie or a drop, and the entire step is discarded, leaving the previous skill unchanged.

A rejected edit isn't simply wasted. Every rejected step, along with the failure pattern it was trying to fix and how much the score dropped, gets logged into a short-lived **rejected-edit buffer**. That history is injected as context into the analyst and ranking calls for the **next** step, effectively saying: "We already tried this, and it hurt the validation score — don't propose it again." It's a small mechanism, but it stops the optimizer from repeating the same bad idea step after step.

{{< admonition tip "Engineering Safety Net: When the Optimizer Hallucinates a Target String" >}}
The optimizer's proposed edits are applied to the skill file via exact string matching, and LLMs do occasionally hallucinate a target string that doesn't literally appear in the document. When that happens, that particular edit gets marked `skip` and logged in `edit_apply_report.json`, rather than crashing the whole pipeline — the other, unaffected edits in the same batch still go through as normal.
{{< /admonition >}}

## Macro-Level Control at the End of Every Epoch

Step-by-step edits are, by design, short-sighted — each one only reacts to the most recent batch of 40 tasks. To catch longer-horizon regressions, SkillOpt adds a second, slower control loop that runs once per epoch instead of once per step.

### The Slow Update: A Protected, Epoch-Level Memory

At each epoch boundary, the system randomly samples 20 tasks from the training set and re-runs both the **old skill from the previous epoch** and the **new skill from this epoch** on that same fixed set of 20 — a controlled A/B comparison, not just a raw score comparison. Those 20 tasks then get sorted into one of four buckets: improved, regressed, still failing, or stably succeeding. The **regressed** bucket matters most, because it's the clearest signal that the recent step-level edits — even though each one individually passed its own validation gate — have, in aggregate, made something worse.

A dedicated "slow update" call (`slow_update.md`) reads this comparison and writes a macro-level strategic note, which gets inserted into a specially marked, protected block inside `best_skill.md`, fenced by `<!-- SLOW_UPDATE_START -->` / `<!-- SLOW_UPDATE_END -->` comments. For the rest of that epoch, ordinary step-level edits are forbidden from touching that block — only the epoch-boundary process can update it. This is the text-space equivalent of momentum or an exponential moving average in a traditional optimizer: it captures a longer-horizon trend that shouldn't be erased by short-term noise. Even this update isn't trusted unconditionally — it still has to pass the \( D_{sel} \) validation gate, and gets rolled back if it doesn't actually help.

### The Meta Skill: Teaching the Optimizer to Optimize

Beyond the slow update, there's a second, more unusual mechanism: the **meta skill**. This is a separate document the optimizer writes for itself, summarizing which kinds of edits tend to pass validation in this particular domain and which tend to get rejected. It never makes it into `best_skill.md`, and the target model never sees it at all — instead, it's prepended to the **optimizer's own** system prompt for the next epoch, so the "coach" gets better at proposing edits over time without the deployed skill file gaining a single extra token. It's a small but clean example of meta-learning: the optimizer is learning how to optimize in this particular environment, entirely separate from what actually gets deployed.

## Does Any of This Actually Work?

The paper's main results come from a comparison spanning six benchmarks, a range of target model sizes (from GPT‑5.5 down to the much smaller Qwen3.5‑4B), and three execution harnesses (direct chat, Codex, Claude Code) — 52 (model, benchmark, harness) combinations in total.

### Main Results Across 52 Combinations

{{< image src="table1.png" alt="Main results table: SkillOpt is best or tied-best on all 52 measured (model, benchmark, harness) cells, with consistent positive gains over the no-skill baseline." caption="Table 1 — Main results on the held-out test splits, comparing SkillOpt against the no-skill baseline and several other prompt-optimization baselines. (Source: original paper.)" >}}

SkillOpt lands best or tied-best on every one of those 52 cells, beating baselines like TextGrad, GEPA, and EvoSkill across the board. How much it gains depends a lot on the harness: roughly +23.5 points on average in plain direct chat, a comparably large +24.8 points in the tool-using Codex harness, and a substantial +19.1 points in the Claude Code harness. The Codex number is arguably the more interesting of the two — it suggests there's a lot of headroom in tool-using agents that has nothing to do with the underlying model's raw capability, and everything to do with how clearly the surrounding procedure is spelled out.

### How Cheap Is the Final Artifact?

More convincing than "we just tuned really hard on the test set" is evidence about how cheap the final artifact is, and how few edits it actually took to get there.

{{< image src="table6.png" alt="Cost and edit economy across six benchmarks: each benchmark accepts only 1 to 4 edits, while the training-token cost per point of improvement varies widely." caption="Table 6 — Cost and edit economy for the GPT‑5.5 / GPT‑5.5 training runs, showing final skill length, number of accepted edits, and training tokens spent per absolute test-point gain. (Source: original paper.)" >}}

Across all six benchmarks, the final skill file needed only **one to four accepted edits** — the validation gate rejected the vast majority of proposed edits, exactly the kind of selectivity you'd want from a cautious system like this. The token cost per point of improvement, though, varies enormously by task type:

| Task Type | Training Tokens per Point Gained |
| --- | --- |
| Short, tool-call-heavy (SpreadsheetBench, OfficeQA) | 0.6M – 1.1M |
| Long-context (SearchQA, DocVQA) | 38M – 46M |

A genuinely practical number for anyone deciding whether this approach is worth running on a given task.

### Does It Generalize? Transfer Experiments

The paper also asks a harder question: is what the model learns genuinely general, or is it just memorizing answers to the specific questions it saw during training? The transfer experiments are the strongest evidence for the former.

{{< image src="table4.png" alt="Transfer results along three axes — across models, across execution harnesses, and across benchmarks. Every transferred cell shows a positive gain over the target's own no-skill baseline." caption="Table 4 — Transfer results for the optimized skill across model scale, execution harness, and benchmark; every transferred cell beats the target's own no-skill baseline. (Source: original paper.)" >}}

{{< admonition success "The Skill Transfers Better Than It Trains" >}}
A skill trained on spreadsheet tasks inside the Codex harness, dropped into the Claude Code harness with zero further optimization, pushed that harness's score from 22.1 to 81.8 — a gain of +59.7 points, and one that actually **exceeds** the skill trained directly inside Claude Code (80.4).
{{< /admonition >}}

That strongly suggests what the optimizer extracts is closer to "how to think about spreadsheet data using Pandas" than "how to phrase instructions for this specific harness's syntax." Across all three transfer axes tested — model scale, harness, and benchmark — not a single transferred cell fell below the target's own no-skill baseline.

### Optimizer Strength: Does It Need to Be Frontier-Grade?

Finally, the paper checks how much of this depends on having a frontier-grade optimizer model in the first place.

{{< image src="table5.png" alt="Effect of optimizer strength: even swapping in a weaker, target-matched optimizer recovers most of the gains achieved with a stronger frontier optimizer." caption="Table 5 — Effect of optimizer strength, comparing a strong frontier optimizer (GPT‑5.5) against a target-matched optimizer, with everything else in the pipeline held fixed. (Source: original paper.)" >}}

Even when the "coach" is downgraded to a model matching the target's (much smaller) scale — the target model essentially optimizing itself — the combination of bounded updates and a validation gate still recovers 56% to 74% of the gains achieved with a frontier-grade optimizer. That's a genuinely practical result for teams without the budget for a frontier model during offline training: self-coaching comes at a discount, but it's far from useless.

### Is the Validation Gate Actually Picking Winners?

That selectivity can also be checked from another angle: does the checkpoint the validation split picks out actually line up with the checkpoint that performs best on the unseen test set?

{{< image src="figure3.png" alt="Performance trends across epoch checkpoints for three benchmarks: the training rollout score, the best validation score, and the test score track each other closely." caption="Figure 3 — Performance trends across training epochs for SpreadsheetBench, SearchQA, and LiveMath. (Source: original paper.)" >}}

On all three benchmarks, the peak of the validation-score line (orange) lines up closely with the peak of the test-score line (green). That's a good statistical signal: it means the validation gate is actually picking out the version that generalizes best, rather than one that happens to shine on the training batch and falls apart on different questions.

## Where the Cracks Show

A 52/52 clean sweep is easy to take at face value and stop digging, but the paper (and the discussion this piece is based on) is fairly upfront about where this design is likely to strain in a real production setting.

### The Scoring-Function Bottleneck

{{< admonition warning "Everything Depends on a Cheap, Reliable Scorer" >}}
The whole system depends entirely on the validation gate, and the validation gate depends entirely on a **cheap, reliable, automated scoring function**. For tasks with verifiable answers — code that either passes tests or doesn't, spreadsheet transformations that either hit the target or don't — that's a reasonable assumption. But for open-ended, highly subjective tasks (creative writing, open-ended customer support), building a scorer good enough to gate on honestly might require something like LLM-as-judge, which brings back exactly the cost and noise this whole pipeline was trying to avoid.
{{< /admonition >}}

### The Token Economics

The economics cut both ways, too. Deployment cost really is zero — no extra inference, no extra latency, just a static text file — but as Table 6 above shows, training even a single skill can cost anywhere from tens of millions to hundreds of millions of training tokens. That trade-off clearly favors **high-frequency, structurally stable, high-stakes-when-wrong** production agents (automated financial reporting, ops-script execution), and much less so one-off or low-frequency tasks, where that token investment probably never pays for itself.

### One File Doesn't Scale Forever

Structurally, the design deliberately crams everything into a single `best_skill.md` file to stay simple — and that's exactly where it would become a bottleneck in a large, heterogeneous deployment covering hundreds of different business scenarios. A single Markdown file hits context limits fast, and rules meant for different scenarios can start contradicting each other inside the same document. If this really needs to scale to that size, the natural next step looks like pairing SkillOpt with some form of skill-library routing — multiple, independently optimized skill files for different domains, selected at runtime by a dispatcher, instead of everything crammed into one file.

## Conclusion

What SkillOpt is really arguing for is a shift in mindset: prompt/skill iteration shouldn't be a black-box process of trial and error — it should be a real optimization pipeline, with the same discipline deep learning has long taken for granted. Batched evidence instead of single anecdotes. Bounded steps instead of unconstrained rewrites. A genuinely blind validation split instead of a gut feeling that "this edit looks helpful." And a longer-horizon mechanism to keep short-term patches from eroding lessons already learned. None of this touches the model's weights, and none of it costs anything extra once deployed — which is exactly why any team maintaining a frozen-model agent that keeps making the same mistake is worth taking a serious look at this approach.

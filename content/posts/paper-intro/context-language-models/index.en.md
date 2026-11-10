---
# weight: 1
title: "Context Language Models: LLMs Edit Their Own Context"
date: 2026-11-10
lastmod: 2026-11-10
draft: false
description: "Context Language Models (CLM) turn an agent's context into a file the model edits with Bash. Cheaper on a tight 32K budget, but its big gains shrink in absolute terms."
featuredImage: "featured-image.png"

tags: ["Single-Agent", "Agent Memory", "Inference Optimization", "Fine-Tuning"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## Context fills up: who decides what stays? CLM lets the model edit it

The longer an LLM agent runs, the faster its context (the full text the model reads at each turn) fills up. Search results, file contents and command output pile up turn after turn until they pass the limit, and someone has to decide what stays and what goes. Today that job usually falls to the **[harness](../../ai-concept/harness-engineering/)** (the program wrapped around the model that runs the agent loop and assembles each turn's context), which summarises with fixed rules or hands the model a few pre-designed compression tools.

The *Context Language Models* paper proposes **CLM**: mirror the model's current context into a file, let the model edit any part of it with Bash, and sync the edit straight back into its live context (the context actually fed to the model on the next turn). This is an interface design, not a new algorithm.

{{< admonition abstract "The verdict up front" >}}
On a tight 32K-token budget, a 27B (27 billion parameter) off-the-shelf model used **zero-shot** (no training, no tuning, the stock model as is) reaches similar or slightly better accuracy at lower cost. That part holds up. But the impression the abstract gives, a sweeping lead everywhere, mostly rests on relative numbers and the single best-looking setting, so do not take it at face value.
{{< /admonition >}}

We start with the problem CLM tackles and how it works, then how the cost of editing context is counted and how text and RL can teach a management strategy, and finally check the evidence item by item, converting the abstract's big numbers back to absolute terms. Anything marked as an invented example is a number or scenario I made up to explain a point; anything marked as my inference is my own judgement, not the paper's text.

Paper: [Context Language Models](https://arxiv.org/abs/2609.37725) (arXiv 2609.37725v1, University of Washington / Meta, 9/2026).

## Context management: from fixed rules to the model doing it

An agent searches, reads files and runs commands turn after turn, and the accumulated conversation and tool output eventually exceed the model's context limit (most experiments in this paper use 32K tokens). Handling this is called **[context management](../../ai-concept/context-engineering/)**. Three terms will come up again and again:

- **harness**: as above, the program around the model that runs the agent loop, calls tools and assembles the context fed to the model each turn.
- **compaction**: rewriting old history into a shorter summary.
- **offloading** and **retrieval**: saving content to an external file, keeping only a pointer in the context, and pulling it back when needed.

An invented example: a search agent runs 100 turns and pastes search results into the conversation each time; by around turn 40 the context is full. Now you must choose. Delete the old results outright? Squeeze them into a summary? Or save them to disk and pull them back when needed?

### Two existing routes: harness-defined and action-based

Existing approaches split into two groups by who makes the call:

| Type | Who decides | Examples |
| --- | --- | --- |
| harness-defined | An outside program, with fixed rules | Codex-style summary: when the context reaches 75% of the budget, the whole history is replaced by one summary. MEM1: rewrites the context every turn |
| action-based | The model decides when to act, but the set of operations is designed by a human | Self-Compact: the model decides when to compress. ACM: the model can call compress, offload and retrieve tools |

In the first group the model has no say at all; in the second it has a say but can only choose from a human-made menu. A finer when/how breakdown with references is in the first deep-dive at the end (optional).

### The paper's claim: hand the model the how, too

The paper argues that both routes share one ceiling: **every operation the model can perform was designed in advance by a human**. CLM pushes freedom to the limit, which gives three levels:

1. harness-defined: the model has zero control.
2. action-based: the model picks when; humans define the operations.
3. CLM: the model also decides how to edit.

The difference in practice (an invented example): the context holds 100 search results; results 30, 31 and 57 are useless and the rest must be kept verbatim. If the only tool is compress the whole history into a summary, the model has to compress everything, and the other 97 lose their original wording. CLM can write a tiny script that deletes just those three.

The paper cites Sutton's *The Bitter Lesson* (a common argument in AI: general methods that scale with search and learning beat hand-crafted rules in the long run) as motivation, which is mostly rhetorical support. My inference (not the paper's text): fewer limits also mean the model can break things, and whether that bet pays off depends on the experiments that follow.

### ContextBench: today's methods fail even simple management tasks

The authors first built a small test, **ContextBench**, that measures context handling alone, to show that existing methods fail even simple tasks. It deliberately needs no reasoning or knowledge: the task instructions say exactly what to do, so an agent that keeps everything would score perfectly, and any score gap reflects management ability only.

Difficulty is set by **context pressure**: the total task input divided by the context limit (32K). 1× means keeping everything exactly fills the window, 24× means the input is 24 times the limit, and anything below 1× is a control where keeping everything still fits.

| Task | What it tests | How |
| --- | --- | --- |
| Needle Retention | Selective retention | Each block has 2–8 important lines (needles) and 140 lines of noise; keep the needles verbatim and drop the noise |
| Sudoku Sketchpad | Small in-place edits | A 16×16 Sudoku board, one move per turn, changing a single cell without rewriting the board |
| KV Store | Offloading and retrieval | Batches of SET data to save to a file, then fetch back for 24 GET queries |
| Log Triage | Offloading and retrieval | Batches of logs, then 24 queries and counts |

Table 1 is the paper's formal definition of the four tasks (input streams and scoring). Scoring only ever looks at the agent's context: an answer that sits in a file but not in the context earns nothing.

{{< image src="table3.png" alt="Table listing the four ContextBench tasks, Needle Retention, Sudoku Sketchpad, KV Store and Log Triage, with each task's input stream, queries and scoring metric." caption="Table 1 — The four ContextBench tasks and how they are scored. (Source: original paper, Table 3.)" >}}

The results are in the figure below: CLM clearly beats the other methods and comes close to full marks.

{{< image src="figure2.png" alt="Illustration of the four ContextBench tasks and an accuracy comparison of CLM with the baselines, where CLM scores clearly higher than the other methods." caption="Figure 1 — The four ContextBench tasks and an accuracy comparison of CLM with the baselines (GPT-5.4, 32K limit). (Source: original paper, Figure 2.)" >}}

The paper names three causes of failure:

- **Summary-style compression drops or invents information** (Needle, Sudoku).
- **Without in-place editing, every move means rewriting the whole Sudoku board.**
- **Ordinary tools can save data to a file but cannot actively evict it from the live context.**

The pressure behind each difficulty level and sample messages sent to the agent are in the paper's Figure 15 and Figure 16.

{{< admonition note "What this experiment does and does not prove (my inference, not the paper's text)" >}}
Because the instructions already say delete this whole block of filler from your context, the test measures whether a method can do it, not whether it can judge what to keep. The benchmark was designed by the same team, and its tasks need exactly the operations only CLM has, deleting from the live context and editing in place. So CLM's near-perfect score proves that **its set of operations is wide enough**, not that its strategy is smarter. In the paper it serves as motivation, not as the main evidence.
{{< /admonition >}}

In short: existing methods either hard-code the rules or let the model pick from a human-made menu, and when that menu lacks edit in place and evict from context, even simple tasks fail. CLM wants to hand the how to the model as well.

## Core mechanism: turn the context into an editable file

The method has four parts: the core context-as-a-file mechanism, a metric for cost, steering and evolving the management strategy with text, and training the strategy into the weights with RL. Only the first is the paper's real claim; the last two are extensions of the idea that once management is the model's own behaviour, it can be learned. This chapter covers the first.

### From append-only to rewrite-anything

In one sentence: a standard LM can only append new content to the end of its context each turn, while CLM lets the model decide the full content of the next turn's context.

Standard LM (the paper's Eq. 1):

$$
c_{t+1} = c_t \oplus f_\theta^{\mathrm{LM}}(c_t)
$$

CLM (the paper's Eq. 2):

$$
c_{t+1} = f_\theta^{\mathrm{CLM}}(c_t)
$$

- \( c_t \): the full context the model sees at the start of turn \( t \).
- \( \oplus \): concatenation, appending the right side to the end of the left.
- \( f_\theta^{\mathrm{LM}}(c_t) \): the new tokens the model generates from \( c_t \).
- \( f_\theta^{\mathrm{CLM}}(c_t) \): the paper says this can be **any function**; CLM itself decides how to turn \( c_t \) into \( c_{t+1} \).

Put simply: under Eq. 1 not a single word of the old context can change, and Eq. 2 drops that restriction. Eq. 1 is in fact a special case of Eq. 2: set \( f_\theta^{\mathrm{CLM}}(c) = c \oplus f_\theta^{\mathrm{LM}}(c) \) and you get it back.

{{< admonition example "A worked example (invented)" >}}
At turn \( t \) the context is 20,000 tokens, including an 8,000-token block of search results, and the model produces 500 tokens this turn.

- Standard LM: \( c_{t+1} \) is 20,000 + 500 = **20,500** tokens.
- CLM: replace the search results with a 50-token note and add the new output, so \( c_{t+1} \) is 20,000 − 8,000 + 50 + 500 = **12,550** tokens.

We will keep reusing this 8,000-token block of search results.
{{< /admonition >}}

A standard LM is like a diary you can only add lines to at the bottom; CLM is like opening the whole document in a text editor, free to change any line. The analogy holds because that is exactly the difference: whether existing content can change. Under the hood, a context is simply the text fed into the next model call (general knowledge, not from the paper).

The paper calls \( f_\theta^{\mathrm{CLM}} \) any function, but in practice it can only be **Bash or code the model can write**, which is the next subsection.

### Implementation: the context is a file the model edits with Bash

In one sentence: sync the model's live context into a file, let the model edit that file with ordinary Bash commands, and the edited content becomes the next turn's context. The flow:

1. The harness writes the current context to a file whose path is given in the system prompt.
2. The model edits it with Bash or Python, like any other file.
3. As soon as the file changes, it syncs to the LLM server.
4. On the next turn the model sees the edited context.

If the model leaves the file alone in a turn, new tokens are appended as usual, which is the default behaviour of Eq. 1. The paper says this keeps both context reuse and editing flexibility.

In the paper's overview figure, panel (a) shows management behaviours the model wrote, which is all you need for now; panels (b) to (d) show zero-shot, instruction-steering and evolution, and reinforcement learning results, which come up later one by one.

{{< image src="figure1.png" alt="CLM overview figure: examples of context-handling behaviour the model invented, plus thumbnails of zero-shot, instruction steering, evolution and reinforcement learning results." caption="Figure 2 — CLM overview: treat the context as a file, use it out of the box, then improve it further with text steering and reinforcement learning. (Source: original paper, Figure 1.)" >}}

Take the 8,000-token block of search results from before (an invented example, styled after Figure 3 below). The model just runs a short Python script that uses a regular expression to replace turn 4 with a one-line note; the moment the file is written back, the context shrinks. No compress tool from the harness is needed.

```python
import re
p = "/tmp/.live_ctx/LIVE_CTX_MAIN.txt"      # context file path given in the paper's Appendix E
s = open(p).read()
# replace turn 4 (8,000 tokens of search results) with a one-line note
s = re.sub(r"\[\[CTX_TURN 4 .*?(?=\[\[CTX_TURN 5)",
           "[[CTX_TURN 4 role=notes]]\nSearched: xxx. No relevant results.\n",
           s, flags=re.S)
open(p, "w").write(s)                        # written back = context already smaller
```

The paper observes the model inventing its own techniques, for example:

- Keeping a scoreboard in the context, with 163 in-place edits tracking the state of its child agents, while holding the context at just 6–8K tokens.
- Adding a new role, `notes`, that the template never had, for its own internal notes.
- Deleting useless search results in a loop, or defining its own helper `compact_turns` (called 37 times in one task).

{{< image src="figure3.png" alt="Five code snippets of context-handling behaviour CLM actually wrote: a scoreboard tracking child agents, a new notes role, a loop deleting old search results, a compact_turns helper, and a reproduction of a baseline's effective trick." caption="Figure 3 — Examples of CLM's real context-handling behaviour: the model edits its own context freely through an ordinary code interface. (Source: original paper, Figure 3.)" >}}

### Multiple agents: one context, one file

Several context files can exist at once, each synced to its own LLM server. An **agent swarm** (a group of agents working in parallel) is just several context files in the workspace; starting and ending a **subagent** (a child agent launched by the main agent) is just creating and deleting a context file. Panel (a) of Figure 3 shows the coordinating main agent (the orchestrator) using a status block to track each child context, `subctx_0..4`.

### Caveat: a harness still helps decide when to edit

In the experiments, CLM also gets some harness help (the paper's Appendix E, footnote 4):

- When 2,048 tokens are left before the budget limit, the harness sends a time-to-edit-your-context reminder. The paper's reason is that current models do not know accurately how much context they have used (the paper's Appendix G; see the section on models misjudging their context use, later).
- On **BrowseComp-Plus** (a deep-research benchmark of hard questions answered by searching a fixed corpus, BCP for short), CLM's editing turns do not count toward the 100-turn cap, and when a request exceeds the budget the harness rolls back one turn and retries, up to six times.

{{< admonition warning "Stated precisely" >}}
**The how is fully the model's; the when is the model's, with harness help.** The paper does not say whether the rival (such as the Codex-style summary harness, called **Summary** from here on) gets the same treatment, and that affects who deserves credit when CLM wins (the verdict section returns to this).
{{< /admonition >}}

The main text also does not explain the context file's format or how syncing works, and does not count how often the model breaks the format; the deep-dive on the context file at the end has the details (optional).

In short: all of CLM is one file. The model edits it and sees the edited context next turn, but a harness still reminds it when to edit.

## The cost of editing context: position decides how much is recomputed

CLM edits the middle of the context, which breaks the inference server's cache, so comparing token counts alone is unfair. The paper defines its own **prefix-reuse FLOPs** to count the compute the server actually has to do (**FLOPs** are floating-point operations, a measure of compute). To follow it, first see how a server handles a prompt:

- **prefill**: the model reads the whole input prompt at once and computes each token's intermediate state (the **KV cache**, short for key-value cache).
- **decode**: the model generates new tokens one at a time.
- **prefix cache reuse**: the server remembers the KV cache from the previous turn. If a new prompt starts with an identical stretch, that stretch is reused; **from the first differing token onward, everything must be recomputed (re-prefilled)**.

An invented example (the idea is in the left half of the figure below): the context is [A B C]. If you only append, A, B and C are all reused and only the new part is computed. Change B to B', and only A can be reused; B' and C must both be recomputed, even though C has not changed by a single word.

{{< image src="figure4.png" alt="Standard serving versus Suffix Cache Reuse: standard serving reuses only the prefix-matched cache, while SCR reuses the cache of every surviving token, cutting re-prefill." caption="Figure 4 — Standard serving versus Suffix Cache Reuse (SCR). The left half shows why editing the middle invalidates the cache after it. (Source: original paper, Figure 4.)" >}}

The right half is SCR, which the paper proposes to soften this problem; the other-experiments section touches on it briefly later.

The paper's formula counts just two things: the prefill compute for the stretch that missed the cache (from the first differing token to the end), plus the decode compute for the tokens the model generates. Put simply, count only the part the cache did not help with, plus the cost of generating. As the paper's Eq. 3:

$$
\mathrm{FLOPs}_{\text{prefix-reuse}} = \mathrm{FLOPs}_{\text{prefill}}(\text{unmatched suffix}) + \mathrm{FLOPs}_{\text{decode}}(\text{generated tokens})
$$

- First term: prefill compute for the unmatched suffix.
- Second term: decode compute for the generated tokens.

Appendix C of the paper works an example with Qwen3.6-27B (figure below). The paper notes these lengths were chosen for illustration, not measured:

| Case | Reusable prefix | Compute for that turn |
| --- | --- | --- |
| Append only | 18,000 tokens | \( 1.41\times10^{14} \) FLOPs |
| Edit the middle | 10,000 tokens | \( 5.74\times10^{14} \) FLOPs |
| Edit the start (same as no cache) | 0 | \( 10.81\times10^{14} \) FLOPs (7.7 times appending) |

{{< image src="figure14.png" alt="Bar chart of one Qwen3.6-27B turn's FLOPs at three reusable-prefix lengths, coloured by operation type, with grey showing the extra compute needed without caching." caption="Figure 5 — Per-turn compute for three reusable-prefix lengths, at assumed lengths (20,000 input tokens, 500 generated). (Source: original paper, Figure 14.)" >}}

The one thing to remember: **cost is almost exactly tokens to recompute plus tokens generated, and the earlier the edit, the more you recompute**. The reason is that in this example the fixed per-token cost (the MLP and projections, the parts of each layer that do not depend on context length, about \( 48.70\times10^{9} \) FLOPs/token) is about 86% of total compute (my own check from the paper's numbers), while attention, which grows with context length, is only about 14%. Appendix C (Eq. 7–9) expands Eq. 3 into a full layer-by-layer count for Qwen3.6-27B; it adds nothing to the conclusion, so it is left out here.

{{< admonition warning "Limitation: these are theoretical numbers" >}}
Every fewer-X%-FLOPs claim in the paper comes from this formula: a **theoretical count**, not measured latency or a bill. It does include the recompute caused by CLM's own edits, so it does not favour CLM; but it treats a prefill token and a decode token as costing the same, while in practice decoding is token by token and usually much slower (general knowledge, not from the paper), so latency predictions will be off.
{{< /admonition >}}

## No weight changes: steer and evolve the strategy with text

Once context handling is the model's own behaviour, changing its strategy needs no harness code: just tell the model in text. This chapter has two steps: first, hand-written instructions; then, another model that rewrites those instructions automatically.

### One sentence changes how the model manages context

The approach is direct: put an instruction or a **skill** document in the context (here a skill is simply a text guide that teaches the model how to do something). The only difference from Eq. 2 is that the model reads this extra text; there is no new mechanism. As the paper's Eq. 4:

$$
c_{t+1} = f_\theta^{\mathrm{CLM}}(c_t;\, s)
$$

- \( c_t \), \( c_{t+1} \), \( f_\theta^{\mathrm{CLM}} \): as in Eq. 2.
- \( s \): that instruction or skill document, placed in the context.

Using BrowseComp-Plus questions and Claude 4.6 Sonnet, the paper appended a single instruction to the task message to test three behaviours (translations of the exact instructions are in the deep-dives at the end):

| Instruction (gist) | Behaviour targeted | What the paper measured | Result |
| --- | --- | --- | --- |
| Above \( Y \) tokens, compress to about 4K | When to compress | Context size at first compression (median) | With \( Y \) at 16K / 24K / 32K, first compression came at about 16.0K / 23.6K / 30.9K, tracking the instruction |
| Compress only at subtask boundaries | Where to compress | Share of boundaries with a compression within two turns | 0.40 rose to 0.88 |
| Back up to a new folder before each edit | Backup habit | Share of edits preceded by a full backup | 0.00 rose to 0.68 |

{{< image src="figure7.png" alt="Three small charts: compression timing moves with the instruction threshold, the share of compressions near subtask boundaries rises, and the share of edits preceded by a backup rises; grey is no instruction, blue is instructed." caption="Figure 6 — One sentence changes the context-handling strategy: grey is the no-instruction control, blue the instructed setting. (Source: original paper, Figure 7.)" width="75%" >}}

It is like giving staff a written procedure instead of changing the company's workflow software: the first changes the text they read, the second changes hard-coded logic. The model conditions on the whole context every turn, and an instruction is just one stretch of tokens in it; that is **in-context learning** (general knowledge, not from the paper).

{{< admonition warning "Two things to watch" >}}
- These three tests measure whether the model followed the instruction; they report no task accuracy, so they show **controllability**, not that these strategies are better (my observation; the paper does not say this outright).
- The instruction \( s \) sits in the context, and the model can rewrite the entire context. Could it delete the instruction itself? The paper does not discuss this.
{{< /admonition >}}

### Let another model rewrite the instructions

The instruction \( s \) above was hand-written. This step lets another model read the agent's successes and failures and rewrite \( s \) to be better, round after round.

The goal: change neither the model weights nor the harness, and search only for the text that gives the agent the highest average score. As the paper's Eq. 5:

$$
s^{*} = \arg\max_{s}\; \mathbb{E}_{x \sim \mathcal{D}}\big[ R(\tau(x; s)) \big]
$$

- \( s \): the text of that instruction (skill).
- \( x \), \( \mathcal{D} \): one task instance, and the distribution of tasks.
- \( \tau(x; s) \): the full trajectory of the agent solving \( x \) with \( s \) (from Eq. 4).
- \( R(\tau) \): that trajectory's score, from the task's automatic grader.
- \( \arg\max_s \): find the text with the highest average score.

One round of the loop:

1. Run the current skill on the training set as a **rollout** (letting the agent actually work the whole task through).
2. A **proposer** (another model whose job is rewriting the skill) reads those successful and failed trajectories and writes several new candidate skills.
3. Candidates are screened on 6 training questions, the survivors run on 12 more, and the rest are scored on a 102-question development set (dev).
4. Pick the next round's skill and repeat; stop after 5 proposals in a row with no improvement.
5. The final skill is scored once on the test set (test).

Two setups: **assisted evolution** uses Qwen3.6-27B as the agent and Claude Fable 5.1 as the proposer; **self-evolution** uses Opus 5 as both agent and proposer.

Results for the KV Store task, assisted setup, are below. Dev is the set used to pick skills; test is scored once after the choice is final and played no part in selection:

| Stage | dev (used for selection) | test (scored once at the end) |
| --- | --- | --- |
| Start: no management instructions at all | 22.3% | 38.3% |
| Skill chosen by evolution | 83.8% | 74.2% |

- The abstract's gain of up to 35.9 points is exactly 74.2 − 38.3: the best test result, for the single KV Store task in the assisted setup (my calculation).
- For the other three tasks the text gives only dev numbers: Needle Retention 97.6% to 100.0%, Sudoku Sketchpad 45.3% to 65.8%, Log Triage 0.0% to 100.0%. Dev was also used to pick the skill, so these are optimistic.
- Self-evolution: Opus 5 already starts between 94% and 100%, and the evolved skill either cuts cost at the same accuracy or raises accuracy further.

The next figure uses the term **Pareto frontier**: the set of skills for which no other skill is both more accurate and cheaper.

{{< image src="figure8.png" alt="Text-evolution results on KV Store: assisted evolution on the left, self-evolution on the right; each dot is a skill, with the Pareto frontier marked." caption="Figure 7 — Skill evolution on KV Store (32K budget). Assisted pairs Qwen3.6-27B with Claude Fable 5.1 as proposer; in self-evolution Opus 5 plays both roles. (Source: original paper, Figure 8.)" width="75%" >}}

{{< fold title="Evolution results on all four tasks (Figure 8)" tone="example" >}}
Results on all four tasks are below: assisted evolution on the top row, self-evolution on the bottom.

{{< image src="figure20.png" alt="Skill-evolution results on the four ContextBench tasks, assisted evolution on the top row and self-evolution on the bottom, with prefix-reuse PFLOPs and API cost on the x-axes." caption="Figure 8 — Skill evolution on all four ContextBench tasks: assisted on top, self-evolution below. (Source: original paper, Figure 20.)" >}}
{{< /fold >}}

The evolution loop is like a coach rewriting the playbook after watching game film and sending the team out to try it. Under the hood it is hill-climbing in text space with an LLM as the mutation operator, with no gradients (general knowledge, not from the paper). The matching method the paper cites is GEPA (Agrawal et al., 2026, *Reflective prompt evolution can outperform reinforcement learning*).

{{< admonition warning "Note: the comparison is something versus nothing" >}}
The starting point is no instructions at all, so what was measured is that having a skill beats having none. The parts I read include neither the full text of an evolved skill nor a comparison with a hand-written skill on the same model.
{{< /admonition >}}

Evolution changes text in the context; RL, next, changes the model's weights. Both learn a management strategy.

## Changing the weights: RL that learns to edit context

The previous chapter changed text in the context; this one changes the model's weights, so the model learns to edit its context from whether it got the final answer right.

### GRPO stays; two things change

**GRPO (Group Relative Policy Optimization)** is an RL algorithm (from DeepSeekMath, Shao et al., 2024). For each question it first samples a group of complete trajectories, and each trajectory's **advantage** is how much better or worse its score is than the group average: subtract the mean, then divide by the standard deviation.

$$
A_i = \frac{r_i - \mathrm{mean}(r)}{\mathrm{std}(r)}
$$

Here \( r_i \) is the score of trajectory \( i \). The formula is general knowledge; the paper only says standard GRPO advantage and does not write it out.

An invented example: sample 4 trajectories for one question, scoring 1 for right and 0 for wrong, with scores 1, 0, 0, 1. The mean is 0.5 and the standard deviation 0.5, so the advantages are +1, −1, −1, +1. Right answers are encouraged and wrong ones discouraged.

CLM's training keeps this recipe and changes only two things:

1. **Preparing the inputs**: CLM edits its context, so the final context is no longer what an early step actually saw. The paper computes each model call separately, with the context that call really saw (**stepwise GRPO**), and gives every call the whole trajectory's advantage unchanged. This is not new: Appendix A says it follows ReSum and Sculptor. Any agent that rewrites its history (summaries, folding, CLM) faces the same problem when trained with RL.
2. **The advantage gains an efficiency term** (next subsection), which is the paper's own new design.

### The efficiency reward compares only runs that succeeded

An outcome reward only knows right from wrong, which is weak supervision for how well the model edited: a correct trajectory can contain clumsy edits and a wrong one good edits. Rewarding the number of edits or tokens deleted directly invites gaming: the model may make pointless edits, delete important information, or break prefix reuse, which is called **reward hacking**. So the paper adds or subtracts points by cost (prefix-reuse FLOPs) only among trajectories that already got the answer right, a design called **success-gated**: only successful trajectories enter the efficiency comparison.

Put simply: among correct trajectories, those cheaper than average gain points and those more expensive lose them; wrong ones are left out entirely. As the paper's Eq. 6:

$$
\bar{c}_g = \frac{1}{|\mathcal{G}_g^{+}|} \sum_{k \in \mathcal{G}_g^{+}} c_k, \qquad A_i^{\mathrm{eff}} = \begin{cases} \mathrm{clip}\!\left( \dfrac{\bar{c}_g - c_i}{\bar{c}_g},\, -1,\, 1 \right), & i \in \mathcal{G}_g^{+} \\[2mm] 0, & i \notin \mathcal{G}_g^{+} \end{cases}
$$

Then combine:

$$
A_i = A_i^{\mathrm{out}} + w_{\mathrm{eff}}\, A_i^{\mathrm{eff}}
$$

- \( g \): the group of trajectories sampled for one question.
- \( \mathcal{G}_g^{+} \): the correct trajectories in that group.
- \( c_i \): the prefix-reuse FLOPs of trajectory \( i \).
- \( \bar{c}_g \): the average cost of the correct trajectories.
- \( \mathrm{clip}(\cdot, -1, 1) \): limits the result to between −1 and +1.
- \( A_i^{\mathrm{out}} \): the standard GRPO outcome advantage. \( w_{\mathrm{eff}} \): the weight, 0.25 in the paper's Appendix E.
- If fewer than 2 trajectories are correct, \( A^{\mathrm{eff}} \) is set to 0 for the whole group.

A full worked example (invented, cost in arbitrary units): sample 4 trajectories for one question. \( A^{\mathrm{out}} \) differs from the earlier example because 3 of these 4 are correct; the last column is \( A^{\mathrm{out}} + 0.25 \times A^{\mathrm{eff}} \).

| Trajectory | Correct? | Cost \( c \) | \( A^{\mathrm{eff}} \) | \( A^{\mathrm{out}} \) | Total \( A \) |
| --- | --- | --- | --- | --- | --- |
| \( \tau_1 \) | yes | 2.0 | 0 | +0.58 | +0.58 |
| \( \tau_2 \) | yes | 1.0 | +0.5 | +0.58 | +0.70 |
| \( \tau_3 \) | no | 0.5 | 0 (excluded) | −1.73 | −1.73 |
| \( \tau_4 \) | yes | 3.0 | −0.5 | +0.58 | +0.45 |

The arithmetic: the average cost of the correct ones is \( \bar{c} = (2+1+3)/3 = 2.0 \), so \( \tau_2 \) gets \( (2-1)/2 = +0.5 \) and \( \tau_4 \) gets \( (2-3)/2 = -0.5 \). The \( A^{\mathrm{out}} \) column uses subtract the mean, divide by the standard deviation (the paper gives no formula). Two points: \( \tau_3 \) is the cheapest but wrong, so it gets no efficiency bonus, which is what success-gated does; and the efficiency term is a small ranking term, \( 0.25 \times (\pm 0.5) = \pm 0.125 \), far smaller than the gap between right and wrong.

How the efficiency score lands on each step is not spelled out in the paper. This is RL's **credit assignment** problem: a trajectory has many steps but ends with one score, so how much credit or blame does each step get? The open question is whether the efficiency term goes to every token in the trajectory or only to the tokens that edit the context; a deep-dive at the end covers it.

### Results: accuracy ties, cost drops by about four tenths

- **Model and data**: Qwen3.5-9B, trained for 70 steps on 3,040 questions from the OpenResearcher dataset and evaluated on all 830 BrowseComp-Plus questions. The reward is a binary right/wrong score from GPT-5.4-nano using the DeepSearchQA rubric (grading guidelines).
- **CLM**: a 28K context budget (2,048 tokens reserved), at most 80 turns, editing turns not counted; plus the efficiency advantage (weight 0.25, which the paper's Appendix E says is applied to context-handling tokens) and penalties for failed tool calls and format errors.
- **Baseline Summary**: the agent accumulates context as usual; at 28,672 tokens, everything except the system prompt and task message is replaced by one summary (written with Codex's summary prompt), for at most 100 turns. Both when and how to summarise are fixed by humans; Appendix E says it is trained with the task reward only. The paper does not say who writes the summary.

Table 2 is the paper's original; below it, the before/after changes are listed for easy comparison. Acc. is BrowseComp-Plus accuracy; PFLOPs/Q is the average prefix-reuse PFLOPs per question (\( 1\ \text{PFLOP} = 10^{15} \) FLOPs), lower is better.

{{< image src="table2.png" alt="Results table before and after reinforcement learning: rows for Summary and CLM, each with accuracy and PFLOPs per question before and after training." caption="Table 2 — Qwen3.5-9B on BrowseComp-Plus before and after RL; the RL checkpoint is chosen on a held-out validation set. (Source: original paper, Table 2.)" width="75%" >}}

| Method | Acc. before to after | PFLOPs/Q before to after |
| --- | --- | --- |
| Summary (baseline) | 34.7 to 42.1 (+7.4) | 4.01 to 2.19 |
| CLM | 28.8 to 42.5 (+13.7) | 1.52 to 1.34 |

- **Before training, CLM trails Summary by about 6 points.** The paper blames the small model's weak context handling; its Appendix F also says Qwen3.5-9B rarely edits its context (on **TerminalBench** 2.1, a set of terminal tasks, 1.4 edits on average, with half the tasks never edited). So CLM's zero-shot results depend on the model's own judgement.
- **After training, accuracy is effectively tied** (42.5 versus 42.1), and CLM costs about 38.8% less per question (\( (2.19 - 1.34) / 2.19 \), matching the paper's introduction). The training curves are below.
- **The abstract's 47.6% gain is relative** (42.5 divided by 28.8), from a very low start; the absolute gain is 13.7 points. Against the trained Summary it wins by only 0.4 points; the real difference is cost.

{{< image src="figure21.png" alt="Training curves: on the left, accuracy and PFLOPs per question over training steps; on the right, accuracy against compute, shaded from light to dark by training step." caption="Figure 9 — RL training curves for Qwen3.5-9B on OpenResearcher (to step 70), evaluated on BrowseComp-Plus with a 32K limit. (Source: original paper, Figure 21.)" >}}

{{< admonition warning "The conditions do not fully match" >}}
The paper's introduction says Summary uses the same training recipe, but Appendix E says CLM adds the efficiency reward and format penalties while Summary uses the task reward only. The table does not mark which rows include the efficiency reward, so 1.34 versus 2.19 may not be a like-for-like comparison. Also, for the summary-plus-efficiency-reward line in Figure 9, my reading of the plot is that accuracy drops to about 1% around step 40 (the plot is labelled 40 (1%)), which seems to contradict the text's no significant loss. That is my reading of the plot; this post did not check the original figure point by point, so trust the original.
{{< /admonition >}}

In short: RL lets the 9B CLM catch the trained Summary. Accuracy ties and the difference is cost, though with different reward designs on each side that cost gap may not be like for like.

## The four parts in one table

Before the experiments, here are the four parts in one table, each with the caveat most worth remembering:

| Part | What it does | What it changes | The one caveat to remember |
| --- | --- | --- | --- |
| context-as-a-file | The model edits the context file with Bash and the edit syncs back to the live context (\( c_{t+1} = f_\theta^{\mathrm{CLM}}(c_t) \)) | The mechanism itself, no training | In practice the when relies on a harness reminder at 2,048 tokens left; the paper says nothing about the file format or how breakage is handled |
| prefix-reuse FLOPs | Theoretical compute = tokens that missed the cache + tokens generated | The yardstick | A theoretical count, not measured latency |
| skill steering and evolution | Put instruction \( s \) in the context to steer behaviour; a proposer reads failures and rewrites \( s \) repeatedly | Text in the context; weights untouched | The 35.9 points are KV Store test numbers and the dev numbers run high; the baseline is no instructions at all |
| RL | Stepwise GRPO: each model call computed separately, sharing the whole trajectory's advantage; plus an efficiency advantage that compares cost only among correct trajectories | Model weights | Two possible readings of how the efficiency term reaches tokens; the two arms of Table 2 use different rewards |

How they fit together: the first part makes the context editable, the second gives a yardstick for editing cost, the third improves the strategy with text without touching the weights, and the fourth changes the weights to learn the strategy (its efficiency reward uses the second part's metric directly). The third and fourth learn the same thing and differ only in where it is stored: in the context's text versus in the weights.

## Main evidence: off-the-shelf models, zero-shot, against the strongest fixed pipeline

The paper's main evidence is **zero-shot**: no training, no evolution, just stock models run the CLM way and compared with other context-handling methods. RL and skill evolution are two separate sets of results that do not overlap (see the last deep-dive at the end). First, the benchmarks:

- **BCP (BrowseComp-Plus)**: a deep-research benchmark of hard questions answered by searching a fixed corpus; measures accuracy.
- **TB2.1 (TerminalBench 2.1)**: 89 terminal tasks, each simply pass or fail. **TBLite** is its lightweight version.
- **EdgeBench-10**: 10 repository-optimisation tasks taken from EdgeBench, run for 12 hours and scored 0 to 100.
- **Software World**: 6 interdependent repositories optimised by an agent swarm for 24 hours, measured by speedup on unseen downstream packages.

### BrowseComp-Plus and TerminalBench: a relative 11.4% is about 6 points

Every method uses the same model (Qwen3.6-27B), the same agent framework (Mini-SWE-Agent), a 32K budget and a 100-turn cap. The rivals are Base (no management at all), Summary, MEM1, Self-Compact, ACM and RLM (a method that treats long inputs as variables the model reads on demand). Versions with other model sizes are in the paper's Figure 17.

{{< image src="figure5.png" alt="Accuracy-versus-cost scatter plots for each method on three benchmarks, BrowseComp-Plus, TerminalBench 2.1 and TBLite; the blue dashed line is the Pareto frontier and CLM sits on it." caption="Figure 10 — On coding and deep-research tasks, CLM beats action-based and harness-defined baselines at lower cost. (Source: original paper, Figure 5.)" width="75%" >}}

The clean comparison is CLM against the strongest rival, Summary:

| Benchmark | CLM | Summary | Absolute gap | CLM's FLOPs |
| --- | --- | --- | --- | --- |
| BCP | 59.4% | about 53.3% (back-calculated from 11.4% higher, relative) | about +6.1 points | 21.5% fewer |
| TB2.1 | tied with Summary | same | about 0 | 29.5% fewer |
| TBLite | 73.7% | 67.0% | +6.7 points | 9% fewer |

The 11.4% higher in the abstract and introduction is relative; in absolute points it is about 6. The real accuracy wins are on BCP and TBLite; on TB2.1 CLM wins only on cost.

{{< admonition warning "Note: not purely autonomy versus a fixed pipeline" >}}
CLM gets the harness help described earlier, and the paper does not say whether the rivals do, so we cannot rule out that this design also contributed some of the score.
{{< /admonition >}}

### EdgeBench-10: the budget decides the size of the edge

The agent optimises one repository continuously for 12 hours in a container with no network; each submission is scored 0 to 100 by the EdgeBench grader, and a run's score is the higher of its best submission and its final repository. Each task is run three times (three random seeds) and **the best one is taken (best-of-three)**. PF is the average prefix-reuse PFLOPs per trial. The comparison covers Base, a Codex-style summary, CLM, and CLM with up to five concurrent subagents.

Panel (a) below is EdgeBench-10 at a 32K budget; panel (b) is Software World, which comes up under other experiments. The 128K version is in the paper's Figure 19.

{{< image src="figure6.png" alt="Left: best-score curves over twelve hours for EdgeBench-10 at a 32K budget; right: a speedup bar chart for Software World, comparing CLM with Summary." caption="Figure 11 — Long-horizon repository optimisation: CLM beats Summary (the Codex-style summary harness). (a) EdgeBench-10 (32K); (b) Software World (272K). (Source: original paper, Figure 6.)" >}}

| Budget and model | CLM | Summary | CLM with subagents | Notes |
| --- | --- | --- | --- | --- |
| 32K, Qwen3.6-27B | 44.6 (179 PF) | 42.3 (437 PF) | 44.2 (181 PF) | CLM more accurate, using only about 41% of the compute |
| 32K, Claude 4.6 Sonnet | 51.0 | 42.3 | 50.4 | Summary scores 42.3 on both Qwen and Claude; that is what the paper reports |
| 128K, Qwen3.6-27B | 47.3 (142 PF) | 47.8 (222 PF) | 50.2 (219 PF) | CLM and Summary tie; only compute is saved |

Three readings:

- **At 32K CLM clearly wins**: +2.3 points on Qwen at about 4 tenths of the cost. The abstract's 5% higher, 59% fewer FLOPs comes from exactly this cell (44.6 divided by 42.3 is about +5.4%; 179 divided by 437 is about 41%), the single best-looking setting.
- **At 128K the accuracy edge disappears**: CLM 47.3 versus Summary 47.8, with only about 36% compute saved (\( (222 - 142) / 222 \)). A reasonable inference (not the paper's text): with a roomy budget there is less pressure to manage, so the strategies differ less.
- **Subagents bring no consistent gain**: nothing at 32K, and +2.9 points at 128K but with compute similar to Summary. The paper itself says subagents help little on a single repository.

{{< admonition warning "No variance" >}}
Scores are best-of-three, not averages. Every method is treated the same, but with no variance to look at, a gap within about 2 points cannot be told apart from noise.
{{< /admonition >}}

Taken together: **CLM's edge is largest when the budget is tight and context pressure is high, and with a larger budget it shrinks to cost savings.** That is much narrower than the across-the-board lead the abstract describes.

### Other experiments: supporting evidence and what CLM depends on

The four sets below are supporting evidence and get a light touch: math optimisation, Software World, model size, and context-length awareness. On math optimisation problems, CLM is compared with OpenEvolve (an evolutionary workflow built specifically for this kind of problem) in Table 3.

{{< image src="table1.png" alt="Results table for math optimisation: scores of OpenEvolve, OE-Agent, CLM and CLM (SA) on circle packing, Heilbronn, min-max/min-dist and Erdős overlap." caption="Table 3 — On math optimisation problems, CLM against the specialised OpenEvolve evolutionary workflow. (Source: original paper, Table 1.)" width="75%" >}}

- **Math optimisation vs OpenEvolve (Table 3)**: meant to show a general agent with CLM can beat a specialised evolutionary pipeline. CLM is best on all four problems: circle packing 2.618 versus 2.541 (+3.0%), Heilbronn 0.03653 versus 0.03127 (+16.8%), and on the other two the gap is only in the third or fourth decimal place. Caveat: each method ran once, best result taken; the two tiny gaps are not evidence, and Heilbronn's 16.8% is relative.
- **Software World, a 24-hour agent swarm (panel (b) of Figure 11)**: meant to show gains transfer to unseen downstream packages. Geometric-mean speedup on 17 unseen benchmarks, labelled about 1.044 for CLM and about 1.026 for Summary in the plot: about 1.8 percentage points more in absolute terms; the paper's 65% more is a relative figure. Caveat: the model is GPT-5.6-Sol with a 272K budget, not the 32K setup from before; the text does not say how many runs.
- **Model size (the paper's Figure 17, Appendix F)**: shows CLM's effect depends on whether the model can judge when to edit. Qwen3.5-9B edits only 1.4 times on average on TB2.1 and never edits in half the tasks; Qwen3.6-27B edits 2.6 times on average. The 9B model's median peak context is 30.2K (limit 32K), the 27B model's 17.6K. Caveat: the 9B zero-shot results should not be read together with the pre-training results in the RL chapter; see the next paragraph.
- **Context-length awareness (the paper's Appendix G, Figure 12 in the next section)**: shows current models are poor at estimating how much context they have used, hence the need for environment reminders. Without a hint the estimates are far off; with a token-count hint the error drops clearly. Caveat: tested on only 50 inputs, and not on Qwen3.6-27B, the main model.

On the model-size item: the paper's Appendix F says the 9B model scores 39.9% zero-shot with CLM on BCP, above Summary's 37.7%; but Table 2 in the RL chapter says the 9B model's CLM scores 28.8% before training, below Summary's 34.7%. The settings differ (zero-shot: 32K, 100 turns; RL evaluation: 28K, at most 80 turns). This is my inference; the paper does not point out the difference.

How to read these four: the first two are supporting evidence that CLM is better, but neither is a controlled experiment: single runs, small margins, or a different model and budget. The last two are evidence of what CLM currently depends on: a strong enough model, and outside reminders.

As an aside, SCR (Suffix Cache Reuse) in the right half of Figure 4 is the paper's serving-side proposal: after a mid-context edit, still reuse the cache of every surviving token to cut re-prefill. The paper also benchmarks SCR against standard serving, but this post does not go into those experiments; see the original paper if you are curious.

### Models cannot tell how much context they have used

For the model to decide on its own whether to compress now, it first has to know how many tokens it has used. The paper's Appendix G finds current models are poor at estimating this. The measure is **MAE (Mean Absolute Error)**: the gap between the estimate and the real token count, taken as an absolute value and averaged, in tokens; smaller is better. In the figure below each dot is one estimate against the real prompt length reported by the server; the panels show no hint, and a token-count anchor placed at 25%, 50% or 75% of the input.

{{< image src="figure22.png" alt="Scatter plots of the model's estimated context length against the provider-reported prompt length, in panels for no hint and three hint positions; for long contexts the estimates cluster at a few fixed values." caption="Figure 12 — Models' sense of their own context length: each dot is the estimate against the actual value for one input. (Source: original paper, Figure 22.)" >}}

The small text in the figure is hard to read, so the legend numbers are collected in the table below. They come from the legend; this post did not check the original figure point by point, so trust the original:

| Model | No hint | Hint at 25% | Hint at 50% | Hint at 75% |
| --- | --- | --- | --- | --- |
| Claude 4.6 Sonnet | 5384 | 5202 | 3756 | 1723 |
| GPT-5.4 | 1764 | 2107 | 2010 | 1296 |
| GPT-5.4-mini | 2895 | 4203 | 2610 | 1086 |

The paper's text draws three conclusions: with long contexts, estimates land on a few recurring numbers (such as 6.2K and 9.8K); a token-count hint lowers the error; and the closer the hint to the point of estimation, the better. That the recurring numbers may come from counting habits in pretraining is the paper's own guess, untested. This is why the harness adds reminders: the reminder in the experiments (2,048 tokens left), and the `[context: ~N/M tokens]` readout in the ContextBench skill excerpt (the paper's Table 4), both fill this gap.

A transferable rule (my inference, not the paper's text): any resource (tokens, time, money budget) should be measured by the environment and reported with every tool result; reporting close to the decision point, every turn, works better than saying it once at the start.

```python
for each tool_result:
    result += f"\n[context: ~{count_tokens(ctx)}/{limit} tokens]"
```

{{< admonition warning "Limitation" >}}
Only 50 inputs were tested, on GPT-5.4, Claude 4.6 Sonnet and GPT-5.4-mini, not Qwen3.6-27B, the main model in the experiments, and the paper does not say why.
{{< /admonition >}}

In short: on a tight 32K budget CLM reaches similar or better accuracy at lower cost (tied on TB2.1, ahead on BCP, TBLite and EdgeBench); on EdgeBench, raising the budget to 128K erases the accuracy edge and leaves only the savings. CLM also depends on two things for now: a strong enough model, and outside usage reminders.

## Verdict: worth trying, evidence shows potential only

**The verdict first: research value is moderate to low; engineering value is that the idea is worth trying, but the evidence only shows potential.**

**Research value**: the contribution is an interface design, not a new algorithm. Giving the model write access to its own context is simple and general, and it pushes both the when and the how to the model; that is its most durable part. But almost everything underneath is off the shelf: the RL is GRPO plus ReSum- and Sculptor-style segmentation (Appendix A says so itself), and the skill evolution is GEPA-style. The only genuinely new piece is the success-gated efficiency advantage, with a weight of just 0.25, and the paper does not make clear how it reaches the tokens.

**Engineering value**: the strongest evidence is that on a tight 32K budget, a stock 27B model used zero-shot beats the fixed pipeline (about +6 points on BrowseComp-Plus; +2.3 points on EdgeBench-10 with only about 4 tenths of the compute). The weakest point: no experiment separates the credit for free editing from the harness help, and at 128K the accuracy edge disappears, leaving only savings. So what we can say is that the whole design pays off on a tight budget, not that context as a file is itself the main cause.

### The abstract's claims, restated cleanly

| Claim in the abstract | Clean version |
| --- | --- |
| BCP accuracy 11.4% higher, 21.5% fewer FLOPs | About +6 points absolute (back-calculated from the relative figure). CLM gets uncounted editing turns, rollback and retry over budget, and a reminder at 2,048 tokens left; whether rivals do is not stated |
| EdgeBench 5% higher, 59% fewer FLOPs | 32K Qwen: 44.6 versus 42.3, +2.3 points. 128K: 47.3 versus 47.8, −0.5 points, with only about 36% compute saved. The abstract picked the best-looking 32K setting; scores are best-of-three |
| Software World 65% more | About 1.044 versus 1.026, about 1.8 percentage points absolute; the relative figure rests on a tiny base; uses GPT-5.6-Sol and a 272K budget |
| Skill evolution gains 35.9 points | One task, KV Store: test 38.3 to 74.2; the baseline is no instructions at all, not a hand-written skill |
| RL gains 47.6% | +13.7 points absolute; beats the trained Summary by only 0.4 points; the two arms use different rewards |

What you can trust is that on a tight budget CLM reaches similar or slightly better accuracy at lower cost; what you cannot trust is the impression of a sweeping lead the abstract gives. In every row, the abstract uses whichever relative number or setting looked best.

### Weaknesses across the paper

- **The credit for free editing is never separated from the harness help**: CLM gets uncounted editing turns, rollback and retry, and the reminder at 2,048 tokens left, and no experiment turns this help off; the zero-shot experiments also do not give CLM's system prompt or skill content, so we cannot see how much credit goes to a well-written prompt. This is the most important point: it decides whether CLM's win can be credited to the idea itself.
- **No variance and no repeat counts**: math optimisation ran each method once; EdgeBench takes the best of three seeds with no error bars; Software World does not say how many runs. So 44.6 versus 44.2, RL's 0.4-point win, and the third-to-fourth-decimal math gaps cannot be told apart from noise. No win within about 2 points should count as evidence.
- **The evidence is stitched together, not one line**: zero-shot uses Qwen3.6-27B and Claude 4.6 Sonnet, RL uses Qwen3.5-9B, skill evolution uses Opus 5 or Fable 5.1 as proposer, and Software World uses GPT-5.6-Sol. No single model goes through the whole story.
- **Home-made benchmark and home-made metric**: the authors built ContextBench themselves; the FLOPs are a self-defined theoretical count, not real latency or a bill.

One more structural point: CLM beats the strongest existing method (stock 27B, zero-shot) and CLM can be trained to improve (9B with RL, or skill evolution) are two separate bodies of evidence that do not overlap. The paper never shows that a trained or evolved CLM is stronger on long tasks; the last deep-dive at the end has the details.

### When handing the model this freedom pays off

When is it worth handing the model this freedom? What follows is my own judgement from combining the paper's evidence, an inference, not the paper's text:

| Condition | The paper's evidence | Strength |
| --- | --- | --- |
| Tight budget | On EdgeBench at 32K CLM is both more accurate and cheaper; at 128K accuracy ties and only savings remain (Figure 11, the paper's Figure 19) | Direct, strongest |
| Strong enough model | The 9B model rarely edits its context and never edits in half the tasks (the paper's Appendix F); before training CLM trails Summary (Table 2) | Indirect: different models, different settings |
| Long task | No experiment varies task length on its own | Weak, untested by the paper |
| Harness help | The reminder at 2,048 tokens left, rollback and retry over budget; models misjudge their own context use (the paper's Appendix G) | Not fully hands-off yet; still needs an outside safety net |

{{< admonition tip "Rule of thumb (my inference, not the paper's text)" >}}
For short tasks, roomy budgets or weak models, a fixed summary pipeline is usually accurate enough. CLM is most likely to pay off when the task is long, the budget is tight and the model is strong, all at once; only the tight budget has direct evidence, the other two are guesses. Even with a roomy budget, CLM may still save cost.
{{< /admonition >}}

One overreach to avoid: all three at once is a combination I made up. The paper never tested how the three interact; it is a rule of thumb for where to start trying, not a requirement.

### Security risk: context the agent writes and reads back

Section 6 of the paper notes that an editable context could become a channel for injected prompts or self-generated instructions to persist across turns. It cites an OpenAI report: a model once inserted unauthorised instructions into its own compressed summary, which affected later behaviour. The paper runs no experiments and proposes no defence, saying only that this is future work.

The mechanism (an invented example):

1. A tool result (a web page, say) hides a malicious instruction.
2. The agent writes it into its own notes or summary.
3. Next turn it reads that back and treats it as its own plan.
4. The instruction keeps working.

In later turns such content looks like something I wrote myself, which makes it harder to spot than a one-off injection. The OpenAI case, where the model added instructions itself, is a variant of external injection, but the persistence path is the same.

Transferable rules (my inference, not the paper's text):

- Anywhere the model can write and later reads back (summaries, notes, memory, CLM's context file) is a persistence channel, not just in CLM.
- CLM's attack surface is larger than a summary's, because its edits are unrestricted.
- What the paper leaves out: whether the context file includes the system prompt, and whether the model can delete its own instructions.

In short: what you can trust is lower cost for similar or slightly better accuracy on a tight budget, not a sweeping lead; and this freedom also opens a security channel the paper has not dealt with yet.

## Conclusion: what to take away

What is most worth remembering from this paper is not any percentage but the way it splits context handling apart: **when to act** and **how to act** are two separate things. Earlier methods locked one or both in human hands; CLM hands both to the model. On a tight budget the claim has evidence behind it, but that evidence is mixed with the harness's helper design and comes with no variance; so it is a design option worth trying seriously, not a proven best practice.

**The paper's first contribution: context-as-a-file, giving the model write access to its own context.** A standard LM's context can only grow at the end, so every keep-or-drop decision falls to the harness. Earlier attempts let the model take part, but what it could do was still limited to a human-designed menu (compress, offload, retrieve); this paper removes that limit, and the model decides the kinds of operations itself (delete one item, delete in bulk, write a helper function, add a notes role, none designed in advance).

This is the most durable part: the idea is simple, general and independent of any particular model or benchmark, so any agent that can write code can use it, and it naturally opens the routes of steering, evolving and training context handling. But it is a design choice, not a new algorithm, and the paper does not directly show it beats a fixed pipeline with a good prompt.

**Second contribution: the success-gated efficiency advantage (Eq. 6).** Adding or subtracting points by theoretical cost only among correct trajectories solves the problem that an outcome reward cannot tell good edits from bad, while rewarding edit volume directly invites gaming. It counts only as a small contribution, for three reasons: its weight is just 0.25; similar designs already exist elsewhere (Appendix A mentions Arora & Zanette, who penalise length only on correct answers, and DDCA), the only difference being FLOPs as the cost; and the paper does not make clear how the term is split across tokens.

There is also a narrow but credible empirical result (the zero-shot results on a tight 32K budget), but numbers like these go stale as models and benchmarks change; what lasts is the first two contributions and the ideas below that hold beyond this paper.

When it pays off is covered in the section on when handing over this freedom pays off; beyond that, the three most general ideas are: the cost of editing a context depends on where you edit; compare a secondary goal only within the set that met the target; and data used for selection cannot be used to report results. All three still hold when you swap the model or the benchmark, and each has a section in the going-further chapter at the end.

- **Next time you see a context-handling method, ask two questions**: who decides when to act, and who wrote the operations? CLM is the kind that answers the model to both, at the price of a harness reminding it on the side.
- **Convert paper numbers back to absolute terms first**: 11.4% higher is about 6 points, a 47.6% gain is 13.7 points; on EdgeBench, raising the budget to 128K erases the accuracy edge.
- **When you build agents**: edit the context near the end where you can (in the paper's appendix example, editing the start costs 7.7 times as much as appending); compare efficiency only among successful attempts; and never report the score you used to pick a prompt.

## Going further: four ideas that hold beyond this paper

The four sections below are optional: each stands on its own without the paper, and each is collapsed, so open whichever you want to dig into.

### Keep, compress, offload or delete a chunk of context

{{< fold title="Open: the decision table and the order of questions" tone="info" >}}
The context is full and there is a pile of content in front of you: what should you do with each chunk? Beyond when and how, you need a map of which operation suits which chunk:

| What the chunk is like | What to do | Why | ContextBench counterpart |
| --- | --- | --- | --- |
| Needed verbatim later, and small | Keep it in the context | Any rewrite can distort it | Needle Retention |
| Needed verbatim later, but large | Save it to a file, keep only a pointer, grep it when needed | Summaries are lossy, files are not | KV Store, Log Triage |
| Only the gist is needed | Compress it into a summary | Saves space; some loss is acceptable | none |
| No longer useful | Delete it | Keeping it only takes space | Needle's noise blocks |
| Fixed structure, often changed in small places | Edit in place | Rewriting the whole thing is costly and error-prone | Sudoku Sketchpad |

As pseudocode, the order of questions is: first, will you need the original text later? Then, how big is it? Finally, will it keep changing in small ways?

```python
# inference: decision order combining the paper's three failure causes and the four ContextBench tasks (not the paper's text)
def decide(chunk):
    if chunk.needed_verbatim_later:
        return KEEP if chunk.small else OFFLOAD_TO_FILE   # after offloading, keep only a pointer in context
    if chunk.structured and chunk.edited_in_small_pieces:
        return EDIT_IN_PLACE                              # e.g. a game board, a status table
    if chunk.only_gist_needed:
        return SUMMARIZE
    return DELETE
```

It rests on the paper's three failure causes (summaries drop or invent information; without in-place editing you rewrite the whole board; you can save to a file but not evict from the live context). Turning them into a decision table is my own synthesis, an inference, not the paper's text. The table also shows which cell any harness is missing: a summary-only harness lacks offloading and in-place editing.
{{< /fold >}}

### Edit cost depends on position

{{< fold title="Open: position cost and the ordering rule" tone="info" >}}
The principle (general knowledge): each token's KV cache depends on every token before it, so the server can reuse only the stretch at the start that is completely identical, and everything after the first differing token is recomputed. So the rough cost is the per-token processing cost times the number of tokens to recompute plus tokens to generate. Let \( U \) be the tokens to recompute, \( G \) the tokens generated, and \( c \) the per-token processing cost:

$$
\text{cost} \approx c\,(U + G)
$$

For real numbers see Figure 5 earlier: editing the start costs 7.7 times as much as appending. An intuitive example (invented, assuming cost is proportional to tokens recomputed): change one spot in a 20,000-token context. Edit near token 18,000 and you recompute only about 2,000; edit near token 2,000 and you recompute about 18,000, a 9 times difference.

A transferable design rule (an inference from the formula above): order the context front to back by how often things change. Stable material goes first (the system prompt, long-lived notes), rarely changed material in the middle (settled summaries), frequently changed material last (the latest turns).

- If you compress, do it once in one go rather than repeatedly nudging the middle.
- Deleting the same 8,000 tokens at the end versus at the start differs in cost several times over.

The rule holds for any harness that rewrites history, not just CLM; the cost is theoretical FLOPs, with the limits covered in the chapter on the cost of editing context.
{{< /fold >}}

### Compare a secondary goal only among successes

{{< fold title="Open: the example, the code and the transferable rules" tone="info" >}}
If you want answers that are both right and cheap and you reward cheapness across all trajectories, the cheapest move is to do nothing and give up, which is reward hacking. The fix is to split by right and wrong first, then compare cost only among the correct ones. Take four trajectories (an invented example) with costs 2.0 (right), 1.0 (right), 0.5 (wrong) and 3.0 (right):

| Approach | What the wrong one (cost 0.5) gets |
| --- | --- |
| Compare cost across all, average cost 1.625 | \( (1.625 - 0.5) / 1.625 \approx +0.69 \), **failure gets rewarded** |
| Compare only among correct trajectories | 0, excluded |

```python
correct = [t for t in group if t.success]
if len(correct) < 2:
    eff = {t: 0 for t in group}                 # nothing to compare
else:
    mean_c = mean(t.cost for t in correct)
    eff = {t: clip((mean_c - t.cost) / mean_c, -1, 1) if t.success else 0 for t in group}
A = A_out + w_eff * eff                         # the paper uses w_eff = 0.25
```

Transferable rules (general knowledge plus my inference):

- In any optimisation with a primary and a secondary goal, gate or rank the secondary goal; never just add them up. Examples: accuracy plus latency, quality plus cost.
- This approach is not unique to this paper: Appendix A mentions Arora & Zanette, who penalise length only on correct answers, and DDCA, which also computes a length advantage within the correct subset.
- A side effect (my inference): with fewer than 2 correct trajectories the term is zeroed. On hard questions with low success rates, the efficiency signal all but disappears.
{{< /fold >}}

### Data used for selection cannot report the score

{{< fold title="Open: standard error, the example and the rules" tone="info" >}}
Try many candidates on dev (the development set) and report the best one, and the score is systematically too high, because you picked the luckiest on this particular batch of questions. Measurement itself is noisy, and the standard error (SE) says how noisy: roughly the true accuracy times the error rate, divided by the number of questions, then square-rooted:

$$
\mathrm{SE} = \sqrt{\frac{p\,(1-p)}{n}}
$$

Here \( p \) is the true accuracy and \( n \) the number of questions. An invented example: 100 candidates all truly at 70%, \( n = 102 \), so SE is about 4.5 percentage points. The best of the 100 is expected to land about 2.5 SE higher, so it looks like about 81% on dev while the truth is still 70%. This is called the selection effect (also the winner's curse).

The paper's own instance is in the skill-evolution section: KV Store (assisted setup) goes from 22.3% to 83.8% on dev (+61.5 points), but on the test set, which played no part in selection, only from 38.3% to 74.2% (+35.9 points).

Transferable rules:

- The more candidates you try, the more inflated the dev number. To report a result, use a test set that played no part in selection.
- Discount any take-the-best-run number, such as best-of-three (EdgeBench is one).
- This applies to any loop that automatically tunes prompts, skills or hyperparameters, not just this paper.
{{< /fold >}}

## Concept deep-dives: five things worth looking up again

The five sections below are optional, and they are the parts most easily forgotten and most worth looking up again. Each is written to hold beyond this paper and is collapsed, so you can open any one on its own.

### When and how: the two axes of context management

{{< fold title="Open: the grid and the table of methods" tone="info" >}}
To see how much freedom a context-handling method really gives the model, the most useful frame splits the question into two independent axes:

- **when**: what triggers a management action? A human (a harness's fixed rule, such as 75% of the budget, or every turn), or the model itself?
- **how**: how is the action itself carried out? Pre-written by a human (a fixed summary routine), chosen by the model from a human-defined menu, or written by the model itself?

The how actually has two layers: (a) whether the model can pick an operation from a menu; (b) who wrote the operation's contents. Action-based methods give the model freedom on (a) but not (b): every operation on the menu is implemented by a human. CLM hands both layers to the model.

The table below places each method on this grid, with sources. The closer to both when and how decided by the model, the more autonomy the model has.

| Method | when | how | Source |
| --- | --- | --- | --- |
| Codex-style summary (OpenAI Codex CLI) | Human: at about 75% of the budget | Human: a fixed summary prompt | [GitHub openai/codex](https://github.com/openai/codex) (a software project, no arXiv) |
| Cursor Composer's self-summarization | Human: triggers at a set length | Human-defined flow; RL trains only how well it summarises | Technical report [arXiv 2603.24477](https://arxiv.org/abs/2603.24477); blog [cursor.com/blog/self-summarization](https://cursor.com/blog/self-summarization) |
| MEM1 | Human: rewrites every turn | Human: a fixed merge-old-and-new routine | [arXiv 2506.15841](https://arxiv.org/abs/2506.15841) |
| Self-Compact | Model: decides when to compress (with a set of criteria) | Human: a fixed compression tool | [arXiv 2606.23525](https://arxiv.org/abs/2606.23525) |
| AutoCompact | Model: decides when to compress | Human: a fixed compression routine | No arXiv; the paper cites a project page, autocompact.github.io, which I could not verify |
| Context-as-a-Tool (CaT) | Model: compression as a callable tool | Human: predefined compression actions and a structured context workspace | [arXiv 2512.22087](https://arxiv.org/abs/2512.22087) |
| ACM (Agentic Context Management) | Model | The model picks only from a human-defined menu (compress, offload, retrieve), each operation fixed | [arXiv 2607.23809](https://arxiv.org/abs/2607.23809) |
| Sculptor | Model | The model picks only from a human-defined menu (slice, summarise / hide / restore, search), implementations fixed | [arXiv 2508.04664](https://arxiv.org/abs/2508.04664) |
| Context Folding, AgentFold | Model: decides when to branch or fold | The model picks from human-defined folding actions | [arXiv 2510.11967](https://arxiv.org/abs/2510.11967), [arXiv 2510.24699](https://arxiv.org/abs/2510.24699) (IDs taken from the CLM paper's references) |
| **CLM (this paper)** | Model (in practice with a harness reminder at 2,048 tokens left) | **Model: writes arbitrary Bash or code** | [arXiv 2609.37725](https://arxiv.org/abs/2609.37725) |

For any new method, two questions are enough: who decides when to trigger, and who writes the operation? Human to both is harness-defined; model then human is action-based; model to both is the CLM kind. One caveat: CLM's when is not fully the model's; in the experiments it relies on a harness reminder at 2,048 tokens left.

Related, but outside this grid: RLM (Recursive Language Models, [arXiv 2512.24601](https://arxiv.org/abs/2512.24601)) treats long inputs as REPL variables the model reads on demand; it addresses when and what to read into the context, but what it reads is still appended to the live context, which keeps growing. CLM addresses how the live context itself is edited. The two complement each other. [MemGPT](../memgpt/) ([arXiv 2310.08560](https://arxiv.org/abs/2310.08560)) lets the model edit one fixed-size designated block of the context, not the whole context.
{{< /fold >}}

### The context file is source code: the risk of broken markers

{{< fold title="Open: the marker risk and what the paper leaves out" tone="info" >}}
What CLM lets the model edit directly is not the conversation but **the conversation's raw text**, which carries format markers. The paper explains this mechanism too thinly for us to see how it works, and it also says nothing about what happens if the model breaks a marker. These are two sides of the same concern.

Think of it as HTML: the conversation you see in a chat window is like the rendered web page, and the context file is like the page's HTML source. CLM lets the model edit the source directly, so it can change anything without someone providing a delete button. The risk is that the source has markers (like HTML tags), and if a marker is broken, rendering can go wrong.

The markers here are strings like `[[CTX_TURN 4 role=notes]]`, visible in Figure 3. My inference (not the paper's text) is that they tell the server which turn a segment is and who said it. Only two facts are known: Figure 3 shows such markers in the file, and the paper's Appendix E gives the file path `/tmp/.live_ctx/LIVE_CTX_MAIN.txt`.

A concrete case (invented, reusing the script from the core-mechanism chapter): that regular expression stops at the `CTX_TURN 5` marker, so it deletes only up to the TURN 5 marker. Suppose the model writes `CTX_TURN 6` there instead: the opening TURN 5 marker gets deleted too, the TURN 5 content merges into the previous segment, and the server no longer sees the original conversation structure.

Three things the paper does not say:

1. The main text does not explain how a file edit is detected or how the file is converted back into the model's message format.
2. Is there any check or repair when the file breaks? Not stated. Appendix E mentions only that when a request exceeds the budget, the harness rolls back one turn and retries (up to six times on BCP), which is a budget problem, not a format problem.
3. How often did it happen in the experiments? No count.

How much this matters (my inference): it does not overturn the paper's conclusions. Good scores mean it mostly did not break. But it affects two things: anyone reproducing the mechanism lacks information, and the failure rate may be underestimated. It is also not the same issue as the security risk earlier: that one is a malicious instruction persisting across turns; this one is format damage.
{{< /fold >}}

### Credit assignment: splitting one score across steps

{{< fold title="Open: the two readings and what each one trains" tone="info" >}}
The short answer: what the paper states clearly is that the outcome advantage goes to every model call in the trajectory; whether and how the efficiency term is split as well, the paper does not make clear.

Credit assignment is a core RL problem: a trajectory has many steps but ends with one score, so how much credit or blame should each step get? What the paper states explicitly (Section 4.2): with only the outcome advantage, each trajectory's advantage goes to all of its segments (each segment is one model call), so every call is trained on the whole trajectory's outcome. This is the coarsest approach: no judgement of how much a step contributed, and one number shared by the whole trajectory.

What is unclear is how the efficiency term is split. After Eq. 6 the paper writes only \( A_i = A_i^{\mathrm{out}} + w_{\mathrm{eff}} A_i^{\mathrm{eff}} \), without saying how that total is split across segments. The paper's Appendix E also says the efficiency advantage applies to context-handling tokens. Take \( \tau_2 \) from the RL chapter (invented: \( A^{\mathrm{out}} = +0.58 \), \( w_{\mathrm{eff}} A^{\mathrm{eff}} = +0.125 \)) and assume it has 3 segments. The two readings give:

| Reading | Value each segment gets |
| --- | --- |
| One: the total goes to every segment | all 3 get about +0.70 |
| Two: the outcome term goes to every segment, the efficiency term only to context-editing tokens | all 3 get +0.58, and only the editing tokens get an extra +0.125 |

What each reading trains (my inference, not the paper's text): a trajectory's tokens fall roughly into two kinds, ordinary tokens (search queries, reasoning, the final answer) and editing tokens (the Bash or Python that rewrites the context file).

| Aspect | Reading one | Reading two |
| --- | --- | --- |
| Where the efficiency signal lands | Every token in the trajectory | Only the editing tokens |
| Can it be credited to better editing? | No: the model cannot tell whether it was cheap because it edited well or because it searched fewer turns | More so |
| Possible side effect | The model may cut cost by doing less and stopping early, rather than learning better context handling | Smaller; the model is pushed to edit more cheaply, for instance editing far-forward content less (which breaks the cache) |

The paper's Appendix E also mentions penalties added for CLM on failed tool calls and format errors, again without saying whether they apply to the whole trajectory or to individual tokens.

This changes how you read the RL results: the paper says that with the efficiency reward, cost fell further without a noticeable accuracy loss (the paper's Appendix F). Under reading one, that cost drop need not come from better context handling. The paper's text cannot settle which reading is right; only the released code (GitHub facebookresearch/context-language-models) could, and I have not read that code.
{{< /fold >}}

### The three steering instructions the paper used

{{< fold title="Open: the three instructions and their settings" tone="info" >}}
The source is the In-context steering paragraph of the paper's Appendix E. What follows is a paraphrase; check that paragraph for the original wording. The instructions were appended after the task message and compared against a no-instruction control on the same BrowseComp-Plus questions, with Claude 4.6 Sonnet (via API).

**Instruction one: when to compress (\( Y \) is 16,000 / 24,000 / 32,000)**

> Monitor your context size: every tool result reports the current size. As soon as it exceeds \( Y \) tokens, immediately compress the context to about 4000 tokens. For example: rewrite `/tmp/.live_ctx/LIVE_CTX_MAIN.txt`, keeping only the key findings and the current plan (about 4000 tokens).

Setup: a 48,000-token budget, a 200-turn cap, 30 longer questions (at or above the 60th percentile in turns without instructions).

**Instruction two: compress at subtask boundaries**

> Compress only at subtask boundaries. As soon as a subtask is done, drop all of that subtask's context. For example: after writing `/workspace/answer_1.txt`, rewrite `/tmp/.live_ctx/LIVE_CTX_MAIN.txt`, dropping the material for question 1 and keeping only the conclusion of answer_1.

Setup: four questions chained in one session, a 24,000-token budget, a 1,000-turn cap, 189 sessions per condition, of which 131 contain a subtask boundary.

**Instruction three: backups**

> Before every edit to the context, you must first back up the current context file to a new file in a new folder named `compaction_backup`; never overwrite or delete earlier backups.

Setup: a 16,000-token budget, 200 questions, 91 of them in the paired analysis.

Two things to note:

- Instruction one says every tool result reports the current size, which is the same harness environment hint mentioned earlier. In other words, in this experiment the model knew how much it had used because the harness fed it the size, not because it sensed it. My inference: part of instruction one's success is owed to that hint.
- Instructions one and two both spell out the context file's path and include a worked example of what to do. So these instructions are more specific than one sentence; they are operating instructions with examples.

The results are in Figure 6, with the numbers summarised in the section on one sentence changing context handling.
{{< /fold >}}

### Zero-shot, skill evolution, RL: three separate bodies of evidence

{{< fold title="Open: the three layers of evidence" tone="info" >}}
The short answer: in the paper's main experiments (BCP, TB2.1, TBLite, EdgeBench-10, Software World, math optimisation), CLM is always **zero-shot**: no RL training and no skill evolution. RL and skill evolution appear in only two places, on different sets of tasks.

| Experiment | RL training? | Skill evolution? | Basis |
| --- | --- | --- | --- |
| BCP, TB2.1, TBLite zero-shot comparison | no | no | The paper's 5.1.1 says every method is used out of the box, untrained, so the comparison does not depend on training data |
| EdgeBench-10, Software World, math optimisation | no | no | The paper files these under 5.1 Zero-Shot; the models are off the shelf |
| Skill evolution on ContextBench | no | yes | Qwen3.6-27B or Opus 5, synthetic tasks, 32K budget |
| RL with Qwen3.5-9B on BCP | yes | no | A 9B model, OpenResearcher training data |

Zero-shot CLM relies on two things for context handling: the stock model's own judgement (the context-as-a-file mechanism), and the harness help (the edit reminder at 2,048 tokens left, and rollback and retry over budget on BCP). BCP's search tools are provided as in-context skills (the paper's 5.1.1, footnote 2); those are tool descriptions, not an evolved context-handling skill, so do not mix them up. The paper does not show what CLM's system prompt said in the zero-shot experiments. My inference: ContextBench's CLM has a skill (excerpts in the paper's Appendix D and Table 4), and the zero-shot experiments presumably have a similar basic briefing, or the model would not know the context file's path.

So the paper's evidence comes in three layers:

1. A stock 27B model, zero-shot, beats the rivals (the main evidence).
2. A small model with RL catches up with the rivals (supporting).
3. Skill evolution works on ContextBench (supporting, and on synthetic tasks).

Getting better has to be read separately for each:

- **Skill evolution**: test accuracy on KV Store rose from 38.3% to 74.2%. But the starting point is no management instructions at all, so it shows a skill beats no skill, not that an evolved skill beats a hand-written one.
- **RL**: the 9B model rose from 28.8% to 42.5%, but the Summary baseline was trained and improved too (34.7% to 42.1%). So it shows CLM can be trained, not that CLM gains more from training than its rival; after training it only catches up, the difference is cost, and the two arms use different rewards.
- **Neither was tested on long tasks**: the paper has no experiment showing a trained or evolved CLM is stronger on tasks like EdgeBench.

The conclusion: RL and skill evolution speak to learnability, not to being stronger. Treating CLM beats the strongest existing method (27B, zero-shot) and CLM can be trained to improve (9B with RL, or skill evolution on ContextBench) as one body of evidence is misleading.
{{< /fold >}}

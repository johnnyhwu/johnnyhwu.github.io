---
# weight: 1
title: "SKILL.state: Agents Keep State, Not History"
date: 2026-11-23
lastmod: 2026-11-23
draft: false
description: "Long-running agents paste their history into every prompt, so cost grows with the square of the steps. SKILL.state keeps one state: 41x fewer tokens, shakier accuracy."
featuredImage: "featured-image.png"

tags: ["Agent Memory", "Single-Agent", "Inference Optimization"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## Agents get pricier the longer they run: swap history for state

Give an AI agent a warehouse job that takes 200 steps: customers order, stock arrives, items move between shelves, one event after another. Almost every agent today runs this the same way. At each step it pastes every earlier observation and thought back into the prompt and rereads the whole thing. The longer it runs, the longer the prompt, and the cost and wait time balloon. Over the same 200 steps, the setup that keeps the full conversation history burns 5,041,164 tokens. Keeping only a record of what the warehouse looks like right now uses 122,384. That is 41 times fewer.

On accuracy, the state-only setup did come out ahead: 0.94 versus 0.88 for full history. But that edge is not reliable. In a software-repository environment, where branches, commits and PRs all depend on each other, the state-only setup even lost to the history-keeping baseline on 25-step tasks. **The evidence that this saves money is strong; the evidence that it is more accurate is shakier**, and it does not hold everywhere.

The approach comes from SKILL.state: Scalable Long-Horizon Agent Skills, a paper from Google and Purdue. At every step the model sees only the task instructions, a structured state describing what the world looks like now (in the warehouse, what sits on each shelf), and the newest observation. Its reasoning is thrown away after use; only its conclusion about how the state should change is kept. The prompt size then no longer depends on how many steps have passed, and total cost grows linearly with the number of steps instead of with its square.

Paper: [SKILL.state: Scalable Long-Horizon Agent Skills](https://arxiv.org/abs/2608.26263) (Google, Purdue)

## Two problems with conversational execution: prompts grow and stale facts linger

The usual way to run an agent today is called ReAct: at each step the model writes some reasoning and picks an action, the environment returns an observation, and all three are appended to the prompt to be read again next step. Everything the model can see in one call is its [context](../../ai-concept/context-engineering/). This conversational style of execution has two concrete problems. First, the prompt grows with every step, and token cost and latency grow with it: the longer the run, the more the context holds.

Second, old information lingers, and the model has to work out what is still valid. Early observations and past reasoning stay in the context long after they expire. At every step the model has to decide again whether an old line still counts, which is extra work and easy to get wrong: if something outside has already changed the world but the old observation is still sitting there, the model may well act on the stale version.

For example, early in the context it says "shelf_42 holds item_12". Later someone moves the item, and that appears only in one observation much further down. Next time the model looks for item_12, it has to decide which line to believe.

Adding a [memory system](../mem0/) (summaries, retrieval) does not really fix either problem. These methods still repackage the past text history and feed it back, so the model's decisions still rest on reconstructing what happened rather than reading what the world looks like now. The execution logic is unchanged; only the way history gets compressed is different.

The question the paper actually goes after: can the current state of the world become something separate from the text history, something the model reads directly instead of rebuilding it from a pile of text every time?

## How SKILL.state works: three inputs per step

The paper's appendix uses a warehouse scenario, and it runs through this whole section: an agent manages the shelves of a warehouse, and its only actions are Store, Ship, Move and Wait.

### Three inputs, three outputs, and a merge to update state

Each step feeds the model the same three things. \( P \) is the fixed task instruction (the procedural specification), such as "You are a warehouse manager; available actions are Store/Ship/Move/Wait"; it never changes during the run. \( \Sigma_t \) is the **structured execution state** at step \( t \), a JSON dictionary recording what the world looks like now, such as "shelf_42 holds item_12". \( O_t \) is the newest observation from the environment, such as "Customer ordered item_12". The paper writes the three together as \( A_t \):

$$
A_t = (P,\ \Sigma_t,\ O_t)
$$

Figure 1 puts the two approaches side by side. On the left, the traditional prompt holds the instructions and newest observation plus a growing stack of conversation history, past observations and past reasoning. On the right, the SKILL.state prompt has only the instructions, the state and the newest observation. The bar charts at the bottom are the point: the context on the left keeps growing, while the one on the right stays under a cap.

{{< image src="figure1.png" alt="Side-by-side architecture diagram. Left, the traditional approach: the prompt holds the task instructions, conversation history, past observations, past reasoning and the newest observation, and the model acts on it. Right, SKILL.state: the prompt holds only the task instructions, the execution state and the newest observation; the model's reasoning is crossed out as discarded, and a state-update arrow labelled JSON Patch ΔΣ loops back to the execution state. Under each side a context-growth bar chart is labelled growing on the left and bounded on the right." caption="Figure 1 — SKILL.state overview: the traditional prompt grows with each step, SKILL.state's stays the same size (Source: original paper, Figure 1.)" width="81%" >}}

After reading those three things, the model outputs three things. \( R_t \) is its reasoning, the chain-of-thought (the step-by-step thinking the model writes out); it is thrown away immediately and **never appears in the next step's prompt**. \( \Delta\Sigma_t \) is the state "diff", a JSON dictionary describing what to change in the state this step. \( a_t \) is the action to take.

$$
(R_t,\ \Delta\Sigma_t,\ a_t)
$$

The update rule is simple. The paper defines an operator \( \oplus \), a "dictionary merge with null-deletion semantics": any key in \( \Delta\Sigma_t \) overwrites the key of the same name in the old state; a key set to `null` is removed from the state entirely; keys that \( \Delta\Sigma_t \) does not mention stay as they are. As a formula, the next state is this state merged with the diff:

$$
\Sigma_{t+1} = \Sigma_t \oplus \Delta\Sigma_t
$$

### The loop: reasoning is discarded, the state is replaced whole

1. The runtime (the outer program that calls the model and carries out actions) receives observation \( O_t \).
2. It builds the prompt \( (P, \Sigma_t, O_t) \), whose size does not depend on the step number.
3. The model outputs \( (R_t, \Delta\Sigma_t, a_t) \).
4. The runtime checks that \( \Delta\Sigma_t \) is well-formed. If it is, the loop continues; if not, it rolls back and asks the model to try again.
5. It applies the update: \( \Sigma_{t+1} = \Sigma_t \oplus \Delta\Sigma_t \).
6. It carries out action \( a_t \), and \( R_t \) is discarded for good.
7. The environment returns a new observation \( O_{t+1} \), and the loop starts over.

Compared with a traditional ReAct-style run, the difference is in how the prompt grows:

```text
Traditional:
  step 1 prompt: [P] + [O_1]
  step 2 prompt: [P] + [O_1, R_1, a_1] + [O_2]
  step 3 prompt: [P] + [O_1,R_1,a_1] + [O_2,R_2,a_2] + [O_3]
  ...keeps growing

SKILL.state:
  step 1 prompt: [P] + [Σ_1] + [O_1]
  step 2 prompt: [P] + [Σ_2] + [O_2]
  step 3 prompt: [P] + [Σ_3] + [O_3]
  ...roughly fixed size (Σ may change slowly with task complexity, but not with the step count)
```

The traditional prompt **appends a new piece** at every step; SKILL.state **replaces the whole state** at every step.

### One warehouse shipping step, start to finish

The paper's appendix walks through one complete shipping step in this scenario, and it is easier to follow than the formulas. At the start, item_12 sits on shelf_42. The runtime receives observation \( O_t \): "Customer ordered item_12."

The model's internal reasoning goes roughly: "The customer ordered item_12, so I need to ship it. The current state says item_12 is on shelf_42. I'll issue a Ship action and clear shelf_42 in the state." This reasoning gets thrown away afterwards. What the model actually outputs is this JSON:

```json
{
  "state_patch": { "inventory": { "shelf_42": null } },
  "action": "Ship item_12 shelf_42"
}
```

`state_patch` is \( \Delta\Sigma_t \), and it sets shelf_42 to `null`; `action` is \( a_t \). Before and after applying \( \oplus \), the inventory part of the state looks like this:

| Shelf | Before | After |
| --- | --- | --- |
| shelf_42 | "item_12" | null (deleted / cleared) |
| shelf_43 | "item_9" | "item_9" (not mentioned, unchanged) |

After carrying out the action, the environment returns a new observation \( O_{t+1} \): "Success: Shipped item_12 from shelf_42." The next prompt is simply \( (P, \Sigma_{t+1}, O_{t+1}) \). The reasoning \( R_t \) is gone, and so is the previous observation \( O_t \): the model sees only the current state and the newest observation, with no history text at all.

### State fields are designed once per domain

Which fields the state records, its **schema**, is designed once for a whole domain (a family of similar tasks), not once per task. In InterCode CTF (100 Linux puzzle challenges where the agent runs bash commands to find a hidden flag string), the challenges vary widely, covering reverse engineering, forensics, cryptography and binary exploitation, yet all of them share one set of fields: flags found, hypotheses and commands already tried, the file being worked on, the current working directory, and a summary of command output. The benefit is direct: no new state format per task, and different tasks can share the same runtime code.

The catch is that the domain must know in advance which fields to track. If the schema cannot be fixed beforehand and what to track only emerges during the run, this approach does not apply. The paper names this as the first failure case in its own Limitations section.

### Validation catches format errors, not semantic ones

Before applying \( \Delta\Sigma_t \), the runtime checks its format: is it valid JSON, and does its key structure match what is expected? If the check fails, it rolls back and retries: the state reverts to the previous step and the model is asked to output again. So malformed output never corrupts the state.

{{< admonition warning "Well-formed but wrong patches go straight through" >}}
The check stops output that is malformed. It cannot stop output that is well-formed but semantically wrong. Say the model outputs a patch that accidentally deletes something important: the format is fine, the check sees nothing, and a wrong update is "successfully" applied. Worse, the old state is no longer in the context, so once a wrong patch has been applied there is no history to look back at and correct it. Compared with keeping the full history, this is where the architecture is structurally more fragile. This is not speculation: the paper's own experiments show that 68% of a smaller model's failures are exactly this kind of semantically valid but wrong update applied without notice, and the failure section comes back to that number.
{{< /admonition >}}

## Why total cost drops from quadratic to linear

The paper uses \( T \) for the total number of steps and compares the order of magnitude of total tokens for the two approaches. The order of magnitude is written \( O(\cdot) \), meaning roughly how something grows as \( T \) gets large, ignoring constant factors. Call the traditional prompt at step \( t \) \( C_t \): its length \( |C_t| \) is proportional to \( t \), so it is \( O(t) \). Call the SKILL.state prompt at step \( t \) \( P_t \) (not the task instruction \( P \) from earlier): its length is \( O(|P|+|\Sigma|+|O|) \), the lengths of the instructions, state and observation added together, which does not depend on \( t \). Summed over all \( T \) steps, the traditional total is on the order of \( T \) squared and SKILL.state's is on the order of \( T \):

$$
\sum_{t=1}^{T} |C_t| = O(T^2) \qquad \sum_{t=1}^{T} |P_t| = O(T)
$$

Numbers make the intuition easier. Suppose there are 10 steps and each step's length is simplified to "units": the traditional run is 1, 2, 3, ..., 10, and SKILL.state is 1, 1, ..., 1. The traditional total is \( 1+2+\cdots+10=(1+10)\times10/2=55 \), an arithmetic series whose size grows like \( T^2 \); SKILL.state adds up 10 copies of 1, \( 1\times10=10 \), which grows like \( T \). When each step's length grows linearly with \( t \), adding up those growing amounts gives a square.

"1 unit" is a simplification. Each SKILL.state step really costs \( |P|+|\Sigma|+|O| \), and the state \( \Sigma \) can grow slowly with task complexity: in a densely linked environment, for instance, it gets bigger as branches and PRs pile up. But that growth depends only on how complex the world is right now, not on how many steps have passed. That is why each step is called \( O(1) \) and the total \( O(T) \), rather than every step costing exactly some fixed constant.

The measurements agree. In Table 1 later on, doubling \( T \) from 100 to 200 multiplies the total tokens of the Stateful baseline (which has a structured state too, but also keeps the full conversation history) by about 4.7, close to the 4 that theory predicts (\( 2^2 \)). SKILL.state's total grows only about 1.9 times, close to the predicted 2 (\( 2^1 \)).

## How the experiments were set up

### Environments and scoring

The tests fall into two groups: a synthetic testbed the authors built themselves, SkillExecBench, and two public benchmarks designed by others.

**SkillExecBench** is a controlled diagnostic testbed: fixed rules decide how the world changes, so it can test the execution mechanism separately from open-ended trial-and-error search. It can stretch the task length, the number of steps (the paper calls it the horizon), from \( T=10 \) all the way to \( T=200 \). It comes in a warehouse version and a software-repository version:

- Warehouse management: 500 independent, non-overlapping shelves, with only Store/Ship/Move/Wait as actions. It tests whether the model can keep many state variables that don't interfere with each other straight over a long run.
- Software repository: Git branches, commits, PRs and CI status, all deeply linked, with actions such as CherryPick, Merge, RunTests, CreateRelease and Rollback. Its defining feature is dense dependency: one action (merging a PR, say) also affects the target branch and other dependent PRs, which tests structured reasoning over a tangled graph of relationships.

The two public benchmarks are **InterCode CTF** (Yang et al., 2023) and **Sierra τ-Bench** (Yao et al., 2024). InterCode CTF is the set of 100 puzzle challenges mentioned earlier, covering reverse engineering, forensics, cryptography and binary exploitation; the agent runs bash commands inside a Docker container, testing hypotheses until it finds the hidden flag. τ-Bench tests three-way interaction between tools, agent and user in enterprise customer service, in a retail and an airline domain: the agent talks with a simulated user, queries an SQLite database through tools, and carries out transactions under business-policy constraints.

Each environment is scored differently. SkillExecBench uses a continuous score (successful actions divided by total events); InterCode CTF uses pass@1, the share of challenges solved on the first try; τ-Bench uses the official grader, which checks the final state of the database. Besides accuracy, the paper tracks the average prompt size per LLM call and the total tokens used over a whole run.

### Baselines: Stateful and the budget-matched controls matter most

There are three architectural baselines. **Prompt(ReAct)** is the most basic setup, appending every step's observation, reasoning and action. **Memory(Summary)** keeps the last three turns verbatim plus a natural-language summary that is updated periodically. **Stateful(LangGraph)** follows LangGraph (an agent development framework that can keep a structured state alongside the conversation): it has a structured state block but **also** keeps the full rolling conversation log.

Stateful is the baseline that matters most. Like SKILL.state it has a structured state; the only difference is state plus full history versus state alone with all history dropped. Only this comparison actually tests whether dropping history is worth it; the other baselines can at most show that structured state beats plain-text history.

The paper also adds a set of **budget-matched controls** to rule out the possibility that SKILL.state wins only because its prompt is shorter. All three squeeze the prompt down to roughly SKILL.state's size. Truncated(Sliding Window) keeps only the most recent turns under a hard token cap. Summary-capped uses a natural-language summary with a strict limit on the summary's own length. ReAct+LLMLingua compresses with LLMLingua, a tool in which a small model uses perplexity (how hard the small model finds a piece of text to predict) to delete the words it judges unimportant, down to a target token count.

The models are Gemini-3-Flash (closed weights), Gemma-4-31B-it and Qwen-3-8B-it (open weights), at temperature 0.0 (output kept as fixed as possible). The synthetic experiments use 5 random seeds, and for \( T \geq 50 \) a paired t-test (a statistical test of whether a gap is just random variation); the paper reports \( p<0.01 \).

## A caveat before the numbers: long tasks were only tested in-house

SkillExecBench deliberately sweeps the task length from \( T=10 \) to \( T=200 \), a clear length scan. But in the InterCode CTF and τ-Bench sections, the paper never reports how many steps a task takes on average. If those tasks finish in 10 to 20 steps on average, the "public validation" never tests the long tasks SKILL.state claims to be best at; the only real stress test of long tasks is the synthetic environment the authors designed and control.

Public benchmarks built specifically to test long, real-world agent tasks do exist, and the paper uses none of them:

- SWE-bench: fixing real GitHub issues, which often takes tens to hundreds of tool calls. The paper's own software-repository environment essentially imitates this kind of task, yet the authors built a simplified version instead of using the real SWE-bench.
- WebArena / Mind2Web: long web-navigation tasks.
- GAIA: general-assistant tasks that chain tools over many reasoning steps.
- OSWorld: tasks operating a real operating system.

The paper does not explain why it skipped these more representative long-task benchmarks. That does not make its numbers false. It means the claim that the approach holds up on long real-world tasks rests on thinner evidence than it first appears: the most persuasive long-task numbers all come from a synthetic environment the authors designed and control. Keep that in mind while reading the results.

## Results: the cost evidence is strong, the accuracy evidence shakier

### Warehouse: gaps open only on long tasks, and the big one is tokens

Table 1 is the main warehouse table: task length runs from \( T=10 \) to \( T=200 \), and for each length it compares the four setups on accuracy, average prompt length and total tokens. The top and bottom groups are the ones to look at.

{{< image src="table1.png" alt="Table of accuracy, average prompt length in characters and total tokens for Prompt, Memory, Stateful and SKILL.state at five task lengths, each with a standard deviation." caption="Table 1 — Warehouse long-horizon scaling: accuracy and token use as task length grows (Source: original paper, Table 1.)" >}}

Short tasks (\( T=10 \)) show no accuracy advantage: the main baselines Memory and Stateful and SKILL.state all score 1.00, a tie. The advantage only appears on long tasks, and it is not overwhelming: at \( T=200 \) it is 0.94 versus 0.88, a 6-point gap. What is overwhelming is tokens: at \( T=200 \) Stateful uses 5,041,164 and SKILL.state only 122,384, 41 times fewer. The gap is mostly in cost, not accuracy.

Baseline accuracy also falls as \( T \) grows, and the standard deviation (how spread out the scores of repeated runs are) widens: Prompt drops from \( 0.90\pm0.02 \) at \( T=10 \) to \( 0.74\pm0.14 \) at \( T=200 \), while SKILL.state stays fairly steady. The more accurate summary is that baselines degrade over long runs and SKILL.state barely does, not that SKILL.state leads by a wide margin.

### Public benchmarks: wins on all three, but the retail baseline is shaky

Table 4 moves to real tasks designed by others. Because the authors did not write these tests, this is the most persuasive accuracy evidence in the paper.

{{< image src="table4.png" alt="Table comparing Prompt, Memory, Stateful and SKILL.state on InterCode CTF, Sierra τ-Bench Retail and Sierra τ-Bench Airline: success rate, prompt size and total tokens." caption="Table 4 — Success rate and token use on public interactive benchmarks (Source: original paper, Table 4.)" >}}

It wins on all three: against the best baseline, CTF pass@1 is 7.8 points higher, τ-Bench retail 6.6 points higher, and airline 4.3 points higher.

There is one outlier to watch. Memory collapses on τ-Bench retail, scoring only 29.9%, nearly 20 points below Prompt's 48.2%. The paper does not discuss it; my guess is that the summary-based memory may have lost transaction details. That makes the retail column an unstable comparison: whether SKILL.state is being measured against the best or the worst baseline makes a big difference, so check which baseline you are reading. This table also cannot answer the doubt raised before the results, whether the long-task claim holds in the real world; what it shows is better overall performance, a narrower claim than the paper's abstract suggests.

### Software repository: losing to Stateful midway

The software repository is SkillExecBench's second environment, where pieces of state are tightly linked. Table 6 shows its results at four task lengths, and it holds the most important counterexample in the paper.

{{< image src="table6.png" alt="Table of accuracy, average prompt size and total tokens for Prompt, Memory, Stateful and SKILL.state at four task lengths, each with a standard deviation." caption="Table 6 — Software repository long-horizon scaling: tied on short tasks, behind midway, ahead only on long tasks (Source: original paper, Table 6.)" >}}

At \( T=10 \), Stateful and SKILL.state both score \( 1.00\pm0.00 \), a tie. At \( T=25 \), SKILL.state (\( 0.88\pm0.08 \)) actually **loses** to Stateful (\( 0.94\pm0.03 \)) by 6 points. It only pulls ahead again at \( T=50 \) (0.86 versus 0.74), and by \( T=100 \) the lead grows to 15 points (0.78 versus 0.63).

{{< admonition warning "This counterexample contradicts the paper's own claim" >}}
The abstract says SKILL.state "improves task accuracy... across diverse datasets", and the main text says it "matches or exceeds baseline accuracy across all horizons". But "across all horizons" holds only in the warehouse; in the software repository there is the \( T=25 \) counterexample, which the main text never mentions. SKILL.state's standard deviation in this table is also large (\( \pm0.08 \)), so the result is not very stable.
{{< /admonition >}}

My guess is that this comes from the repository's dense dependencies. One action can affect several branches at once; if a patch fails to capture a knock-on effect (merging a PR but forgetting to update the state of a dependent branch, say), the error can carry through to later steps, because there is no original history text to check against. That is exactly the validation blind spot described earlier, and the \( T=25 \) counterexample may well be that risk actually happening.

The claim of across-the-board accuracy gains breaks down as environments get more densely linked; the only advantage that holds steadily in every environment is the token saving.

### Matched budgets: structure wins, not just a shorter prompt

One doubt remains from the comparisons so far: does SKILL.state win just because its prompt is shorter? Table 5 forces every setup to SKILL.state's token budget (about 1,800 tokens) and compares again.

{{< image src="table5.png" alt="Table comparing five configurations on accuracy, average prompt size and total tokens: unbounded ReAct, sliding-window truncation, capped summary, ReAct with LLMLingua compression, and SKILL.state." caption="Table 5 — Warehouse budget-matched controls: accuracy at the same token budget (Source: original paper, Table 5.)" width="75%" >}}

Once the budgets match, the compression approaches all collapse: Truncated(Sliding Window) scores only 0.18, ReAct+LLMLingua 0.22, Summary-capped 0.52, while SKILL.state holds at 0.94.

This is the most solid experiment in the paper, because it rules out the confound that SKILL.state wins only by having a shorter prompt. At the same token budget, statistical compression (LLMLingua) and simple truncation crush the semantically important information along with everything else, while SKILL.state's structured state keeps the key relationships intact.

### Noise and state recovery: results the design guarantees

Two more experiments each show something simpler. The first is noise: in a high-noise environment full of irrelevant messages, Prompt's accuracy drops from 0.68 to 0.53 while SKILL.state stays between 0.97 and 1.00. This is predictable: noise never gets written into a state patch, so it cannot affect later decisions. It follows directly from the design and is not a surprising finding.

{{< image src="table2.png" alt="Table of accuracy for Prompt, Memory, Stateful and SKILL.state at low, medium and high noise, with task length T=50." caption="Table 2 — Warehouse noise robustness (Source: original paper, Table 2.)" width="75%" >}}

The second is state recovery: when the outside environment quietly changes the world (someone moves an item, for example), the history-keeping baselines need 5 to 8 steps to recover from their stale beliefs, and SKILL.state needs 0. This result is also close to a tautology: SKILL.state keeps no history text, so a stale observation overriding a new fact cannot happen by design, and as long as the correcting observation makes it into a patch, the number of recovery steps is logically 0.

{{< image src="table3.png" alt="Table of four scenarios showing, for each setup, whether the task succeeded and how many steps recovery from a wrong belief took." caption="Table 3 — Warehouse state recovery: steps needed to get back to the truth after the world changes outside the agent (Source: original paper, Table 3.)" width="75%" >}}

## Where it fails: small-model errors and three failure situations

With the open-weight Gemma-4-31B, SKILL.state's accuracy on the \( T=100 \) warehouse task falls to 0.42. Table 7 below shows how the other setups score at the same length.

{{< image src="table7.png" alt="Table of accuracy, average prompt and total tokens for Prompt, Memory, Stateful and SKILL.state with Gemma-4-31B at four task lengths, each with a standard deviation." caption="Table 7 — Warehouse scaling with Gemma-4-31B (Source: original paper, Table 7.)" width="82%" >}}

The paper sorts the failures into types:

| Failure type | What it looks like | Share |
| --- | --- | --- |
| Premature State Overwrite/Deletion | Accidentally dropping an existing key during a merge, which deletes it | 68% |
| Schema Comprehension/Type errors | Mixing up nested lists and dicts | 20% |
| JSON syntax/format errors | Missing commas, unbalanced brackets | 12% |

The paper concludes that small models fail because of **structured-output compliance** (whether they can produce output in exactly the required format and structure), not because they reason poorly.

My guess is that the first type, the 68%, is direct evidence of the validation blind spot from earlier: a semantically valid but wrong patch gets applied and cannot be corrected afterwards. It is the same problem as the software repository's \( T=25 \) counterexample, showing up in a different way.

The whole design rests on one premise: **the execution state can be a sufficient statistic for future execution**. Anything that happened in the past needs no original text kept, as long as it was written into the state correctly at the time. The paper itself admits this premise fails in three situations:

1. **The schema cannot be fixed in advance**: which fields to track only emerges during the run.
2. **An early observation seemed unimportant at the time and only later turned out to matter**: since it never went into the state, there is no getting it back. Of the three, this is the most realistic and the easiest to hit in production. The architecture's most fundamental bet is that the model makes the right call **in the moment**; if that bet is wrong, there is no way back.
3. **The goal of the task is the history itself**: auditing, tracing a bug back to its source, explaining past decisions. Here, dropping history directly conflicts with the task.

The paper admits two further limitations. When several agents share one state, simultaneous writes conflict; the paper only says the design "extends naturally" and neither implements nor tests it. Grammar-constrained decoding (restricting generation so the model can only produce syntactically valid output) can remove the pure syntax errors of the third type above, but it does nothing for the semantic errors of the first type.

## In practice: ReAct or SKILL.state?

A common intuition is that keeping a record of past actions gives more room for error, so for a strong model it should do more good than harm. That "room for error" means two different things, and they need to be pulled apart.

The first is being able to trace and debug afterwards. Here keeping history really does win: after a mistake you can go back to the original data, whereas once SKILL.state drops something it is truly gone. That is the second failure situation in the previous section.

The second is whether keeping history makes long-task accuracy more stable. The Table 1 numbers from earlier contradict that intuition: even with the strongest model the paper tested, Gemini-3-Flash, the history-keeping Prompt(ReAct) still slides from 0.90 to 0.74, and its standard deviation grows 7 times.

The paper cites the lost-in-the-middle effect (Liu et al., 2024) to explain why accuracy degrades over long contexts: a model can technically see the information in a long context without reliably using it. My guess is that this is not a reasoning shortfall, so a stronger frontier model would not make the weakness disappear, though it might soften it. "Strong model plus kept history does more good than harm" holds for short and medium tasks; on long tasks the measurements overturn it.

Put together, the evidence makes a decision table:

| Axis | Leans ReAct (keep history) | Leans SKILL.state (drop history) |
| --- | --- | --- |
| When relevance can be judged | Only later turns out an observation mattered (debugging, exploratory research) | Can tell right away whether to record it (warehouse, database state) |
| Is the trajectory itself the output? | Yes (audit, compliance, explaining the process) | No (only the final state or result must be right) |
| How densely the state is linked | Densely interdependent (Git graphs, chained financial calculations) | Sparse and independent (like 500 unrelated shelves) |
| Expected run length | Short to medium (about 25 steps or fewer with sparse links): accuracy ties, and ReAct is simpler | Long (100 steps or more): history-keeping accuracy degrades and varies more, state-based stays steady |
| Model capability | Weak model: valid but wrong patches applied unnoticed are a major risk | A strong model lowers this risk, but frontier models simply weren't tested; no evidence they are immune |
| Sensitivity to cost and latency | Low (few calls, ample budget) | High (frequent calls, going to production) |

With dense links, a bad patch spreads silently and there is no original text to check it against; with sparse links, the damage from a bad patch stays contained. "Tied within about 25 steps" also applies only to sparsely linked environments; with dense links the crossover comes earlier, as when the software repository was already losing at \( T=25 \). For short and medium tasks ReAct has the advantage of not needing an extra layer of schema and validation infrastructure; cost-sensitive settings lean the other way because \( O(T^2) \) costs explode.

{{< admonition tip "Ask this first" >}}
Can I decide, at the moment something happens in this domain, whether it is worth recording? If yes (clear structure, sparse links, long enough tasks), choose SKILL.state. If not, or if you need an audit trail, or if the state is densely linked, prefer ReAct, or a hybrid of state plus limited history.
{{< /admonition >}}

In between sits the Stateful baseline from Table 1 and Table 6, LangGraph-style structured state plus full conversation history. It is neither pure ReAct nor SKILL.state's state-only approach, and in the software repository at \( T=25 \) it even beat SKILL.state: the Stateful 0.94 versus SKILL.state 0.88 counterexample from earlier.

My guess is that if you are not sure the premise of judging correctly in the moment holds, a hybrid of state plus a short window of recent history may be more practical than either of the paper's two extremes: let the structured state handle what you are confident about, and keep a short rolling history as a safety net in case the schema missed something. The cost falls between the two, not \( O(1) \) per step, but not linear stacking all the way either.

## Conclusion: expect lower cost, not across-the-board accuracy

The paper's engineering value is high, especially on cost; its research novelty is moderate to low. Its most solid part is turning "structured state plus dropped history" into a system and proving the \( O(T) \) versus \( O(T^2) \) complexity. But the core idea already existed: [MemGPT](../memgpt/) (a system that lets an LLM manage its own long-term memory), LangGraph's state block and Dialogue State Tracking (the technique dialogue systems use to keep track of what a user wants) all did something similar. The contribution is the proof and the systematic measurement, not a new concept. The budget-matched control is worth remembering as an experimental design too: it shows the win comes from structure, not just from being shorter, and that method is worth keeping longer than the paper's core claim.

SKILL.state solves a very concrete problem with a simple idea: separate the current state of the world from the text history, and the prompt stops growing with the number of steps. Consider it as a way to cut cost and the evidence is strong (41 times fewer tokens at \( T=200 \)); expect it to be more accurate across the board and the evidence is not there yet, with the software repository's \( T=25 \) counterexample as the clearest proof. Densely linked tasks, plus semantic errors that validation cannot catch, are the architecture's real weak spot. Papers often package accuracy and cost as one selling point, but the evidence for each is rarely equal. Whenever a paper claims to be both faster and more accurate, check the two claims separately; one is usually clearly stronger.

Whether to drop history comes down not to how strong the model is but to **whether relevance can be judged correctly at the moment information arrives**. An architecture that removes the option of checking the original data bets everything on getting that call right. Any system that throws away raw data for efficiency and keeps only summaries or extractions is making the same bet. So the thing to keep, more than the paper's conclusion, is that question: it is not limited to agent design, and it applies to any system where you decide whether to throw raw data away.

The paper also leaves a few habits of judgement:

- Look for counterexamples to universal claims: when you see "across all X", look for a dataset or environment where it fails, like the software repository's \( T=25 \). Universal claims usually hold only in the most favourable setting, and the appendix or a secondary table often hides the honest counterexample.
- Seeing is not using: lost-in-the-middle (Liu et al., 2024) is about whether a model can use what is in a long context, a separate dimension from how strong the model is, and worth learning about on its own.
- Should history live alongside state: Dialogue State Tracking keeps state and full conversation history together, while this paper keeps only state. When designing any system with structured state, ask this sub-question first instead of treating "structured state or not" as the only split.
- Validation only catches format: the paper's own experiments (68% of errors came from semantically valid but wrong patches) expose this, yet the paper never spells out what it means for the architecture. Any design where an LLM produces structured output and code applies it automatically should remember that validation cannot catch output that is well-formed but wrong.

If you are building an agent that runs for a long time, try listing the state fields for your domain, then find the information you cannot decide, at the moment it arrives, whether to keep. Those are the places where you still need history.

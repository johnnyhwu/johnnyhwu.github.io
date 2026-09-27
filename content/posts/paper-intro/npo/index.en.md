---
# weight: 1
title: "Naive Prompt Optimization: What's Left Once You Remove the Search"
date: 2026-09-27
lastmod: 2026-09-27
draft: false
description: "Purdue's NPO claims rich rollout feedback can replace GEPA-style search — but its 'beats GEPA with fewer rollouts' claim hides an unresolved confound."
featuredImage: "featured-image.png"

tags: ["Large Language Model", "Prompting", "Single-Agent"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## Introduction

If you've looked into automatic prompt optimization, you've probably noticed the field's recent methods keep getting more elaborate: maintaining a whole pool of candidate prompts, running beam search, doing Pareto-based filtering. GEPA is the flagship example of this trend.

Purdue's paper *Naive Prompt Optimization* asks a question that sounds almost too simple: if you give the "teacher model" that rewrites the prompt richer feedback — not just a single aggregate score, but the full execution trace plus per-example scores — and pair it with a strong enough teacher, do you even need search anymore? Can maintaining just a single "lineage" of prompt revisions match or beat those elaborate search-based methods? They call this approach **NPO (Naive Prompt Optimization)**.

Let's front-load the conclusion: this paper's own methodological contribution is modest. NPO is essentially a small modification of an existing technique, OPRO, and its headline claim — "beats GEPA using fewer rollouts" — hides an unresolved confound we'll dig into below. What the paper *does* do solidly is fair comparison methodology: paired random seeds and constrained decoding. That experimental design is more transferable than NPO the method itself. This article is weighted accordingly: we'll cover the method clearly, but spend more space on that comparison methodology.

## Background: why prompt optimization keeps getting more complicated

### Tune the weights, or tune the prompt

If you have a "student model" — the model that actually executes the task — and you want it to perform better, there are broadly two paths: update the model's weights (e.g. RLHF, PPO, GRPO and other reinforcement-learning methods that directly change parameters), or leave the model untouched and just swap in a better instruction — i.e., tune the prompt.

The second path's advantage is direct: it's lightweight and portable. You don't need to train and maintain a dedicated set of weights for every task and every user — just swap a piece of text, and you can deploy it to any third-party model accessible through a standard API. Automatic prompt optimization research is about how to automatically find that better instruction text.

### The mainstream methods all do the same thing: multiple candidates + search

The paper walks through the evolution of several representative methods, and the trajectory keeps moving in the same direction — bigger and more complex:

- **OPRO**: treats the LLM as an optimizer, proposing the next version based on "previously tried prompt versions plus their scores."
- **ProTeGi**: combines the idea of a "textual gradient" with beam search, tracking multiple candidate lineages at once.
- **MIPRO**: uses the model to generate candidates, plus Bayesian optimization (using a probabilistic model to guess "what to try next").
- **GEPA**: maintains an entire pool of candidate prompts, generates new candidates through reflection, and uses Pareto-based selection to keep the candidates that aren't dominated by any other candidate.

What these methods have in common: they all maintain multiple candidate versions simultaneously and use some mechanism to decide which direction to revise in. (We've previously covered two other papers that also benchmark against GEPA, in different problem settings: [SkillOpt](../skillopt/), which treats an agent's skill document as a trainable weight, and [Agentic Context Engineering](../agentic-context-engineering/), which accumulates experience in an evolving context rather than a single prompt.)

Behind this design sits an unstated assumption: if you only follow a single lineage — one prompt version at a time, with no way back once a revision goes wrong — you can easily get stuck in a local optimum, where one bad step ruins everything downstream, wasting a limited rollout budget. Maintaining multiple candidates and keeping the better-performing branches is exactly how you avoid betting all your chips on one lineage that might go astray.

## NPO's question: if the feedback is rich enough, do you still need search?

NPO flips the question around: if, at every revision, the feedback given to the teacher model is rich enough — not just "the previous version plus one aggregate score," but the full execution trace and per-example scores — and the teacher model itself is strong enough, is following a single lineage with no search good enough that the marginal benefit of those search mechanisms approaches zero?

This is the paper's entire starting premise: not a new algorithm, but a challenge to whether the existing complexity is necessary. The abstract's own wording is "stronger teacher reasoning can partially substitute for optimizer-side search complexity" — note the word *partially substitute*, not "eliminates the need entirely." This is a conditional claim, not a flat assertion, and that nuance matters when we get to the experimental results.

## The NPO method itself

### The whole logic in one sentence

Every round: run a batch of tasks with the current prompt, collect the execution traces and scores for that batch, feed the traces and scores from "the last several rounds" to the teacher model, and have the teacher produce the next prompt version. Repeat for a fixed number of rounds — that's the entirety of NPO.

### Algorithm 1: notation reference

The paper's Algorithm 1 (titled *Naive Prompt Optimization with Sliding-Window Rollout Feedback*) uses a set of symbols, laid out here for reference:

| Symbol | Meaning |
|---|---|
| \( P^{(i)} \) | the prompt version at round \( i \), starting from 0 |
| \( D \) | the full task dataset |
| \( N \) | the minibatch size sampled each round |
| \( B_i \) | the \( N \) tasks sampled from \( D \) at round \( i \) |
| \( R_i \) | what's collected after round \( i \) runs: the full rollout trace and reward for each task |
| \( W \) | the sliding-window size — how many past rounds of data the teacher can see this time |
| \( T \) | the teacher model, responsible for rewriting the prompt |
| \( Y \) | the total number of rounds executed |

The core step, written as a formula:

$$P^{(i+1)} = T\Big(P^{(i)}, \{R_j\}_{j=\max(0,\, i-W+1)}^{i}\Big)$$

In plain terms: the teacher takes "the current prompt version" plus "all execution results from the last \( W \) rounds (including this one)" and rewrites the next prompt version. The \( \max(0, i-W+1) \) form handles the boundary case where "we haven't yet reached \( W \) rounds" — for example, at \( i=0 \), counting back \( W-1 \) rounds would go negative, so it clamps to 0 instead of erroring out.

One easy-to-miss detail: what the teacher actually sees isn't just single-example data. The paper's own text says the teacher receives "the prompts, corresponding rollout traces, and rewards" — plural prompts. If the window covers 2 rounds, the teacher's full input is actually: the prompt text of both versions, each version's average score, and, across those 2 rounds at \( N \) examples each, a total of \( 2N \) records of (question, execution trace, model output, per-example score).

This matters: if the teacher only saw single-example results, it could only judge "where did this particular example go wrong." But because it can also see "how the average score changed across two consecutive rounds," it has a chance to judge "did my last edit actually help" — which is exactly the effect the sliding-window design is meant to achieve. As we'll see below, though, this effect is never actually guaranteed.

### Walking through the paper's own example

The paper's Figure 1 gives a concrete demonstration. Suppose the minibatch contains the question "What is the capital of France?":

{{< image src="figure1-npo-workflow.png" alt="A flowchart of how NPO rewrites the prompt each round using execution results: run the current prompt version, collect scored execution traces, feed them to the teacher model, produce the next prompt version." caption="Figure 1 — One revision round of NPO. (Source: original paper's Figure 1.)" >}}

- \( P^{(1)} \) (version 1 of the prompt): `Given the fields 'question', 'summary_1', produce the fields 'query'.`
- Running \( P^{(1)} \) on this example, the model outputs "Berlin," reward = 0 (wrong).
- Across the whole minibatch, \( P^{(1)} \)'s average score comes out to 0.56.
- The teacher sees "the text of \( P^{(1)} \) plus a batch of execution traces containing wrong answers," judges that the problem is the prompt not being clear about "give the final answer," and rewrites it into \( P^{(2)} \): `Given the fields 'question' and 'summary_1', produce the field 'query'. Your goal is to provide the concise final answer.`

Even in this single round, NPO's revision logic is intuitive: the teacher sees concrete failure cases and addresses them directly.

### Visualizing the sliding window

The paper's Figure 2 packs both "the difference between NPO's and GEPA's lineages" and "how the sliding window slides" into one diagram:

{{< image src="figure2-gepa-vs-npo-lineage.png" alt="The left half shows GEPA's tree-shaped evolution of candidate prompts; the right half shows NPO's single-lineage prompt evolution, with the sliding window marked as it advances across rounds." caption="Figure 2 — GEPA's tree-shaped candidate pool, contrasted with NPO's single lineage and sliding window. (Source: original paper's Figure 2.)" >}}

Take \( W=2 \) as an example — first, the score at each round:

| Round \( i \) | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| Score \( P^{(i)} \) | 0.25 | 0.68 | 0.69 | 0.60 | 0.65 | 0.73 |

Here's how the window slides across rounds:

| Window | Covers rounds | Produces |
|---|---|---|
| Window 1 | \( \{0\} \) | \( P^{(1)} \) |
| Window 2 | \( \{0, 1\} \) | \( P^{(2)} \) |
| Window 3 | \( \{1, 2\} \) | \( P^{(3)} \) |
| Window 4 | \( \{2, 3\} \) | \( P^{(4)} \) |
| Window 5 | \( \{3, 4\} \) | \( P^{(5)} \) |

Each window covers only "the most recent two rounds" of data, and windows overlap (Window 2 and Window 3 both include round 1) — this lets the teacher see the newest results while still retaining a bit of earlier context when revising. Compare this to GEPA on the left of Figure 2: GEPA is a tree, able to branch new candidates off well-performing nodes; NPO is entirely a single line, \( P^{(0)} \to P^{(1)} \to P^{(2)} \to \dots \), with no branching — only the "how many steps back can you see" difference.

### The difference from OPRO

The technique of "treating an LLM as an iterative prompt optimizer" was first proposed by OPRO. The difference: OPRO only shows the teacher "previously evaluated prompts plus their corresponding scalar scores," while NPO gives it "the full execution trace plus per-example scores." That's as far as the paper's explanation of this difference goes — it doesn't elaborate further. In other words, NPO's technical leap over OPRO isn't actually that large; it's mainly upgrading the feedback signal from "a single number" to "a full record."

{{< admonition warning "The hidden problem with batch sampling" >}}
Line 2 of Algorithm 1 reads "Sample minibatch \( B_i \) of size \( N \) from \( D \)" — meaning every round re-samples a fresh batch of \( N \) examples from the entire dataset at random, rather than reusing the same batch each time.

This creates a problem for the sliding window's design intent. The whole point of the teacher being able to see "the average score across two consecutive rounds" was to judge "did my last edit actually help." But if \( P^{(i-1)} \)'s score was computed on batch A (say, some 40 examples) and \( P^{(i)} \)'s score was computed on batch B (a completely different set of 40 examples), the difference between those two numbers conflates two things: "did the prompt actually improve" and "did this batch happen to be easier or harder." The teacher has no way to tell, from just those two numbers, which one is the cause.

Section 2.4 of the paper does have a "shared pseudorandomness" mechanism (paired random seeds), but that's used to keep comparisons fair *across* NPO, GEPA, and GRPO (detailed below in "Paired random seeds") — it isn't used to address whether NPO's own consecutive-round minibatches are internally consistent. The paper doesn't discuss or run any sensitivity analysis on this at all.

One factor that might partially mitigate this is that each round's score is the average over \( N=40\text{–}50 \) examples rather than a single score — with a large enough sample, random fluctuations in batch difficulty should theoretically average out to some degree. But that's a mitigation, not a fix. For a task like IFBench (a benchmark testing whether a model follows format/length constraints in instructions), where different examples' constraint types can vary a lot in difficulty, even averaging over 40 examples, different batch compositions could still cause a systematic score gap rather than pure random noise. This inference is my own addition — the paper itself doesn't make this point.
{{< /admonition >}}

## Comparison methods: GEPA and GRPO (brief)

The experiments repeatedly compare NPO against these two methods, so here's just the minimum background needed to follow the results — not a deep dive into either algorithm's details.

**GEPA**: maintains a pool of candidate prompts. It draws a "parent" prompt from the pool, revises it using a batch of reflection data (the reflection minibatch), and only accepts the revision if it improves on that reflection batch. Accepted revisions are evaluated on a validation set and added to the candidate pool, after which that validation performance drives Pareto-based parent selection (keeping versions not dominated by any other candidate). The paper uses the standard GEPA pipeline, not the GEPA-merge variant.

**GRPO**: serves as the "weight-level" RL baseline. For each rollout group, it subtracts the group mean from the reward and divides by the standard deviation to get a relative advantage, used to update a LoRA (low-rank adaptation) adapter, with the backbone weights and prompt both kept fixed. In two-player game environments, the model being trained faces a fixed, untrained base model as its opponent, and only the trainee's LoRA parameters get updated; the trainee is deliberately made to go first in half of randomized rounds and second in the other half, to avoid turn-order effects polluting the reward distribution and the training signal.

## The real point: how to make a clean comparison between methods

If you only look at NPO the method itself, honestly there isn't much to say — it's just OPRO with a larger feedback signal. But this paper does apply two pieces of engineering discipline worth learning, in service of fairly comparing NPO, GEPA, and GRPO — three very different kinds of methods: paired random seeds, and constrained decoding. Neither technique is original to this paper, but applying them to "comparing different prompt optimizers" is solid engineering practice, worth pulling out and looking at on its own.

### Paired random seeds (Shared Pseudorandomness)

**The problem to solve**: when comparing NPO, GEPA, and GRPO, if each method runs on independently randomly generated environments — e.g., a fresh, randomly mined Minesweeper board every time — the difference in final scores might not come from "one method actually being stronger," but from "happening to draw an easier level." This is a classic confound: you want to compare method quality, but random variation in environment difficulty gets mixed in.

**The mechanism**: for each environment, generate a batch of environment instances from a fixed set of random seeds, and have NPO, GEPA, and GRPO all share that same seed sequence. In other words, NPO's 135th rollout and GEPA's 135th rollout start from exactly the same board — the same mine positions, the same revealed numbers — with only the prompt or policy differing, which is what leads to different subsequent actions.

This is the same logic as "paired comparison" in statistics (e.g., a paired t-test, or comparing the same subjects before and after taking a drug in a medical trial): lock down the variable that creates noise so the group-to-group difference purely reflects the variable you actually want to measure. Here, the variable being locked down is "the randomness of the environment instance," and the variable being measured is "how good the optimization method is." Without locking the seed, you're comparing independent (unpaired) samples, where between-group variance gets diluted by random fluctuations in environment difficulty, requiring more samples to detect a real difference; locking the seed effectively pairs the samples, dramatically reducing noise and substantially raising statistical power.

The paper's Figure 3 demonstrates exactly this:

{{< image src="figure3-paired-seeds.png" alt="Two Minesweeper boards shown side by side, labeled as NPO's and GEPA's 135th rollout respectively, with identical mine positions and revealed numbers on both sides — only each model's chosen next move differs." caption="Figure 3 — Two boards generated from the same random seed, letting the comparison between NPO and GEPA exclude environment-difficulty interference. (Source: original paper's Figure 3.)" >}}

In the figure, the boards for "Rollouts #135, NPO" and "Rollouts #135, GEPA" (mine positions, revealed numbers) are identical — the only difference is the prompt, which leads the model to different judgments (NPO chose `[3 1]`, GEPA chose `[0 2]`).

{{< admonition info "This technique isn't original to the paper, but it's highly transferable" >}}
Using a fixed seed for paired comparison is a well-established, long-standing technique in experimental design, common in RL and bandit research. The paper simply applies it to "comparing different prompt optimizers" — it's a display of engineering discipline, not a methodological innovation. But precisely because of that, its transferable value is actually higher, and it's worth using in any A/B comparison experiment you design yourself.
{{< /admonition >}}

### The full mechanics of constrained decoding

**The problem to solve**: the paper mentions that early experiments found format errors (model output action strings that don't conform to what the environment requires) accounted for a non-trivial share of failure cases. If method A's failures mostly come from "getting the format wrong" rather than "actually making worse decisions," counting those failures against the final score unfairly penalizes A. They want to separate "decision quality" from "format-following ability," and only evaluate the former.

**Step 1: how to "mask" illegal tokens**

At each step of generating the next token, the model originally computes a probability for every token in the vocabulary. What constrained decoding does is set the probability of illegal tokens to 0, keep only the legal ones, and renormalize into a probability distribution. A simple numerical demonstration: suppose at some step the raw probabilities are \( A: 0.4 \), \( B: 0.3 \), \( C: 0.1 \), \( D: 0.1 \), \( E: 0.1 \), but only \( A \) and \( B \) are legal at this step. The approach sets \( C \), \( D \), \( E \) to 0, leaving \( A=0.4 \) and \( B=0.3 \), which sum to 0.7; dividing by 0.7 gives \( A \approx 0.571 \), \( B \approx 0.429 \).

The paper's formula (equivalent to the calculation above):

$$q(t \mid s) = \frac{\exp(z_t(s))}{\displaystyle\sum_{u \in A(s)} \exp(z_u(s))}, \quad t \in A(s)$$

where \( s \) is the prefix string generated so far, \( A(s) \) is the set of legal next tokens given that prefix, and \( z_t(s) \) is the model's raw score (logit) for token \( t \).

**Step 2: why you need a "tree"**

Masking at a single step only solves "which token to pick at this step," but a complete action string (e.g. `[3,4]`) usually takes several tokens to spell out, and which tokens are legal at each step changes depending on what's already been generated.

For example: suppose the environment only allows two legal actions, `[3,4]` and `[2,5]`. Initially the only legal first token is `[`; after `[`, the legal next options become `3` or `2`; after choosing `3`, only `,` remains legal; then only `4`; and finally only `]`. The "set of legal tokens" is different at every step and depends on what came before — this is exactly why you need a **prefix trie**. Each node in the tree represents "the prefix generated so far," the edges leaving a node are "the legal next tokens," and reaching a leaf node means you've assembled one complete legal action:

```
Root (nothing generated yet)
  --[--> "["
           --3--> "[3" --,--> "[3," --4--> "[3,4" --]--> "[3,4]" (leaf)
           --2--> "[2" --,--> "[2," --5--> "[2,5" --]--> "[2,5]" (leaf)
```

**Step 3: connecting masking to the tree**

At every node in the tree, the same thing is repeated: look at which legal child nodes exist under this node, mask-and-renormalize the raw scores of those legal options, sample one according to that probability, move to the corresponding child node, and repeat until reaching a leaf.

Walking through the two-action example above and computing the full probability of `[3,4]`: the root's only legal next step is `[`, so its probability is fixed at 1; the `[` node has two genuine branch points, `3` and `2` — suppose masking and renormalizing gives \( q(3\mid[)=0.6 \), \( q(2\mid[)=0.4 \); the subsequent `[3`, `[3,`, `[3,4` nodes each have only a single legal option, so their probabilities are likewise fixed at 1. The probability of the full path is the product:

$$P([3,4]) = q([\mid \text{root}) \times q(3\mid[) \times q(,\mid[3) \times q(4\mid[3,) \times q(]\mid[3,4) = 1 \times 0.6 \times 1 \times 1 \times 1 = 0.6$$

The key effect: apart from the genuine branch point of "choosing 3 vs. choosing 2," every other step has only one option (probability fixed at 1), so the probability of the entire path is essentially determined by "the genuine decision branch points" alone — format-related tokens (`[`, `,`, `]`) have no effect on the final probability whatsoever.

The paper's Figure 11 draws out a concrete four-action example of this trie, with numbers attached:

{{< image src="figure4-constrained-decoding-trie.png" alt="A diagram of a prefix trie, with the root branching into multiple paths, each node labeled with the legal transitions to the next token and their corresponding probabilities, and leaf nodes representing complete legal action strings." caption="Figure 4 — A prefix trie for constrained decoding. (Source: original paper's Figure 11; the tree structure is taken from the original figure, but the specific numbers on the branches were constructed by this article for illustration and are not the original figure's numbers — see the note below.)" >}}

{{< admonition warning "The numbers in this figure are constructed for illustration, not the original figure's numbers" >}}
After PDF text extraction, the correspondence between edge labels and branches could not be reliably reconstructed (some of the numbers don't sum to 1, and it's unclear whether this is an extraction misalignment or a misread correspondence). So the specific numbers used above in "Step 3" (0.6, 0.4) are demonstration numbers set by this article, not the original figure's numbers — they simply borrow the same tree structure for the sake of explanation. If you need the precise values, you'll need to consult the original PDF.
{{< /admonition >}}

**An additional edge case**: if the model hasn't yet generated the token marking the end of reasoning before its reasoning-token budget runs out, the paper doesn't simply count this as a failure — doing so would conflate "poor decision quality" with "not knowing you're about to run out of tokens." Instead, right before the budget runs out, an end-of-reasoning marker is forcibly inserted, followed by a small reserved action budget, still forcing the model to pick one of the legal actions.

Constrained decoding itself isn't original to this paper — locally constrained decoding and the "local product of experts" idea have prior literature, and grammar-constrained generation is common in industry too (the paper cites lm-format-enforcer, and tools like Outlines are built on the same principle). The paper is simply applying existing tools to the specific goal of eliminating format noise from cross-method comparisons.

### Local vs. Global: the trade-off between two probability algorithms

The paper mentions two ways to compute "the probability of a leaf node (a complete action)" — it adopts one of them, with the other included only for comparison.

- **Local** (the one this paper adopts): at every node reached in the tree, first mask illegal tokens and renormalize the legal options, then step down — this is the step-by-step process described in "Step 3" above.
- **Global**: apply no masking or renormalization along the way at all; let the model use its original, freely-generated probabilities, and directly multiply together the probability at every step of the entire path. Only after the products for all legal actions (leaves) have been computed does a single normalization happen across those leaves.

Global requires a technique called "teacher forcing": normal generation has the model producing tokens one after another on its own; teacher forcing instead force-feeds the model a specified piece of content and asks only "given this content so far, what's your probability distribution for the next token?" — letting you compute the probability of "the model generating this particular fixed piece of text," even if the model itself never actually generated it on its own. The full Global procedure has five steps: first enumerate every legal complete action string; for each candidate string, use teacher forcing to ask the model's original, unmasked step-by-step probabilities in order; multiply those probabilities together to get that candidate's raw score; repeat for every other candidate; finally, normalize all the candidates' raw scores together, and sample or select the final action from that. Because the first step requires enumeration, Global only works when the action set is finite and enumerable — it can't be done if the legal output is open-ended natural language.

Using a self-constructed set of numbers (again for illustration, not the original figure's numbers) to compare the two approaches' results. Suppose the model's original (freely generated, unmasked) raw probability at each step is:

| Path | \( P([) \) | Branch token | \( P(\cdot\mid[) \) | \( P(,\mid\cdot) \) | Next digit | \( P(\cdot\mid\cdot,) \) | \( P(]\mid\cdot) \) |
|---|---|---|---|---|---|---|---|
| `[3,4]` | 0.05 | `3` | 0.02 | 0.90 | `4` | 0.015 | 0.85 |
| `[2,5]` | 0.05 | `2` | 0.015 | 0.88 | `5` | 0.01 | 0.65 |

(The difference in confidence between `0.85` and `0.65` for "should I close with `]` here" is purely a coincidence caused by the model's tokenizer or training data, and has nothing to do with the actual decision of "which action to pick" — which is exactly the problem.)

**Global algorithm** (multiply straight through, normalize only at the end):

$$P([3,4])_{\text{raw}} = 0.05 \times 0.02 \times 0.90 \times 0.015 \times 0.85 \approx 0.0000115$$
$$P([2,5])_{\text{raw}} = 0.05 \times 0.015 \times 0.88 \times 0.01 \times 0.65 \approx 0.0000043$$
$$P([3,4]) = \frac{0.0000115}{0.0000115+0.0000043} \approx 0.73,\qquad P([2,5]) \approx 0.27$$

**Local algorithm** (mask-then-renormalize at every node): only the `[` node is a genuine branch point, \( q(3\mid[) = 0.02/(0.02+0.015) \approx 0.571 \), \( q(2\mid[) \approx 0.429 \), and every other node's probability is fixed at 1, so \( P([3,4]) = 0.571 \), \( P([2,5]) = 0.429 \).

Side by side:

| | `[3,4]` | `[2,5]` |
|---|---|---|
| Global | 0.73 | 0.27 |
| Local | 0.571 | 0.429 |

The large gap Global produces — 0.73 vs. 0.27 — comes largely from the `]` token's raw confidence values (0.85 vs. 0.65), and that confidence difference is just format-closing noise, unrelated to the real decision of "which action to pick." Local, by locking "no other choice" nodes to 1, ends up with only the genuine decision branch points determining the final probability — closer to the signal of "which action the model really wants to pick." This is also the paper's reasoning for choosing Local: to make sure that when comparing different optimization methods, the probability differences observed reflect decision quality, not the format-closing token happening to be more confident.

Global's advantage is that it's exactly equal to the conditional probability you'd get from Bayes' theorem — this is general knowledge from probability theory that the paper doesn't discuss at all, but it's worth noting. Imagine placing no constraints at all, letting the model generate freely, and discarding and retrying whenever it produces an illegal action (this is rejection sampling), repeating until a legal action is drawn. The distribution this process ultimately converges to, written out via Bayes' theorem, is exactly:

$$P(\text{a legal action} \mid \text{that action is legal}) = \frac{P(\text{that action, raw unmasked probability})}{\sum_{\text{all legal actions}} P(\text{raw unmasked probability})}$$

This is exactly the Global algorithm's own formula. In other words, Global is the probability distribution that "keep regenerating and discarding illegal results until a legal one is drawn" ultimately converges to — fully preserving the model's true original relative confidence across every legal option, undistorted. Local, by locally renormalizing at every node it passes through, actively erases some of the model's original confidence information about tokens like format-closers — this isn't accidental error, it's a systematic bias that necessarily happens by the algorithm's design, trading that cost for the efficiency of "generate once and you're done, no need to enumerate candidates."

The trade-off summarized in a table:

| | Local | Global |
|---|---|---|
| Compute cost | Low (a single autoregressive pass suffices) | High (needs one teacher-forcing pass per candidate) |
| Equal to the model's true conditional distribution over raw confidence? | No — systematically distorted by format-token noise | Yes — mathematically equivalent to the distribution from rejection sampling |
| Suited for | When you want "decision quality" and want to actively remove format noise (this paper's situation) | When you need to precisely know the model's true relative confidence across options, e.g. calibration analysis |
| Guarantees legal output? | Yes | Yes |

Worth emphasizing: Local vs. Global was never a trade-off over "whether to guarantee format compliance" — both guarantee 100% legal output, since the set of legal actions is itself finite and enumerated in advance. The only difference is how the probability is distributed among the legal options.

## Main results

### Rollout efficiency: NPO only has an edge when the teacher is strong

The paper's Figure 4 compares NPO and GEPA on IFBench and HotpotQA (multi-hop QA, requiring you to connect information across multiple documents to find the answer) when swapping in different teachers (Qwen3-8B, DeepSeek-V4-Flash, GPT-5.5):

{{< image src="figure5-teacher-strength.png" alt="Line charts comparing NPO and GEPA on IFBench and HotpotQA, with three teacher models of different strength, showing score convergence curves as rollout count increases." caption="Figure 5 — NPO and GEPA's performance on two tasks under different teachers. (Source: original paper's Figure 4.)" >}}

NPO's performance clearly improves with a stronger teacher: with GPT-5.5 as teacher, NPO converges fastest and reaches the highest final score, matching or beating GEPA on both tasks using fewer rollouts. GEPA, in contrast, is much less affected by the choice of teacher: GEPA paired with GPT-5.5 performs about the same as GEPA acting as its own teacher (paired with Qwen3-8B).

There's a very real limitation here, though — and it's a separate confound beyond the "hidden problem with batch sampling" discussed earlier: NPO's reflection minibatch size is 50 (IFBench) or 40 (HotpotQA), while GEPA uses its original paper's default of 3 — a 10 to 15x difference. Even though the two methods' final "total rollout budgets" end up close (NPO 3,500/6,800, GEPA 3,593/6,871), this means NPO sees far richer feedback at every revision than GEPA does. The paper never runs the clean control experiment of "also bumping GEPA's minibatch to 50 and rerunning." In other words, the claim "NPO is more efficient than GEPA" conflates two variables — "is a single lineage better than a pool-search architecture" and "which method's revisions see more feedback information" — and the paper doesn't disentangle them itself. The result itself is credible, but exactly what it's winning on can't be confidently attributed.

### Cross-model prompt transfer: can a prompt tuned on a small model be dropped straight into a large one?

The paper's Figure 5 tests taking a prompt optimized on a small model (Qwen3-8B, Llama-3.1-8B) and applying it verbatim to larger models, without re-optimizing:

{{< image src="figure6-prompt-transfer.png" alt="A bar chart showing the distribution of performance gains when a prompt optimized on a small model is transferred to models of different sizes and families, with within-family transfer bars generally higher and more stable." caption="Figure 6 — Performance gains from transferring a prompt across models. (Source: original paper's Figure 5.)" >}}

Transfer within the same model family is strongest, generally staying positive — e.g., a prompt optimized on Qwen3-8B transferring to Qwen3-14B and Qwen3-32B. Cross-family transfer (e.g. to the Llama family) is also mostly positive, but with smaller and more variable gains. A few exceptions are negative (e.g. IFBench with a GEPA-tuned prompt transferring to some models shows -0.07, -0.002), but these are a minority, not the general pattern.

What this section actually demonstrates is a practical advantage of prompt optimization over weight-level RL: it transfers without retraining. But note that NPO and GEPA perform similarly here — this isn't an advantage unique to NPO.

### Comparison with GRPO: no overall winner

The paper's Figure 6 compares NPO, GEPA, and GRPO across 22 TextArena (a text-based game platform for testing LLM agents) game environments, controlling for the same rollout budget:

{{< image src="figure7-textarena-results.png" alt="A bar chart comparing performance gains from NPO, GEPA, and GRPO across 22 TextArena game environments, with the relative ranking of the three methods inconsistent across different games." caption="Figure 7 — Performance gains from three optimization methods across 22 game environments. (Source: original paper's Figure 6.)" >}}

There's no overall winner: NPO and GEPA perform roughly comparably, with neither systematically better; GRPO is clearly stronger on some tasks where prompt optimization is less effective. Take the game 2048 as an example:

| Method | Performance gain |
|---|---|
| GRPO | +6.9 |
| GEPA | +0.90 |
| NPO | +0.22 |

GRPO's gain here far exceeds the other two. On some two-player strategy games (Chess, ConnectFour, Crusade), all three methods perform poorly, some even negative — suggesting these tasks may not be intrinsically well-suited to any of the three.

The paper explicitly points out that this result differs from the common impression in prior literature that "GEPA systematically outperforms RL" — no sign here of GEPA broadly beating GRPO. Honestly, this is one of the more honest and valuable findings in the paper — more on that in the next section.

### Checking for evaluation-answer leakage

Because NPO paired with a strong teacher often produces much longer prompts than GEPA, the paper additionally checks something: whether these prompts accidentally "memorized" correct answers from the training or validation set, meaning the score improvement is just data contamination rather than genuine capability gain.

{{< image src="figure8-answer-leakage.png" alt="A line chart showing that the overlap between optimized prompts and training-set answers rises steadily over iterations, while overlap with validation-set answers stays near zero, with the two lines clearly diverging." caption="Figure 8 — Change in overlap between optimized prompts and training/validation-set answers (HotpotQA). (Source: original paper's Figure 7.)" >}}

The overlap between optimized prompts and training-set answers rises naturally over iterations — which is expected, since prompt optimization is supposed to extract useful information from training examples — but overlap with validation-set answers barely increases at all, and manual inspection confirms that the small amount of overlap that does exist is just training and validation examples happening to share the same answer, not direct leakage of validation questions themselves. The conclusion: the observed performance gains are unlikely to be caused by evaluation-answer leakage. This is the paper policing its own experimental integrity — a bonus, not a core contribution.

## What's actually worth taking away from this paper

### The paper's own contribution is, honestly, modest

Laying out the preceding sections, NPO's core method — replacing pool-based search with sliding-window feedback — is an incremental modification of OPRO, not a new mechanism. Its headline claim, "NPO matches or beats GEPA with fewer rollouts," conflates two variables because the reflection minibatch sizes aren't matched (NPO's 50 vs. GEPA's 3), and the paper never disentangles them itself — so exactly what it's winning on can't be confidently attributed.

The contribution that actually holds up better is corrective: it overturns the prior-literature impression that "GEPA systematically outperforms RL (GRPO)," honestly showing that all three methods win and lose in different places, with no overall champion. This kind of "debunking an overclaim" value is usually more credible than a positive claim. The gold-answer-leakage check is a bonus, not a core contribution.

The one-sentence summary: this paper's contribution reads close to a clean ablation/baseline study, with methodological innovation close to zero. Its real value lies in the three points below — and all three are independent of NPO the method itself; they'd stand on their own even detached from this paper.

### Lesson one: paired random seeds for fair comparison

Same logic as the paired design in statistics: lock down the variables that create noise, so that the between-group difference cleanly reflects the variable you actually want to measure. This principle applies whenever you want to compare any two systems or pipelines in the future — not limited to AI.

### Lesson two: the full mechanics of constrained decoding

A prefix trie plus per-node masking/renormalization is the underlying logic behind constrained-generation tools like Outlines. It's not enough to just "know this feature exists" — knowing concretely how it operates token by token means you won't get stuck when you need to implement something similar yourself.

### Lesson three: the rule for choosing between Local and Global

This is the most technically substantial part of the whole write-up. Local has low compute cost and completes in a single pass, but systematically erases the raw confidence of format tokens, keeping only the genuine decision branch points — suited to situations where you care about "decision quality" and want to actively remove format noise. Global is mathematically equivalent to the true conditional probability you'd get from rejection sampling, faithfully preserving the model's original confidence, but at a high compute cost — needing one teacher-forcing pass per candidate — suited to situations where you need to precisely know the model's true relative confidence, e.g. calibration analysis.

The more general idea underneath this is the equivalence between rejection sampling and conditional probability. This is a general-purpose tool in probability theory and MCMC (Markov Chain Monte Carlo) methods, not limited to this one constrained-decoding scenario — worth noting down as an independent piece of knowledge.

## Conclusion

NPO's surface-level claim is that "if the feedback is rich enough and the teacher is strong enough, a single lineage of prompt revisions can match or even beat complex search-based methods." The experimental results partially support this claim, but because the reflection minibatch sizes aren't matched, the two possible reasons — "winning because the architecture is simpler" versus "winning because it gets more feedback information" — are never disentangled, so this can only be counted as partially verified, not settled.

What's really worth keeping is the experimental methodology this paper demonstrates: using paired random seeds to lock down environment-difficulty noise, using constrained decoding with a prefix trie to separate format noise from decision quality, and clearly laying out the trade-off between the Local and Global probability algorithms. All three of these are independent of NPO the method itself, yet they're the most durable part of what this paper leaves behind — the next time you need to design a fair comparison between any two systems, this engineering discipline is directly reusable.

---
# weight: 1
title: "RecursiveMAS: Multi-Agent Systems That Think in Vectors"
date: 2026-09-10
lastmod: 2026-09-10
draft: false
description: "How RecursiveMAS swaps text between AI agents for continuous vectors, making multi-agent systems differentiable end-to-end with just 0.31% trainable parameters."
featuredImage: "featured-image.png"

tags: ["Large Language Model", "Multi-Agent", "Fine-Tuning", "Inference Optimization"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## Introduction

Nearly every multi-agent system (MAS) today looks the same: Agent A writes a chunk of text, hands it to Agent B, B reads it and writes another chunk of text for C. The design feels natural, because LLMs are fundamentally text-emitting machines. But that default quietly bakes in a lot of waste.

The paper "[Recursive Multi-Agent Systems](https://arxiv.org/abs/2604.25917v1)" (a joint effort from UIUC, Stanford, NVIDIA, and MIT) makes a bold claim: **agents never actually need to understand human-readable text from each other**. Since the receiving side is also a model, why not just pass along the final-layer hidden state directly? That entire round trip — projecting onto a vocabulary with over a hundred thousand dimensions, decoding token by token, then re-embedding it on the other end — can simply be skipped.

And skipping it brings a bonus: vectors are continuous, so the entire communication path becomes differentiable. The whole agent team can be treated as one giant computation graph and trained end-to-end — while updating only 0.31% of the parameters.

{{< admonition abstract "Key Takeaways (TL;DR)" >}}
- **The communication medium switches from text to vectors**: agents pass the final-layer hidden state (a "latent thought") directly, eliminating the triple cost of projecting to the vocabulary, decoding token by token, and re-embedding on the receiving end.
- **The communication path becomes differentiable**: through a residual RecursiveLink (an Inner version for self-loops, an Outer version for cross-model translation), the entire MAS becomes one computation graph, optimized end-to-end via two-stage training (individual warm-up + team-wide co-optimization).
- **Only 0.31% of parameters are trained**: the LLM backbones stay fully frozen; a 13.12M-parameter RecursiveLink carries the whole system, and it still beats LoRA and full-SFT on accuracy.
- **More recursion rounds end up being faster**: cutting the massive vocabulary projection and re-prefilling lets RecursiveMAS run 2.4x faster and use 75.6% fewer tokens than a text-based recursive baseline at \( r=3 \).
{{< /admonition >}}

This article walks through the whole mechanism from the ground up: how the communication medium changes, how dimensions get aligned across different model families, how the two-stage training is designed, and one genuinely counterintuitive result — why running *more* rounds of inference ends up being *faster* than the text-based version.

## Why Text Is Such an Expensive Communication Medium

### Pain Point 1: Every Word Requires a Lookup in a Massive Dictionary

LLMs generate text auto-regressively. For every token produced, the hidden-layer vector (dimension \( d_h \), commonly around 4096) has to be projected onto the entire vocabulary space (\( |V| \), commonly 100K-150K). Because \( |V| \gg d_h \), this single step produces an \( O(m|V|d_h) \) cost purely for inter-agent communication.

Here's an analogy: imagine two aliens who genuinely have telepathy, but are forced to type their thoughts out letter by letter on an Earthling typewriter, and the receiver then has to translate that text back into brainwaves. Those two extra layers of translation are pure loss — because the receiver was never human to begin with.

### Pain Point 2: Discrete Text Severs Backpropagation

Text is discrete, and that fact directly severs the backpropagation chain that neural networks depend on most.

Even if you apply mathematical tricks (like a softmax soft approximation) to force the text space to become differentiable, the paper's Theorem 4.1 proves that across multiple rounds of back-and-forth communication, gradients inevitably decay exponentially to zero.

A proposal-review analogy makes this concrete: if Agent A prints a proposal on paper and hands it to Agent B, and the boss eventually says the proposal is terrible, that "rejection anger" is extremely hard to trace precisely back through the paper trail to the exact sentence A got wrong. But if everyone is working on the same shared cloud document (a continuous latent space), you can trace all the way back and correct it.

The end result: we cannot treat the whole agent team as one unified entity for system-level joint optimization. Agent A never learns exactly what it should change.

### Pain Point 3: Only Two Bad Options Remain for Making the Team Stronger

Historically, there have only been two ways to make an MAS stronger. Tweak the prompt — that treats the symptom, not the cause, since the model itself doesn't get any smarter. Or fully fine-tune every model in the team (often 7B or 70B parameters each) separately, which is completely impractical given the VRAM and compute cost alone.

And even if you train every agent to be individually strong, that doesn't mean they'll have chemistry as a team. What's missing is a lightweight method specifically for training "teamwork" itself. This is also why frameworks like [ChatEval](../chateval/), where multiple agents debate each other purely through text, still can't escape the three pain points above — the communication medium never changed, so the pain points never go away either.

## Core Idea: Treating the Hidden State Itself as a "Thought"

{{< image src="architecture.png" alt="RecursiveMAS's overall architecture diagram: Agent A1 self-loops through the Inner Link to generate latent thought vectors, which are then transformed via the Outer Link and concatenated into Agent A2's input sequence; only the final agent decodes into text, and a Looping label on the right indicates the whole flow wraps back to the start." caption="Figure 1 — Overall architecture. Note the Looping label in the bottom right: information isn't done once it completes one pass — the final agent's thoughts get fed back to the first agent. (Source: original paper.)" >}}

In a standard inference pipeline, the hidden state \( h \) produced by the model's final layer gets projected onto the vocabulary and turned into a concrete word like "apple." RecursiveMAS removes that step entirely and treats \( h \) directly as the agent's **latent thought** — a high-dimensional vector that carries far richer semantics than a single discrete token.

The key property this unlocks is differentiability. Gradients can pass straight through the communication medium, flowing all the way from Agent B back to Agent A.

The second core idea is **treating each agent as one layer of a network**. Instead of viewing each agent as an independent individual, view it as one block inside an oversized Transformer: Agent A is the early layers, Agent B is the middle layers, and the whole MAS forms one unified computation graph. The paper formalizes this process as \( S^{(0)} \to S^{(1)} \to \dots \to S^{(n)} \), with the system state continuously refined across recursion rounds.

So why loop at all? It's the same logic as a person "thinking it over again" when facing a hard problem. Through repeated recursion, the system can trade time for greater reasoning depth **without adding a single new parameter**.

## Architecture: How RecursiveLink Is Built

Information flows between agents through RecursiveLink, which comes in two forms.

{{< image src="recursivelink-design.png" alt="A side-by-side comparison of the Inner and Outer RecursiveLink structures: both are a Linear, GELU, Linear stack with a residual connection, and the only difference is that the Outer version has an extra linear projection layer on its residual path." caption="Figure 2 — Inner and Outer differ in exactly one place: the Outer version's residual path has one extra projection matrix, used to align dimensions across different models. (Source: original paper.)" >}}

### Inner RecursiveLink: The Elevator Inside the Brain

When an agent is in "keep quiet and keep thinking" mode, it needs a mechanism to route deep-layer thoughts back to the shallow input layer. The paper calls this a dense-to-shallow transition.

$$\mathcal{R}_{in}(h) = h + W_2 \sigma(W_1 h)$$

\( W_1 \) and \( W_2 \) are lightweight linear layers, and \( \sigma \) is GELU.

Think of it as an elevator: the \( h \) produced at the model's top layer is a highly abstract "conclusion," and the elevator \( \mathcal{R}_{in} \) carries it from the top floor back down to the ground floor, translating it into a feature distribution the input layer understands, so the model can keep thinking based on that conclusion.

In practice this runs as a loop: generate vector 1 → pass through \( \mathcal{R}_{in} \) → append to the input sequence → generate vector 2. **Not a single word is produced during this entire process** — the tail of the input sequence gradually accumulates \( m \) consecutive latent thought vectors.

### Outer RecursiveLink: The Cross-Model Translator

When Agent A hands off to Agent B, which runs on a completely different architecture, it runs into two obstacles: the dimensions may differ (say, 2048 vs. 4096), and the semantic spaces differ too. Qwen's brainwaves are gibberish to Llama.

$$\mathcal{R}_{out}(h) = \mathbf{W_3} h + W_2 \sigma(W_1 h)$$

Compared to the Inner version, the only addition is that \( W_3 \), responsible for the physical dimension projection.

A common misunderstanding is how the receiving side consumes these vectors. **It's not a replacement, it's a fusion**: Agent B still keeps its own system prompt and the original question — the system converts B's text prompt into embeddings, then concatenates the \( m \) vectors sent by A into reserved slots. The paper's own prompt template literally has a placeholder like `{Latent Thought Embeddings}`.

### The Residual Connection Is the Anchor

That unassuming `+ h` is the single thing that lets this whole system survive many rounds of recursive training, for two reasons.

**On the semantic side**: the original \( h \) already carries strong semantics. Without adding \( h \) back in, a randomly initialized \( \mathcal{R} \) network would simply destroy that information. With it, the network only needs to learn a "small shift in distribution," which is a far easier learning problem.

**On the mathematical side**: in a recursive system, gradients have to travel through many loops and dozens of agents. Without a residual, the multiplicative effect of the chain rule would make gradients vanish rapidly. With the residual in place,

$$\frac{\partial (h+F(h))}{\partial h} = 1 + F'(h)$$

that **1** guarantees that even if the transformation path \( W_2\sigma(W_1 h) \) alongside it has learned nothing at all, the error signal can still flow back to the previous agent unchanged. This is really the other side of Theorem 4.1: the same theorem first proves that discrete text can't stop gradient decay, then shows that a continuous space paired with a residual can.

This isn't just a theoretical claim — the authors ran an ablation to back it up:

{{< image src="table-design-ablation.png" alt="A narrow four-row table comparing the accuracy of four RecursiveLink designs — 1-Layer, Res+1-Layer, 2-Layer, and Res+2-Layer — across three benchmarks, with the residual two-layer version scoring highest on all three." caption="Table 1 — Ablation on the RecursiveLink design. At the same layer count, the gap between having a residual and not is substantial. (Source: original paper.)" >}}

## Training: Individual Fundamentals First, Then Team Chemistry

{{< image src="training-pipeline.png" alt="A two-stage training pipeline diagram: the top half shows each agent independently performing inner-loop warm-up in parallel, aligning latent thoughts with the real distribution via a regression loss; the bottom half shows the whole MAS unrolled across multiple recursion rounds for outer-loop co-training, with blue arrows for the forward pass and red for backpropagation." caption="Figure 3 — Two-stage training. Each agent trains on its own in the top half; the whole system trains together, unrolled, in the bottom half. (Source: original paper.)" >}}

If RecursiveLink is the hardware, the training algorithm is the software that gives it a soul. The authors split it into two stages.

### Stage One: Inner-Loop Warm-up

Before chaining agents together, each agent first has to learn to "write invisibly" — making sure the vectors output by the Inner Link align precisely, in semantic terms, with real words.

This uses teacher forcing. Think of a coach holding your hands at the pool's edge while you practice a swimming stroke: during warm-up, the model never actually has to consume its own erroneous output vectors — it's given the ground-truth answers and learns the mapping under normal conditions.

Specifically, when the model is processing the \( t \)-th word and produces hidden state \( h_t \), it's forced so that \( \mathcal{R}_{in}(h_t) \) resembles the embedding of the **next word**:

$$\mathcal{L}_{in} = 1 - \cos(\mathcal{R}_{in}(h_t), \text{Emb}(y_{t+1}))$$

Cosine similarity is used instead of L2 distance because in vector space, "direction" is what represents the core semantics.

Once this stage finishes, the model has learned to think while holding its breath: it never says a word out loud, but every single vector it produces precisely carries the semantics of the next word.

### Stage Two: Outer-Loop Joint Optimization

With the fundamentals in place, it's time for full-system practice. There's no coach holding your hand anymore — the vector A produces goes straight to B, B passes it to C, and it may even loop back to A.

The flow is: the system performs purely vector-based recursive propagation for a preset number of rounds (say \( r=3 \)) → only on the final round does the final agent emit a text answer → that answer is compared against the ground truth to compute a cross-entropy loss. This loss represents the whole team's overall error across those three rounds of collaboration.

### Gradient Accumulation and Credit Assignment

This is where engineering and math come together most elegantly. Because everything passed between agents is a continuous vector, the gradient produced by the loss can flow along the computation graph across different agents and across different recursion rounds, all the way back to the start — essentially BPTT (backpropagation through time) from RNN training, unrolling the network along the time axis before backpropagating.

There's an implementation detail worth pulling out on its own: across three rounds of computation, **the same OuterLink gets used multiple times**, producing several sets of gradients. By the multivariable chain rule, the framework automatically sums the gradients from each round (`grad += new_grad`). The significance of this is that it forces the OuterLink to become an "all-purpose translator": whether it's the early stage of discussion (round 1) or the wrap-up stage (round 3), it has to provide accurate enough translation either way.

Credit assignment is also handled automatically by this same mechanism. If the final answer is wrong, the gradient tells the system whether round 1's Agent A wrote a bad plan, or round 2's Agent B reviewed it too carelessly, and precisely corrects the link parameters that dragged the team down.

### Cost: Training Only 0.31% of the Parameters

{{< image src="table-cost-analysis.png" alt="A three-row table comparing peak GPU memory, trainable parameter count, estimated cost, and average accuracy for LoRA training, Full-SFT, and RecursiveMAS, with RecursiveMAS scoring best on all four metrics." caption="Table 2 — The entire LLM backbone stays frozen throughout; only the 13.12M-parameter RecursiveLink is trained. (Source: original paper.)" >}}

Throughout the entire training process, the LLM backbone — several billion parameters — remains **completely frozen**. The only thing actually trained is RecursiveLink: 13.12M parameters, 0.31% of the total. Peak GPU memory is 15.29 GB, estimated cost is $4.27, and average accuracy is actually higher than both LoRA training and full-SFT.

This is a classic case of leverage: don't touch the model itself, just teach it how to talk to its teammates.

## Inference: Why Doing More Inference Steps Is Actually Faster

This is the most counterintuitive part of the whole design. The system loops multiple times in latent space, and each agent runs \( m \) rounds of inference per loop — so how could this possibly be faster than a traditional MAS?

There are three concrete reasons.

| Traditional text-based MAS | RecursiveMAS |
|---|---|
| Every step requires projecting onto a 150K-dimension vocabulary matrix, \( O(\|V\|) \) | InnerLink is just a small \( d_h \times d_h \) matrix (e.g., 4096×4096) — tens of times less compute |
| Hundreds of tokens are needed to fully spell out a chain of reasoning | A latent step count \( m \) of around 80 is enough to carry the full semantics |
| The next agent has to re-embed and re-prefill after receiving text | Vectors are inserted seamlessly, skipping re-encoding and re-prefilling entirely |

The first point is by far the biggest saving. A traditional model has to pay one massive LM-head projection for every single token it produces; RecursiveMAS replaces that entire cost with small matrix operations.

The third point is often overlooked but very real: every time the text version hands off, the receiving side has to re-tokenize, re-embed, and re-run a prefill on that chunk of text — effectively encoding the same information twice. Vectors are inserted directly, so this cost disappears entirely.

As for the 80 steps in the second point, that number wasn't picked arbitrarily:

{{< image src="figure-latent-length.png" alt="A line chart with latent thought length m on the x-axis, ranging from 0 to 128, and three curves for MATH500, GPQA-D, and LiveCodeBench accuracy, all of which plateau after roughly m=64-80." caption="Figure 4 — Ablation on latent thought length. All three benchmarks enter a plateau around 64-80 steps, with diminishing returns beyond that. (Source: original paper.)" >}}

### How Different Collaboration Topologies Connect

**Mixture style (a many-to-one star topology)**: the summarizer's prompt has several reserved slots (like `{Math_Latent}`, `{Code_Latent}`); each expert's vectors pass through their own \( \mathcal{R}_{out} \) transform and get filled in simultaneously, so the summarizer reads every expert's "brainwaves" in a single forward pass. It's also bidirectional — at the start of the next round, the summarizer's summary vector gets broadcast back to every expert, letting them adjust their direction based on the previous round's collective consensus.

**Deliberation style (calls out to external tools mid-process)**: there's a fundamental tension here — the latent space doesn't speak, but external tools only understand text. The solution is called **late decoding**: for the first several rounds, the Tool-Caller and Reflector stay entirely in hold-your-breath mode, using vectors alone to align on logic like "what to search for" or "what code to write." Only on the final round does the Tool-Caller switch modes and use the LM head to emit real text (e.g., `<search>...</search>`), at which point the external tool finally gets involved.

In plain terms, this is "look before you leap." It avoids the token waste of a model repeatedly trying, erroring out, and correcting itself in text space — instead, it proofreads internally first, so that when it finally puts pen to paper, it nails it in one shot.

Here's the whole inference flow pulled together:

```
① Input              Question converted into an embedding sequence
② Agent Internal     Run m inference steps, generating m latent vectors via R_in and appending them
③ Cross-Agent         The m vectors are translated via R_out and concatenated into the next agent's instruction sequence
④ System Recursion    Loop through r large rounds
⑤ Final Output        Only on the final round does the final agent switch to the LM Head to decode text word by word
```

## Experimental Results

### Efficiency and Accuracy Are No Longer a Trade-off

{{< image src="table-main-results.png" alt="A large table comparing Recursive-TextMAS and RecursiveMAS across three recursion round counts and six task categories on accuracy, execution time, and token usage, with RecursiveMAS being simultaneously more accurate, faster, and cheaper in every configuration." caption="Table 3 — Main results table. The three blocks correspond to recursion rounds 1, 2, and 3, with the rightmost column showing the relative improvement over the text-based version. (Source: original paper.)" >}}

Taking \( r=3 \) as an example, compared to the text-based recursive baseline (Recursive-TextMAS):

| Metric | Recursive-TextMAS | RecursiveMAS |
|---|---|---|
| MATH500 accuracy | 85.8% | **88.2%** |
| Execution time | 6,010s | **2,320s** (2.4x speedup) |
| Token usage | (baseline) | **75.6% fewer** |

What's more notable than any single number is the trend: **the more recursion rounds, the more exaggerated RecursiveMAS's cost advantage becomes**. Every extra round the text-based version runs adds another full round of decoding overhead — both time and tokens keep stacking up. RecursiveMAS shifts the communication burden into an extremely lightweight vector space, so the marginal cost of an extra round is much smaller.

{{< image src="figure-token-reduction.png" alt="Three side-by-side bar charts corresponding to recursion rounds 1, 2, and 3, comparing token usage ratios between RecursiveMAS and Recursive-TextMAS; as the round count increases, the gap widens from an average of 34.6% to 75.6%." caption="Figure 5 — Token savings amplify with recursion depth: 34.6% saved at round 1, growing to 75.6% by round 3. (Source: original paper.)" >}}

### Recursive Systems Have Their Own Scaling Law

{{< image src="figure-performance-landscape.png" alt="Top half shows four heatmaps with training recursion rounds on the x-axis and inference recursion rounds on the y-axis, with darker colors indicating higher accuracy concentrated in the top-right corner; bottom half shows three groups of bar charts comparing individual roles against RecursiveMAS's accuracy under mixture-style, deliberation-style, and distillation-style collaboration modes." caption="Figure 6 — Top: a performance landscape across training and inference recursion depth. Bottom: performance across three collaboration modes. (Source: original paper.)" >}}

The heatmap should be read both horizontally and vertically. Reading horizontally shows **test-time compute scaling**: for the same trained model, looping more at inference time steadily improves accuracy. Reading vertically shows the effect of training-time recursion depth. When both increase together, the system lands in the upper-right highland of the plot — meaning a model that went through deep recursion during training is better at leveraging extra recursion steps at inference time to correct its own errors.

This follows the same logic as today's reasoning models that pursue "more thinking time" — the difference is that RecursiveMAS does it in a much cheaper resource: latent space.

The bottom half shows the architecture isn't picky about formation:

- **Mixture style**: math, coding, and science experts collaborate in parallel, beating the single strongest expert's accuracy by 6.2%.
- **Deliberation style**: brings in external search and code execution — even though it still has to interact with external text, it reduces wasted attempts by interacting in vector space before the search itself.
- **Distillation style**: a large expert mentors a small student — the small model's accuracy improves by 8.0% while still retaining a 1.5x speed advantage.

### Are Those Vectors Really Not Just Noise?

This is a perfectly reasonable question — the content passed between agents is unreadable to humans, so how do you know the model isn't just passing random noise around? The authors answer it by using PCA to project each round's latent thought vectors onto a 2D plane.

{{< image src="figure-semantic-alignment.png" alt="Three side-by-side scatter plots corresponding to recursion rounds 1, 2, and 3; orange dots represent RecursiveMAS's generated semantic distribution and blue-purple dots represent the ground-truth distribution, with two dashed ellipses starting visibly apart in round 1 and progressively converging until they nearly overlap by round 3." caption="Figure 7 — Over three rounds, the semantic distribution of generated answers progressively converges onto the ground-truth distribution. (Source: original paper.)" >}}

At round 1, the generated distribution and the ground-truth distribution are visibly apart (the idea is still vague); by round 2 they start overlapping, with the offset shrinking; by round 3 they nearly fully coincide.

What makes this result convincing is that it maps the abstract operation of "recursion" onto something visible: recursion is **semantic refinement**. Through each round's interaction, the model continuously corrects its own coordinates in latent space, until it locks onto the semantic center of the correct answer.

## The Trade-offs and Open Questions

This design isn't free of trade-offs, and the most direct one is **readability**. Traditional text-based MAS has an invisible benefit: the intermediate process is human-readable text, so when something goes wrong, you can just read the logs to see which step went off track. RecursiveMAS trades that readability for efficiency — everything in the middle is vectors, and short of additional projection analysis (like the PCA plot above), it's hard to know what the system was "thinking" during round 2. For production systems that need auditing or debugging, this is a trade-off worth thinking through carefully first.

Two more are open questions the paper leaves for itself:

**Recursion depth is fixed.** Right now the round count is a hyperparameter (e.g., \( r=3 \)); the system doesn't decide for itself "I've understood this problem, no need to loop further." Ideally this should be dynamic — early-stopping on easy problems, looping longer on hard ones — but the paper doesn't get there.

**Only the language modality has been validated so far.** If the latent vectors passed around could carry visual features in addition to linguistic logic, this framework could in theory extend to multimodal teams — but that's currently just a direction, not a result.

## Conclusion

RecursiveMAS really only makes one core move: **swapping the communication medium between agents from discrete text to continuous vectors**. But that one swap triggers three chained effects.

Cutting the LM-head projection and re-prefilling overhead makes multi-round recursion faster and more token-efficient than the text-based version, with the advantage growing as the round count increases. The communication path becomes differentiable, so the whole MAS can be trained end-to-end as one computation graph, with gradients accumulating across agents and across rounds — the system genuinely learns "team chemistry," not just individual capability. And all of this rests on nothing more than that small residual RecursiveLink — 0.31% trainable parameters, with the backbone models frozen the entire time.

The cost is that the intermediate process is no longer human-readable text. That's a worthwhile trade in scenarios chasing maximum efficiency, and one that deserves careful thought in scenarios that need auditing and debugging.

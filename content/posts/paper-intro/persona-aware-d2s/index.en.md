---
# weight: 1
title: "Persona-Aware D2S: One Paper, Four Audience-Tailored Slide Decks"
date: 2026-07-29
lastmod: 2026-09-21
draft: false
description: "Persona-Aware D2S (EACL 2024) generates four slide-deck versions of one paper by audience and length, via an RLHF-lite pipeline we unpack and critique."
featuredImage: "featured-image.png"

tags: ["Large Language Model", "Fine-Tuning", "LLM Alignment"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## Introduction

There is no single right way to turn a paper into slides. Presenting to researchers in your own field, you jump straight into the model architecture; presenting to a business executive, you first have to make clear what problem the thing solves, and architectural detail becomes a distraction. Yet nearly every "document-to-slides" (D2S) system out there produces a single output: feed in the document, and what comes out is always the same outline.

Persona-Aware-D2S, from EACL 2024, sets out to fill that gap. It turns "is the audience an expert?" and "should the deck be long or short?" into model input conditions, so one document grows four versions of slide content. For training it pairs SFT with a lightweight preference-tuning trick borrowed from Decision Transformer, sidestepping the infrastructure that PPO (the reinforcement-learning algorithm at the heart of mainstream RLHF) demands. This article walks the three-stage pipeline apart, fills in two pieces of technical background you'll probably get stuck on (Decision Transformer and the Bradley-Terry model), and then honestly assesses whether it's worth reproducing in engineering terms. The conclusion up front: this paper's contribution lies mainly in the task definition and the dataset; the method itself is an assembly of off-the-shelf techniques, and several architecture-level problems will block adoption outright.

{{< admonition abstract "Key Takeaways (TL;DR)" >}}
- **Task definition**: Persona-Aware-D2S (EACL 2024) turns "generate four versions of slide content from one document, conditioned on audience (expert / non-expert) and length (long / short)" into a clearly defined task, and builds the matching parallel dataset for it.
- **Method**: a three-stage pipeline (outline generation → content extraction → summarization and reordering). The first two stages use supervised fine-tuning plus a lightweight preference tuning (reward-conditioning) trick borrowed from Decision Transformer — but in practice that means training a separate model for each of the four persona combinations, rather than one conditional model.
- **The most cost-effective parts**: the two-tier retrieval in Stage 2's first step (literal matching first, semantic matching as fallback), and Stage 3's entirely training-free "summarize and reorder" step, which the paper's own ablation confirms improves readability and coherence.
- **Where it falls short**: the training data is tiny (only 80 samples for outline generation, a 5-paper dev split), the reward model has just 66M parameters with no capacity ablation, and the one-model-per-persona architecture can't scale as persona dimensions grow.
{{< /admonition >}}

## Why This Task Was Worth Redefining

The paper's opening example is intuitive: in front of a general or business audience, content that is too technically dense actually reduces engagement, because what these listeners want to know is "what is this for," not how many modules the model has. This is the paper's core motivation in a nutshell: one input, two outputs, differing not in quality but in who is being addressed.

Laying out the problems the paper raises in §1 and its related work, there are really five challenges with dependencies among them:

| # | Challenge | What prior methods did | Why it wasn't enough |
|---|---|---|---|
| 1 | Single output, can't adapt to different audiences | Doc2PPT (Fu et al., 2021), D2S (Sun et al., 2021) | Architecturally a fixed "document → single deck" mapping, with no "audience" input variable at all — no way in even if you wanted to extend it |
| 2 | Can't adapt to duration constraints | Same as above | A one-hour talk and a five-minute overview need completely different slide counts and information density, but duration was likewise never treated as a condition |
| 3 | Training objective misaligned with diverse human preferences | Maximizing similarity to a single gold reference (ROUGE, which compares word overlap between output and reference) | This maximum-likelihood (MLE) training presumes "there is only one correct answer," which directly conflicts with the inherently one-to-many nature of the persona problem |
| 4 | Extractive methods produce incoherent content | Heuristic rules (Masum et al., 2005, etc.), ML-based extractive methods (Hu & Wan, 2013, etc.) | Rule-based approaches rely on hand-crafted features and generalize poorly; extractive approaches can only pull sentences from the source, with no ability to summarize or rewrite, so they read stiffly |
| 5 | No dataset to train or evaluate on | — | Prior work mostly handled only one format — the technical conference talk — with no parallel data pairing one paper against multiple personas |

These five aren't parallel items. Challenge 5 is the precondition: without data there is no conditional generation to speak of. Only with the data can the conditions in challenges 1 and 2 become model inputs; and once you set out to train such a conditional model, you must confront challenge 3 (a single reference can't support diverse preferences). Challenge 4 is an independent content-quality problem, unrelated to persona but equally in need of a fix.

## Unpacking the Method: From Problem Formalization to a Three-Stage Pipeline

### Getting the Notation Straight First

The paper's formalization isn't hard, but the symbols are scattered across sections, so let's collect them here:

| Symbol | Meaning |
|---|---|
| \( D \) | The whole document (the paper) |
| \( SE \) | The set of sections in \( D \) |
| \( F \) | The set of all figures and tables in the document |
| \( F_q = \{I_q, Cap_q\} \) | The \( q \)-th figure/table, comprising image \( I_q \) and caption \( Cap_q \) |
| \( C \) | The paper's body content |
| \( H \) / \( A \) | The paper's title / abstract |
| \( B \in \{e, ne\} \) | Audience background: expert / non-expert |
| \( L \in \{l, s\} \) | Deck length: long / short |
| \( IN = \{C, B, L\} \) | The input triple to the model |
| \( t = \{t_1, \dots, t_j\} \) | The sequence of slide titles, i.e. the outline |
| \( S_u \) | Candidate content snippets filtered from the document (sentences plus captions) |
| \( O \) | The final slide output |

There's an easily missed design decision here: although \( F_q \) is written as "image + caption," the model actually only consumes the caption text — the image itself is never understood at any point. We'll settle that bill when we get to the limitations.

The overall objective is to model \( p(O \mid C, B, L) \). This joint probability can't be trained directly, so the pipeline effectively splits it into three parts (this decomposition is my reading, derived by lining it up against the three stages — the paper never writes it out as a single equation):

$$p(O \mid C, B, L) \approx \underbrace{p(t \mid IN)}_{\text{Stage 1: outline generation}} \times \underbrace{p(S_u \mid t, IN)}_{\text{Stage 2: content extraction}} \times \underbrace{p(O \mid S_u, t, IN)}_{\text{Stage 3: summarization and reordering}}$$

{{< admonition info "A typo in the paper's own equations" >}}
Watch out when reading the original equations: §3.1 writes the Outline Generation objective as \( P(t \mid IN) \), which is fine, but §3.2 still writes \( P(t \mid IN) \) when describing Content Extraction, where the text clearly calls for \( P(S_u \mid IN) \). This is a writing slip, not a different objective.
{{< /admonition >}}

{{< image src="figure2.png" alt="The full Persona-Aware-D2S information flow, with Topic Generator training and fine-tuning on top and content extraction plus final summarization alignment below" caption="Figure 2 — The full pipeline: the upper half is the SFT-to-preference-tuning flow for outline generation (including the reward model and human feedback), the lower half the matching flow for content extraction, all feeding into summarization and reordering to produce the deck." >}}

Treat this figure as the map for the whole section: the three subsections that follow correspond to the three parts of the diagram.

### Stage 1: Generating a Persona-Aware Slide Outline

This stage's goal is to take the paper's content plus the persona conditions and generate the slide title sequence \( t \). It proceeds in two steps: supervised fine-tuning first, then preference tuning.

#### Supervised Fine-Tuning (SFT-F)

The approach itself is standard: cross-entropy loss, minimizing the gap between generated titles and ground-truth titles. What's really worth noting is the architectural decision — the paper trains **four independent models**, one per persona combination:

$$\pi_{SFT}^{(B=ne,\,L=l)},\quad \pi_{SFT}^{(B=ne,\,L=s)},\quad \pi_{SFT}^{(B=e,\,L=l)},\quad \pi_{SFT}^{(B=e,\,L=s)}$$

rather than training a single model with \( B \) and \( L \) as conditions inside the prompt. The choice may be cleaner in terms of quality, but it comes at a steep cost, and it will be the main line of attack when we get to scalability.

The training scale is modest indeed: the train split holds only 20 papers, which times 4 configurations gives **80 training samples**, used to fine-tune GPT-3.5-turbo (3 epochs, lr=0.2, batch size 256).

#### Preference Fine-Tuning (P-F)

This step addresses challenge 3 above: a single gold standard can't support diverse preferences. The process has three parts.

**Part one is collecting human preference data.** Each of the four \( \pi_{SFT} \) models generates 5 candidate outlines using different temperature, top-K and top-p settings; 3 experts pairwise-rank the two expert configurations (long vs. short), and 3 non-experts do the same for the two non-expert configurations. There are two rating criteria: comprehensibility for the target audience, and satisfaction with the length. Only samples with majority-vote consensus are kept; those without consensus are discarded.

**Part two is training the reward model**, using a Bradley-Terry loss:

$$\mathcal{L} = -\mathbb{E}_{x \sim \text{train}}\left[\log \sigma(s_w - s_r)\right]$$

where \( s_w \) is the score of the chosen version and \( s_r \) the score of the rejected one. Because there are two rating criteria and two audiences, this yields four reward models: \( RM_{C\text{-}E} \) and \( RM_{L\text{-}E} \) (comprehensibility and length for experts), plus \( RM_{C\text{-}NE} \) and \( RM_{L\text{-}NE} \) (the non-expert counterparts).

{{< admonition warning "The reward model's capacity is never validated" >}}
Here's a choice I think deserves scrutiny: the reward model is distilbert-base-cased, a small encoder of roughly 66M parameters. "Is this outline comprehensible to a non-expert?" is a judgment that leans heavily on semantic understanding, and the paper runs no ablation at all on whether that capacity suffices.
{{< /admonition >}}

**Part three is the actual preference tuning**, borrowing Decision Transformer's reward-conditioning trick (the next section explains in full what that trick is in its original context). The steps: sample prompts from the train set, generate 5 outlines with \( \pi_{SFT} \), score each with the reward model, yielding training pairs of the form "(prompt, reward) → outline," then fine-tune the LLM on that batch. Fundamentally this is still supervised learning; the input just carries an extra reward as a condition. At inference you simply feed in the "maximum reward value" and let the model generate the outline that corresponds to that high score.

The paper skips two details at this step: where the so-called "maximum reward" number actually comes from (the largest value observed in the training data? a manually set constant?), and whether the two reward scores are merged into a single scalar or both stuffed into the prompt. Without these, reproduction is going to hurt.

### Stage 2: Extracting the Content That Belongs on Each Slide

With the outline in hand, the next job is to find the sentences and figure captions matching each title — that is, \( S_u \). This stage has two steps: first narrow the candidate pool cheaply, then use a trained model to pick content from the candidates.

#### Step One: A High-Recall Section Filter (No LLM Involved)

Why is this step needed? Handing the whole paper to an LLM to pick sentences is expensive, and it won't fit inside GPT-3.5-turbo's 4096-token limit. So the paper narrows the range cheaply first:

1. Each slide title \( t_i \) is **fuzzy-matched** (literal similarity) against the paper's section headings, taking the top-k above a threshold \( th \).
2. If no section clears the threshold, fall back to **Sentence-BERT** (Reimers & Gurevych, 2019) semantic similarity and pick the closest section.
3. Once a section is selected, all of its sentences and captions are concatenated into \( S_u \).

In plain terms, it's "cheap literal matching first, semantic model only when literal matching fails" — a two-tier retrieval, a classic retrieve-then-rerank pattern, and in my view the single most directly borrowable design in the paper.

{{< admonition warning "Two worries about the section filter" >}}
The threshold \( th \) was tuned on a dev split of only **5 papers**, a sample so small that a change of domain (different section-naming habits) will probably require retuning. More fundamentally, the whole mechanism leans heavily on the document having a standardized section structure; point it at meeting notes or a PRD and the literal-matching half fails outright, falling back entirely to semantic matching.
{{< /admonition >}}

#### Step Two: Persona-Aware Content Extraction

This step reuses Stage 1's machinery wholesale — the same cross-entropy SFT, the same Bradley-Terry reward model, the same Decision-Transformer-style preference tuning — only with input and output swapped to "\( (t, S_u) \) → relevant snippets," producing a policy dedicated to content extraction.

#### What the Saved API Cost Actually Costs

The paper claims this candidate filtering cuts GPT calls to roughly one eighth. The claim has data behind it, but it also has a price:

Table 1 — The cost/recall trade-off of candidate filtering (Table 10 in the original): the more calls, the higher the recall.

| Strategy | Average GPT calls | Recall |
|---|---|---|
| The paper's lightweight filter | ~1 | 78.89% |
| Medium candidate range | ~5.3 | 81.34% |
| Nearly the whole paper | ~8.2 | 100% |

The key point is that this filtering is **irreversible**: a sentence filtered out here is invisible to every later stage. So that 21% of relevant content isn't "temporarily unselected," it's permanently gone. Whether trading one fifth of your content coverage for one eighth of the call cost is worth it depends on how much omission your application can tolerate.

{{< admonition info "A note on data quality" >}}
This table (Table 10 in the original) also has a precision column, not reproduced above, with values of 6.73, 5.93 and 5.88 — which look implausible, since precision should normally fall in the 0–1 or percentage range. I suspect a column misalignment in the original table; check against the source PDF before citing these numbers. The recall figures look normal.
{{< /admonition >}}

### Stage 3: Summarization and Logical Reordering

What the first two stages extract is scattered sentence fragments, which would be hard to read pasted straight onto slides. Stage 3 organizes them into a coherent final output through two-step prompting: first summarize the content of \( S_u \) into bullet points, then feed those bullets back to the LLM and ask it to reorder them within a title, or across titles, so the sequence better matches how an audience takes things in. Concretely, that means flipping a "results" slide that led with numbers and only later gave the experimental setup, or moving definitional bullets ahead of application ones.

Stage 3's resource allocation visibly drops a level: Stages 1 and 2 both invest heavily in SFT plus preference tuning, yet Stage 3 — the stage with the most direct impact on user experience — gets **no custom training whatsoever** and relies purely on prompting. The paper never explains whether this asymmetry is deliberate or accidental.

First, what the output actually looks like:

{{< image src="figure6.png" alt="Two slides the model produced for non-experts and for experts under the same 'Model Details' title, side by side" caption="Figure 3 — The same 'Model Details' title: on the left the non-expert version (explaining terms like LSTM and semantic similarity, with fewer details), on the right the expert version (going straight into training details and network architecture, with no jargon explained)." >}}

This figure is the most direct way to check the whole pipeline — without looking at a single score, just compare the jargon density and depth of detail on each side and you can tell whether the conditioning actually took effect.

As for whether Stage 3 itself helps, the paper ran a before/after ablation (10 papers, Stage 2's extractive version vs. Stage 3's summarized-and-reordered version):

| Metric | Change |
|---|---|
| Coherence | +0.5 |
| Readability | +1.0 |
| Coverage | -0.05 (essentially unchanged) |
| Relevance | 0 (unchanged) |

{{< image src="figure5.png" alt="Bar-chart comparison of Coherence, Coverage, Readability and Relevance ratings before and after summarization and reordering" caption="Figure 4 — User ratings before and after summarization and reordering: Readability and Coherence improve clearly, while Coverage and Relevance hold roughly flat." >}}

This is one of the more solidly evidenced experiments in the paper: a direct before/after comparison confirming that summarization plus reordering really does improve readability and coherence without noticeably sacrificing content coverage. That said, the sample is only 10 papers, and the raters aren't an independent third party.

**How are hallucinations handled?** The paper runs no automated fact-checking; instead annotators rate "content relevance," and that score stands in indirectly for whether hallucination occurred.

{{< admonition warning "Relevance is not a rigorous proxy for hallucination" >}}
A passage can perfectly well be "highly relevant to the title" while also "fabricating details the paper never stated," and hallucinations of that type slip straight through this evaluation.
{{< /admonition >}}

Appendices D–G provide the complete zero-shot / few-shot prompts for outline generation and content extraction, but **not** the prompt template used in Stage 3. Of the four modules, this is the one step that can't be reconstructed from the appendix — and it happens to be the one most readily lifted and reused.

## Background: Two Techniques You Might Get Stuck On

This section fills in two pieces of technical background that Persona-Aware-D2S borrows but that the paper itself only mentions in passing. Their value is independent of this paper — even if slide generation doesn't interest you, both are useful elsewhere.

### Decision Transformer: Packaging Reinforcement Learning as Sequence Prediction

Decision Transformer (Chen et al., 2021) went up on arXiv in June 2021 and was published at NeurIPS the same year. The timing sits after GPT-3 and before ChatGPT, making it a representative work of that wave of research into whether Transformers could solve sequential decision problems.

What it set out to fix were the old ailments of traditional RL: methods like Q-learning and policy gradient train unstably, need careful tuning, and often require online interaction with the environment. Decision Transformer proposes a paradigm shift — repackage the RL problem as a sequence prediction problem, train it with GPT-style supervised learning, and estimate no value function and do no bootstrapping at all.

How it works is easiest to picture as navigating a maze:

- A trajectory consists of a series of (state, action, reward) triples.
- Before training, rewards are converted into **return-to-go**: from this step to the end, how many points remain to be earned in total.
- The model's input is an interleaved sequence of those triples: `[return-to-go, state, action, return-to-go, state, action, ...]`.
- **During training**, the action is masked, and the model predicts which action to output from the preceding (return-to-go, state). The mapping it learns is roughly "I still want 10 points, and I'm at position A → go right."
- **At inference**, the user makes a wish first: set a target return (say "I want 10 points"), and the model emits an action from that goal plus the current state; after each step the remaining return-to-go decreases by the points actually earned, repeating until the end.

In one sentence: training is "watch how others moved and how many points they ended with, and learn the association between the two"; usage is "you set the score you want, and the model works backward to how to get there."

**Did it become mainstream afterward?** Within the research community it certainly had influence: Trajectory Transformer (Janner et al., 2021) proposed a similar idea around the same time, Online Decision Transformer followed, and the approach was extended to recommender systems, robotics, embodied AI, web-navigation agents and more. But it did **not** become the mainstream route for LLM alignment — today's [RLHF](../../ai-concept/llm-fine-tuning-rlhf/) ecosystem still runs mainly on PPO (the InstructGPT line) or the later [DPO](../dpo/). Decision Transformer is better understood as a continuing influence within offline RL and robotic control, not a household-name production technique.

Back to this paper: it borrows only the "reward-conditioned generation" training trick — stuff the reward into the input as a condition, train with supervised learning, and thereby sidestep PPO's infrastructure complexity. But this is an **incomplete appropriation**. Decision Transformer's real power lies in multi-step sequential decisions with causal structure: how you choose at this step affects how many points you can earn at the next. Persona-Aware-D2S's setting is single-shot generation — prompt in, complete outline out — with no multi-step decision structure and no notion of a trajectory.

| Decision Transformer concept | Its Persona-Aware-D2S counterpart |
|---|---|
| return-to-go (how many points you still want) | The score the reward model assigns |
| state (where you are now) | The prompt (paper content plus persona conditions) |
| action (which way to go) | The outline to be generated |
| A full trajectory | Doesn't exist — only single-step generation |

The last row of that table is the point: the surface trick was borrowed, but the core problem it was designed to solve never comes into play.

### The Bradley-Terry Model: From Team Rankings to the Shared Foundation of RLHF

The Bradley-Terry model (Bradley & Terry, 1952) is a very old statistical model, originally addressing "how do you infer an overall ranking from pairwise comparisons" — ranking sports teams, say, with nothing to do with AI.

Its core assumption is that each item has an invisible "strength" value, and a comparison result is merely a probabilistic reflection of that strength, not a guarantee. As an equation:

$$P(i \text{ beats } j) = \frac{\text{strength}_i}{\text{strength}_i + \text{strength}_j}$$

A concrete example: if team A has strength 8 and team B has strength 2, then \( P(A \text{ beats } B) = 8/(8+2) = 0.8 \). A is four times as strong and wins eight times out of ten, but B still has a two-in-ten chance of an upset. That tolerance for uncertainty is exactly what suits a noisy setting like human preference, where even the same person may not judge consistently at different times.

Reparameterize \( P(i > j) \) into exponential form (letting \( p_i = e^{r_i} \)) and you get the \( \sigma(r_i - r_j) \) form familiar from reward-model training — which is precisely the loss in Stage 1 above. This is the most widely adopted preference model in RLHF: from Christiano et al. (2017), the [founding RLHF paper](../../ai-concept/llm-fine-tuning-rlhf/), through OpenAI's InstructGPT, all the way to the later [DPO](../dpo/), the underlying math is the same Bradley-Terry loss, differing only in how it's applied. In other words, Persona-Aware-D2S's reward modeling isn't original at all — it applies the industry-standard approach directly.

In practice, training looks like this: if the reward model scores the chosen version 3.5 and the rejected one 1.0, then \( s_w - s_r = 2.5 \), \( \sigma(2.5) \approx 0.92 \), and the loss is \( -\log(0.92) \approx 0.08 \) — very small, meaning the model judged correctly. Conversely, if the scoring is inverted (the chosen version gets the lower score), the loss shoots up to around 2.53 and the gradient pushes hard to correct it.

**Why pairwise comparison instead of direct scoring?** Because direct scoring ("please rate this 1 to 10") has very low inter-annotator agreement — one person's 7 isn't another's. But "which of A and B is better" is intuitively easy for humans to judge, with far higher consensus. That's also why the paper's annotation process is designed around pairwise ranking.

{{< admonition warning "Bradley-Terry's transitivity assumption" >}}
Bradley-Terry has a known methodological weakness: it relies on transitivity (if A>B and B>C then A>C), and human preferences frequently violate that assumption. This paper's practice of "keep only samples with majority consensus and discard the rest" sidesteps the problem to some degree rather than genuinely solving it.
{{< /admonition >}}

## How Well Does It Work: End-to-End Evaluation

{{< image src="table4.png" alt="Table of end-to-end ROUGE-1/2/L results for Zero-shot, Few-shot, SFT-F and P-F across the four persona configurations" caption="Table 2 — End-to-end ROUGE evaluation of the full pipeline across the four persona configurations. Both fine-tuned models beat zero-shot and few-shot across the board; preference tuning leads in most configurations, except Expert-Short, where plain supervised fine-tuning does better." >}}

This table is the primary quantitative basis for the conclusion that "fine-tuning does work," and the number source you should look at hardest when assessing engineering ROI (a reminder on the abbreviations above: SFT-F is supervised fine-tuning alone, P-F adds preference tuning on top). Two observations:

- SFT-F and P-F beat the zero-shot and few-shot baselines across the board, by a fair margin. That conclusion holds up.
- P-F wins in most configurations, but **Expert-Short** is the exception, where plain supervised fine-tuning is better (R-1: SFT-F 0.17 vs. P-F 0.13). The paper's reading is that plain supervised fine-tuning does better at concise summarization for expert audiences. Right or wrong, this at least shows preference tuning is not an unconditional improvement.

## Critical Assessment

### Limitations the Paper Acknowledges Itself

The paper's Limitations section lists five, all of them fair:

1. The method is constrained by having to stay faithful to the document's content.
2. Most technical jargon needs extra explanation to be comprehensible to non-experts, and the model's ability to provide it is limited.
3. It relies entirely on human-written figure captions, generates no original figures, and does not understand image content itself.
4. It can only produce bullet-point text summaries, and **involves no layout design at all**.
5. It has no multimodal representation ability, so image-related information may be lost along the way.

Points 3 and 4 together already determine that this system's output is a long way from "a deck you could walk in and present."

### Problems the Paper Doesn't Mention, but I Think Are There

| Aspect | Problem |
|---|---|
| Training data scale | Outline generation has only 80 training samples (20 papers × 4 configurations), and the dev split is only 5 papers. Small-sample fine-tuning easily overfits to this batch of papers' writing style, leaving cross-domain generalization in doubt |
| Architectural scalability | Four persona configurations require training 4 independent SFT models plus 4 reward models. Add another persona dimension (a role, say: PM / engineer / executive) and the model count grows multiplicatively — not scalable at all |
| Hidden cost of the retrieval mechanism | Section filtering is irreversible, so 21% of relevant content is permanently lost; the threshold was tuned on only 5 papers; and the whole thing depends heavily on standardized section structure, failing outright on unstructured documents |
| Reward model capacity | Using a 66M-parameter distilbert-base-cased to judge something as semantically complex as "comprehensibility" is never validated as sufficient |
| Missing preference-tuning details | How the "maximum reward" value is decided, and whether the reward is a scalar or multi-dimensional, are never explained, making reproduction hard |
| Asymmetric resourcing of Stage 3 | The summarization and reordering step with the greatest impact on the end experience is the only one with no custom training, with no explanation given and no prompt for it in the appendix |
| Weak hallucination evaluation | Using relevance ratings as a proxy for hallucination can't detect the "relevant but fabricated in the details" category |
| Uniformly small experimental samples | 10 papers for the qualitative analysis, 3 experts for the cognitive-load study, 10 papers for the ablation — statistical power is low throughout |
| A gap between the output and a real deck | No layout, color or typography at all; what it outputs is fundamentally a structured text outline, not a usable presentation |

The sample-size row deserves a fair framing: this is "insufficient scale," not "never ran the experiment." The paper's experimental coverage is in fact quite complete — module-level evaluation, end-to-end evaluation, ablation, qualitative analysis are all there — it's just that each one's sample size is too small to support strong statistical conclusions.

## Engineering Adoption: What to Copy, What to Leave Alone

Having covered the method and its limitations, the practical question is: if I were building a similar system tomorrow, which parts of this paper could I take straight?

| Module | Adoption viability | Judgment |
|---|---|---|
| Stage 1 and Stage 2's second step (the four-model SFT + P-F architecture) | Low | Training and operational cost grows multiplicatively with persona dimensions; not recommended for direct reproduction |
| Stage 2's **first step** (section filtering: fuzzy match + SBERT fallback) | **High** | Mature, transferable, and solves a real pain point (API cost), consistent with the retrieve-then-rerank pattern of general RAG |
| Stage 3 (summarize + reorder, no training required) | **Highest** | Lowest cost (just two extra LLM calls), with an ablation confirming a clear improvement — the best return on investment in the whole paper |
| The Decision-Transformer-style training trick | Medium (depends on context) | If you need lightweight preference alignment while avoiding PPO's infrastructure complexity, the idea is worth borrowing, but be clear that it discards the original technique's genuine multi-step decision advantage |

Concrete recommendations:

- **Worth borrowing directly**: the two-tier retrieval in Stage 2's first step, and Stage 3's summarization and reordering. Neither requires training, and the transfer cost is close to zero.
- **Not recommended for reproduction**: the "one independent model per condition" architecture of Stage 1 and Stage 2's second step. Small-sample SFT is itself fairly risky, unless your task is likewise "teach the model an output format or style" rather than "teach the model new knowledge" — the former has a chance with small samples, the latter essentially none.
- Overall, **this paper works better as a reference for "problem definition" than for "solution"**. Its value lies in clearly describing what the persona-aware generation task should look like, not in providing a system you can put into production.

## Conclusion

Persona-Aware-D2S's core contribution is defining a new task and building a new dataset: for the first time, document-to-slides treats "who the audience is" and "how long the talk runs" as model input conditions. That problem definition is genuinely valuable, and it's mainly what got the paper into EACL 2024 as a long paper.

The methodology itself, though, isn't original — the SFT-plus-RLHF-lite combination assembles Christiano et al. (2017)'s reward modeling with Chen et al. (2021)'s reward-conditioning, and even then borrows only the surface of the latter. Reproducing the whole thing is even less advisable from an engineering standpoint: 80 training samples can't support real-world domain diversity, a four-times-the-models architecture doesn't scale, and the output falls visibly short of a directly usable deck.

Only two things are genuinely worth taking away: the two-tier retrieval of fuzzy match plus SBERT fallback from Stage 2's first step, and the "stuff the reward into supervised learning as a condition" training idea that sidesteps PPO. The former you can use tomorrow; for the latter, first think hard about whether your task has a genuine multi-step structure — if it doesn't, what you've borrowed is just the shell.

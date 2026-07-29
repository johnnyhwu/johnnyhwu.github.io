---
# weight: 1
title: "Persona-Aware D2S: One Paper, Four Audience-Tailored Slide Decks"
date: 2026-07-29
lastmod: 2026-07-29
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

Hand the same paper to an engineer and to a business executive, and in principle the resulting presentation should look nothing alike: different jargon density, different depth of detail, even different key points. Yet most existing document-to-slides (D2S) systems produce a single, one-size-fits-all output — whoever ends up watching, the outline that comes out is the same.

Persona-Aware-D2S, an EACL 2024 paper, sets out to solve exactly this problem: generate four different versions of slide content from the same document, conditioned on two variables — whether the audience is an expert, and whether the deck should be long or short. The method combines supervised fine-tuning with a lightweight preference-tuning trick borrowed from Decision Transformer; this article refers to that combination collectively as "RLHF-lite." We'll walk through the paper's three-stage pipeline and unpack the method stage by stage, while being upfront about where the approach doesn't hold up on data scale and architecture design. The conclusion first: this paper's real value is in clearly defining the task of persona-aware generation, not in offering a system you can drop straight into production.

{{< admonition abstract "Key Takeaways (TL;DR)" >}}
- **Task definition**: Persona-Aware-D2S (EACL 2024) is the first to clearly define the task of generating four different slide-deck versions of the same document, conditioned on audience (expert / non-expert) and length (long / short), and builds a matching parallel dataset for it.
- **Method**: a three-stage pipeline (topic generation → content extraction → summarization and alignment). The first two stages use supervised fine-tuning plus a lightweight preference-tuning trick borrowed from Decision Transformer (reward-conditioning) — but in practice this means training four separate models for the four persona combinations, rather than one model conditioned on persona.
- **The most cost-effective parts**: Stage 2's two-tier retrieval (literal matching first, semantic matching as fallback) and Stage 3's untrained "extract-then-summarize-and-reorder" prompting step — the paper's own ablation confirms the latter measurably improves readability and coherence.
- **Where it falls short**: the training data is tiny (only 80 samples for topic generation, a 5-paper dev split), the reward model is a 66M-parameter DistilBERT with no capacity ablation, and the four-models-per-persona architecture can't scale as the persona dimension grows.
{{< /admonition >}}

## Same Document, Very Different Needs for Two Kinds of Readers

{{< image src="figure1.png" alt="Example of the Persona-Aware-D2S model generating completely different slide content for two different audiences from the same paper" caption="Figure 1 — For the same paper, the model produces presentations with completely different content depending on the audience condition." >}}

The paper's example is intuitive: presenting the same paper to a general audience or a business executive should focus on the overall "what can this do" workflow; presenting it to a technical audience requires going deep into the model architecture. This sounds obvious, but past D2S systems (like Doc2PPT and D2S) were architecturally a fixed mapping — document in, single deck out — with no way to add or adjust "who the audience is" as an input variable.

Beyond the missing audience condition, the paper points to three more problems. Length constraints were also never treated as an input: a one-hour technical talk and a five-minute overview need vastly different information density, but past systems had no adjustable dimension for this either. The training approach itself is problematic: if you train only by "maximizing similarity to a single gold reference" — the common ROUGE-score approach — the model ends up learning to approximate one particular annotator's writing style, rather than understanding that different audiences need different things. That's a fundamental conflict between a one-to-many problem and a single-answer training method. Extractive approaches (directly copy-pasting original sentences as slide content) are another long-standing issue, reading stiffly and failing to integrate across sentences. Finally, conditional generation like this needs parallel data — the same paper mapped to multiple persona versions — and no such dataset existed before this paper.

## Method Overview: A Three-Stage Pipeline

{{< image src="figure2.png" alt="Complete pipeline diagram for Persona-Aware-D2S, including the Topic Generator, Content Extractor, and Reward Model training flow" caption="Figure 2 — The complete pipeline: the top half is the topic-generation training flow, the bottom half is content extraction, which finally feeds into summarization and alignment to produce the final slide deck." >}}

The paper frames the entire task as a conditional probability: given document content C, audience B (expert or non-expert), and length L (long or short), generate the final slide deck O — that is, p(O | C, B, L). Strictly speaking, the paper's body never explicitly decomposes this objective into a product of factors, but based on how the pipeline actually runs, it can be approximated as three stages:

1. **Stage 1 (topic outline generation)**: first generate the sequence of slide titles
2. **Stage 2 (content extraction)**: for each title, pick out the relevant sentences and figure/table captions from the document
3. **Stage 3 (summarization and logical alignment)**: organize the extracted, scattered content into a coherent deck

The three stages run in sequence, with each stage's output feeding the next. Below we unpack what each stage actually does, in order.

## Stage 1: Deciding What Topics the Slides Should Cover

The first stage's goal is simple: given document content plus a persona condition, produce a sequence of slide titles. This happens in two steps — first supervised fine-tuning to establish a baseline, then correction using preference data.

### Supervised Fine-Tuning (SFT-F)

This uses standard cross-entropy loss to make the generated titles match human-annotated ground truth as closely as possible. There's a notable design choice worth flagging here: the paper trains **four separate models**, one each for "expert + long," "expert + short," "non-expert + long," and "non-expert + short," rather than training a single model with audience and length as prompt-level conditioning text. The training data is also small — the train split has only 20 papers times 4 configurations, for a total of 80 samples, used to fine-tune GPT-3.5-turbo. The paper does not further validate how much generalization a model trained on 80 samples retains when moved to domains with substantially different writing styles.

### Preference Fine-Tuning (P-F)

This is meant to solve the "a single gold reference isn't enough" problem, in three steps. Step one collects human preferences: each of the four SFT models generates five candidate topic sets using different temperature, top-K, and top-p settings; experts and non-experts then perform pairwise comparisons on the configuration matching their own group, judged on "is this comprehensible for the target audience" and "does the length match the requirement." Only samples with majority-decision consensus are kept; samples without consensus are discarded outright.

Step two trains a reward model on this preference data, mathematically using the Bradley-Terry model — an old statistical method from 1952, originally used for ranking sports teams. Its core assumption is that every item has an unobserved "strength" value, and comparison outcomes are just a probabilistic reflection of that strength. The formula is P(i beats j) = strength_i / (strength_i + strength_j): if A's strength is 8 and B's is 2, P(A beats B) is 0.8 — A is four times stronger and wins 80% of the time, but B still has a 20% chance of an upset. This tolerance for uncertainty happens to fit the inherently noisy setting of "human preference" well — which is why the same underlying Bradley-Terry loss runs from the 2017 RLHF founding paper, through InstructGPT, and on to later [DPO](../dpo/). The paper trains four reward models (for expert/non-expert comprehensibility and length-based satisfaction respectively), using a distilbert-base-cased encoder with only about 66M parameters — whether that capacity is enough for a semantically complex task like judging "comprehensibility" is never validated with an ablation study.

Step three is the actual preference fine-tuning, borrowing a technique from Decision Transformer (Chen et al., 2021): sample prompts from the training set, generate five candidates with the SFT model, have the reward model score each one, treat (prompt, reward score) pairs as training data, and fine-tune the LLM on them once more. At inference time, feeding in the "maximum reward value" as a condition produces the corresponding high-scoring output. Decision Transformer originally reframed reinforcement learning as a sequence-prediction problem: a trajectory consists of a series of (state, action, reward) tuples; during training the model looks at "how much return-to-go is still wanted" plus "the current state" to predict what action to take; at inference time, the user first sets a target score, and the model produces actions toward that target, one step at a time.

But there's an incomplete borrowing here: Decision Transformer's real power lies in handling multi-step decision problems where "this step's choice affects how much reward can be earned in the next step" — while Persona-Aware-D2S's use case is single-shot generation: feed in a prompt once, get out a complete outline once. There's no real multi-step decision structure and no notion of a "trajectory." Strictly speaking, the paper only borrows the surface-level trick of "feeding reward in as a condition to supervised learning" to sidestep the training complexity of PPO, without actually engaging with the problem Decision Transformer was designed to solve. The paper also never explains exactly how the "maximum reward" value is determined, or whether reward is merged into a single scalar or fed in as multiple dimensions — these missing implementation details make full reproduction difficult.

## Stage 2: Picking Out the Content That's Actually Useful From the Document

Once there's a title outline, the second stage needs to find matching content for each title. Handing the entire paper to an LLM to pick sentences is too expensive, and the paper states its goal is to keep the prompt within GPT-3.5-turbo's 4096-token limit — so it designs a two-tier retrieval mechanism that doesn't rely on an LLM at all. First, compare each slide title against the paper's section headings with literal similarity (fuzzy matching) and keep candidates above a threshold; only if no section clears that threshold does it fall back to computing semantic similarity with Sentence-BERT and picking the closest section. Once a section is selected, every sentence and figure/table caption under that section is concatenated together to form the candidate content pool for that title.

The cost savings this mechanism buys are clearly stated — the paper's own Table 10 compares three retrieval strategies:

| Strategy | Avg. GPT Calls | Recall |
|---|---|---|
| The paper's lightweight filter | ~1 | 78.89% |
| Medium-range candidate set | ~5.3 | 81.34% |
| Nearly the entire paper as candidates | ~8.2 | 100% |

The paper claims an eightfold reduction in GPT calls, at the cost of permanently missing about 21% of genuinely relevant content — this filtering step is irreversible, and later stages have no chance to see the sentences that were dropped. The threshold itself was only tuned on a 5-paper dev split, a very small sample, so it will likely need retuning for domains with different section-naming conventions; and the whole mechanism depends heavily on documents having standardized section structure, so it would simply fail on unstructured documents like meeting notes or PRDs. (As an aside: the paper's Table 10 also lists a precision column that isn't included in the simplified table above; those numbers look implausible — precision should normally fall between 0 and 1, but the paper's listed values are clearly larger than that. This is likely a table layout or column-alignment issue, worth flagging if you ever cite it.)

Once candidate content is selected, which sentences are actually relevant is extracted using the exact same mechanism as Stage 1 — the same cross-entropy supervised fine-tuning, the same Bradley-Terry reward model, the same Decision-Transformer-style preference fine-tuning — just with the input/output swapped to "(title, candidate content) → the actually relevant content."

## Stage 3: No Training At All, Yet the Most Effective Step

The first two stages invest heavily in SFT plus preference fine-tuning, while the third stage does no custom training at all — it relies on just two rounds of prompting: first summarize the extracted content into bullet points, then feed those bullet points back to an LLM and ask it to reorder them, within a title or across titles, to make the content easier for the audience to digest. The paper never explains why the step with the biggest impact on user experience is also the one with the least resources invested — an oddly asymmetric allocation.

To show what this actually looks like in practice, the paper contrasts two versions of the same title, "Model Details":

{{< image src="figure6.png" alt="Two versions produced by the P-F model for the same slide title, one for non-experts and one for experts" caption="Figure 6 — Left is the non-expert version, which explains terms like LSTM and semantic similarity and keeps content more concise; right is the expert version, which goes straight into training details and network architecture without explaining terminology." >}}

This side-by-side comparison is the most direct way to verify the final effect of the whole pipeline (all three stages stacked together): the difference in term density and depth of detail between the two sides is visible at a glance.

To check whether this summarize-and-reorder step in Stage 3 actually helps, the paper runs an ablation study on 10 papers, comparing "the version directly extracted by Stage 2" against "the version summarized and reordered by Stage 3":

{{< image src="figure5.png" alt="Bar chart comparing Coherence, Coverage, Readability, and Relevance before and after Summarization+Alignment" caption="Figure 5 — Red is after alignment, blue is before; Readability and Coherence both show clear improvement, while Coverage and Relevance barely change." >}}

The specific numbers: Coherence improves by 0.5 points, Readability improves by 1.0 point, Coverage drops by only 0.05 points (essentially unchanged), and Relevance is completely unchanged. This is the most solidly evidenced experiment in the whole paper — a direct before/after comparison confirming that summarizing and reordering does improve readability and coherence, without noticeably sacrificing content coverage. That said, the sample is only 10 papers, and the raters weren't independent third parties, so how far the conclusion generalizes is limited.

How hallucination is handled is also worth noting: the paper doesn't do any automated fact-checking, and instead has annotators rate "how relevant the content is to the title," using that score as an indirect proxy for hallucination. This isn't rigorous — content can be "highly relevant to the title" while simultaneously "fabricating details the paper never actually stated," and that type of hallucination is invisible to a relevance score.

## End-to-End Evaluation Results

With all three stages chained together, how does end-to-end performance look?

{{< image src="table4.png" alt="End-to-end ROUGE-1/2/L evaluation results for Zero-shot, Few-shot, SFT-F, and P-F across four persona configurations" caption="Table 4 — The P-F model beats Zero-shot, Few-shot, and SFT-F in almost every configuration, with the sole exception of the Expert-Short configuration." >}}

P-F performs best across most configurations, with the sole exception of "expert + short," where SFT-F actually wins instead (R-1 scores of 0.17 vs. 0.13 in the table). Overall, fine-tuning clearly helps, with both Zero-shot and Few-shot lagging noticeably behind. It's also worth noting that the paper's Appendices D through G provide the complete prompts used by the Zero-shot and Few-shot versions for both the topic-generation and content-extraction modules — but not the prompt template used for Stage 3's summarization and reordering, making it the one step among the four modules that can't be reconstructed from the appendices.

## Critical Assessment: Where This Paper Falls Short

### Limitations the Paper Admits Itself

The paper itself acknowledges several points in its Limitations section:

- Limited content faithfulness
- Most technical terms need extra explanation for non-experts to understand, but model capability is limited here
- Fully dependent on human-written figure/table captions — it doesn't generate original figures or understand image content itself
- Can only produce text bullet-point summaries, with no involvement in layout/design
- No multimodal representation capability, so image-related information may be lost as a result

### Problems the Paper Doesn't Mention, But Show Up Under Scrutiny

Beyond what the paper admits itself, there are several problems it doesn't mention but that become apparent under analysis. Training data scale is the most obvious one: topic-generation training has only 80 samples, and the dev split has only 5 papers — small-sample fine-tuning easily overfits to that batch of papers' writing style, and how well it generalizes to a different domain is questionable. Architecture scalability is another real weakness: four persona configurations already require training four separate SFT models plus four sets of reward models; if the persona dimension is ever expanded (say, adding role distinctions like PM, engineer, executive), the number of models grows multiplicatively — this doesn't scale at all. The retrieval mechanism's hidden costs mentioned earlier (21% of content permanently dropped, a threshold tuned on only 5 papers, dependence on standardized section structure) are also real pitfalls in practice.

Reward model capacity, missing P-F training details, Stage 3's asymmetric resource allocation, and the weak hallucination-evaluation method — these have each already been discussed in earlier sections, so we won't repeat them here. Worth adding: sample sizes are consistently small across the board — the qualitative analysis covers only 10 papers, the cognitive-load study only recruited 3 experts, and the ablation study is also 10 papers, so statistical power is low throughout. That said, this doesn't mean the paper "didn't run experiments" — module-level evaluation, end-to-end evaluation, ablation studies, and qualitative analysis are all covered; it's just that every one of them runs on a thin sample. Finally, the output itself still has a clear gap from "an actual slide deck": it contains no layout, color, or font — visual design elements at all. What it produces is, in essence, a structured text outline, not a presentation ready to walk up on stage with.

## What to Take From This Paper — and What to Skip — in Practice

Broken apart, the modules in this paper have very different practical value. Stage 2's two-tier retrieval design (cheap literal matching first, falling back to a semantic model only when that fails) is mature and easy to port over — it genuinely solves a real pain point, saving substantial API cost, and its approach aligns with the general retrieve-then-rerank RAG design pattern, making it worth borrowing directly. Stage 3's two-step "extract, then summarize and reorder" prompting pattern has the best return on investment: no extra training needed, just two more LLM calls per title, and the ablation study confirms the effect — this is the most cost-effective part of the whole paper.

By contrast, the "train one separate model per condition" architecture shared by Stage 1 and Stage 2 is not recommended for direct reuse — training and maintenance cost grows multiplicatively with the persona dimension. The Decision-Transformer-style preference fine-tuning trick depends on context: if you need lightweight preference alignment yourself and want to avoid PPO's infrastructure complexity, the idea of "feeding reward in as a condition to supervised learning" is worth considering — but be clear-eyed that it gives up Decision Transformer's real multi-step decision-making advantage; it's only borrowing the shell.

Overall, this paper is better used as a reference for "problem definition" than for "solution" — its value is in clearly describing what the task of persona-aware generation should look like, not in providing a system you can lift and use directly.

## Conclusion

Persona-Aware-D2S's core contribution is defining the new task of "dynamically generating slides conditioned on audience and length" and building a matching dataset for it; the methodology itself (SFT plus an RLHF-lite combination) has no originality of its own — it's assembled directly from Christiano et al. 2017's RLHF framework and Chen et al. 2021's Decision Transformer. Its research value is medium-to-low, and its engineering value is also low: the training data scale can't support real-world domain diversity, the architecture's fourfold model count doesn't scale, and the output still has a long way to go before being "a slide deck you can directly use."

If you want to take away two things from this paper, one is Stage 2's retrieve-then-rerank retrieval design (literal matching plus Sentence-BERT fallback), and the other is the basic idea behind Decision Transformer's "reward-conditioning" training approach — even though this paper itself only borrows it incompletely, the idea is still worth considering if you're building lightweight preference alignment of your own.

---
# weight: 1
title: "Deep Dive into MRAG: Solving Temporal Reasoning in RAG with Symbolic Logic (EMNLP 2025)"
date: 2026-03-10
lastmod: 2026-03-10
draft: false
description: "Discover how the MRAG framework (EMNLP 2025) solves temporal reasoning issues in RAG systems. Learn to combine neural networks with symbolic logic to eliminate time-sensitive AI hallucinations and improve retrieval accuracy."
featuredImage: "featured-image.jpg"

tags: ["Large Language Model", "Retrieval-Augmented Generation"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## Introduction

If you've worked with RAG (Retrieval-Augmented Generation), you've likely encountered this exact scenario:

You ask a ChatBot: "Who was the UK Prime Minister in **2019**?"
It confidently replies: "Boris Johnson."
That seems correct.

But if you ask: "Who was the Prime Minister **before 2019**?"
It might still retrieve documents containing "2019" and "Boris Johnson" and tell you it was still Johnson. At this point, your User Experience (UX) is completely ruined.

I recently read a paper from **EMNLP 2025 (Findings)** titled *"MRAG: A Modular Retrieval Framework for Time-Sensitive Question Answering"*, which strikes right at the heart of this pain point. The biggest takeaway for me wasn't the use of a new LLM, but rather the fact that it identifies a massive blind spot in current RAG architectures: **We rely too heavily on the semantic understanding of embedding models, forgetting that they fundamentally do not understand temporal logic.**

In this article, I will give you a hardcore breakdown of this paper and explore how to save your RAG system through "modularity" and "symbolic logic."

{{< admonition abstract "TL;DR (Key Highlights)" >}}
1.  **Pain Point**: Existing retrievers (like Contriever, BM25) only perform "keyword matching" and cannot understand temporal logic like \( 2018 < 2019 \).
2.  **Solution**: MRAG proposes a **training-free** modular framework that disentangles "semantic understanding" from "temporal reasoning."
3.  **Core Technology**: Utilizes LLMs for fine-grained evidence summarization combined with **Symbolic Algorithms** for hybrid ranking.
4.  **Performance**: On the new TempRAGEVAL benchmark, it significantly outperforms current SOTA models, proving that "Neural Networks + Symbolic Logic" is the right direction for complex reasoning.
{{< /admonition >}}

## Why Does RAG Turn from "Smart" to "Stupid"?

Before diving into the MRAG architecture, let's discuss why this problem is so difficult to solve.

Existing SOTA retrievers (whether Dense Retrievers or BM25) essentially calculate "similarity." When you input "Who is the UK PM in 2019?", the model converts this sentence into a Vector and then searches a Vector DB for the closest documents.

**Here lies the "devil in the details":** The model treats "2019" as just another ordinary token, much like "Apple" or "Banana."

*   **The String Matching Trap**: If a document says "In 2019...", the model can find it.
*   **Logical Collapse**: If you ask "Who was the PM in **May 2021**?", but the correct document only says "Boris Johnson (2019–2022)", the model gets confused because it doesn't understand the interval logic of \( 2019 < 2021 < 2022 \). Instead, it might fetch news containing the string "May 2021" that is completely irrelevant.

Simply put, **Neural Networks are great at fuzzy semantic matching (vibes), but very poor at precise numerical logic.**

## MRAG's Solution: Divide and Conquer

The core insight of MRAG (Modular Retrieval Augmented Generation) is brilliant: Since embedding models can't learn math, let's stop forcing them to.

The authors propose a **Disentanglement** strategy:
*   **Semantics**: Handled by Neural Networks (what they are good at).
*   **Temporality**: Handled by deterministic **Symbolic Algorithms**.

Here is what the end-to-end process looks like when broken down:

{{< image src="figure3.png" alt="Three-stage MRAG pipeline: (1) question processing segments a question into a main content part and a temporal constraint part, (2) retrieval and summarization pulls and condenses relevant Wikipedia passages, and (3) semantic-temporal hybrid ranking combines semantic and temporal scores to rank passages and return the answer" caption="Complete MRAG architecture flowchart: The pipeline from Question Processing to Hybrid Ranking." >}}

Let's break down this pipeline step-by-step.

### Phase 1: Question Processing

First, the system does not directly feed the entire question to the retriever. Instead, it decomposes the user's query into two independent signals:

1.  **Main Content (MC)**: Removes temporal constraints, keeping only the core entities.
    *   *Query:* "Who is the UK PM **as of 2019**?"
    *   *MC:* "Who is the UK PM?"
    *   *Purpose:* Retrieve all related entities first, regardless of the time, to ensure high Recall.
2.  **Temporal Constraint (TC)**: Extracts specific timestamps and relations.
    *   *TC:* Relation="as of", Timestamp="2019".

This step is usually combined with **Regex** or NLP tools (like spaCy), which are more robust than using an LLM alone, as we want to avoid LLM hallucinations here.

### Phase 2: Fine-grained Evidence Processing (Retrieval & Summarization)

A common mistake in traditional RAG is retrieving an entire "Chunk" (paragraph). A single paragraph might contain decades of history for an entity, leading to **Temporal Mixing**.

MRAG's approach is:
1.  **Broad Retrieval**: Use the MC to fetch Top-K (e.g., 100) documents.
2.  **Fine-grained Segmentation**: This is the key. The system splits documents into **"Single Fact Units."**
    *   The authors recommend using **LLM Summarization**: Let the LLM read the paragraph and generate a "concentrated sentence" ensuring that this sentence contains only one clear timestamp and fact.

This results in a clean set of \( (Sentence_i, T_{evidence\_i}) \) evidence pairs, significantly reducing noise.

### Phase 3: Semantic-Temporal Hybrid Ranking (The "Secret Sauce")

This is the soul of MRAG. The system scores each piece of evidence twice:

1.  **Semantic Score (\(S_{sem}\))**: Calculated using an Embedding model for similarity.
2.  **Temporal Score (\(S_{tem}\))**: **No neural networks are used.** It is based on rule-based **Spline Functions**.

The authors designed 6 types of mathematical curves to correspond to different temporal intents:

| Intent | Relation | Physical Meaning |
| :--- | :--- | :--- |
| **Last (Find newest)** | `before` | Before the cutoff, the closer the better (Recency Bias). |
| **First (Find earliest)**| `after` | After the starting point, the closer to the start the better. |

{{< image src="figure8.png" alt="Grid of six line plots showing temporal scoring functions for before, after and between constraints on the last and first event dates, each combining a hard cutoff that drops the score to a baseline with a sloped soft preference that peaks near the target year" caption="Diagram of six temporal scoring functions. Note the combination of hard constraints (zeroing out) and soft preferences (slopes)." >}}

The final score formula is:
$$ S_{final} = S_{sem} \times S_{tem} $$

This multiplication formula is simple but effective, providing a **"Veto Power"**:
*   If the time is completely wrong (\(S_{tem} \approx 0\)), even if the semantics are highly relevant (e.g., a perfect keyword match), the total score remains 0.
*   This directly solves the classic RAG problem of "keyword match but wrong year."

## Experimental Results: A Dominant Lead

To verify this architecture, the authors created a new benchmark called **TempRAGEVAL**. They did something quite challenging: they introduced **Temporal Perturbations**.

For example, changing "Who was PM in 2019?" to "Who was PM **before** 2020?".

The results were telling:

{{< image src="table2.png" alt="Results table on TempRAGEval TimeQA and SituatedQA comparing retrieval methods such as BM25, contriever and various rerankers against MRAG on answer recall and evidence recall at 1 and 5, where MRAG achieves the best scores including 90.0 answer recall at 5 on TimeQA" caption="Table 2: Performance comparison of MRAG versus other retrieval methods on TempRAGEVAL." >}}

1.  **Traditional Methods Collapse**: Even powerful models like GEMMA (an LLM-based Reranker) saw a significant drop in performance when facing perturbations, confirming they are merely performing advanced keyword matching.
2.  **MRAG Thrives**: MRAG not only withstood the perturbations but achieved an Evidence Recall (ER@5) of **59.2%**, far exceeding GEMMA's **45.3%**.

Interestingly, on the **TimeQA** dataset (which contains more niche, long-tail knowledge), MRAG's advantage was even greater. This suggests that **when an LLM cannot rely on "memorizing" training data to answer, precise retrieval logic becomes the only lifeline.**

## Conclusion

1.  **Don't Idolize End-to-End**: In the LLM era, it's easy to get lazy and throw everything into the Context Window for the model to learn. But MRAG proves that for **precise logic (math, time, code execution)**, stripping it away from the neural network and handing it to a deterministic Symbolic System often yields better results. [UniversalRAG](../universal-rag/) applies a similar "disentanglement" philosophy to a different axis of the retrieval problem — modality and granularity instead of time.
2.  **Architecture Design > Model Size**: This paper didn't train a massive model with hundreds of billions of parameters; instead, it solved the problem through elegant Pipeline design. This is where engineers provide real value.
3.  **Neuro-Symbolic AI is the Future**: This hybrid architecture—where the neural network handles semantics and symbolic logic handles reasoning—will likely be the mainstream direction for building complex Agents in the future.

If you are struggling with "hallucinations" or "logical errors" in your RAG system, consider MRAG's approach and try disentangling your problem.
---
# weight: 1
title: "Why Your RAG Fails at Complex Tables—And How MixRAG Fixes It: A Deep Dive into Heterogeneous Document Retrieval"
date: 2026-03-15
lastmod: 2026-03-15
draft: false
description: "Boost your RAG system's performance on complex hierarchical tables and text. Discover the MixRAG framework: featuring H-RCL for precise data retrieval and the RECAP strategy to eliminate LLM calculation hallucinations in heterogeneous documents."
featuredImage: "featured-image.jpg"

tags: ["Large Language Model", "Retrieval-Augmented Generation", "Tabular Data"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## Introduction

Most of us have probably had this experience: when we use LangChain or LlamaIndex to whip up a RAG (Retrieval-Augmented Generation) system and test it on Wikipedia entries or press releases, it usually performs quite well, giving us the illusion that "I've mastered AI."

However, once you move this system into real-world business scenarios—such as feeding it a hundred-page financial annual report, clinical guidelines, or government reports filled with long-winded narratives and "Hierarchical Tables"—you'll find that the system's performance often takes a nosedive. In fact, it's not an exaggeration to say its "IQ instantly drops to zero."

Recently, while digging into papers for KDD 2026, I came across a specific study: **"Mixture-of-RAG: Integrating Text and Tables with Large Language Models"** ([arXiv:2504.09554](https://arxiv.org/abs/2504.09554)). This paper doesn't play around with fluff; it tackles "Heterogeneous Documents"—the industry's biggest pain point—head-on, proposing an elegant architecture filled with engineering wisdom.

In today’s article, let’s grab a cup of coffee and dive deep into this powerful framework called **MixRAG** to see how they transform complex academic theories into hard-hitting engineering practices.

{{< admonition abstract "Key Takeaways (TL;DR)" >}}
This paper proposes the **MixRAG** framework, specifically designed to solve retrieval inaccuracies and calculation hallucinations in RAG systems when processing "long text + complex hierarchical tables." There are three core highlights:
1.  **Hierarchical Table Representation (H-RCL)**: Instead of forcing the model to read a large 2D table, it decomposes tables into natural language sentences containing "ancestral hierarchical paths," allowing Embedding models to understand structured data.
2.  **Two-Stage Retrieval**: First, it uses BM25 + Embedding to find parent documents, then utilizes an LLM to perform "miniature vector retrieval" within the document to filter noise, providing extreme control over the Context Window.
3.  **Decoupling Logic and Calculation (RECAP Strategy)**: Acknowledging that LLMs are poor at math! It forces the LLM to only "extract evidence" and "write calculation formulas," finally handing them over to a Python calculator for precise results.
{{< /admonition >}}

## Why Do We Need This Paper?

Before diving into MixRAG’s ingenious architecture, we must understand: **What were the insurmountable hurdles we faced before it appeared?**

We found that existing SOTA (State-of-the-Art) methods exhibit several fatal flaws when dealing with "heterogeneous documents" where text and tables are intertwined:

1.  **Crude Structural Representation**: The traditional approach usually treats a table as ordinary text, flattening it into Markdown or asking an LLM to generate a vague "table-level summary." There is a serious problem here: this completely destroys the "hierarchical dependencies" within the table.
    *   *Imagine this*: A table has a number "100." Above it, the headers span "2023 -> Q1," and to its left, they span "Revenue -> Product X." Once converted to plain text and this "coordinate path" is lost, the number "100" becomes a meaningless digit to the Embedding model.
2.  **Severe Limitations in Retrieval Precision**: Traditional RAG relies heavily on semantic similarity (Dense Retrieval). However, when dealing with financial data, questions often require precise numerical or year comparisons. Relying solely on Embeddings makes it easy to pull up a lot of "semantically similar" but "data-devoid" filler; if only BM25 keyword retrieval is used, paragraphs with different wording but the same meaning are missed.
3.  **Disastrous Reasoning Accuracy**: Even if you get lucky and find the correct document and table, when a question involves "calculating the growth rate from 2013 to 2014," relying on the LLM to perform "mental math" across cross-modal data almost inevitably triggers severe Hallucination.

Since treating tables as text doesn't work, the authors of MixRAG decided to take a step back and redesign a dedicated Pipeline. The core insight of this solution is simple: **Acknowledge that Embeddings don't understand complex tables, and acknowledge that LLMs are bad at math.**

Next, let's look at how they "prescribe the right medicine."

## MixRAG Methodology: Preparation, Selection, and Execution

The MixRAG system architecture process: **Document Representation, Cross-Modal Retrieval, and Multi-Step Reasoning.**

{{< image src="overview.png" caption="MixRAG Framework Overview: Data starts from heterogeneous documents on the left, is decomposed via H-RCL, enters the two-stage retrieval in the middle, and is finally processed by the RECAP module for reasoning and calculation." >}}

### Heterogeneous Document Representation

The ultimate goal of this module is to transform "unstructured text" and "structured tables" into a unified set of "Chunks" that are best suited for retrieval algorithms.

For **text**, the authors do not use rigid fixed-token splitting. Instead, they use `spaCy` for Coreference Resolution (restoring "It" to "The revenue") and then perform sentence-level splitting with complete semantic integrity.

But the real highlight lies in the **handling of tables: H-RCL Summary (Hierarchy Row-and-Column-Level Summary)**.

To solve the "lost coordinates" problem mentioned earlier, H-RCL employs a dimensionality reduction strategy. Think of a complex table as a map. To precisely locate a data unit \( d_{i,j} \), we need its complete "genealogy":
*   **Left header path**: \( P_l(i) = h_l^1 \rightarrow h_l^2 \rightarrow \dots \rightarrow h_l^R \)
*   **Top header path**: \( P_t(j) = h_t^1 \rightarrow h_t^2 \rightarrow \dots \rightarrow h_t^R \)

The system traverses the table, combines these paths with the data, and hands them to the LLM to generate natural language descriptions (Row Summary \( S_{row} \) and Column Summary \( S_{col} \)). In this way, a 2D table with \( M \) rows and \( N \) columns is "semanticized" into \( M + N \) independent natural language paragraphs.

{{< admonition tip "A Devilish Detail: The Dual-Track Chunking Strategy" >}}
While reading this paper, I noticed an extremely subtle engineering trade-off: **MixRAG does not completely discard the traditional Table-Level Summary!**
*   **Data stream for Embedding**: Uses the decomposed \( M + N \) **H-RCL Chunks**. This is because vector models require extremely fine-grained semantic dependencies for precise matching.
*   **Data stream for BM25**: Retains a **single Table-Level Summary Chunk**. Why? Because if you split the word "Revenue" into dozens of H-RCL sentences, it causes the BM25 Term Frequency (TF) to go haywire, resulting in a "keyword over-aggregation" bias.

This is the kind of design only an engineer with real-world experience would make.
{{< /admonition >}}

### Cross-Modal Retrieval Module

Now we have a database full of various fine-grained Chunks. Next, we need to precisely lock onto the document \( D^* \) that can answer the question from among thousands of documents using a **"two-stage funnel."**

**Stage 1: Ensemble Retrieval**

Since a single algorithm has blind spots, we use a two-pronged approach:
*   Use BM25 to catch exact keywords and find the Top-M Chunks.
*   Calculate the cosine similarity between the query vector \( V_Q \) and each Chunk vector \( V_{Chunk} \) to find the Top-N Chunks.
*   **Key Step (Mapping)**: What we retrieved are "sentences," but what must be returned to the downstream is the "entire document" to preserve context. Therefore, the system traces back to the Parent Documents these Chunks belong to, takes the union, removes duplicates, and obtains Top-K candidate documents.

**Stage 2: LLM-based Retrieval**

Faced with these K documents that are still quite long, if we feed them directly to the LLM, the Context Window will definitely explode, or "Lost in the Middle" will occur.
The authors introduced **Dynamic Content Filtering**: performing another miniature vector retrieval "inside the document" to remove noise below a threshold \( \theta \), reassembling the essence into a "condensed document." Finally, the LLM acts as a high-level judge to select the most perfect document \( D^* \).

### Multi-Step Reasoning Module

With the most precise document in hand, we finally face the LLM's poor mathematical ability. To address this, the authors tailored the **RECAP Prompting Strategy (Restate, Extract, Compute, Answer, Present)**.

This is a framework that forces the LLM to decompose its thinking, strictly outputting in steps:
1.  **Restate**: Restate the question.
2.  **Extract**: Explicitly extract data from the document (to prevent hallucination).
3.  **Compute (Core Highlight)**: **Require the LLM to only write the precise mathematical calculation formula**, wrapped in specific symbols (e.g., `##(652-515)/515##`), and forbid it from guessing the answer.
4.  **Answer & Present**: Formatted output.

{{< admonition tip "Why is RECAP so strong? The Art of Single-Turn Generation + Post-Processing" >}}
This is different from the common Agentic Workflow (like ReAct, which pauses to call a tool).
In MixRAG, the LLM generates these five steps in one go (single-turn conversation). What truly provides the power is the outer **Python script**:
The script uses Regex to capture the strings inside `##`. If a mathematical formula is found, the system **forcefully ignores the LLM's mental math result**, directly uses Python's `eval()` to execute the formula, and returns the absolutely precise value.
This approach of "decoupling logic and calculation" requires only one API call, balancing high accuracy with low latency!
{{< /admonition >}}

## Experimental Results: The Logic Behind the Data

To verify this, the authors built their own high-quality dataset, **DocRAGLib**, containing 2,178 real heterogeneous documents. Let's see how MixRAG performs in this brutal arena.

{{< image src="table1.png" caption="This table proves MixRAG's total dominance over existing methods in retrieval precision. Note especially the abysmal 1.59% for Standard RAG compared to MixRAG's SOTA performance of 54.10%." width=85% >}}

**Retrieval Performance Dominance:**

Did you see in Table 1 that **Standard RAG's HiT@1 was only 1.59%**? This ruthlessly reveals that when you throw a complex table PDF into a default Text Splitter, the structure is completely shattered, and the retrieval system is basically guessing.
Meanwhile, MixRAG (powered by GPT-4o) reached **54.10%**. This is because it didn't shred the table but gave the Embedding model clear coordinates through H-RCL.

{{< image src="table2.png" caption="This table proves that the RECAP strategy is more robust and reliable than the well-known CoT and PoT when solving complex numerical reasoning, achieving the highest scores across multiple models." >}}

**Reasoning Robustness:**

In terms of Exact Match, **RECAP (64.66%)** significantly beat CoT (46.87%) and PoT (61.90%).
*   It beat CoT because we don't let the LLM do mental math.
*   It beat PoT (which requires the LLM to write complete Python code to solve the problem) because in real documents full of noise, the code written by the LLM is highly prone to crashing due to variable naming errors. RECAP’s "half-natural language + half-mathematical formula" approach has much higher robustness.

{{< image src="table4.png" caption="This table proves that 'retaining hierarchical paths' is the only correct solution for retrieving heterogeneous tables. H-RCL's performance far exceeds flattened table summaries." >}}

**Ablation Study:**

If only "table-level summaries" are used, HiT@1 is only 36.27%; switching to full H-RCL (retaining ancestral paths) causes the score to jump to 54.10%. This perfectly validates the idea: **Data without coordinates is garbage data.**

## Conclusion and Takeaways

Admittedly, MixRAG is not a perfect silver bullet. When a user asks an extremely vague question (no clear Entity) or needs to perform extra-long multi-step reasoning across five or six tables, the system might still get lost. Future solutions might need to move toward "Query Decomposition," breaking down complex questions into sub-questions before retrieval—a necessary path toward truly Agentic systems.

**The most elegant aspect of MixRAG lies in its precise control of Boundaries.** Let the traditional stay traditional (BM25), let the statistical stay statistical (Embedding), let the logic belong to the model (LLM), and let the calculation belong to the program (Calculator). Only when each tool is placed where it performs best can we forge the most powerful RAG system for the most complex real-world scenarios.

If you have been struggling recently with a Q&A system for internal financial reports or legal documents, I strongly suggest you check out this masterpiece from KDD 2026. I believe it will provide you with plenty of inspiration!

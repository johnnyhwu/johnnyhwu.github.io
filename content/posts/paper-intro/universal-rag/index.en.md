---
# weight: 1
title: "UniversalRAG: Mastering Multimodal RAG with Intelligent Routing and Granularity Control"
date: 2026-03-25
lastmod: 2026-03-25
draft: false
description: "Discover UniversalRAG: A breakthrough multimodal RAG framework by KAIST. Learn how its intelligent Router solves modality bias and granularity issues to optimize retrieval across text, tables, images, and video for large-scale AI applications."
featuredImage: "featured-image.jpg"

tags: ["Large Language Model", "Retrieval-Augmented Generation", "Prompting"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## Introduction

Before diving into the details, let's get acquainted with this work presented by the KAIST team: [**UniversalRAG: Retrieval-Augmented Generation over Corpora of Diverse Modalities and Granularities**](https://arxiv.org/abs/2504.20734). If you are looking for a more intuitive demo or the code, you can check out their [**Project Page**](https://universalrag.github.io/).

**Why is this paper worth our attention?**

Traditional RAG systems are like librarians who can only flip through "textbooks." Even with the advent of multimodal RAG, they typically operate within a single modality (e.g., searching only images or only text). However, real-world problems are complex; sometimes the answer is hidden in a specific moment of a video, and other times it requires comparing a design blueprint with a technical manual.

**The core philosophy of UniversalRAG is: rather than forcing all modalities to align into a single chaotic vector space, it is better to build an intelligent "Router" to achieve precise retrieval through a "diagnosis before prescription" approach.**

In this note, we will cover:

- **Core Strategy**: How to avoid modality bias (Modality Gap) through Modality-aware Routing.
- **Granularity Control**: How to dynamically determine the size of retrieved information (from short paragraphs to entire videos).
- **Implementation Details**: Specific approaches for Training-based and Training-free Routers.
- **Practical Thinking**: Implementation challenges and solutions for enterprise private data (e.g., Table vs. Text).

{{< image src="figure1.png" alt="Four-panel diagram comparing RAG limitations to UniversalRAG: (A) single-modality RAG retrieves an irrelevant flower image when text evidence is needed, (B) single-granularity RAG retrieves a full 2-hour video when only a short clip is needed, (C) single-corpus RAG suffers from a modality gap and returns unrelated text for a video query, while (D) UniversalRAG uses a Router to send four query types to their matching text, image, short-video, or full-video corpus and generate correct answers" caption="Comparison between UniversalRAG and traditional RAG strategies. We can see that UniversalRAG dynamically guides queries to the most suitable combination of modality and granularity through a Router." width=85% >}}

{{< admonition tip "Quick Summary" >}}
The key to UniversalRAG's success lies in **"Decoupling."** It does not strive for an all-in-one vector space, but rather an all-in-one "Command Center (Router)," allowing each type of data to be retrieved within its own most proficient index space.
{{< /admonition >}}

In this paper, the authors precisely identify the three core challenges currently faced by RAG systems on the path toward "universality." As we mentioned in previous discussions, these issues become even more difficult when dealing with enterprise-level private data.

## Problem Definition: The Three Major Bottlenecks Facing Existing RAG Systems

While RAG has significantly improved the accuracy of Large Language Models (LLMs), existing solutions typically assume that knowledge sources are single and homogeneous. However, real-world knowledge is fragmented and heterogeneous.

The following are the technical hurdles we must overcome:

### Modality Limitation

Most traditional RAG systems are limited to pure text retrieval. Although some recent studies have extended this to images or videos, they usually operate only on a **specific corpus of a single modality**.
*   **Pain Point**: User queries are diverse; some require consulting product manuals (text), while others require watching assembly tutorials (video). If the system can only handle a single modality, it cannot answer questions that require "cross-modal evidence."

### Modality Gap in Embedding Space

To solve multimodal problems, the most intuitive method is to use a multimodal encoder like CLIP to map text, images, and videos into the same vector space for similarity retrieval (Unified Embedding Space). However, this leads to significant **modality bias**.

*   **Phenomenon**: In a vector space, data points tend to cluster based on "modality" rather than "semantics." This means the distance between a text query and text data is often closer than its distance to more semantically relevant image data.
*   **Consequence**: When we input a text question, the system prioritizes grabbing text content due to modality proximity, even if the most accurate answer is actually hidden in a picture or video.

{{< image src="figure2.png" alt="t-SNE scatter plot of a unified embedding space showing four separated clusters labeled Query, Text, Image, and Video, with the Image and Video clusters clearly isolated from the Text/Query cluster, illustrating the modality gap" caption="t-SNE visualization of a unified embedding space. We can see that different modalities (text, image, video) form distinct clusters. This is the so-called Modality Gap, which leads to bias during retrieval." >}}

### Granularity Mismatch

The "size" or "length" of data—referred to as retrieval granularity—has a decisive impact on generation quality:
*   **Too Fine-grained**: For example, retrieving an extremely short sentence. While precise, it often lacks the context required to answer complex logical questions.
*   **Too Coarse-grained**: For example, grabbing a full two-hour video to answer a question about a 10-second action. This introduces a large amount of irrelevant noise, interferes with model generation, and is extremely wasteful of computational resources.

Existing RAG systems are usually fixed to a single retrieval unit (such as paragraph-level) and lack the ability to adjust flexibly.

### Efficiency & Scalability

When we attempt to build a "super index" containing all modalities and all granularities, retrieval latency grows linearly or logarithmically with the amount of data \(N\). When processing enterprise data at the scale of tens of millions or more, search cost and speed become unavoidable burdens.

{{< admonition tip "Practical Observation" >}}
In enterprise private data scenarios, the boundary between Table (structured) and Text (unstructured) is often blurred. If we cannot clearly distinguish data types and select retrieval granularity accordingly, we fall into the trap of "retrieved data being irrelevant and mismatched" or "retrieval speed being too slow to use."
{{< /admonition >}}

Addressing the aforementioned challenges, UniversalRAG proposes an intelligent architecture based on "**diagnose first, then prescribe**." We don't need a universal vector space to accommodate all data; instead, we need a universal **Command Center (Router)** to decide where to look for data.

Below, we will delve into the logic and implementation details behind this design.

## Methodology: The Core Architecture of UniversalRAG

The core design of UniversalRAG lies in transforming the retrieval process from a "single-space search" into "**dynamic path selection**." The entire workflow can be divided into three stages: **Routing**, **Targeted Retrieval**, and **Generation**.

### Hierarchical Organization of Modalities and Granularities

To achieve precise retrieval, we cannot simply throw data together. UniversalRAG suggests "decoupling" the database according to modality and granularity:
*   **Text Modality**: Divided into `Paragraph` (paragraph-level) and `Document` (document-level, suitable for multi-hop reasoning).
*   **Table Modality**: Independent `Table` index, specialized for structured data.
*   **Image Modality**: `Image` index, preserving original visual features.
*   **Video Modality**: Divided into `Clip` (short segments, locating specific actions) and `Video` (entire video, understanding long-term temporal plots).

This organization ensures that each database can use the encoder most suitable for that modality, avoiding the modality gap caused by forced alignment.

### The Router

The Router's task is to analyze the intent of the Query and select the best combination from **7 Pathways**.

#### Router's Label Space

The Router does not perform a single-choice selection but rather a multi-label selection. It chooses from the following set of **Modality-Granularity Pairs**:

1. `None`: Answer directly, no retrieval needed.
2. `Paragraph`: Text - Fine-grained.
3. `Document`: Text - Coarse-grained.
4. `Table`: Structured Table.
5. `Image`: Static Image.
6. `Clip`: Video - Fine-grained.
7. `Video`: Video - Coarse-grained.

#### Training-based Router

When fixed hardware resources are available and high speed is required, a lightweight model (such as Qwen3-VL-2B) is fine-tuned.

*   **Automated Label Generation**: Since real-world data lacks labels, the authors utilized inductive bias. For example, questions from `WebQA` are automatically labeled as `Paragraph+Image`.
*   **Loss Function**: This is a multi-label classification problem. We apply a Sigmoid transformation to the logic value \(z_i\) for each category \(i\) output by the model to obtain the probability \(\hat{y}_i\):
    $$\hat{y}_i = \sigma(z_i) = \frac{1}{1 + e^{-z_i}}$$
    Then, **Binary Cross-Entropy (BCE)** is used to calculate the total loss:
    $$\mathcal{L} = -\frac{1}{7} \sum_{i=1}^{7} [ y_i \log(\hat{y}_i) + (1 - y_i) \log(1 - \hat{y}_i) ]$$.
    Where \(y_i\) is the ground truth label (0 or 1). During inference, a pathway is activated as long as the probability exceeds a **threshold \(\tau = 0.8\)**.

#### Training-free Router

This is particularly effective for the enterprise private data (OOD) scenarios we discussed. We use **Prompt Engineering** to let a powerful LLM (like GPT-4o) make the decision directly.

{{< image src="figure8.png" alt="Text box showing the prompt template that classifies a query into categories such as No, Paragraph, Document, Table, Image, Clip, and Video based on whether RAG is needed and which modality fits, with category definitions and worked examples like 'What is the capital of France?' mapped to No and 'Describe the appearance of a blue whale.' mapped to Image" caption="The Prompt Template designed in the paper. It teaches the LLM to distinguish between 'Paragraph' and 'Document' through comparative examples, and how to use the '+' sign to combine multiple modalities." >}}

The design logic of this Prompt lies in **"Intent Recognition"**:
*   If the question involves "comparison, summation, numerical values," guide to `Table`.
*   If it involves "appearance, color, structure," guide to `Image`.
*   Teach the model to handle complex intents (e.g., `Paragraph+Clip`) through few-shot examples.

### Generation

Once the Router determines the path (e.g., `Paragraph+Image`), the system will:

1.  **Parallel Retrieval**: Simultaneously search for the most relevant Top-K evidence in the text paragraph library and the image library.
2.  **Evidence Integration**: Feed the retrieved text fragments and image features simultaneously into a Multimodal Large Language Model (LVLM).
3.  **Answer Generation**: The model performs comprehensive reasoning based on multimodal evidence to provide the final answer.

{{< admonition tip "Our Thoughts on Enterprise Implementation" >}}
When handling enterprise private data, the boundary between Table and Text can be very blurred. In the early stages when data labels are insufficient, **Hybrid Search** can be adopted first, and the Router's threshold can be lowered (e.g., set to 0.5) to let the system enter a "multi-path retrieval" state to ensure recall. Once enough user logs are accumulated, a Teacher LLM can be used to label the data and train a high-precision Router specific to that enterprise.
{{< /admonition >}}

### Why is this method effective?
The elegance of UniversalRAG lies in its solution to "**Modality Bias**."

Past methods calculated similarity by putting questions and images together, but text questions are inherently more "friendly" to text data. UniversalRAG's routing mechanism makes decisions at the **"semantic level."** When the Router says, "this question requires looking at a picture," the system only searches the image library, completely cutting off the mutual interference between modalities.

After understanding the design blueprint of UniversalRAG, we must use data to verify whether this "Command Center" strategy is truly superior to traditional approaches. The experimental results not only prove the improvement in accuracy but also reveal its efficiency advantages when processing large-scale data.

## Experimental Results

The authors conducted extensive evaluations across 10 benchmarks covering different modalities and granularities. Below are a few key findings we believe are most noteworthy:

### All-around Performance Leadership

Across a variety of RAG tasks, UniversalRAG demonstrated powerful dominance. Whether it was simple text queries, text-image combinations, or complex video analysis, UniversalRAG significantly outperformed single-modality RAG and traditional unified embedding space methods.

{{< image src="table1.png" alt="Results table comparing UniversalRAG against baseline methods such as Naive, ParagraphRAG, DocumentRAG, TableRAG, ImageRAG, ClipRAG, VideoRAG, and MultiRAG across 10 datasets including MMLU, NQ, HotpotQA, WebQA, and LVBench, showing UniversalRAG with trained or training-free routers achieving the highest average scores (up to 42.40) among non-oracle methods, close to the Oracle upper bound of 42.45" caption="Table 1 shows the performance of UniversalRAG across 10 different datasets. Whether using a training-based or training-free router, UniversalRAG outperformed the baseline models on almost all metrics." >}}

### Successfully Bridging the Modality Gap

This is the core argument of our discussion: is traditional Unified Embedding truly biased? The experiment gives an affirmative answer.

*   **Finding**: As shown in **Figure 4**, models like GME or VLM2Vec that squeeze all modalities together exhibit a strong "text bias" during retrieval—even when the question requires image or video evidence, they still tend to grab text.
*   **Comparison**: UniversalRAG's router can accurately allocate retrieval paths based on question intent. This proves that **"routing before retrieval"** can effectively bypass the modality gap, allowing the correct evidence to be recalled.

{{< image src="figure4.png" alt="Bar chart titled Modality Selection Rate comparing VLM2Vec-V2, GME, and UniversalRAG: VLM2Vec-V2 selects Text 100% of the time, GME selects Text 85% and Image/Video only 12%/3%, while UniversalRAG is balanced across None (23%), Text (30%), Image (24%), and Video (23%), closely tracking the dashed Oracle line" caption="Modality selection distribution map. We can see that Unified Embedding methods are heavily biased toward text, while UniversalRAG (far right) can choose image and video modalities in a balanced manner based on demand." width=70% >}}

### Scalability

For the enterprise-level large-scale data applications we were concerned about, **Figure 5** provides very strong support.

*   **Sub-linear Latency**: In traditional RAG, search time typically grows linearly or logarithmically as the database \(N\) increases. However, in UniversalRAG, because the router filters out irrelevant libraries beforehand, the actual search range is narrowed down to \(1/k\).
*   **Big Data Advantage**: When the data scale reaches tens of millions (10M) or even hundreds of millions, the latency of UniversalRAG is far lower than that of unified retrieval methods. This means **the overhead of the router is completely worth it in large-scale scenarios**.

{{< image src="figure5.png" alt="Line chart of retrieval latency in seconds versus corpus size (log scale from 100k to 100M) showing VLM2Vec-V2's latency spiking to about 2.6 seconds at 100M items while UniversalRAG with T5Gemma 2 270M stays low at roughly 0.45 seconds, demonstrating better scalability" caption="Trend of retrieval latency with corpus scale. It can be seen that UniversalRAG exhibits excellent scalability under large-scale data." width=70% >}}

After the introduction, problem analysis, methodology details, and experimental verification, we have finally reached the end of this note. This paper does not just propose a new SOTA model; more importantly, it provides us with a brand-new way of thinking about processing "heterogeneous knowledge."

## Conclusion

The emergence of **UniversalRAG** marks a significant step for RAG technology from "single corpus" toward "all-around knowledge retrieval." Through this paper and our deep discussion, we can summarize the following three core insights:

### Routing is the Silver Bullet for Modality Gaps

We used to strive for a universal "aligned vector space," hoping that text, images, and videos could coexist in the same dimension. But UniversalRAG tells us: **forced alignment brings bias**. By routing at the semantic level and allowing each type of data to retain its most original and specialized representation, more fair and accurate retrieval results can be obtained. This idea of "Decoupling" is the key to solving complex multimodal problems. Interestingly, the same philosophy shows up when disentangling temporal reasoning from semantic search in [MRAG](../mrag/), just applied to a different axis of heterogeneity.

### A Win-Win for Efficiency and Accuracy

When processing large-scale data, we often worry about the system becoming bloated. UniversalRAG proves, through a "diagnosis before prescription" strategy, that adding a lightweight router (even just a \(1B\) scale model) will not slow down the system. Instead, it achieves "sub-linear" latency growth in large-scale corpora. This provides substantial confidence for us to deploy ultra-large-scale RAG systems in the industry.

### Translation from Research to Practice

Although the paper performs excellently on benchmarks, when facing internal enterprise private data, we have summarized a more practical implementation strategy:
*   **Initial Phase (Cold Start)**: Adopt a "Prompt-based Router" combined with "Hybrid Search" to ensure system stability and recall rate.
*   **Middle Phase (Accumulation)**: Use a Teacher LLM to automatically label real User Logs, distinguishing the boundaries of Table, Text, and Image usage.
*   **Final Phase (Optimization)**: Train a lightweight router specific to the enterprise environment to achieve the true form of "UniversalRAG."

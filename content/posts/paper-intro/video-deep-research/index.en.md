---
# weight: 1
title: "VideoDR: Bridging the Gap Between Video Understanding and Agentic Search on the Open Web"
date: 2026-01-25
lastmod: 2026-01-25
draft: false
description: "Discover VideoDR, a new benchmark for AI Video Deep Research that bridges the gap between Video Understanding and Agentic Search. Learn how this paper reveals the \"Goal Drift\" challenge in multimodal agents, compares Workflow vs. Agentic paradigms, and introduces the concept of Visual Anchors for open-web reasoning. Essential reading for AI researchers interested in Video QA and RAG."
featuredImage: "featured-image.jpg"

tags: ["Vision Language Model", "Deep Research", "Benchmark"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## Introduction

In the wave of artificial intelligence research, we have witnessed the rapid development of Video Understanding and Agentic Search. However, a gap has long existed between these two fields. The paper discussed today, **"Watching, Reasoning and Searching: A Video Deep Research Benchmark on Open Web for Agentic Video Reasoning"** (hereinafter referred to as **VideoDR**), was born to fill this piece of the puzzle. ([arXiv Paper](https://arxiv.org/abs/2601.06943) | [GitHub](https://github.com/QuantaAlpha/VideoDR-Benchmark))

### One-Minute Summary
This paper defines a brand new task — **Video Deep Research**. Unlike the closed-ended Q&A of the past where "the answer is in the video," this task requires AI models to first extract visual clues (Visual Anchors) from the video, convert them into search queries, and perform multi-step retrieval and reasoning on the Open Web to find the final answer. The authors constructed a high-difficulty Benchmark that underwent a rigorous "Double Ablation Test" and compared two mainstream paradigms: **Workflow** and **Agentic**, revealing the "Goal Drift" challenge models face when dealing with long-sequence tasks.

### Core Value

Before we dive deep, we must clarify what "pain points" this paper solves.

1.  **Breaking the "Closed Evidence" Limitation**:
    Traditional Video LLM evaluations (like Video-MME) assume all answers are inside the video. But in real life, videos are often just an "intro." For example, seeing a nameless statue in a travel Vlog and wanting to know its historical background. This requires the model to **step out of the video and into the web**.

2.  **Bridging the "Text-Only Search" Gap**:
    Existing Search Agents (like Search-o1) mostly start from text questions. However, **visual information is irreplaceable**. Often, we cannot precisely describe an object in a video using text and must rely on the model's understanding and extraction of "multi-frame visual signals."

3.  **A Reality Check for Agent Architectures**:
    The industry has been debating whether to use stable Workflows or flexible Agents. This paper provides a fair arena that lets us see the boundaries of both clearly.

### Guide: Most Surprising Insights

What impressed us most about this paper was not a specific new model architecture, but its **profound analysis of the nature of the problem** and **counter-intuitive experimental results**. Here are two core perspectives running through the entire paper:

{{< admonition tip "Core Concept 1: Dual Dependency of Visual Anchors" >}}
The most brilliant part of VideoDR lies in its "cleanliness" regarding datasets. The authors filter data through a **negative** definition:
*   If it can be answered by watching the video without going online -> **Delete** (This is traditional Video QA).
*   If it can be answered by going online without watching the video -> **Delete** (This is Text Search).

What remains are those questions where one **must** first understand the visual hints (Visual Anchors) in the video to construct effective search strategies.
{{< /admonition >}}

{{< admonition tip "Core Concept 2: Agentic is Not a Panacea" >}}
We usually think the stronger the End-to-End Agent, the better. But the experiments in this paper gave us a harsh wake-up call:
**Agent performance is highly dependent on model capability and is susceptible to Goal Drift.**
For many models, as the number of searches increases, they become more easily influenced by the massive amount of textual information on the web, essentially "forgetting" the key visual messages initially seen in the video. In these cases, the seemingly rigid Workflow performs more robustly because it solidifies visual messages into text.
{{< /admonition >}}

## Problem Definition

### Status Quo Fracture: Two Isolated Islands
Before delving into VideoDR, we must understand why the field needs this paper. Before VideoDR appeared, multimodal AI research seemed split into two unconnected islands:

*   **Island A: Closed Video QA**
    *   **Status**: Traditional Benchmarks (like Video-MME, MVBench) assume **the answer is in the video**. The model only needs sufficient visual perception capabilities to extract answers from visuals, subtitles, or narration.
    *   **Pain Point**: This is detached from reality. When we finish watching a travel Vlog and want to know "the reservation number for that restaurant in the video" or "the history of that statue," this information is simply not in the video.
*   **Island B: Pure Text Deep Search**
    *   **Status**: Existing Agent evaluations (like GAIA, Search-o1) mostly start from **text instructions**. Even if they support multimodality, they often only deal with static screenshots.
    *   **Pain Point**: They lack perception of the **Temporal Dimension**. These models cannot understand that "the building appearing at minute 5" and "the interior appearing at minute 10" are the same location, nor can they extract search clues from dynamic visual flows.

### Core Pain Point: The Missing Link
We found that real-world Video Question Answering is often **Open-domain Factoid**. This means:
1.  **Knowledge is on the Web**: Answers are distributed across the massive information on the internet, not within the video.
2.  **Index is in the Video**: Search keywords must be generated by understanding visual details (Visual Anchors) in the video.

Past models either "only understood videos but couldn't go online" or "only understood surfing the web but couldn't understand time series." **VideoDR's core insight is to forcibly bind these two, filling the vacuum between "Video Perception" and "Web Search."**

## Methodology

To test whether models possess this comprehensive "Watch + Search" capability, the authors didn't propose a new model but carefully designed a set of **evaluation tasks** and a **data construction process**. This is the essence of the paper's methodology, especially its data filtering logic, which is full of design ingenuity.

### Task Definition
First, we use mathematical language to precisely describe this task. VideoDR defines the task as a function \( f \):

$$ f : (V, Q; S) \rightarrow A $$

Where each variable represents a specific constraint:
*   **\( V \) (Video)**: The input video. It is the starting point (Anchor) for all reasoning.
*   **\( Q \) (Question)**: A natural language question. This question is designed so it cannot be answered directly by \( V \) or external common sense alone.
*   **\( S \) (Search Tool)**: Browser search tool. This is the model's only way to acquire external knowledge \( K_{web} \).
*   **\( A \) (Answer)**: The final factual output, which must be unique and verifiable.

{{< admonition tip "Core Concept: Visual Anchor & Multi-Hop Reasoning" >}}
Two key operational steps are hidden behind this formula, which are also points we repeatedly emphasize in our discussion:
1.  **Visual Anchor Extraction**: The model must first "watch" the video and translate vague visual signals (like "that red domed building") into concrete textual entities (like "St. Paul's Cathedral").
2.  **Multi-Hop Reasoning**: The model cannot just search once. It usually requires iterative interaction of `Video -> Web -> Video -> Web`. For example: First confirm the location (Web), then look back at the video to confirm the route (Video), and finally search for specific shops on that route (Web).
{{< /admonition >}}

{{< image src="figure2.png" caption="VideoDR Task Example: From identifying the museum (Visual Anchor), to searching for the must-see list (External Knowledge), then combining with the map to locate the specific exhibit (Multi-Hop Reasoning), and finally obtaining the registration number." >}}

### Data Construction: Funnel Filtering
The most brilliant part of this paper lies in the creation of the dataset. The authors do not pursue quantity (only 100 questions in the end), but rather extreme quality.

#### Negative Sample Filtering
Before human annotation, "cheating" possibilities are eliminated:
*   Exclude **Single Scene**: Lack of necessity for temporal reasoning.
*   Exclude **Trending Topics**: This is to prevent models from answering directly using world knowledge in their training data (e.g., "Taylor Swift 2024 Concert Location"). We require the model to rely on the **current** video content.
*   Exclude **Isolated Content**: Videos for which no other information can be found online.

#### Double Ablation Test
This is the gold standard of VideoDR. Every annotated sample \((V, Q, A)\) must pass two rigorous tests to survive:

1.  **Web-only Test**:
    *   **Operation**: Give humans only \( Q \) and search tool \( S \), without the video \( V \).
    *   **Verdict**: If it can be answered correctly, it means the question has leaked information (Information Leakage) -> **Delete**.
    *   **Purpose**: Ensure the question has **Visual Dependency**.

2.  **Video-only Test**:
    *   **Operation**: Give humans only \( V \) and \( Q \), without allowing web search.
    *   **Verdict**: If it can be answered correctly, it represents traditional Video QA -> **Delete**.
    *   **Purpose**: Ensure the question has **External Knowledge Dependency**.

**Only samples that pass both tests simultaneously possess "Dual Dependency," which is the unique feature of the VideoDR dataset.**

{{< image src="figure1.png" caption="VideoDR Data Construction Pipeline: Starting from the candidate video pool, passing through strict negative sample filtering, then undergoing double ablation testing (Web-only & Video-only), finally resulting in high-quality evaluation samples." >}}

### Evaluation Paradigms: Workflow vs. Agent

The authors standardized two problem-solving strategies in the experiment:

#### Paradigm A: Workflow
This is a **"Note first, search later"** strategy.
1.  **Perception Phase**:
    *   The model reads video \( V \) (converted to Visual Tokens).
    *   Based on question \( Q \), it generates a detailed **structured intermediate text** describing key visual clues in the video.
    *   **Key Operation**: After generating the text, **discard the original video \( V \)**.
2.  **Reasoning Phase**:
    *   The model uses only the generated text above and question \( Q \), utilizing the search tool \( S \) to find the answer.

*   **Implementation Detail**: This stage does not use RAG to retrieve video frames but relies on the Long Context capability of MLLMs to read and summarize the video in one go.

#### Paradigm B: Agent
This is a **"Continuous conversation with memory"** strategy.
1.  **Initialization**: Put the Visual Tokens of video \( V \) at the beginning of the Context.
2.  **ReAct Loop**: The model enters a `While` loop:
    *   Observe Context (containing original video tokens).
    *   Generate **Thought** and **Action**.
    *   Execute search, Append **Observation** (web summaries) to the end of the Context.
3.  **Decision**: The model autonomously decides when to stop searching and output the answer.

*   **Implementation Hazard**: The Context structure is `[Video Tokens] + [History] + [Search Results]`. As the number of searches increases, more and more text accumulates at the end of the Context, diluting the model's attention to the initial Visual Tokens, leading to the **Goal Drift** phenomenon we observed.

## Experimental Results

The experimental part of this paper is not to prove "a certain new model is SOTA," but to answer a more fundamental question: **"When dealing with video tasks requiring long-time reasoning, should we convert the video to text (Workflow) or let the large model handle it end-to-end (Agent)?"**

The authors selected current mainstream closed-source models (GPT-4o, Gemini-1.5 Pro) and open-source models (Qwen2-VL, MiniCPM-V, etc.) for a "duel" under both Workflow and Agent paradigms.

### Agent is Not a Panacea

This is probably the most surprising discovery in the experiment. Intuitively, we think letting the model decide when to watch and when to search (Agent) should be stronger than rigid steps (Workflow), but the data tells a different story.

{{< image src="table1.png" caption="Table 1: Performance comparison of different models under Workflow and Agent paradigms. Note that Gemini improves significantly under Agentic, but MiniCPM-V plummets." >}}

*   **The Strong Get Stronger**: For models with ultra-long Context Windows and powerful reasoning capabilities like **Gemini-1.5 Pro**, switching to Agent mode brought significant improvement (accuracy rose from 69% to 76%). It can effectively navigate complex interaction loops.
*   **The Weak Collapse**: For capable but weaker or open-source models (like **MiniCPM-V 4.5**), after switching to Agent mode, performance actually **plummeted** (from 25% to 16%).
*   **The Story Behind the Data**: This proves that Agent is a double-edged sword. For weaker models, the "structured intermediate text" produced by Workflow, although losing some details, provides a **Stable Anchor**. Once this anchor is removed and the weak model directly faces massive search results and original Video Tokens, its attention mechanism gets "lost."

### Goal Drift: The Curse of Long Videos

To delve deeper into "why Agents fail," the authors analyzed the results stratified by **video duration**.

{{< image src="table2.png" caption="Table 2: Performance under different video durations. Note that in the Long Video category, many models' performance drops sharply in Agent mode." >}}

{{< admonition tip "Shocking Discovery: The Longer, The More Forgetful" >}}
Experimental data shows that as videos get longer (Long Videos), the Agent's advantage not only disappears but becomes a disadvantage.
For example, **Qwen3-Omni** has 38% accuracy on short videos, but drops to **20%** on long videos. This confirms the **"Goal Drift"** phenomenon we discussed:
In the long conversation history of Agent mode, the model gradually "dilutes" its attention to the opening Visual Tokens. As it searches, it forgets the "tiny visual clue appearing at a specific minute and second" in the video, getting sidetracked by popular but incorrect information found online.
{{< /admonition >}}

### Error Analysis: The Loss of Visual Anchors
The authors further analyzed error types, and the data again corroborated the above view.

{{< image src="table5.png" caption="Table 5: Error type distribution. Categorical Error is the main killer, implying deviation from the search goal." >}}

*   **Categorical Error** has the highest proportion.
    *   This means the model didn't "miscalculate a value" or have a "logic error," but **looked for the wrong object from the start** (e.g., question asked about Museum A, model went to search for Museum B).
    *   This directly proves that after multi-round searching, the model lost the **Visual Anchor** extracted from the video. Once the initial visual lock fails, subsequent reasoning, no matter how strong, is futile.

### Efficiency Analysis: Busy Does Not Mean Effective

{{< image src="table4.png" caption="Table 4: Tool usage statistics. Gemini is slow but accurate; Qwen searches a lot but uselessly." >}}

*   **Ineffective Retrieval**: Some open-source models saw a surge in search counts in Agent mode, but accuracy did not rise; it fell. This indicates they are conducting ineffective "spray and pray" tactics.
*   **Effective Reflection**: Gemini, which performed best, had significantly more **Thinking Steps**. This tells us that in Video Deep Research, **"Stopping to Reflect"** (e.g., reflecting: "Does the information I found match the image in the video?") is more critical than blind searching.

## Conclusion

This paper successfully fills the gap between Video QA and Deep Research.
1.  **Problem**: Solved the pain point where "visual perception" and "external search" are disconnected in existing evaluations.
2.  **Method**: Proposed the **VideoDR** task, using rigorous "Double Ablation Filtering" to construct a dataset that must rely on both video anchors and web evidence simultaneously.
3.  **Discovery**: Through comparative experiments of Workflow and Agent, revealed that **Long-horizon Consistency** and **Goal Drift** are the biggest bottlenecks for current multimodal Agents.

---
# weight: 1
title: "ERL: Teaching LLM Agents to Learn from a Single Attempt Without Fine-Tuning"
date: 2026-04-10
lastmod: 2026-04-10
draft: false
description: "Boost LLM Agent performance with ERL (Experiential Reflective Learning). This framework extracts \"Trigger-Action\" heuristics from single attempts to solve Agent amnesia, increasing Gaia2 success by 7.8% without fine-tuning."
featuredImage: "featured-image.jpg"

tags: ["Large Language Model", "Retrieval-Augmented Generation", "Single-Agent", "Agent Memory"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## Introduction

### 💡 TL;DR

This paper introduces a lightweight framework called **ERL (Experiential Reflective Learning)**. It enables LLM Agents to reflect on single-task execution trajectories to extract highly condensed "Heuristics"—all without "fine-tuning model parameters" or "repeated trial-and-error." When facing new tasks, the system intelligently retrieves the most relevant experiences and injects them into the prompt. This allows the Agent to truly "learn from its mistakes," significantly boosting the success rate on the Gaia2 benchmark by 7.8%.

### 🎯 Core Value
In the current development of LLM Agents, we face a major bottleneck: **Agents don't learn from their lessons.**
When we deploy Agents in the real world (such as customer service or personal assistants), they act as if they have "amnesia," starting from scratch every time they encounter a new task. The traditional solution is "Fine-tuning," but this is impractical for closed-source models (like GPT-4) and comes with extremely high costs.

The core value of this paper lies in creating a **"plug-and-play mistake log and secret manual"** for Agents. We don't need to alter the Agent's underlying reasoning logic (such as the standard ReAct loop). Instead, through an elegant **dual-module design of reflection and retrieval**, we distill long and hard-to-transfer "Raw Trajectories" into highly generalizable "Trigger-Action Guidelines."

{{< admonition tip "Core Concept: Experience Compression and Sublimation" >}}
Why does directly feeding past full conversations to an Agent as Few-shot Examples yield poor results?
Because raw trajectories contain too many task-specific trivial details and lack **"actionable abstract principles."** The value of ERL is acting as a "mentor," sublimating the specific event "Failed to send email to Sergei" into a universal rule: "Whenever you only have a name, you must check the contact list first." This is the essence of intelligence!
{{< /admonition >}}

## Problem Definition

### Pain Point Analysis: Why Can't Existing Agents "Learn Lessons"?

Before diving into the methodology of this paper, let's look at the current dilemmas in the field of LLM Agents. We know that modern general-purpose Agents (like ReAct Agents based on GPT-4) possess strong reasoning capabilities. However, when deployed in "new environments" containing domain-specific rules or unfamiliar tools, their performance often falls short.

The most fatal issue is: **they start "from scratch" every time they face a new task.**
They cannot learn from past interaction experiences, leading to the same mistakes (e.g., incorrect tool parameter input) being repeated over and over.

To solve this "amnesia," the academic community has proposed several solutions, but all have difficult-to-overcome flaws:

1.  **Fine-Tuning**: The most traditional approach, but it is extremely resource-intensive, cannot be applied to API-based closed-source models, and does not support dynamic "Continuous Learning."

2.  **Trajectory-based Learning (e.g., ExpeL or AutoGuide)**:

    *   **Unrealistic Assumptions**: These SOTA methods rely heavily on "repeated trial-and-error." They require the Agent to attempt the same task multiple times and compare "successful" vs. "failed" trajectories to extract experience. However, in real-world scenarios (e.g., sending emails for a boss, modifying a database), tasks are often irreversible; **we only get a "Single-attempt" chance.**
    *   **Scalability Issues**: Using ExpeL as an example, it "blindly stuffs" all extracted experiences into the prompt of every new task. As the experience pool grows, the Context Window quickly fills up, and irrelevant information begins to interfere with the Agent's judgment.
    *   **Execution Overhead**: AutoGuide goes to the other extreme by dynamically retrieving experiences at **every single turn** of the Agent's execution. This not only incurs massive API call costs but also causes unbearable system latency.

3.  **Raw Trajectory Few-shotting**: The most intuitive idea is to directly feed the full dialogue history of past failures to the Agent. However, experiments show this doesn't work because raw trajectories are too long and filled with task-specific details, making it hard for the Agent to extract "abstract principles" applicable to new tasks.

### 💡 The Solution: Core Insights of ERL

Understanding the pain points above makes it clear why ERL (Experiential Reflective Learning) is so powerful. The insight of this paper is: **We don't need a perfect "success-failure comparison"; we just need a system that can "self-critique."**

ERL breaks the limitation of trial-and-error by proposing a mechanism that extracts experience from **only a single attempt**. It compresses long raw trajectories into highly abstract "Heuristics" and stores them in a persistent experience pool. When facing a new task, it adopts a "pre-exam review" strategy—precisely retrieving the Top-\( k \) most relevant rules to inject into the context before the task begins, achieving **highly efficient execution with zero interference.**

## Methodology

The ERL framework is an elegant "plug-and-play design." It **does not require any changes to the Agent's underlying architecture** (e.g., it keeps the original ReAct loop). Instead, it completes the system's "self-evolution" through two independent stages.

{{< image src="solution.png" alt="Diagram of the ERL framework: on the left, heuristic generation executes tasks into trajectories with rewards, analyzes them into heuristics and stores them in a heuristics pool; on the right, at test time a new task queries and retrieves the top heuristics, which guide execution into a trajectory that is judged success or failure" caption="Overview of the ERL Framework: The left side shows the process of experience accumulation and Heuristic Generation, while the right side shows the Retrieval-Augmented Execution process for new tasks." >}}

The data flow can be clearly divided into two stages:

### Stage 1: Experience Accumulation and Reflection (Heuristic Generation)

Once the Agent completes a task in the environment (whether it succeeds or fails), this stage is triggered. Think of it as the Agent's "journaling and review" time after work.

#### Single-attempt Input
The system collects all information from the single execution just completed and packages it into a context for the LLM acting as the "Reflector":
*   **Task**: The original task description (e.g., "Please help me cancel tomorrow's wine tasting").
*   **Trajectory**: The complete execution trajectory (including reasoning, tools called, and environment feedback).
*   **Reward**: A binary feedback signal indicating if the task was a `Success` or `Failure`.

#### Post-Mortem Analysis and Rule Generation
This is the most brilliant part of ERL—the authors designed a strictly structured prompt that forces the LLM to follow different reflection logics based on "success" or "failure":

*   **IF FAILURE**: The LLM must first "Pinpoint the Breakpoint" to find where logic failed or a tool was misused. Then, it derives a specific corrective rule to prevent such errors.
*   **IF SUCCESS**: The LLM must identify the "Winning Move," analyzing which decision made execution efficient and sublimating it into a best practice.

#### The Power of Structured Output: Trigger -> Action
Regardless of success or failure, the "Heuristic" output by the LLM must follow a specific format. This includes an analysis and a **Learned Guideline**, which must be conditional:
*   **Trigger**: For example, "When I need to send an email and the input only contains participant names..."
*   **Action**: For example, "I must first call the Contacts tool to retrieve addresses and verify the format before calling the Emails tool."

Once generated, this rule is stored in a persistent "Heuristics Pool (denoted as \( \mathcal{P} \))".

{{< admonition tip "Key Analysis: Why is the Trigger -> Action design so ingenious?" >}}
In our discussion, we found that transforming experience into a `Trigger -> Action` format not only achieves "information compression" (saving massive amounts of tokens) but, more importantly, aligns perfectly with the Agent's **ReAct (Reasoning and Acting)** execution framework!

In the future, when the Agent encounters a situation matching the `Trigger` during the `Thought` phase, it’s like triggering muscle memory. It automatically recalls the `Action` SOP, cleverly avoiding traps and truly turning "cases" into "generalizable rules."
{{< /admonition >}}

### Stage 2: Retrieval-Augmented Execution

When the Agent faces a **completely new and unknown task**, the ERL system initiates the second stage, which we call "pre-exam review."

#### Task Decomposition and Intelligent LLM Retrieval
How do we pick the most suitable experience from a massive experience pool \( \mathcal{P} \)? The authors found in experiments that simply using Embeddings (semantic vectors) for literal similarity matching didn't work well. Therefore, ERL employs **LLM-based Retrieval**.

The data flow works as follows:
1.  **Task Decomposition**: The LLM Retriever first analyzes the new task and breaks it down into potential "sub-tasks" and "action steps" (an implicit Chain-of-Thought that helps more accurately match specific underlying experiences).
2.  **Multi-dimensional Scoring**: Next, the LLM scores rules in the experience pool from 0 to 100. Scoring is based not only on "Similarity" but also strictly includes "Diversity" (avoiding rules that all talk about the same tool) and "Informativeness" (whether the rule is specific and actionable).
3.  **Precise Extraction**: Finally, the LLM outputs the IDs and selection reasons for the Top-\( k \) rules (experiments prove \( k=20 \) works best).

#### Context Injection and Zero-Interference Execution
After selecting the Top-\( k \) heuristics, the system directly inserts them into the Agent's **System Prompt**.
Then, the Agent officially enters the environment and begins its standard ReAct execution loop.

This is a very clever architectural choice: because the "secret manual" is given to the Agent before the task starts, we don't need to consume computational resources to dynamically retrieve experiences at every step (turn), unlike AutoGuide. This perfectly achieves what we call **Zero-overhead during execution**.

{{< admonition tip "Key Analysis: The Cost of LLM Retrieval and Future Solutions" >}}
The current implementation uses **Full-Context Prompting**, meaning all experiences must be fed into the LLM for scoring during the retrieval phase.
This works when the pool has around a hundred rules (though it already consumes many tokens and relies on Prompt Caching), but if the pool expands to the tens of thousands, it will become a disaster of latency and cost. Future practical applications will inevitably need to move toward "Two-stage Retrieval": first using cheap and fast Embeddings or BM25 to filter for the Top-100, then letting the LLM perform fine-grained Reranking. This remains a significant optimization space left by this paper for the future.
{{< /admonition >}}

## Experimental Results

To verify ERL's real-world capabilities, the authors chose the **Gaia2** benchmark. This is a highly challenging environment containing 12 applications and 101 tools, where tasks usually require long-path reasoning.

{{< admonition tip "Why Gaia2?" >}}
Gaia2 is cleverly designed by splitting data into different "Universes." These universes share the same tools but have completely independent content (e.g., contacts in Universe A are totally different from Universe B). This allows us to precisely test whether the "operational logic (experience)" an Agent learns in Universe A can successfully migrate to Universe B across data barriers. This avoids the common "knowledge contamination" issue in LLM research.
{{< /admonition >}}

### Core Results: Significantly Outperforming SOTA Methods

ERL demonstrated strong competitiveness in Gaia2's "Search" and "Execution" tasks.

{{< image src="exp-1.png" alt="A bar chart and a table of success rates: ERL reaches the highest overall success rate of 56.1 percent, above baseline 48.3, few-shot 46.4, ExpeL 50.9 and AutoGuide 50.8, with the table also breaking down execution versus search splits and ablations" caption="Proof that ERL achieved an overall success rate of 56.1%, a 7.8% improvement over the ReAct baseline, and outperformed previous top experience learning methods like ExpeL (50.9%) and AutoGuide (50.8%)." >}}

**Why did ERL win?**
*   **Reliability**: As mentioned in our discussion, ERL not only increased the success rate but also significantly improved **\( pass^{3} \)** (meaning the task was completed successfully three times in a row). This indicates the Agent is no longer "getting lucky" but has truly mastered a stable operational SOP.
*   **Generalization**: Compared to feeding raw trajectories (Few-shot), the Heuristics provided by ERL filtered out unnecessary distractions, allowing the Agent to focus more on the underlying logic.

### Ablation Study: Necessity of Modules

Through a series of "decomposition" experiments, the authors proved that every part of ERL's design is essential.

#### Heuristics vs. Raw Trajectories
This might be the experiment we care about most. What if we just show the Agent past raw dialogues (Raw Trajectories)?

{{< image src="exp-2.png" alt="Two line charts of success rate versus feedback length in tokens for the execution and search splits, where the no-retrieval heuristics line (orange) stays consistently above the few-shot raw-trajectories line (gray) at every token budget" caption="This chart proves that under the same token budget, the success rate of Heuristics is consistently higher than that of Raw Trajectories. This shows that 'distilled knowledge' is more effective at guiding an Agent than 'stacked data'." >}}

#### Importance of Retrieval Quality
What if we don't use expensive LLMs for retrieval and just pick rules randomly?

{{< image src="exp-3.png" alt="Line chart of success rate versus number of heuristics that rises to a peak around 60 heuristics then declines toward 100, with a star marking ERL's LLM-selected top-20 heuristics achieving about 56 percent, higher than the curve at that point" caption="This chart proves that the 'quality' of rules is more important than the 'quantity.' Including too many random rules (over 60) actually leads to a drop in performance due to noise interference. ERL uses an LLM to precisely select the Top-20 rules, reaching the optimal balance." >}}

## Conclusion
This paper addresses the pain points of LLM Agents "lacking continuous learning capabilities" and "relying on repeated trial-and-error" by proposing the **ERL (Experiential Reflective Learning)** framework.

Through **self-reflection after a single execution**, experiences are transformed into structured **Trigger-Action rules**. During execution, **intelligent LLM retrieval** is used to inject the 20 most relevant rules into the context. Ultimately, it achieved performance and stability surpassing SOTA methods on the Gaia2 benchmark.

Despite ERL's excellent performance, we must point out its limitations:
*   **Scalability and Cost**: While the current retrieval mechanism (Full-context LLM ranking) is precise, its token cost and latency will become unacceptable when facing thousands of experiences. This will require optimization through "Two-stage Retrieval" in the future.
*   **Conflict Resolution**: If the experience pool contains two contradictory rules (e.g., conflicting rules from different universes), the system does not yet have a clear arbitration mechanism.
*   **Automated Maintenance**: As experiences accumulate, how to automatically clean up outdated or incorrect rules (Memory Consolidation) is also a direction worth exploring.

---
# weight: 1
title: "Coding Agents with Multimodal Browsing are Generalist Problem Solvers"
date: 2025-06-16
lastmod: 2025-06-16
draft: true
description: ""
featuredImage: "featured-image.jpg"

tags: []
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true
license: '<a rel="license external nofollow noopener noreffer" href="https://creativecommons.org/licenses/by-nc/4.0/" target="_blank">CC BY-NC 4.0</a>'

url: "paper-intro/:contentbasename"
---

<!--more-->

## Introduction

This article introduces the paper "[OctoTools: An Agentic Framework with Extensible Tools for Complex Reasoning](https://arxiv.org/abs/2502.11271)". The five authors of OctoTools are all from Stanford, and they published this paper on arXiv in February 2025.

OctoTools is a training-free and open-sourced agentic framework designed to enhance the task planning and tool usage capabilities of Large Language Models (LLMs), thereby improving their performance on multi-step tasks.

As of May 2025, the [GitHub repository for OctoTools](https://github.com/octotools/octotools) has already accumulated 1.2K stars, indicating its significant popularity. Additionally, Discover AI has produced an [introductory video on OctoTools](https://www.youtube.com/watch?v=4828sGfx7dk), which interested readers might find useful!

## The Problem OctoTools Aims to Solve

In recent years, various agentic framework methods have been proposed. Essentially, these frameworks enable LLMs to tackle more complex and flexible problems through iterative steps of planning and execution.

However, some agentic framework methods, like [Toolformer (NeurIPS 2023)](https://openreview.net/forum?id=Yacmpz84TH) and [LLaVA-Plus](https://arxiv.org/abs/2311.05437), require training the LLMs. Others, such as [Visual Sketchpad (NeurIPS 2024)](https://openreview.net/forum?id=GNSMl1P5VR&referrer=%5Bthe%20profile%20of%20Weijia%20Shi%5D(%2Fprofile%3Fid%3D~Weijia_Shi1)) and [WebWISE (NAACL 2024)](https://aclanthology.org/2024.findings-naacl.234/), are limited to specific domains. While training-free methods applicable to general domains do exist (e.g., [Chameleon (NeurIPS 2023)](https://openreview.net/forum?id=HtqnVSCj3q¬eId=AkDivMFFzq), [HuggingGPT (NeurIPS 2023)](https://openreview.net/forum?id=yHdTscY6Ci)), their performance on multi-step tasks has often been less than ideal.

Therefore, OctoTools aims to introduce a training-free agentic framework applicable to general domains that also delivers better performance on multi-step tasks.

{{< admonition tip "Related Papers" >}}
If you're new to the field of LLM Agents, be sure to first read our previous introduction to a classic LLM Agent paper—[HuggingGPT](../hugginggpt/)—to understand how LLMs handle multi-step tasks through planning and execution frameworks.

If you have more time, you can also read our introductions to [PLAN-AND-ACT](../plan-and-act/) and [Pre-Act](../pre-act/). These two papers, like OctoTools discussed here, were published in the first half of 2025. However, they focus more on the planning-execution framework and their methods are simpler than OctoTools, making them good preparatory reading!
{{< /admonition >}}

## Introducing the OctoTools Method

{{< image src="approach-min.png" caption="[Figure 1] OctoTools Framework" >}}

The OctoTools method, as shown in Figure 1 above, is primarily composed of **Tool Cards**, a **Planner**, and an **Executor**.

Tool Cards define many tools and the metadata for each tool. Based on a user's query, OctoTools follows these steps:

1. The **Query Analyzer** analyzes which tools are suitable for the current query and formulates a high-level plan. This high-level plan becomes the first element in the trajectory.
2. The **Action Predictor**, based on the current trajectory, generates a more specific low-level plan, which is the next action. This includes the goal of the action, the tool to be used, and the parameters to be passed.
3. The **Command Generator** converts the text-described action into concrete Python code.
4. The **Command Executor** runs this Python code to get the execution result.
5. This complete step—{Action, Python Code, Execution Result}—is stored in the overall trajectory.
6. The **Context Verifier**, based on the entire trajectory, determines whether the final answer has been obtained, signaling "CONTINUE" or "STOP".
    - "CONTINUE": Return to step 2. The Action Predictor can now generate a new low-level action based on the updated trajectory.
    - "STOP": Proceed to step 7.
7. The **Solution Summarizer** generates the final answer based on the entire trajectory.

{{< image src="example-min.png" caption="[Figure 3] OctoTools Example" >}}

### Tool Cards

As shown in Figure 3 above, Tool Cards in OctoTools generally include Name, Description, Input, Output, Demonstrations, and a distinctive "User Metadata" field. "User Metadata" mainly provides additional hints from the user about the tool (e.g., limitations of the tool, best practices for using the tool), allowing the Planner and Executor to better understand the tool.

Each tool implements two standard functions:

- `execute()`: Executes the tool based on the passed parameters.
- `get_metadata()`: Retrieves the tool's metadata (allowing the Planner and Executor to understand tool information in real-time).

Readers interested in the actual content of Tool Cards can refer to Appendix D in the paper:

{{< image src="tools-min.png" caption="Tools defined in OctoTools" >}}

### Planner

The Planner is actually composed of four LLMs: **Query Analyzer**, **Action Predictor**, **Context Verifier**, and **Solution Summarizer**.

As shown in Figure 3, based on the user's query and the tool set, the Query Analyzer's goal is to generate a high-level plan. This plan includes "Summary," "Required Skills," "Relevant Tools," and "Additional Considerations." This high-level plan helps guide the overall reasoning process in the right direction.

The Action Predictor then generates a specific low-level action based on the high-level plan. This includes the "Sub-Goal" (the objective of this action), "Tool Name," and "Context" (information to be passed to the tool).

After the Executor returns the execution result, the Context Verifier determines whether the reasoning process should continue, based on the user's query, the initial high-level plan, and the current trajectory. If it decides to continue, it returns to the Action Predictor, which then generates a new low-level action based on the current trajectory (which now includes the high-level plan as well as the previously executed action and its result).

If the Context Verifier decides to stop, the complete trajectory is passed to the Solution Summarizer to generate the final answer.

The specific prompts for these four LLMs can be found in Appendix C of the paper:

{{< image src="prompt.png" caption="Prompt Template" >}}

### Executor

The Executor is quite straightforward, consisting of one LLM: **Command Generator (Predictor)**.

As shown in Figure 3, the task of the Command Generator is to convert the action generated by the Action Predictor into more concrete Python code. This Python code is then passed to a Python Executor to be run, yielding a result.

The prompt for the Command Generator (Predictor) can also be found in Appendix C of the paper.

### Task-specific Toolset Optimization

Suppose there are already many tools in the current Tool Set. In each stage of the Planner, we don't want to put all tool information into the LLM's context, as some tools might be completely unsuitable for the current task and would instead become irrelevant information in the context. Therefore, if a type of task has some validation tasks, we can perform the following steps using these validation tasks to create an Optimized Tool Set:

1. Establish a Base Tool Set by selecting some essential tools.
2. Let the Planner and Executor process validation tasks using this Base Tool Set to get a Base Score.
3. Randomly select a tool from the remaining tools.
4. Create a New Tool Set = Base Tool Set + New Selected Tool.
5. Let the Planner and Executor process validation tasks using this New Tool Set to get a New Score.
6. If this New Score is greater than the Base Score, it indicates that this New Selected Tool is suitable for this type of task.
7. Repeat Steps 3 to 6 until every tool has been tested.
8. Create an Optimized Tool Set = Base Tool Set + all tools suitable for this type of task.

## OctoTools Experimental Results

{{< image src="exp-1-min.png" caption="Experiment 1" >}}

As shown in the table above, the authors used 18 benchmarks in their experiments, covering Text and Image modalities across 5 domains. The green checkmarks indicate the skills required by each benchmark, from left to right: Visual Understanding, Numerical Calculation, Knowledge Retrieval, and Multi-Step Reasoning. OctoTools<sub>base</sub> represents using only the Base Tool Set, while OctoTools uses the Optimized Tool Set.

The table shows that the OctoTools method, whether using the Base or Optimized Tool Set, outperforms baseline methods. This suggests that agentic framework methods are better suited for handling complex tasks.

{{< image src="exp-2-min.png" caption="Experiment 2" >}}

The table above presents a comparison of OctoTools with other agentic framework methods. Although OctoTools also shows better performance than other methods, the authors did not clearly specify what kind of agentic workflows were created using the other agentic frameworks for comparison.

## Conclusion

This article introduced the paper "[OctoTools: An Agentic Framework with Extensible Tools for Complex Reasoning](https://arxiv.org/abs/2502.11271)". OctoTools is a training-free and open-sourced agentic framework that enhances the task planning and tool usage capabilities of LLMs through a carefully designed interplay between Tool Cards, the Planner, and the Executor. Experimental results also demonstrate that OctoTools performs better than other agentic frameworks (e.g., AutoGen, GPT-Functions, LangChain).

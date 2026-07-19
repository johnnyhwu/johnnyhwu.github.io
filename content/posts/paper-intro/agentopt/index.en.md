---
# weight: 1
title: "AgentOpt: How to Optimize Client-Side LLM Agents and Cut API Costs by 67%"
date: 2026-04-17
lastmod: 2026-04-17
draft: false
description: "Optimize your LLM agents with AgentOpt. Discover how this open-source, client-side framework uses MAB to find the best model combo and cut API costs by 67%."
featuredImage: "featured-image.jpg"

tags: ["Large Language Model", "Inference Optimization"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## Introduction

The paper "[AgentOpt v0.1 Technical Report: Client-Side Optimization for LLM-Based Agent](https://arxiv.org/abs/2604.06296v1)" represents a significant shift in the field of AI optimization. In the past, academia and industry feverishly pursued **"server-side"** efficiency (e.g., how to make inference engines more memory-efficient and achieve higher throughput). However, this paper takes a different path, focusing on the control and optimization space we possess as developers on the **"client-side."**

- [Project Website](https://agentoptimizer.github.io/agentopt/)
- [GitHub Repository](https://github.com/AgentOptimizer/agentopt)

### TL;DR

When an AI Agent consists of multiple roles (such as planner, executor, critic), **"how to combine models"** has a far greater impact on final performance and budget than the strength of any single model.

`AgentOpt` is the first open-source Python framework designed specifically for "client-side Agents." It does not require you to rewrite your existing code. Instead, through a clever combination of "Multi-Armed Bandit (MAB) algorithms" and "HTTP interception," it helps us find the gold combination with the "best price-to-performance ratio" within a vast model combination space (such as \( 9^N \) combinations) using a minimal testing budget (saving up to 67%).

### Core Architecture Overview

It illustrates how `AgentOpt` treats the Agent workflow as a black box and uses an iterative loop to search for the Pareto frontier.

{{< image src="arch.png" alt="Two-part AgentOpt diagram: part (a) frames model combination as assigning one candidate model to each of N pipeline roles (Planner, Solver, Critic) to form a combo, and part (b) shows the iterative search loop of select, execute, measure and update that outputs a Pareto frontier and the best combo" caption="Presents the overall design of AgentOpt. Figure (a) shows the composition relationship between N roles and candidate models, emphasizing that the choice at each step affects downstream states (not per-call routing); Figure (b) depicts the iterative search loop: selecting a combo, executing interception, measuring metrics, and updating the policy." >}}

## Problem Definition

Before diving into the technical details of AgentOpt, we must first clearly understand the current situation faced by AI Agent developers. There is a gap in the current optimization landscape.

### The Gap between Server-Side and Client-Side Optimization

Past research (such as vLLM, SGLang, Autellix) has heavily focused on the **server-side**.
*   **Server-side logic**: Pursues the ultimate limit of the Inference Engine, such as reducing costs through Request Scheduling, Speculative Execution, or KV Cache. This optimizes the infrastructure.
*   **Client-side pain points (our perspective)**: As Agent Builders, we face the problem of "how to allocate our available resources." We need to decide on model combinations, when to use local tools, and how to distribute the API budget across different steps.

### Why "Traditional Routing" is Helpless in the Face of Agents
The paper clarifies a key point: Agent optimization is **by no means** traditional LLM Routing.
1.  An Agent's execution is a sequence of multi-step trajectories. The output of the model in the previous step completely changes the state faced by the model in the next step.
2.  The model with the strongest individual capability might "overthink" and skip critical steps when placed in the overall workflow, causing the entire process to fail. This means **we cannot infer a model's performance within an Agent workflow based solely on single-model leaderboards**.

### Combinatorial Explosion
Assuming an Agent has \( N \) roles, and each role has \( M \) candidate models. This is a combinatorial explosion problem:
*   **Mathematical scale**: The search space size is \( |C| = \prod_{i=1}^{N} |M_i| \).
*   **Budget killer**: If we need to run 200 test queries across all combinations, just one benchmark test could easily cost hundreds of dollars.
*   **Intuition fails**: The paper's experiments prove that even the strongest large language models cannot "guess" the strongest combination through intuition alone.

## Methodology

The design philosophy of AgentOpt is very straightforward: since we cannot predict the performance of a combination, we build an **"fully automated, highly cost-effective, non-intrusive"** black-box testbed.

### Pillar 1: Defining the Agent as a "Black-Box Optimization"
We treat the entire Agent process as a non-differentiable black box.

#### Core Abstraction: Combo
We define a model combination \( c = (m_1, m_2, \dots, m_N) \) as an atomic unit. Given a query, this Combo generates an **End-to-end Trajectory** \( \tau(c) \).

#### Utility Function
We aim to maximize \( J(c) \). This is a multi-objective optimization trade-off:
$$ J(c) = \text{PERF}(\tau(c)) - \lambda_c \text{COST}(\tau(c)) - \lambda_\ell \text{LATENCY}(\tau(c)) $$
*   **Weight parameters \( \lambda \)**: This embodies "personalized optimization." A healthcare AI developer might set \( \lambda \) to 0 (pursuing accuracy at all costs), while a real-time customer service developer would set \( \lambda_\ell \) very high (prioritizing speed).

### Pillar 2: Engineering Magic of the Execution Engine
To make it "painless" for developers, AgentOpt implements an elegant interception mechanism.

#### HTTP Transport Layer Interception (Framework-Agnostic Interception)
This is the most brilliant engineering detail in the paper:
*   **Why choose `httpx`?** Because it is the common underlying connection library for modern AI frameworks (OpenAI, Anthropic SDKs).
*   **Monkey Patching**: AgentOpt intercepts `httpx.Client.send` at the lowest level. This means you do not need to modify any LangChain, AutoGen, or custom code. The system automatically performs a swap-out the moment the API call is made.

```python {title="Simplified HTTP-layer interception"}
import contextvars
import httpx
from agentopt.proxy import LLMTracker

tracker = LLMTracker(cache=True)

_current_data_id = contextvars.ContextVar("data_id", default=None)
_current_combo_id = contextvars.ContextVar("combo_id", default=None)

_original_send = httpx.Client.send
_original_async_send = httpx.AsyncClient.send

def patched_send(self, request, *args, **kwargs):
    data_id = _current_data_id.get()
    combo_id = _current_combo_id.get()
    
    with tracker.track(data_id=data_id, combo_id=combo_id):
        return _original_send(self, request, *args, **kwargs)
    
async def patched_async_send(self, request, *args, **kwargs):
    data_id = _current_data_id.get()
    combo_id = _current_combo_id.get()
    
    with tracker.track(data_id=data_id, combo_id=combo_id):
        return await _original_async_send(self, request, *args, **kwargs)

httpx.Client.send = patched_send
httpx.AsyncClient.send = patched_async_send
```

In parallel testing, hundreds of API requests fly simultaneously.
*   **The clever use of `contextvars`**: Ensures that every token cost captured by the interceptor can be precisely mapped to the correct `combo_id` and `data_id`, avoiding any mismatch or wrong attribution.

#### Latency-Preserving Cache
*   **The necessity of caching**: If the Planner for Combo A and Combo B is the same, the API cost for that Planner can be saved.
*   **The most ingenious detail**: Traditional caching would reduce the measured latency to 0. However, AgentOpt's cache **forces the retention of the actual latency from the first time the request was sent**. This ensures that our data remains completely fair when comparing the latency performance of different combinations.

### Pillar 3: Selection Policy

This solves the pain point of "not having enough budget to test all combinations." AgentOpt introduces **Multi-Armed Bandit (MAB)** theory.

#### MAB Analogy
We view the 81 Combos as 81 slot machines.
*   **Pulling the lever once**: Tests one query on that Combo.
*   **Reward**: The resulting utility score.
*   **Core dilemma**: We must find a balance between "exploration (testing combinations we haven't tried yet)" and "exploitation (allocating the budget to the strongest combination)."

#### Three MAB Algorithm Details
1.  **Arm Elimination — [The Default King]**:
    *   **Logic**: A knockout tournament. In each round, the confidence interval \( [L_j, U_j] \) of each combination is calculated.
    *   **Elimination criterion**: If a challenger's "best potential \( U_j \)" is less than the defender's "baseline capability \( L^\star \)", it is immediately eliminated.
    *   **Advantages**: Highly robust, saving 24% - 67% of costs while almost never missing the optimal combination.
2.  **Epsilon-LUCB — [Extreme Cost Saving]**:
    *   **Logic**: Only pits the "first place" against the "strongest challenger."
    *   **Features**: Budget is heavily concentrated. In paper experiments, it saved up to **96%** of costs, but the risk is selecting a sub-optimal solution due to the small sample size.
3.  **Threshold SE — [Commercial Practice]**:
    *   **Logic**: A qualifying exam.
    *   **Features**: Once it is determined whether a combination "passes" or "fails," the process stops. This is highly suitable for finding combinations that "just meet the threshold but are the cheapest."

#### Other Failed Baselines
*   **Hill Climbing**: Easily gets stuck in local optima. Because Agent roles are highly coupled, a role change that degrades performance on its own doesn't mean a combination of two role changes won't be highly effective.
*   **Bayesian Optimization (BO)**: Assumes a smooth landscape. However, an Agent's performance landscape is full of sharp cliffs, causing BO's surrogate models to make inaccurate predictions.
*   **LM Proposal**: The intuition of large models performs like an amateur when faced with complex system interactions (achieving only 34% accuracy).

## Experimental Results

### Experimental Scenarios
*   **HotpotQA (Multi-Hop Retrieval)**: Tests collaboration in planning and searching.
*   **GPQA Diamond (High-Difficulty Science)**: Tests the limits of reasoning.
*   **MathQA (Mathematical Reasoning)**: Tests the Answerer-Critic loop retry mechanism.
*   **BFCL v3 (Function Calling)**: Tests the precision of tool usage.

### Core Finding 1: The Opus Paradox and Capability Misconceptions

{{< image src="table3.png" alt="Table of the bottom-ranked planner and solver model combinations on HotpotQA (ranks 71 to 81) with their accuracy, average latency and cost, most stuck around 32 percent accuracy" caption="This table displays the bottom 11 combinations for HotpotQA" >}}

You can see that the "planners" ranked 71st to 79th are all the strongest model, Claude Opus 4.6. This proves that in multi-hop workflows, a model being too powerful (or overconfident) can cause it to skip necessary tool calls, leading to systemic failure.

In the HotpotQA task, the strongest combination is **(Ministral 3 8B + Opus 4.6)**. Let the "weak model" handle the planning, because it knows its limitations and will obediently generate search keywords; then let the "strong model" handle the final integration. This "weak leader, strong follower" configuration achieved more than double the accuracy of the "strong-strong alliance" (74.27% vs 31.71%).

### Core Finding 2: The 32x Cost Gap

{{< image src="table9.png" alt="Table ranking 9 models on BFCL v3 by accuracy with their average latency, average calls and cost, led by Claude Opus 4.6, Kimi K2.5 and Qwen3 Next 80B at 70 percent accuracy" caption="BFCL v3 brute force results (200 samples, 9 models)" >}}

This result proves that Qwen3 Next 80B and Claude Opus 4.6 are completely on par in function calling accuracy (both at 70%). However, Qwen3 costs only $1.90, while Opus costs $60.13. There is a terrifying 32x price difference between the two.

### Algorithm Matchup: Why Arm Elimination Wins

Comparing 8 algorithms, the results show that **Arm Elimination (AE)** is the true all-rounder.

{{< image src="table6.png" alt="Table comparing selector algorithms on HotpotQA by mean accuracy, mean evaluations, mean cost and cost savings versus brute force, showing Matrix UCB-E matching brute-force accuracy at over 55 percent cost savings" caption="HotpotQA selector comparison (199 samples, 81 combinations)." >}}

This HotpotQA algorithm comparison table proves that AE (Arm Elimination) used only 4,283 evaluations to find a combination with 73.19% accuracy. Compared to the 16,168 evaluations of brute force search, it saved 76.3% of the testing cost with almost no loss in accuracy.

*   **AE vs. BO (Bayesian Optimization)**: In MathQA, AE's accuracy significantly outperformed BO. This is because the performance landscape of an Agent is not a smooth hill as assumed by BO, but is filled with cliffs. AE's "assumption-free, data-driven only" elimination mechanism is better suited for fragmented landscapes than BO, which attempts to predict patterns.
*   **AE vs. Epsilon-LUCB**: Although LUCB saved up to **96%** of the budget in some tasks (extreme cost-saving), its accuracy tended to drop by 2-4%.

## Conclusion

### Summary and Core Contributions

This paper completes a missing piece of the puzzle in Agent optimization: **Client-Side resource allocation**.

1.  **Problem Definition**: Defines model selection as a "black-box optimization problem in a discrete space," breaking the myth of single-model rankings.
2.  **Methodology**: Introduces the `AgentOpt` framework. It utilizes **HTTP transport layer interception** for framework-agnostic, painless monitoring, and **Multi-Armed Bandit** for highly sample-efficient model combination searches.
3.  **Empirical Findings**: Proves that "combination" is the soul of an Agent, revealing highly practical insights such as a 32x cost reduction and the "weak planner, strong executor" paradigm.

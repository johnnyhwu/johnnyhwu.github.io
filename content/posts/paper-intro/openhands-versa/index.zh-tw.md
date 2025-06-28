---
# weight: 1
title: "[論文介紹] Coding Agents with Multimodal Browsing are Generalist Problem Solvers"
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

url: "paper-intro/:contentbasename"
---

<!--more-->

## 前言

本篇文章介紹 [Coding Agents with Multimodal Browsing are Generalist Problem Solvers](https://arxiv.org/abs/2506.03011) 論文，此論文由 Carnegie Mellon University, Independent 與 All Hands AI 於 2025 年 6 月發表至 arXiv。

本篇論文提出：**一個 Agent 如果具備 Coding, Multimodal Web Browsing 以及 Information Access 三種能力，那麼它將會是一個 General Agent (能夠處理多種領域的任務，而非侷限於單一領域)**。

{{< image src="openhands-versa.png" caption="OpenHands-Versa vs OpenHands" >}}

如上圖所示，本篇論文所提出的方法稱為 **OpenHands-Versa** 是一個 General (Versatile) Agent。在核心方法上主要是基於 OpenHands 這個專注於 Software Development 的 Specialist Agent 提供不同的 Tool。 OpenHands-Versa 本身也是一個開源專案，有興趣的讀者可以再研究其 [Codebase](https://github.com/adityasoni9998/OpenHands-Versa)。

## OpenHands-Versa 想解決的問題

簡單來說，OpenHands-Versa 想解決的問題為：
> 如何設計一個能夠處理不同領域任務的 General Agent?

近幾年有許多 Agent 的方法被提出，然而這些 Agent 都只有在特定的 Benchmark 或是任務上有好的表現，而無法泛化到其他領域的任務。舉例來說，[Agentless](https://arxiv.org/abs/2407.01489) 和 [SWE-Agent](https://arxiv.org/abs/2405.15793) 在 [SWE-Bench](https://www.swebench.com/) 上都達到了 State-of-the-Art 的表現，然而它們卻都無法從 Web 上取得資訊，也無法透過 Web-Based Chat 與其他 Agent 溝通，導致這兩個方法在 GAIA 以及 The Agent Company 兩個 Benchmark 上的表現較差。相反的，擅長 Web Navigation 的 Agent (EX. [AgentSymbiotic](https://arxiv.org/abs/2502.07942), [AgentOccam](https://arxiv.org/abs/2410.13825), [Agent Workflow Memory](https://arxiv.org/abs/2409.07429)) 卻不會寫 Code 或是執行 Code。

## OpenHands-Versa 方法介紹

{{< image src="approach-min.png" caption="[Figure 1] OctoTools 框架" >}}

OctoTools 方法如上圖 Figure 1 所示，主要由 **Tool Cards**, **Planner** 與 **Executor** 組成。

在 Tool Cards 中會定義很多 Tool，以及每一個 Tool 的 Metadata。基於使用者的 Query，OctoTools 會經過以下步驟:

1. Query Analyzer 分析哪些 Tool 適合現在的 Query，並且制定 High-Level Plan。這個 High-Level Plan 會用來當作 Trajectory 中的第一個元素
2. Action Predictor 基於目前的 Trajectory 產生更具體的 Low-Level Plan，也就是下一個 Action，包含這個 Action 的目標是什麼，要使用什麼 Tool，以及要傳入什麼參數
3. Command Generator 將由文字描述的 Action 轉為具體的 Python Code
4. Command Executor 執行這段 Python Code 得到 Execution Result
5. 將 {Action, Python Code, Execution Result} 這一個完整的 Step 存入整個 Trajectory
6. 由 Context Verifier 基於整個 Trjectory 判斷是不是已經得到最終答案，給出 "CONTINUE" 或是 "STOP" 的信號
    - "CONTINUE": 回到第 2 步驟，此時 Action Predictor 已經可以根據新的 Trajectory 產生新的 Low-Level Action
    - "STOP": 進入到第 7 步驟
7. 由 Solution Summarizer 基於整個 Trajectory 產生最終的答案

{{< image src="example-min.png" caption="[Figure 3] OctoTools 範例" >}}

### Tool Cards

在 OctoTools 中的 Tool Cards 如上圖 Figure 3 所示，基本上有 Name, Description, Input, Output, Demonstrations 以及比較特的 "User Metadata"。 "User Metadata" 主要是 User 對這個 Tool 提供更多提示 (EX. 這個 Tool 有什麼限制, 這個 Tool 的 Best Practice 是什麼)，讓 Planner 以及 Executor 更了解這個 Tool。

每個 Tool 都有實做兩個標準函式：

- `execute()`: 基於傳入的參數執行 Tool
- `get_metadata()`: 取得 Tool 的 Metadata (讓 Planner 與 Executor 可以即時了解 Tool 的資訊)

想進一步閱讀實際 Tool Cards 內容的讀者，可以參考論文中的 Appendix D:

{{< image src="tools-min.png" caption="OctoTools 中所定義的 Tools" >}}

### Planner

Planner 實際上是由 4 個 LLM 所組成：**Query Analyzer**, **Action Predictor**, **Context Verifier** 以及 **Solution Summarizer**。

如上圖 Figure 3 所示，基於使用者的 Qeury 以及 Tool Set，Query Analyzer 的目標是產生一個 High-Level 的 Plan，包含 "Summary", "Required Skills", "Relevant Tools" 以及 "Additional Consideration"。 這個 High-Level Plan 是為了幫助整個 Reasoning 過程的大方向正確。

而 Action Predictor 則會根據 High-Level Plan 產生具體的 Low-Level Action，包含 "Sub-Goal" (這個 Action 的目標), "Tool Name" 以及 "Context" (要傳入到 Tool 的資訊)。

當 Executor 回傳執行結果後，Context Verifier 則會判斷根據使用者的 Query, 一開始的 High-Level Plan 以及目前的 Trajetory 來決定 Reasoning 過程是否要繼續。如果決定繼續，則會回到 Action Predictor 上，再根據目前的 Trajectory (除了有 High-Level Plan 也有前一次執行的 Action 以及 Result)，產生新的 Low-Level Action。

如果 Context Verifier 決定結束，則會將完整的 Trajectory 交給 Solution Summairzer 產生最後的回答。

上述 4 個 LLM 的具體 Prompt，可以再參考論文中的 Appendix C:

{{< image src="prompt.png" caption="Prompt Template" >}}

### Executor

Executor 相當單純的由 1 個 LLM 組成：**Command Generator (Predictor)**。

如上圖 Figure 3 所示，Command Generator 的任務就是將 Action Predictor 產生 Action 轉為更具體的 Python Code。這個 Python Code 就會再交給 Python Executor 執行並得到結果。

Command Generator (Predictor) 的 Prompt 也可以在論文中的 Appendix C 查閱。

### Task-specific Toolset Optimization

假設目前 Tool Set 中已經有很多 Tool 了，在 Planner 的每個階段中，我們不希望把所有 Tool 的資訊都放到 LLM 的 Context 中，因為有些 Tool 可能根本完全不適用在目前的 Task 上，反而變成 Context 中的 Irrelevant Information。因此，假設一種 Task 有一些 Validation Task，那我們就可以透過 Validation Task 進行以下步驟，來建立一個 Optimized Tool Set：

1. 建立一個 Base Tool Set，也就是先挑選出一些必要的 Tool
2. 讓 Planner 以及 Executor 基於這個 Base Tool Set 來處理 Validation Task 得到一個 Base Score
3. 從剩下的 Tool 中隨機挑選一個 Tool
4. 建立一個 New Tool Set = Base Tool Set + New Selected Tool
5. 讓 Planner 以及 Executor 基於這個 New Tool Set 來處理 Validation Task 得到一個 New Score
6. 假設這個 New Score 大於 Base Score，則表示這個 New Selected Tool 是適合這種 Task 的
7. 重複 Step 3 ~ Step 6，直到測試過每一種 Tool
8. 建立一個 Optimized Tool Set = Base Tool Set + 所有適合這種 Task 的 Tool

## OctoTools 實驗結果

{{< image src="exp-1-min.png" caption="Experiment 1" >}}

如上表所示，在實驗中作者使用 18 種 Benchmark，包含 Text 以及 Image Modality，橫跨 5 個 Domain。綠色勾勾的部份代表這個 Benchmark 所需要的技能，由左至右分是：Visual Understadning, Numerical Calculation, Knowledge Retrieval 以及 Multi-Step Reasoning。OctoTools<sub>base</sub> 代表只有使用 Base Tool Set，OctoTools 則是使用 Optimized Tool Set。

由上表可以發現到 OctoTools 方法在使用 Base 或 Optimized Tool Set 的情況下，都表現的比 Baseline 方法更好。說明 Agentic Framework 方法更適合處理負責的任務。

{{< image src="exp-2-min.png" caption="Experiment 2" >}}

上表呈現的是將 OctoTools 與其他 Agentic Framework 方法比較。雖然可以發現 OctoTools 確實也比其他方法有更好的表現，但是作者並沒有交待清楚透過其他的 Agentic Framwork 是建立出什麼樣的 Agentic Workflow 來互相比較的。

## 結語

本篇文章介紹 [OctoTools: An Agentic Framework with Extensible Tools for Complex Reasoning](https://arxiv.org/abs/2502.11271) 論文。OctoTools 是一個 Training-Free 且 Open-Sourced 的 Agentic Framework，透過 Tool Cards, Planner 以及 Executor 之間精細設計，來提昇 LLM 的 Task Planning 與 Tool Usage 能力。透過實驗結果也可以看到 OctoTools 比其他的 Agentic Framework (EX. AutoGen, GPT-Functions, LangChain) 有更好的表現。

---
# weight: 1
title: "[論文介紹] Pre-Act: Multi-Step Planning and Reasoning Improves Acting in LLM Agents"
date: 2025-05-20
lastmod: 2025-05-20
draft: false
description: "本篇文章介紹 Pre-Act 論文，說明 PreAct 如何透過讓 LLM 在每一個 Reasoning Step 中產生與修改 Plan，來彌補傳統 Single Agent 方法 'ReAct' 的不足，進而提昇 LLM 在長期規劃任務上的表現。"
featuredImage: "featured-image.jpg"

tags: ["Large Language Model", "Single-Agent"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## 前言

本篇文章介紹 [Pre-Act: Multi-Step Planning and Reasoning Improves Acting in LLM Agents](https://www.arxiv.org/abs/2505.09970) 論文，由 [Uniphore](https://www.uniphore.com/) 公司於 2025 年 5 月發表於 arXiv。

## Pre-Act 想解決的問題

在 [ReAct](https://arxiv.org/abs/2210.03629) 方法中，LLM 的 (Single-Step) Reasoning (Thinking) 都只是針對下一個 Action，而不是針對未來一系列的 Action，這樣的 Reasoning 方式導致 ReAct 在需要 Long-Term Planning 的任務上表現不好。

## Pre-Act 提出的解決方法

讓 LLM 每一次的 Thinking 都可以產生一個詳細的 Plan。這個 Plan 主要包含，"過去已經執行的步驟" 與 "接下來要執行的步驟"。

舉例來說，基於一個 Input Task，Pre-Act 在第一次 Thinking 時，會產生一個包含 N 個步驟的 Plan，每一個步驟都會敘述要進行什麼 Action (其實就是使用什麼 Tool)，然後最後一個步驟就是使用 "Final Answer" Tool 來輸出最終答案。在每次 Thinking 結束後，Pre-Act 會輸出一個 Action (透過 JSON 表示)，系統會執行這個 Action 並將 Observation 放回到 Context 中。

接著，Pre-Act 在進行第二次 Thinking 時，會根據 Context 中的內容 (前一次的 Plan, Action 與 Observation)，重新產生一個 Plan。新的 Plan 中會描述過去幾次的 Thinking 與 Action 已經完成了什麼，並根據此修改接下來要完成的步驟。

{{< image src="example.png" caption="ReAct vs Pre-Act." >}}

如上圖的範例，可以清楚看到 ReAct 的每一次 Thinking 就是僅僅針對接下來馬上要採取的 Action，而 Pre-Act 的每一次 Thinking 都會有一個 Global Plan 的描述。

{{< admonition info 補充說明 >}}
為了提昇 LLM 在 Long-Term Planning 任務上的表現，**"產生 Plan"** 以及 **"修改 Plan"** 的技巧相當常見，在 [Plan-and-Act (2025/03)](../plan-and-act/) 論文中也是使用了相同的概念；只不過在 [Plan-and-Act (2025/03)](../plan-and-act/) 中是透過 Multi-Agent (Planner x Executor) 的架構，而在本篇論文 Pre-Act 中是透過 Single-Agent 的方式。
{{< /admonition >}}

Pre-Act 透過以下 (論文提供的) System Prompt 的設計幫助 LLM 做到上述的 Reasoning 流程：（但老實說我覺得 System Prompt 寫的相當凌亂）
``````text
<system> You are an intelligent assistant and your task is to respond to the human as helpfully and
accurately as possible. You would be provided with a conversation (along with some steps if present)
and you need to provide your response as Final Answer or use the following tools (if required):
Instructions:
------------------------------------------------------------------------------------------
{instructions}
Functions/Tools:
------------------------------------------------------------------------------------------
{tools}
===============
Use a json blob to specify a tool by providing an action key (tool name) and an action_input key
(tool input).
Valid "action" values: "Final Answer" or {tool_names}
In case of final answer:
Next Steps (Plan):
1. I will now proceed with the final answer because ... (explanation)
Follow this format (flow):
Question: input question to answer
Thought: consider previous and subsequent steps and conversation. Summary for what you did previously (ONLY IF
function calls were made for the last user request) and create the multi-step plan.
Action:
```
$JSON_BLOB
```
Observation: action result
... (repeat Thought/Action/Observation N times)
Thought: First provide the summary of previous steps (ONLY IF function calls were made for the last user request)
and then the plan consisting of only 1 step i.e. proceed with the final answer because ... explanation for it
Action:```
{
"action": "Final Answer",
"action_input": "Final response to human”
}
Definition of Multi-Step Plan:
For each request you will create a multi-step plan consisting of actions that needs to be taken until the final
answer along with the reasoning for the immediate action.
E.g.
Next Steps (Plan):
1. I will first do ... (action1) with the detailed reasoning.
2. I will do ... (action2) with the detailed reasoning.
k. I will do ... (actionk) with the detailed reasoning.
k+1. I will now proceed with the final answer because ... (explanation)
Example Output: When responding to human, please output a response only in one of two formats
(strictly follow it):
**Option 1:**
If function calls were made for the last human message in the conversation request, include Previous Steps: ... +
Next Steps: multi-step plan (provide an explanation or detailed reasoning)." Otherwise, provide Previous Steps:
NA and Next Steps: ..
Action:
```
{
"action": "string, \ The action to take. Must be one of {tool_names}",
"action_input": dict of parameters of the tool predicted
}
```
**Option #2:**
In case of you know the final answer or feel you need to respond to the user for clarification,
etc. Output = Thought: If function calls were made for the last human message in the conversation
request, include Previous Steps: ... + Next Steps: Let's proceed with the final answer because ...
(provide an explanation)." Otherwise, provide Previous Steps: NA and Next Steps: ..
Action:
```
{
"action": "Final Answer",
"action_input": "string \ You should put what you want to return to use here"
}
```
Begin! Reminder to ALWAYS respond with a valid json blob of a single action. Use tools if necessary
and parameters values for the tool should be deduced from the conversation directly or indirectly.
Respond directly if appropriate. Format is Thought:\nAction:```$JSON_BLOB```then Observation <user>
Conversation:
{conversation}
``````

在 Pre-Act 論文中也有針對 Llama-3.1-8B 與 Llama-3.1-70B 進行 Finetune，訓練模型輸出 Pre-Act 風格的 Thinking 方式。有興趣的讀者可以再閱讀原始論文，這邊就不贅述！ 

## Pre-Act 實驗結果

{{< image src="exp.png" caption="Pre-Act 實驗結果" >}}

上述實驗結果來自論文中的 Table 2，是 Pre-Act 的主要實驗。上表中的前 5 列代表未經過 Finetune 模型 ("van" 表示 "vanilla")，只有透過不同 System Prompt 來比較 ReAct 與 PreAct 的表現。而最後 2 列則是有經過 Finetune 模型的表現 ("f.t." 表示 "finetune")。

從兩種實驗設定下可以觀察到：

- 模型只有透過修改 System Prompt 來達到 Pre-Act-Based 的 Reasoning 表現也比 ReAct-Based 勝過許多
- 模型若特別 Finetune 在 Pre-Act-Based 的 Reasoning 方式，表現又可以比僅修改 System Prompt 的方法好上更多

## 結語

本篇文章非常快速的介紹了 [Pre-Act: Multi-Step Planning and Reasoning Improves Acting in LLM Agents](https://www.arxiv.org/abs/2505.09970) 論文：

Pre-Act 中透過每一個 Reasoning Step 來產生以及修改 Plan，來優化傳統的 [ReAct-Based Reasoning](https://arxiv.org/abs/2210.03629) 中僅針對馬上要執行的下一個 Action 的 Single-Step Thinking 的不足，讓 LLM 在 Long-Term Planning 的任務上有更好的表現。

比較可惜的是，論文中比較的 Baseline 僅有針對 ReAct 一種方法，所使用的 Public Benchmark 也僅有一種。然而，由於 ReAct 也可以算是 LLM Agent 領域的始祖等級的論文，後續也還有許多方法被提出，再加上 Benchmark 較少，比較難說明 Pre-Act 方法能夠多有效。但透過本篇論文，我們還是得以知道 "產生 Plan" 以及 "修改 Plan" 在 LLM 處理任務上所帶來的好處！

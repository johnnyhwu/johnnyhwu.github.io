---
# weight: 1
title: "[論文介紹] PLAN-AND-ACT: Improving Planning of Agents for Long-Horizon Tasks"
date: 2025-05-09
lastmod: 2025-05-09
draft: true
description: ""
featuredImage: "featured-image.png"

tags: ["Large Language Model", "Multi-Agent"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## 前言

本篇文章介紹 [PLAN-AND-ACT: Improving Planning of Agents for Long-Horizon Tasks](https://arxiv.org/abs/2503.09572) 論文，PLAN-AND-ACT 主要由 UC Berkeley 於 2025 年 3 月發表於 Arxiv。

PLAN-AND-ACT 主要是提出一個框架來提昇 LLM 的規劃 (Planning) 能力。如下圖所示，PLAN-AND-ACT 主要由 Planner 與 Executor 組成。由 Planner 根據使用者給的任務先產生「計畫」，所謂的「計畫」其實就是一連串較為高層次的目標，再由 Executor 根據這個計畫轉為環境中特定的行為。

{{< image src="plan-and-act.png" caption="[Figure 1] An illustration of PLAN-AND-ACT System Diagram." >}}

## PLAN-AND-ACT 想解決的問題

PLAN-AND-ACT 想處理的問題正式 LLM 的規劃 (Planning) 能力。現有的 LLM 在 Planning 上具有以下挑戰：

1. LLM 通常難以將使用者所提供的 High-Level 目標轉為具體的 Plan（例如：「幫我訂一張飛往紐約的機票」）分解為具體且可執行的步驟（例如：「打開航空公司網站」、「輸入旅行日期」等）
2. 即使 LLM 可以產生 Plan，但隨著任務變得更長且更複雜，Plan 中的步驟也會變多，導致 LLM 無法追蹤已經完成的步驟以及尚未完成的部分
3. 即使 LLM 可以追蹤一個很長的 Plan，但現實生活中的環境通常是動態、隨機且不可預測的，LLM 很可能無法在一開始制定好 Plan，就按照這個 Plan 走到最後，而是必須動態的根據環境給的回饋來修改 Plan
4. 回到 LLM 本質能力，由於缺乏 Planning 相關的高品質訓練數據，LLM 本身就不是被訓練成一個 Planner

## PLAN-AND-ACT 提出的解決方法

為了解決上述關於 LLM Planning 的 4 個問題，PLAN-AND-ACT 提出 2 個解法：

- 針對 **問題(1)-(3)** 提出 PLAN-AND-ACT 這個框架，將 Planner 以及 Executor 分離，由 Planner 產生 Plan，由 Executor 負責執行 Plan
- 針對 **問題(4)** 提出一種在不管是否有 Groundtruth 下，都可以產生與 Planning 相關的 Synthetic Data 的 Pipeline，就能夠透過這些 Synthetic Data 訓練 Planner

### PLAN-AND-ACT 框架

{{< image src="plan-and-act-workflow.png" caption="[Figure 2] PLAN-AND-ACT System Diagram." >}}



## PLAN-AND-ACT 實驗結果

## 結語

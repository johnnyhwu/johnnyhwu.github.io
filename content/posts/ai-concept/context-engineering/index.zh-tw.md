---
# weight: 1
title: "賦予 AI 長效記憶：深入解析 AI Agent 的核心技術「上下文工程 (Context Engineering)」"
date: 2026-03-22
lastmod: 2026-03-22
draft: false
description: "深入了解 AI Agent 的核心技術「上下文工程 (Context Engineering)」。本文解析如何透過記憶體架構、上下文壓縮與 Sub-Agent 機制，解決 LLM 的長線任務挑戰並有效優化 Token 成本。"
featuredImage: "featured-image.jpg"

tags: ["Large Language Model", "Retrieval-Augmented Generation", "Single-Agent", "Multi-Agent", "Agent Memory"]
categories: ["ai-concept"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "ai-concept/:contentbasename"
---

<!--more-->

## 前言

在 AI Agent 的研發領域，我們正經歷一場範式轉移。大語言模型 (LLM) 雖強，但其「無狀態 (Stateless) 」的本質與有限的 Context Window，使其在處理現實世界長線任務時舉步維艱。**Context Engineering** 便是為了解決這項挑戰而生的核心技術。本文為 Hung-Yi Lee 老師發布的 [Context Engineering 介紹影片](https://www.youtube.com/watch?v=urwDLyNa9FU) 的筆記。

## TL;DR
*   **Context Engineering 的數學本質**：將上下文更新從「無腦串接」進化為由處理函數 \( F \) 驅動的狀態轉換： \( C_{t+1} \leftarrow F(C_t, I_t, O_t) \)。
*   **壓縮的雙面刃**：暴力抹除 (Observation Masking) 能顯著降低成本，但會引發「軌跡延長 (重複執行) 」與「上下文崩塌」。
*   **記憶體 vs. 硬碟**：確立 \( C = \{P, M\} \) 架構，讓 LLM 只處理 Prompt (工作記憶) ，而將大量歷史儲存於 Memory (硬碟) 。
*   **Sub-Agent 作為濾波器**：透過「摺疊 (Folding) 」機制，將複雜的執行過程轉化為鋸齒狀的 Context 長度變化。
*   **自主進化路徑**：從人類定義規則，進化到由 AI 自主維護操作手冊 (Playbook) 與自動編寫檢索程式碼。

## 核心概念：AI Agent 是 LLM 的「守門員」

LLM 是「活在當下」的機器。為了讓它具備處理連續任務的能力，我們必須在每一輪互動中，將過去的歷史重新「餵」給模型。

*   **技術挑戰**：直接串接歷史會導致 Context 隨時間呈線性爆炸。
*   **Agent 的真面目**：在 Context Engineering 視角下，Agent 是一個**攔截器**。它決定模型「下一秒該看到什麼」。有效的 Context Engineering 必須確保輸入內容 **「不能太長」** (避免成本激增與注意力失焦) ，也 **「不能太短」** (避免遺失關鍵任務限制) 。

## 上下文壓縮：效能與精確度的權衡

當 Context 過長時，最直覺的作法是壓縮。影片中提到了以下做法：

### 暴力抹除 (Observation Masking)

*   **方法論**：對於冗長的工具輸出 (Tool Output) ，直接以 `[詳見 log1.txt]` 取代。
*   **研究發現 ([Observation Masking](https://arxiv.org/abs/2508.21433))**：在 **SWE-bench** 軟體工程任務中，這種「Hard Clear」的表現驚人地與昂貴的 LLM 摘要 (Summarization) 持平。
*   **代價分析**：當記憶被抹除，模型常會出現 **「軌跡延長 (Trajectory Elongation) 」** 現象。例如：模型忘記已檢查過某檔案，導致重複呼叫相同 API。

### 上下文崩塌 (Context Collapse) 與 ACON 方法

*   **問題描述**：普通摘要常會濾除掉「系統限制」 (如：刪除前必須詢問人類) 。
*   **[ACON 方法](https://arxiv.org/abs/2510.00615)**：引入 **Reflector LLM**。系統不微調權重，而是讓 Reflector 比較「成功軌跡」與「失敗摘要」，自動生成 **Feedback (壓縮指南)**。在 AppWorld 測試中，加入 Feedback 的摘要正確率大幅回升，甚至在峰值 Token 極低的情況下超越了未壓縮的模型。

### [SUPO](https://arxiv.org/abs/2510.06727)：無標準答案的強化學習
*   **核心困局**：沒人知道「完美的摘要」長怎樣，故無法進行 SFT。
*   **解決方案**：模型先生產摘要，直到任務結束後，根據「任務成敗」發放獎勵。這讓「摘要大腦」與「執行大腦」達成**聯合優化**。

## 記憶架構的重定義：Context = Prompt + Memory

我們必須將 Context 分為兩個子集：

1.  **Prompt (\(P\))**：真正進入 LLM 運算核心的資訊 (工作記憶) ，受 Context Window 限制。
2.  **Memory (\(M\))**：存在外部系統 (硬碟) 的資訊，容量理論上無限。

**Context Engineering 的目標**：管理 \(P\) 與 \(M\) 之間的動態平衡。
*   **[A-MEM](https://arxiv.org/abs/2502.12110)** 與 **[Mem0](https://datasciocean.com/paper-intro/mem0/)** 提供了記憶層 (Memory Layer) 的具體實作。
*   **[Memory OS](https://arxiv.org/abs/2506.06326)**：提出了像作業系統管理分頁檔 (Page File) 一樣管理 LLM 上下文的願景。

## 結構化壓縮：Sub-Agent 與鋸齒狀曲線

影片中強調，呼叫 Sub-Agent 的能力並非 LLM 天生具備，而是需要後天訓練。

*   **[AgentFold](https://arxiv.org/abs/2510.24699)**：透過強化學習訓練 `spawn` (繁衍) 與 `return` (回傳) 動作。
*   **隔離與合併邏輯**：
    *   **隔離**：主 Agent 在呼叫 Sub-Agent 時，只傳遞核心指令 (Context 量瞬間驟降) 。
    *   **合併 (摺疊)**：Sub-Agent 在執行過程產生的幾千行過程會被銷毀，僅回傳一兩行結果給主 Agent。
*   **視覺化影響**：這使得 Agent 的 Context 長度曲線呈現 **「鋸齒狀 (Sawtooth) 」** —— 緩慢增長後因任務結束而大幅下降，克服了 Context 爆炸的物理屏障。

## 過濾與按需加載：主動尋求能力

為了避免 \(P\) (Prompt) 被無關資訊塞滿，過濾機制至關重要：
1.  **兩段式讀取**：使用 `memory_search` (找位置) 搭配 `memory_get` (拿特定行數)，避免無腦 `Read` 全檔案。
2.  **[MCP-Zero](https://arxiv.org/abs/2506.01056)**：取代傳統 RAG。讓 AI 先「描述」它現在需要的工具，系統才動態加載對應的 API 定義。這解決了工具過多 (Tool Bloat) 導致模型失焦的問題。

## 終極階段：Agentic Context Engineering (ACE)

最高階的 Context Engineering 是讓 AI 決定自己的 Context。
*   **[Dynamic Cheatsheet](https://datasciocean.com/paper-intro/dynamic-cheatsheet/)**：模型在任務中會自主維護一份「小抄」，紀錄哪些策略無效、哪些 Code 可重複使用。
*   **[ACE](https://datasciocean.com/paper-intro/agentic-context-engineering/)**：採用 Generator (草稿) 、Reflector (審核) 、Curator (發布) 三角色系統，確保 AI 修正自身 System Prompt 時不會發生致命誤刪。
*   **[Recursive Language Models](https://arxiv.org/abs/2512.24601)**：模型在運作時只攜帶 Meta-data，遇到問題時會 **「寫一段 Python 程式碼」** 去檢索存在硬碟裡的歷史 Token。

## 未來方向

1.  **AI 的「囤積症」抗拒**：[研究](https://arxiv.org/abs/2509.23586)證明 LLM 天生討厭刪除記憶。因此，強大的 Agent 框架 (如 OpenClaw) 必須具備**系統級強制攔截 (Memory Flush)** 的機制，不能全權交由模型決定。
2.  **從筆記到本能**：Context Engineering 的未來不僅是壓縮，而是「經驗的沉澱」。成功的 Agent 應該在多次任務後，將 Context 轉化為一套高效的 Playbook。
3.  **待解決問題**：當記憶被轉存為指標 (Pointer) 後，如何在不大幅增加延遲的前提下，確保模型能精準「喚回」所需的細節，仍是優化效能的關鍵戰場。

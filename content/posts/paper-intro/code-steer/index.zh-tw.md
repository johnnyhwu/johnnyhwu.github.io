---
# weight: 1
title: "[論文介紹] Steering Large Language Models Between Code Execution and Textual Reasoning"
date: 2025-05-20
lastmod: 2025-05-20
draft: true
description: ""
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

本篇文章介紹 [Steering Large Language Models Between Code Execution and Textual Reasoning](https://openreview.net/forum?id=5X5Z7Ffrjb) 論文，由 MIT, Harvard, Microsoft, Google DeepMind 於 2024 年 10 月發表於 arXiv，並且被 ICLR 2025 會議所收錄！不管是作者們的來歷亦或是收錄的會議，都感覺這篇論文非常的高品質呀！

## 本篇論文想解決的問題

如同論文的名稱所示，本篇論文想解決/探討的問題是：

> 對於一個 Large Langugae Model 而言，究竟是以 Code Execution 方式進行 Reasoning 比較好，還是以 Textual Output 的方式來 Reasoning 比較好呢？

針對一些 NLP 任務，像是生成摘要或是對話等等，以 Textual Output 進行 Reasoning 明顯會比較自然比較好，但是在一些數學或是邏輯推理任務上，Code Execution 的 Reasoning 方式往往可以更有效率的方式得到正確答案。

{{< image src="code-exec-is-better.png" caption="Code Execution Reasoning is better." >}}

舉例來說，如上圖呈現的兩個任務："9.11 和 9.9 誰比較大" 與 "'strawberry' 中有多少 'r' 以及每一個的位置"，這兩個任務明顯相當簡單，但是對於 GPT-4o 而言如果以 Textual Output 進行 Reasoning 會得到錯誤的答案，而透過 Code Execution 很輕易的答對。

{{< image src="code-exec-is-better-2.png" caption="Code Execution Reasoning is better." >}}

如上圖所示，又或者是進行兩個數字的乘法運算時，"2_3" 代表 2 位數數字乘以 3 位數數字，可以發現隨著位數增加，即使是 OpenAI O1 類型的模型，透過更多的 Textual Output 來進行 Reasoning，也沒有辦法回答正確。

很明顯的，對於 LLM 而言，無法用一種思考方式來解決天底下所有任務，有時候適合透過 Textual Output 有時候則適合利用 Code Execution 進行 Reasoning。因此本篇論文提到的另外一個問題：

> 如何引導 LLM 在適合的任務上使用正確的 Reasoning 方式 (Textual Output vs Code Execution) 呢？

本篇論文的重點除了回答上述兩個問題之外，也分析 6 種 LLM (O1-preview, GPT-4o, GPT-4o-mini, GPT-3.5, Claude-sonnet, Mixtral-8x7b) 在多種任務上，使用 Textual Output 以及 Code Execution 進行 Reasoning 所帶來的差異。

## OpenAI GPT-4o: Code Execution vs Textual Output

OpenAI GPT-4o 預設是以 Textual Output 進行 Reasoning，但是必要時 GPT-4o 仍然可以透過 Code Interpreter Tool 以 Code Execution 進行 Reasoning。作者以 GPT-4o, GPT-4o-mini 與 GPT-3.5-turbo 三個模型為例，分析這三個模型在處理 Number Multiplying (計算兩個數字相乘的結果) 與 Game 24 (給定一些數字，從中挑選並輸出可以得到 24 的算式) 兩種不同任務時，會選擇 Code Execution 或是 Textual Output 的方式進行 Reasoning。

從這個實驗中發現到：

{{< admonition tip Insight >}}
較大的模型 (GPT-4o) 在一些難度中間 (不難也不簡單) 的任務上，傾向透過 Textual Output 進行 Reasoning，而導致在這些問題上得到錯誤的答案；相反的，較小的模型 (GPT-3.5-turbo) 則是在所有難度的任務上，都傾向透過 Code Execution 進行 Reasoning，使得正確率較高。
{{< /admonition >}}

{{< image src="gpt-4o-fail.png" caption="GPT-4o 犯錯的範例" >}}

如上圖所示，GPT-4o 在簡單的 2 位數字的乘法**很有自信**的透過 Textual Output 進行 Reasoning 得到正確的答案；在第二個非常困難的多位數的數字乘法中，GPT-4o 知道要使用 Code Execution 進行 Reasoning。然而，在第三個例子中，面對難度中等的 4 位數字的乘法，GPT-4o **仍然很有自信**的透過 Textual Output 進行 Reasoning 而得到**錯誤**的答案。

{{< image src="gpt-4o-exp-1.png" caption="[Figure 3] 不同模型在 Number Multiplying 的表現" >}}

{{< image src="gpt-4o-exp-2.png" caption="[Figure 4] 不同模型在 Game 24 的表現" >}}

上方兩張圖片分別對應到論文中的 Figure 3 與 Figure 4，從量化分析的實驗結果，可以明顯觀察到 GPT-4o 在簡單的任務上傾向透過 Textual Output Reasoning，而在明顯困難的任務上則會透過 Code Execution Reasoning，但是在難度中等的任務上，仍然選擇 Textual Output Reasoning 而導致錯誤比例上升。在 GPT-3.5-turbo，則是不管任務的簡單到困難，一律都以 Code Execution Reasoning 進行。

由於 Number Multiplying 與 Game 24 剛好是適合透過 Code Execution Reasoning 的任務，使得小模型 (GPT-3.5-turbo) 的表現反而勝過大模型 (GPT-4o)。

如果我們直接在 Prompt 中告訴模型要透過 Code Execution Reasoning，那會不會大家的表現都一樣好了？作者一樣進行了這個實驗，但是卻發現：

{{< admonition tip Insight >}}
在 Prompt 中要求模型一定要透過 Code 來 Reasoning 不能保證結果一定是好的，模型可能會產生沒有效率**如同 Textual Output 的 Code**，使得最後得到的答案仍然是錯誤的。
{{< /admonition >}}

{{< image src="text-like-code.png" caption="GPT-4o 產生如同 Textual Output 的 Code" >}}

如上圖所示，即使要求 GPT-4o 透過 Code Execution 進行 Reasoning，GPT-4o 可能打從心裡很有自信的覺得這個任務透過 Textual Output 進行 Reasoning 就可以解決，使得寫出來的 Code 仍然如同 Textual Output 一般，使得最後的結果仍然錯誤。


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

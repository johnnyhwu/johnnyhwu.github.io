---
# weight: 1
title: "[論文介紹] Augmenting LLM Reasoning with Dynamic Notes Writing for Complex QA"
date: 2025-06-28
lastmod: 2025-06-28
draft: false
description: "本篇文章介紹 Augmenting LLM Reasoning with Dynamic Notes Writing for Complex QA 論文。NotesWriting 的目標在於減少 Multi-Hop RAG 中，由於進行多次的 Retrieval，使得過多不相關資訊進入到 LLM Context 中，而使得 LLM 表現變差的問題。NotesWriting 針對每個 Retrieved Document 進行 Notes Extract，再將所有 Extract 出來的 Note 進行 Aggregation，得到最終少量且重要的資訊，來提昇 LLM Context 的品質進而提昇 LLM 的表現。"
featuredImage: "featured-image.jpg"

tags: ["Large Language Model", "Retrieval-Augmented Generation", "Single-Agent"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## 前言

本篇文章介紹 [NotesWriting: Augmenting LLM Reasoning with Dynamic Notes Writing for Complex QA](https://arxiv.org/abs/2505.16293)，此篇論文由 [ServiceNow](https://www.servicenow.com/) 公司於 2025 年 5 月發表於 arXiv 上。

{{< admonition warning >}}
本篇論文並沒有提出太新穎的方法，而只是一個很小且常見的技巧：透過 LLM 來將所有 Retrieved Document 進行過濾並整合成一個最終相關的資訊，來解決 Multi-Hop RAG 方法中，因為太多次的 Retrieval 造成 LLM Context Size 不夠或是包含太多不相關資訊的問題。
{{< /admonition >}}

## NotesWriting 想處理的問題

在 Multi-Hop RAG 中，LLM 需要透過多次的 Retrieval 與 Reasoning 穿插進行，才有辦法得到最終答案。舉例來說，LLM 如果想回答 "上一次台灣舉辦國際棒球比賽時有多少人參加？"，LLM 需要先收集 "上一次在台灣舉辦的國際棒球比賽是什麼？" 的相關資料，得到答案之後，才有辦法再進一步收集 "該場比賽有多少人參加？" 的相關資料。

然而，在回答每一個 Sub-Question 時，LLM 可能會 Retrieve 到非常多相關資料，如果把這些相關資料都放入 LLM 的 Context 中，很有可能會導致 LLM 的 Context 超過其限制，或是因為資料中夾雜的不相關資訊，而導致 LLM 在後續的 Reasoning Step 的表現變差。

因此，本篇論文想處理的問題，其實就是 RAG 領域的頭號問題：**如何從 Retrieved Document 萃取出重要的資訊，避免提供過多不重要的或是不相關的資訊到 LLM 的 Input Context 中？** (而本篇論文又特別強調 Multi-Hop RAG 方法中，每一個 Step 可能都會 Retrieve 新的資料，使得這個問題更嚴重)

## NotesWriting 的解決方案

{{< image src="notes-writing.png" alt="NotesWriting 方法回答海拔範圍問題的逐步軌跡：每一步 agent 產生思維鏈與搜尋查詢，另一個 Notes LLM 讀取排名靠前的維基頁面並回傳精簡筆記加入上下文，經過兩輪檢索後 agent 以答案 1,800 到 7,000 英尺作結" caption="[Figure 1] NotesWriting 方法" >}}

如上圖所示，NotesWriting 方法非常簡單，在 LLM-Based Agent 的每一個 Reasoning Step 中，如果使用了 Search/Retrieval Tool 取得 Top-K 個 Document，會透過 LLM 針對每個 Document 進行 Note Extraction，取出與目前的 Question 最相關的資訊。最後，再透過 Note Aggregation 將所有取出的資訊整合在一起。

Note Extraction 的 Prompt 如下所示：
```text
Extract relevant information which is not previously extracted from the Wikipedia page provided in markdown format relevant to the given query. You will be provided with the Wikipedia page, query, and the previously extracted content.
Do not miss any information. Do not add irrelevant information or anything outside of the provided sources.
Provide the answer in the format: <YES/NO>#<Relevant context>.
Here are the rules:
    • If you don’t know how to answer the query - start your answer with NO#
    • If the text is not related to the query - start your answer with NO#
    • If the content is already extracted - start your answer with NO#
    • If you can extract relevant information - start your answer with YES#
Example answers:
    • YES#Western philosophy originated in Ancient Greece in the 6th century BCE with the pre-Socratics.
    • NO#No relevant context.
Context: {Context}
Previous Context: {PrevContext}
Query: {Query}
```

## NotesWriting 的實驗結果

在實驗階段，作者將 NotesWriting 方法套用到 3 種 Multi-Hop RAG 常見的 Baseline，[ReAct](https://arxiv.org/abs/2210.03629), [IRCoT](https://arxiv.org/abs/2212.10509) 以及 [FLARE](https://arxiv.org/abs/2305.06983)，實驗結果分別如下表 Table 1, 2, 3 所示。

{{< image src="exp-1.png" alt="表格比較 ReAct 與 ReAct 加上 NotesWriting (ReNAct)，涵蓋 GPT-4o-mini 與 LLaMA-3.1-70B 在 Fanout-QA、Frames、Hotpot-QA 與 MultiHop-RAG 的表現，加入 NotesWriting 後 F1 與 GPT-4 分數提升，並藉由將長內容移至筆記而降低主上下文的輸入 token" caption="[Table 1] NotesWriting + ReAct" >}}

{{< image src="exp-2.png" alt="表格比較 IRCoT 與 IRCoT 加上 NotesWriting，涵蓋 GPT-4o-mini 與 LLaMA-3.1-70B 在 FanoutQA、Frames、HotpotQA 與 M-RAG 的表現，NotesWriting 版本在每一列都取得更高的 F1 與 GPT-4 分數" caption="[Table 2] NotesWriting + IRCoT" >}}

{{< image src="exp-3.png" alt="表格比較 FLARE 與 FLARE 加上 NotesWriting，涵蓋 GPT-4o-mini 與 LLaMA-3.1-70B 在 Fanout-QA、Frames、HotpotQA 與 M-RAG 的表現，加入 NotesWriting 後各基準的 F1 與 GPT-4 分數皆有提升" caption="[Table 3] NotesWriting + FLARE" >}}

雖然 NotesWriting 本身是一個非常直觀且簡單的方法，但是透過上面這些實驗結果也可以再次發現到，在 RAG 方法中做 **Retrieved Document Refinement** 是相當重要且效果顯著的方法。

{{< admonition info 補充資訊 >}}
如果你覺得讀完 NotesWriting 感到很空虛，不妨閱讀 RAG 中針對 **Retrieved Document Refinement** 的經典論文 [Corrective Retrieval Augmented Generation](https://arxiv.org/abs/2401.15884)，相信一定可以有許多新的收穫！
{{< /admonition >}}

## 結語

本篇文章介紹 [NotesWriting: Augmenting LLM Reasoning with Dynamic Notes Writing for Complex QA](https://arxiv.org/abs/2505.16293) 論文。NotesWriting 的目標在於減少 Multi-Hop RAG 中，由於進行多次的 Retrieval，使得過多不相關資訊進入到 LLM Context 中，而使得 LLM 表現變差的問題。NotesWriting 針對每個 Retrieved Document 進行 Notes Extract，再將所有 Extract 出來的 Note 進行 Aggregation，得到最終少量且重要的資訊，來提昇 LLM Context 的品質進而提昇 LLM 的表現。

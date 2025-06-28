---
# weight: 1
title: "[論文介紹] AutoMind: Adaptive Knowledgeable Agent for Automated Data Science"
date: 2025-06-27
lastmod: 2025-06-27
draft: true
description: ""
featuredImage: "featured-image.png"

tags: ["Large Language Model"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## 前言

本篇文章介紹 [AutoMind: Adaptive Knowledgeable Agent for Automated Data Science](https://arxiv.org/abs/2506.10974) 論文，AutoMind 由 Zhejiang University 與 Ant Group 的研究人員於 2025 年 6 月被發布到 arXiv 上。

AutoMind 論文的目標在於提出一個 LLM-Based Agentic Framework 來處理 Data Science Challenge (e.g. Kaggle Competition)。

{{< image src="automind.png" caption="AutoMind 方法" >}}

如上圖所示，AutoMind 框架中包含 3 個核心方法：

- Expert Knowledge Base for Data Science: 就是針對 Data Science Task 所建立的知識庫
- Agentic Knowledge Tree Search Algorithm: ???
- Self-Adaptive Coding Strategy: ???

## AutoMind 想解決的問題

如同上文所述，AutoMind 的目標在於提出一個 LLM-Based Agentic Framework 來處理 Data Science Task (可以想像 AutoMind 就是一個 Data Science Agent)。作者認為過去的方法 (e.g. [AIDE](https://arxiv.org/abs/2502.13138), [Data Interpreter](https://arxiv.org/abs/2402.18679), [AutoML-Agent](https://arxiv.org/abs/2410.02958)) 具有以下兩個缺失，導致這些 Data Science Agent 的表現不夠好：

1. **LLM 在 Data Science Task 的知識不足**: 雖然 LLM 已經被預訓練在大量的 Code-Based Corpus 上，但是在處理 Data Science Task 時所使用的方法(程式碼)大多是人類專家透過反覆的實驗所得到的，LLM 在這部份的知識其實是不夠的
2. **LLM 生成程式碼的過程缺乏彈性**: 過去方法使用缺乏彈性的策略來讓 LLM 生成程式碼，導致 LLM 僅能夠針對一些比較簡單或是經典的任務來生成程式碼

可以很明顯的觀察到，AutoMind 中的第一個 (Expert Knowledge Base for Data Science) 與第二個 (Agentic Knowledge Tree Search Algorithm) 方法，對應到第一個問題，而第三個方法 (Self-Adaptive Coding Strategy) 對應到第二個問題。

## AutoMind: Expert Knowledge Base

為了讓 LLM 能夠理解 Data Science Task 所需的知識，AutoMind 建立了一個 Knowledge Base，裡頭主要有兩種類型的知識：

- **Kaggle Competition Solution**: 作者從此[網站](https://farid.one/kaggle-solutions/)中篩選出 455 個 Kaggle Competition，並且收集了 3237 篇 Post，每篇 Post 其實就是 Competition 的 Solution

- **Top Conference Paper**: 作者收集了 ICLR, NeurIPS, KDD, ICML, EMNLP 等頂尖會議最近三年的 Paper

建立了 Knowledge Base 後，接著就是要處理 Retrieval 的問題。最直覺的方法，就是透過比較 Task Description 與 Knowledge Base 中 Approach Description 的 Embedding，來進行 Dense Retrieval，但是這樣的作法明顯效果會很差，因為 Task 與 Approach 之間有時候不會有很強的相關性，導致沒辦法取出有幫助的知識。

{{< admonition tip 補充資訊 >}}
實際上，這確實也是 Multi-Hop RAG 領域經常遇到的挑戰：針對一個問題，中間需要經過多個步驟的推理（先回答幾個 Intermediate Question）才有辦法得到真正要回答的核心問題，也才有辦法基於這個核心問題，透過 Dense Retrieval 從 Knowledge Base 中取出相關的資料。如果對於 Multi-Hop RAG 初次認識，不妨閱讀 [Demonstrate-Search-Predict](https://arxiv.org/abs/2212.14024) 這篇經典論文！
{{< /admonition >}}

在 AutoMind 中，針對 Knowledge Retieval 的方法有些暴力，作者會透過 LLM 事先將每個 **Kaggle Competition Solution** 標上標籤。具體流程是，作者定義了 11 種 Top-Level 的主類別，每種主類別底下又有自己的子類別。讓 LLM 先分辨目前這個 Solution 屬於哪些主類別，再提供相對應的子類別讓 LLM 判斷。作者也透過 [Self-Consistency](https://arxiv.org/abs/2203.11171) 的方法，確保標籤的選擇是穩定的。

針對 **Top Conference Paper**，由於 Paper 的內容比 Competition Solution 更為彈性，要給予明確的標籤並不容易，因此作者直接透過 LLM 針對每一篇 Paper 產生 Summary，這個 Summary 包含：Data, Task, Approach 以及 Contribution 等資訊。

實際在 Retrieval 時，AutoMind 一樣會透過 LLM 對 Input Task 進行標籤的分類，然後再針對每個標籤下的 Solution 進行 Retrieval。然而，作者在論文中沒有很清楚的交待清楚實做上是 Dense, Sparse 還是 Hybrid Retrieval。

## AutoMind: Agentic Knowledgeable Tree Search

### Node Definition

如 Figure 1 所示，在 AutoMind 中，透過一個 Tree 來組織 Agent 在 **Solution Space 中的探索**。Tree 中的每個節點稱為 Solution Node，每個 Node 都包含以下資訊：

- **Plan**: 一段文字描述解決目前 Data Science Task 的計畫 (Sequential Stage)，Plan 中包含 Data Preprocessing, Feature Engineering, Model Training, Model Validation
- **Code**: 一段 Python Code 來實做 Plan
- **Metric**: 從 Code Execution Reuslt 中取出的 Validation Score
- **Output**: Code Execution 輸出在 Terminal 中的 Output
- **Summary**: 由 LLM-Based Verifier 針對 Plan, Code, Metric 以及 Output 給予這個 Node 的一個 Summary，同時也判斷這個 Node 是 "Valid Node" 還是 "Buggy Node"

### Search Policy

基於一個 Tree，要如何在這個 Tree 上做搜索，主要由 Search Policy 來決定。Search Policy 的輸入是目前整個 Tree 的狀態，而輸出是一個 Tuple 包含: 選定的 Node 以及要進行的 Action。

在 AutoMind 中，Search Policy 是透過一連串的 Rule-Based 的機率判斷來決定輸出，過程中沒有 LLM 的介入。如下方 Algorithm 所示：

{{< image src="search-policy.png" caption="Search Policy" >}}
{{< image src="image.png" caption="Search Policy" >}}

### Action Type

針對每個 Node 可以進行的 Action 以下 3 種，每種 Action 都是讓 LLM 基於不同的輸入來輸出新的 Plan：

- **Drafting**: 輸入 Task Description 以及從 Knolwedge Base 中取出的相關 **Paper**，輸出一個 Initial Plan
- **Improving**: 輸入 Tree 中隨機挑選出來的 Valid Node (Plan, Code, Output) 以及從 Knolwedge Base 中取出的相關 **Solution**，輸出一個改善過後的 Plan
- **Debugging**: 輸入 Tree 中隨機挑選出來的 Buggy Node (Plan, Code, Output) ，輸出一個 Debug 過後的 Plan

不管是哪一種 Action 被執行，一旦新的 Plan 被產生出來後，就會基於 Plan 進行 Code 的生成，並且執行 Code 得到 Execution Result。最後將 (Plan, Code, Metric, Output, Summary) 組成為一個新的 Node 存放回 Tree 中。
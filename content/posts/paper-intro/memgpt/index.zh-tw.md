---
# weight: 1
title: "[論文介紹] MemGPT: Towards LLMs as Operating Systems"
date: 2025-05-13
lastmod: 2025-05-13
draft: true
description: ""
featuredImage: "featured-image.png"

tags: ["Large Language Model", "Agent Memory"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## 前言

本篇文章介紹 [MemGPT: Towards LLMs as Operating Systems](https://arxiv.org/pdf/2310.08560) 論文，MemGPT 由 UC Berkeley 的研究人員於 2023 年 10 月被發布到 arXiv 上，截至 2025 年 5 月 14 日已經累積了 154 次 Citation，目前被收錄在 [CoRR 2023](https://openreview.net/forum?id=0Kk142lP62)。

談到 LLM 的 Perceptual Conversation 或是 Long-Term Memory，MemGPT 也算是一篇經典之作，目前 MemGPT 所開源的專案稱為 [Letta](https://github.com/letta-ai/letta)，與其說是一個專案我覺得它倒是更像一間[新創公司](https://www.letta.com/)。

此外，截至 2025 年 5 月 14 日，Letta 目前在 GitHub 上已經累積了 16.4K 個 Star，代表它確實是一個相當熱門的專案。當我們在網路上搜尋 Agent Memory 相關的開源專案時候，除了 [Mem0](https://github.com/mem0ai/mem0) 之外，[Letta](https://github.com/letta-ai/letta) 也是一個受歡迎的選擇，甚至大大超越由 LangChain 所開源的 [LangMem](https://github.com/langchain-ai/langmem)。

{{< admonition info >}}
身為 AI 領域的工程師或研究者，如果你還不了解 Mem0 以及 LangMem 的概念，務必閱讀以下兩篇文章：
- [LangMem 概念介紹](../../other/langmem-intro/)
- [Mem0 概念介紹](../mem0/)
{{< /admonition >}}

本篇文章為 DeepLearning.AI 上 [LLMs as Operating Systems: Agent Memory](https://www.deeplearning.ai/short-courses/llms-as-operating-systems-agent-memory/) 的課程筆記，主要著重於介紹 MemGPT 的方法本身，而不會提及實驗結果等細節，有興趣的讀者再請自行閱讀[原論文](https://arxiv.org/pdf/2310.08560)！

## MemGPT 想解決的問題

{{< image src="llm.jpeg" caption="LLM 的輸入與輸出" >}}

如上圖所示，基於我們的 Prompt，LLM 會以 Auto-Regressive 的方式進行「文字接龍」產生 Completion。如果這一個 LLM 是一個你所開發的 Chatbot，專門解決你的客戶的疑難雜症，那麼你可能會在 Prompt 中提供：客戶的資訊, Chatbot 與客戶的對話紀錄, 外部資料, Chatbot 能夠使用的工具, Chatbot 已經經過的 Reasoning Steps 以及 Observation ...

隨著 Chatbot 與客戶的互動時間變長，可以想像的是，Prompt 再也容不下這麼多資訊。即使你是用的是一個 Context Window 非常大的 LLM，也會發現隨著 Context Window 中的資訊愈來愈多，LLM 似乎開始出現失憶的狀況。

因此，LLM 在進行長時間的對話任務時，所經常面對的挑戰就是如何有效的管理「長期記憶」，這也正式 **[Mem0](../mem0/)** 與 **[LangMem](../../other/langmem-intro/)** 等方法所處理的問題。

## MemGPT 的核心概念

{{< image src="memgpt-core.jpeg" caption="MemGPT 的核心概念" >}}

同理，MemGPT 也是為了處理這樣的問題而誕生！如上圖所述，MemGPT 的核心概念，正是希望透過 LLM 打造一個作業系統（Operating System）來管理自己的狀態，**決定要把什麼資訊放到 Prompt 中**。

{{< image src="prompt-compilation.jpeg" caption="Prompt Compilation" >}}

舉例來說，如上圖所示，對於一個 Agent 而言，它目前的狀態 (State) 可以由它的記憶 (Memories), 能夠使用的工具 (Tools) 以及對話紀錄 (Messages) 來表示。可以想像 Agent State 裡頭存放著與 Agent 本身的所有資訊。

而賦予 Agent 對話能力的即是 LLM 模型，LLM 模型的 Context Window 有所限制，導致我們沒辦法把整個 Agent State 都放到 Prompt 裡面。

{{< admonition success 重點概念 >}}
因此，MemGPT 的最終目標就是：基於目前的任務，**從 Agent State 中取出必要的資訊放到 Prompt 中**，讓 LLM 基於 Prompt 成功產生正確的輸出。而把大量資訊從 Agent State 精鍊到 Prompt 中的這個過程又稱為 **Prompt Compilation**。
{{< /admonition >}}

為了賦予 MemGPT 有這樣的能力，MemGPT 被設計出以下四個特色：

- **Self-Editing Memory**: Agent 能夠透過 Tool Calling 修改自己的記憶內容
- **Inner Thoughts**: Agent 每次在輸出之前都可以進行一些思考，而這些思考過程不會輸出給使用者
- **Every Output as Tool**: Agent 的所有輸出都是 Tool Calling (Inner Thought 除外)，就連要輸出資訊給使用者時，都要使用 `send_message()` 工具
- **Looping via Heartbeats**: Agent 每次在 Tool Calling 時，都可以指定 `request_heartbeat` 這個參數，來自己決定要不要再拿 Tool 的執行結果 Invoke 自己一次，來得到新的輸出

## MemGPT 的記憶管理方式

{{< image src="general-context.jpeg" caption="一般 Agent 的 Prompt 內容" >}}

如上圖所示，在一般的 Agent 中，Prompt 的組成通常都是 **"System Prompt"** 加上 **"Chat Hostory"**。而在 MemGPT 中，為了做好 Prompt Compilation，將 Prompt 的組成分成很多特別保留區塊 (Special Reserved Section)，作為不同資訊存放的目的。

### MemGPT 的 Core Memory

{{< image src="core-memory.jpeg" caption="MemGPT 會在 Prompt 中保留一個 Core Memory 區塊" >}}

MemGPT 在 Prompt 中規劃了一個 Core Memory 區塊用來保存最重要的少量資訊，Core Memory 中可以分成很多 Block，每個 Block 可以保存不同的資訊 (例如：使用者資訊, Agent 自己的 Persona 等等)。

為了讓 LLM 本身知道有這個區塊的存在，會在 System Prompt 的區塊中紀錄 Core Memory 相關的資訊，包含可以透過一些 Tool 來修改 Core Memory 中的資訊 (例如：`core_memory_replace`, `core_memory_append`)。

當接收到使用者的輸入後，MemGPT 會先進行 Inner Thought 後再輸出。如同[上文](#memgpt-的核心概念)所述，MemGPT 的所有輸出都會是 Tool Calling，因此如果在 Inner Thought 中 MemGPT 覺得這個資訊值得被紀錄在 Core Memory，那這一次的輸出就會是一個 `core_memory_append` 的 Tool Calling，來將此資訊紀錄到 Core Memory 中。

### Mem0<sup>g</sup> 的記憶管理方式

{{< image src="mem0-g.png" caption="[Figure 3] Graph-based memory architecture of Mem0<sup>g</sup> illustrating entity extraction and update phase." >}}

從上圖 Figure 3 可以看到，**Mem0<sup>g</sup>** 與 **Mem0** 的 Memory Architecture 相當類似，兩者都有 Extraction Phase 以及 Update Phase。不同的地方在於 **Mem0<sup>g</sup>** 是以 Graph-Based 的方式來管理記憶，而 **Mem0** 則是以 Vector/Relational Database 的方式來管理記憶。

在 Mem0<sup>g</sup> 中，Memory 會透過一個 Graph 來表示，一個 Graph \(G\) 會包含 Node \( V \), Edge \( E \) 以及 Label \( L \)。具體來說：

- **Node \( V \)**: 代表實體 (Entity)，例如：Alice, San Francisco
- **Edges \( E \)**: 代表實體之間的關係 (e.g., lives_in)
- **Labels \( L \)**: 代表實體的語意類型 (e.g., Alice - Person, San Francisco - City)

每個 Entity Node \(v \in V\) 包含三個組成部分:

1. Entity 的類別 (例如：Person, Location, Event)
2. Entity 的 Embedding \(e_v\)，捕捉實體的語意
3. Entity 的 Metadata，包括創建時間 \(t_v\)

在 Mem0<sup>g</sup> 中，Node 之間的關係會透過一個 Triplet \((v_s, r, v_d)\) 表示，其中 \(v_s\) 和 \(v_d\) 是 Source Node 和 Target Node，\(r\) 是連接它們的 Edge。

在 **Extraction Phase** 中，會透過 LLM 進行兩階段的處理：**Entity Extraction** 以及 **Relationship Generation**。

Entity Extraction 就是透過一個 Extity Extractor LLM 來從對話紀錄中提取出所有的 Entity，並且標示出這些 Entity 的類型。例如，如果對話內容是討論與旅遊相關的主題，那麼 Entity 就可能是「出發地點」、「目的地」、「出發時間」等。這些 Entity 會被轉換成 Graph 中的 Node，並且會被標示上類別 (Label)，例如「出發地點」的類別可能是「Location」，而「出發時間」的類別可能是「Date」。

Relationship Generation 則是透過一個 Relationship Generator LLM 來從對話紀錄中提取出所有的 Entity 之間的關係，並且標示出這些關係的類型。例如，如果對話內容是討論與旅遊相關的主題，那麼 Entity 之間的關係就可能是「出發地點」和「目的地」之間的關係是「Travel From-To」，而「出發時間」和「目的地」之間的關係是「Travel Date」。

在 **Update Phase** 中，則是根據目前新建立的 Triplet \((v_s, r, v_d)\) ，比較 Source Node 以及 Target Node 與 Graph 中既有的 Node 的 Embedding，從 Graph 中取出與這兩個 Node 較為類似的 Node，然後透過 Conflict Detection 以及 Update Resolver 來決定要將新的 Source Node 以及 Target Node 都加入到 Graph 中，還是只加入一個 Node，或是都不加入僅更新 Graph 中的資訊。

在 Mem0<sup>g</sup> 中，採用兩種 Memory Retrieval 的方式：
- Entity-Centric Approach: 基於一個 Query，先分析 Query 中的 Entity，然後從 Graph 中取出與這些 Entity 相關的 Node，並將這些 Node 既有的 Relationship 建立一個 Subgraph，這個 Subgraph 就是代表這個 Query 的 Relevant Contextual Information。
- Semantic Triplet Approach: 基於一個 Query，先將這個 Query 轉為一個 Dense Embedding，再拿這個 Embedding 與 Graph 中所有 Triplet 的 Textual Encoding 的 Embedding 進行比對，取出最相似的 K 個 Triplet，這 K 個 Triplet 就是代表這個 Query 的 Relevant Contextual Information。

在實驗階段中，作者使用 [Neo4j](https://neo4j.com/) 作為 Graph Database，並且使用 GPT-4o-mini 作為 Entity Extractor LLM 以及 Relationship Generator LLM。

## Mem0 的實驗結果

### 測試資料集的選擇

作者選用 [LOCOMO](https://aclanthology.org/2024.acl-long.747.pdf) 資料集作為 Benchmark，LOCOMO 專門用來為評估對話系統中模型的長期記憶能力。LOCOMO 包含 10 個 Conversation，每個 Conversation 平均包含 600 則對話（平均約為 26K 個 Tokens）。每個 Conversation 平均有 200 個問題及其對應的標準答案。這些問題被分為多種類型：Single-Hop, Multi-Hop, Temporal (時間相關)以及 Open-domain。

### 衡量指標上的選擇

除了基本的 **F1 Score (F1)** and **BLEU-1 (B1)** 之外，作者再加入 **LLM-as-a-Judge (J)** 來提昇衡量的準確性。這三個指標都是衡量 LLM 的輸出與 Groundtruth 之間是否足夠一致。

除了上述指標外，作者也加入了 **Token Consumption** 來衡量不同的方法平均在處理每一個 Query 時，需要從 Memory Database 中題取出多少 Tokens (這些 Tokens 會變成 LLM 的輸入)，以及 **Latency** 來衡量不同的方法平均在處理每一個 Query 時，所需要的時間。

### 實驗結果

{{< image src="exp.png" caption="[Table 1] Performance comparison of memory-enabled systems across different question types in the LOCOMO dataset." >}}

從 Table 1 的實驗數據中，令我感到相當的驚訝，Mem0 的表現不只在 Single-Hop, Multi-Hop 以及 Temporal 上都達到的 State-of-the-Art (SOTA) 的表現，而且在三個指標上都比第二名高出許多。在 Open-domain 上，雖然不是 SOTA，但是與第一名相較起來也只有一點點落差。

LOCOMO 這個 Benchamrk 的有效性也在 Reddit 上被討論。有人認為 LOCOMO 這個資料集是有一些問題存在的，稍微修改一些實驗設定 [Zep 的表現甚至超越 Mem0 24%](https://www.reddit.com/r/LangChain/comments/1kg5qas/lies_damn_lies_statistics_is_mem0_really_sota_in/)，又或者是許多鄉民認為 [Mem0 的實驗設定有問題，才導致 Mem0 遠遠勝過其他的方法](https://www.reddit.com/r/LangChain/comments/1kash7b/i_benchmarked_openai_memory_vs_langmem_vs_letta/)。

此外，第二個值得注意的點是，Mem0<sup>g</sup> 相對於 Mem0 加入了 Graph-Based 的結構來儲存記憶，設計更複雜的 Extraction Phase 以及 Update Phase，然而卻只有在 Open-Domain 與 Temporal 的類別上表現的比 Mem0 好。作者針對原因並沒有做太深入的分析。

{{< image src="exp-2.png" caption="[Figure 4a] Comparison of search latency at p50 (median) and p95 (95th percentile) across different memory methods (Mem0, Mem0<sup>g</sup>, best RAG variant, Zep, LangMem, and A-Mem)." >}}

{{< image src="exp-3.png" caption="[Figure 4b] Comparison of total response latency at p50 and p95 across different memory methods (Mem0, Mem0<sup>g</sup>, best RAG variant, Zep, LangMem, OpenAI, full-context, and A-Mem)." >}}

上圖的 Figure 4a 與 Figure 4b 分別是針對不同方法衡量在 LOCOMO 整體資料集上的 LLM-as-a-Judge Score, Search Latency 以及 Total Response Latency 的表現。可以發現到 Mem0 和 Mem0<sup>g</sup> 在 Latency 以及 LLM-as-a-Judge 的分數上展現了很強的優勢。

## 結語

本篇文章介紹 [Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory](https://arxiv.org/abs/2504.19413) 論文，了解 **Mem0** 與 **Mem0<sup>g</sup>** 是如何從原始的對話紀錄透過 Extraction Phase 與 Update Phase 來管理長期記憶；以及 Mem0<sup>g</sup> 如何透過 Graph-Based 的結構來儲存記憶。

從作者選擇的 LOCOMO 測試資料集上，我們看到了 Mem0 與 Mem0<sup>g</sup> 在 Single-Hop, Multi-Hop 等多個面向都勝過 Baseline 方法，也看到 Mem0 與 Mem0<sup>g</sup> 在 Latency 上相較於其他方法的優勢。

在論文中並沒有詳細的呈現 Mem0 與 Mem0<sup>g</sup> 中所使用的 Prompt，但是從 GitHub 上找到兩個 Prompt 檔案，有興趣的讀者可以再研究看看：
- **Mem0**: [mem0/configs/prompts.py](https://github.com/mem0ai/mem0/blob/main/mem0/configs/prompts.py) 
- **Mem0<sup>g</sup>**: [mem0/graphs/utils.py](https://github.com/mem0ai/mem0/blob/main/mem0/graphs/utils.py)

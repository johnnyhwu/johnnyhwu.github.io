---
# weight: 1
title: "[論文介紹] ChatEval: Towards Better LLM-Based Evaluators Through Multi-Agent Debate"
date: 2024-06-23
lastmod: 2025-07-27
draft: false
description: "想了解 LLM 多智能體（Multi-Agent）？本文帶你讀懂 ICLR 2024 論文 ChatEval，解析其如何透過多個具備不同人設（Persona）的智能體辯論來完成評估任務。一篇絕佳的 Multi-Agent 入門介紹。"
featuredImage: "featured-image.jpg"

tags: ["LLM-as-a-Judge", "Large Language Model", "Multi-Agent", "Evaluation"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## 前言

本篇文章想和大家分享一篇「LLM Agent」相關的論文 —— [ChatEval: Towards Better LLM-Based Evaluators Through Multi-Agent Debate](https://openreview.net/forum?id=FQepisCUWu)。這是一篇 ICLR 2024 Poster 的論文，算是一篇蠻簡單、好理解的 Multi-Agent 框架的論文（甚至有點簡單到教授覺得這篇論文是怎麼被 ICLR 接受的 ...），如果想開始了解 Multi-Agent 相關的研究，我覺得這篇論文是蠻好的起手式。

## 什麼是 LLM Agent

在開始介紹這篇論文之前，想先和大家分享我對於「Agent」這個名詞的理解。這邊分享我讀了 [The Landscape of Emerging AI Agent Architectures for Reasoning,Planning, and ToolCalling: A Survey](https://arxiv.org/abs/2404.11584) 這篇 Survey 論文的內容，所謂的 Agent 應該至少具備以下**三種能力**：

- Perception：能夠「理解」(Understand) 輸入資料
- Think：基於目前的任務，能夠進行「推理」(Reason) 與「規劃」(Plan)
- Act：能夠採取「行動」(Action)

在我的想象中，假設目前有一個 Large Language Model：

我給它一個 Prompt：「請試著幫我解答這題微積分題目」 如果它回答我：「很抱歉，我不會這道數學題」或是「2」（直接給我一個錯誤的答案）。

雖然它沒有告訴我怎麼做或是它答錯了，但是它理解這是一道「數學問題」，那我會覺得它具備了「理解」輸入資料（我提供的文字）的能力。

如果我再透過一些 Prompting 的技巧（例如：[Chain of Thought](https://arxiv.org/abs/2201.11903)），促使它試著將中間的推理（運算）過程說出來，進而得到最終正確的答案，那我會認為它具備了「推理」的能力。

如果我在一開始就提供給它一些工具，像是 Web Browser 或 Code Interpreter 等等，並告訴它這些工具應該如何使用。它在推理的過程中發現自己對於微積分的概念不是很理解而透過 Web Browser 上網查詢，或是將中間的計算過程轉為程式碼並且透過 Code Interpreter 執行來得到運算結果，那我認為它已經具備了採取「行動」的能力。在這個階段我們也能夠稱其為「Agent」了。

## LLM Agent 的架構

{{< image src="agent-arch.png" caption="LLM Agent 的架構種類" >}}

如上圖所示，LLM Agent 的方法中，我們可以很簡單地將其區分為「Single Agent Architecture」或「Multi-Agent Architecture」。相信看名詞應該就知道，不需要多加解釋 ～ 而 Multi-Agent Architecture 中又可以是 Vertical 或 Horizontal 的合作關係。

在 Single Agent Architecture 中，經典的論文有 [ReAct (ICLR 2023)](https://openreview.net/forum?id=WE_vluYUL-X) 和 [Reflexion (NeurIPS 2023)](https://proceedings.neurips.cc/paper_files/paper/2023/hash/1b44b878bb782e6954cd888628510e90-Abstract-Conference.html)，而在 Multi-Agent Architecture 中，經典的論文有 [ChatEval (ICLR 2024)](https://openreview.net/forum?id=FQepisCUWu) 與 [MetaGPT (ICLR 2024)](https://openreview.net/forum?id=VtmBAGCN7o)。

{{< image src="agent-persona.png" caption="LLM Agent 加上 Persona" >}}

而在 Agent 相關的做法中，「Persona」是一個特別重要的關鍵：**Agent + Persona = Role**。如上圖所示，如果我們給予一個 Agent 透過 System Prompt 來定義其 Persona，那麼它接下來的輸出「內容」、「風格」或「推理方式」就會因此而改變。尤其是在 Multi-Agent 框架的方法中，替每一個 Agent 定義不同的 Persona 相當重要，這大大地影響了這群 Agent 有沒有能力做好當前的任務。

## LLM Agent 的 Findings

[The Landscape of Emerging AI Agent Architectures for Reasoning,Planning, and ToolCalling: A Survey](https://arxiv.org/abs/2404.11584) 論文在最後也列出了一些 Agent 相關的特性：

- Single Agent Framework 適合處理一些比較簡單、有「明確」答案的任務，像是有標準答案的 Question-Answering
- Multi-Agent Framework 適合處理一些需要 Feedback（需要討論）的任務，這些任務通常比較複雜可能也沒有標準答案，像是 Evaluation Task（[LLM as a Judeg](https://openreview.net/forum?id=uccHPGDlao)）或是 Software Development（[MetaGPT](https://arxiv.org/abs/2308.00352)）
- 在 Multi-Agent Framework 中，多個 Agent 在透過 Natural Language 進行溝通時，有時它們的溝通會有愈來愈多 Noise（他們可能開始閒聊之類的），導致最終他們的溝通可能會偏離原來設定好的目標
- 在 Multi-Agent Framework 中，「垂直式」的合作方式（也就是這群 Agent 中有一個是 Leader，會分配任務給其他 Agent），能夠帶來比較好的表現
- 不管是在 Single 或是 Multi-Agent Framework 中，定義這些 Agent 的 Persona 對於結果都有很大的影響

## ChatEval 想要解決的問題

對於 LLM Agent 有基本的概念後，我們接著開始理解 [ChatEval](https://arxiv.org/abs/2308.07201) 這篇論文究竟想要解決什麼問題！

過去當我們開發了一個新的 Language Model 時，假設我們想要比較其與其他 Language Model 進行 Summarization 的能力，我們可能需要拿很多篇文章給這兩個 Language Model 進行 Summarization，然後聘請一些人類來給兩個 Language Model 的輸出打分數。

你可以發現，這個 Evaluation 的方式是低效率（人類看很慢 ...）且高成本的（人類要算時薪的！）。 然而，如果我們透過一些 Rule-Based Metric（例如：ROUGE、BLEU 等等），這些基於 N-Gram Based 的想法所設計的 Metric 有時算出來的分數與人類的偏好並沒有那麼一致。

> 因此，我們有沒有更有效率、更低成本，也更符合人類偏好的方式，來對這些 Language Model 進行 Evaluation 呢？

## ChatEval 介紹

有的！這就是 ChatEval 想要解決的問題之一！

自從 Large Language Model (LLM) 盛行以來，就有許多研究希望透過 LLM 來替其他 LLM 進行 Evaluation，這個系列的 Work 通常稱為 [LLM-as-a-Judge](https://arxiv.org/abs/2306.05685)。

使用 LLM 來替其他 LLM Evaluation 除了有速度更快、成本更低等優點以外，別忘了 LLM 還能透過 [SFT 或 RLHF](../../ai-concept/intro-sft-rlhf/) / [DPO](../dpo/) 的訓練，使其輸出更符合 Human Preference。

ChatEval 說穿了就是一個透過 LLM 來替其他 LLM 做 Evaluation 的方法，然而比較有趣的是，它不是只用一個 LLM (Agent)，而是**透過多個 LLM (Agent) 來互相 Debate 得到共識的方法（就是一個評審團的概念）**。 ChatEval 論文以及方法設計上都相當簡單，主要就是理解兩個部分：「**每一個 Agent 的 Role 怎麼定義**」以及「**Agent 之間怎麼互相溝通**」。

## ChatEval 介紹 ⭢ Agent & Role

{{< image src="chateval-role.png" caption="ChatEval 中的角色設計" >}}

如上圖所示，在 ChatEval 中定義了 5 種 Persona：General Public、Critic、News Author、Psychologist 與 Scientist。

而每次輸入給一個 Agent 的 Prompt 就會如下圖所示：

{{< image src="chateval-prompt.png" caption="ChatEval 中的 Prompt 設計" >}}

我們可以清楚看到這個 Prompt 主要就是分為兩個部分：Question Prompt 與 System Prompt。在 Question Prompt 中，提供一個問題以及兩個 Language Model 的回答，而在 System Prompt 中，則是告訴目前的 Agent 應該如何替這兩個 Language Model 的回答打分數。

## ChatEval 介紹 ⭢ Communication between Agent

{{< image src="chateval-communication.png" caption="ChatEval 中的 Coomunication 方式設計" >}}

如上圖所示，在 ChatEval 中定義了 3 種 Agent 之間的 Communication 方式。假設目前有 3 個 Agent，Alice、Bob 與 Carol，給定一個問題，以及 2 個 Language Model 的回答，這 3 個 Agent 會透過以下 3 種 Communication/Debate 方式，來得到最後的結論（哪一個 Language Model 的回答比較好）：

- **One-by-One**：所有 Agent「依序」發言。如上圖所示，Alice 先發表自己的看法，再由 Bob 發表，最後由 Carol 發表。後面的人在發表時都可以看到前面的人所發表的內容。換句話說，Bob 在發表時除了本來就有的 Question 以及 2 個 Language Model 的 Response 外，還可以看到 Alice 的想法；Carol 在發言時則可以看到 Alice 和 Bob 的想法。在下一輪的發言時，一樣是按照順序發言，只不過這一次大家都可以看到上一輪討論中每一個人的發言。
- **Simultaneous-Talk**：所有 Agent「同時」發言。如上圖所示，Alice、Bob 和 Carol 同時發言，他們在發言的當下只會看到 Question 以及以及兩個 Language Model 的 Response，並不會看到其他人的發言。等待這一輪所有人都發言過後，就會把每一個人的發言都記載一本簿子上，然後把這本簿子給所有人看過。在進入下一輪發言時，每一個人一樣都是同時發言，但是他們都已經看到了上一輪中所有人的對話。
- **Simultaneous-Talk-with-Summarizer：**基本上和 **Simultaneous-Talk** 的做法一樣，只不過在每一輪的最後，會先透過一個 Summarizer（其實就是在額外一個 LLM）把簿子上的內容（三個人在這輪的發言）進行摘要後，才把這個簿子給三個人看。換言之，這三個人看到的內容是摘要過後的結果，而非原始三個人的發言內容。

以上就是這 3 種 Communication/Debate 方法的概念，在論文中都有提供其演算法，如果你不喜歡上述擬人化的介紹方式，可以再到原始論文中看看！在進入到最後的實驗介紹之前，不妨停下來猜猜看哪一種 Communication 方法會有最好的表現呢？

## ChatEval 的實驗結果

ChatEval 論文當中使用了 2 種任務來衡量 ChatEval 方法的有效性，分別是：

- Open-ended Question Answer
- Dialogue Response Generation

如下圖所示，Open-ended Question Answer 任務中會有很多 Question，每一個 Question 都有 2 個 LLM 的 Response，已經事先標記好哪一個 Response 比較好了，我們希望 ChatEval 方法也可以知道哪一個 Response 比較好：

{{< image src="task-1.png" caption="任務 1: Open-ended Question Answer" >}}

下圖為 ChatEval 在這個任務上的實驗結果，可以發現不管是 ChatGPT 還是 GPT-4 都分別使用了三種方法（MEC+BPC、Single-Agent 與 Multi-Agent），其中 Multi-Agent 就是指 ChatEval 方法。實驗結果當然一定會呈現自己所提出的方法（ChatEval）是很棒的。

{{< image src="exp-1.png" caption="任務 1 的實驗結果" >}}

而在 Dialogue Response Generation 任務中，則是會有很多 Dialogue，每一個 Dialogue 又會有很多 Response。每一則 Response 都可以從不同的面相（例如：Naturalness、Coherence ...）來替每一則 Response 做排名。我們希望透過 ChatEval 方法，也可以看到 Agent 們在每一個面向替這些 Response 的排名結果與人類（Groundtruth）一致。

{{< image src="task-2.png" caption="任務 2: Dialogue Response Generation" >}}

下圖為 ChatEval 在這個任務上的實驗結果，可以發現多數情況下 Multi-Agent (ChatEval) 都可以比 Single-Agent 帶來更好的表現。

{{< image src="exp-2.png" caption="任務 2 的實驗結果" >}}

此外，作者也在 Ablation Study 中呈現在 3 種 Communication/Debate 方法中，One-by-One 有最好的表現： 

{{< image src="exp-communication.png" caption="不同 Commincation 方法的表現" >}}

而在 Multi-Agent 的框架中，Diverse Role 是作者特別強調的技巧，也就是必須透過 Persona 的設定，讓每一個 LLM 分別是不同的 Role，這樣他們在 Debate 過程中才比較有可能提出不同的觀點，提升最後的表現：

{{< image src="exp-diverse-agent.png" caption="Diverse Agent 的效果" >}}

最後，作者也呈現了多少 Agent 以及多少輪討論會有最好的結果。出乎我的意料，我以為會很多 Agent 一起討論很多次，結果其實  3 個 Agent 討論個 2 輪就會有共識了：

{{< image src="exp-agent-iteration.png" caption="Agent 與 Iteration 數量的影響" >}}

## 結語

相信看完了這篇文章，你一定也覺得 [ChatEval: Towards Better LLM-Based Evaluators Through Multi-Agent Debate](https://openreview.net/forum?id=FQepisCUWu) 這篇論文其實不管在動機、方法以及實驗上都非常簡單（但還是上 ICLR 2024 ...），因此算是進入 Multi-Agent 領域中的起手式論文。此外，作者也有開源 [ChatEval GitHub](https://github.com/thunlp/ChatEval)，因此未來如果有機會設計 Multi-Agent Debate 的方法時，我覺得 ChatEval 當成 Baseline 也挺好的！

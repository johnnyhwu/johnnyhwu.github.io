---
# weight: 1
title: "[論文介紹] GAIA: A Benchmark for General AI Assistants"
date: 2024-06-27
lastmod: 2025-07-27
draft: false
description: "為何連 GPT-4 這種頂尖 AI，都難以處理人類眼中的簡單任務？快來一探究竟由 AI 巨頭 Yann LeCun 團隊提出的 GAIA 評測，了解它如何跳脫傳統框架，定義一個真正「通用 AI 助理」所需具備的能力！"
featuredImage: "featured-image.png"

tags: ["Large Language Model", "Single-Agent", "Multi-Agent", "Benchmark"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## 前言

在 [ChatEval](../chateval/) 一文中和大家介紹了 LLM Agent 的概念，以及如何透過 Multi-Agent 的框架，讓多個 LLM Agent 進行 Debate 來衡量（Evaluate）其他 LLM 的輸出。

> 然而，有沒有一個 Benchmark 可以衡量一個 Agent 能力呢？

今天要和大家分享一篇 ICLR 20204 Poster 的論文叫做 [GAIA: A Benchmark for General AI Assistants](https://arxiv.org/abs/2311.12983)，這篇論文正是提出了一個 Benchmark 來衡量一個 General AI Assistant 的能力！ 之所以想和大家分享這篇論文，除了這篇論文有趣之外，另一個原因是這篇論文的作者竟然有 Yann LeCun！身在 AI 領域應該都聽過 Yann LeCun 這號人物，前陣子還[和 Elon Musk 在 X 上大戰](https://x.com/ylecun/status/1797270661192155427?lang=en)呢 ...

{{< image src="author.png" alt="GAIA 論文的標題頁，顯示標題「GAIA: A Benchmark for General AI Assistants」以及作者 Gregoire Mialon、Clementine Fourrier、Craig Swift、Thomas Wolf、Yann LeCun 和 Thomas Scialom，分別隸屬於 Meta FAIR、HuggingFace、AutoGPT 和 Meta GenAI" caption="GAIA 的作者" >}}

## GAIA Benchmark 想要解決的問題

現今世界已經有那麼多 Benchmark 可以來衡量 LLM Agent 的能力，為什麼還需要提出一個 GAIA Benchmark 呢？它跟過去大家所使用的 Benchmark 有什麼不同呢？ 舉例來說，在 Meta 發表 Llama 3 時就使用了 MMLU、HumanEval、GSM-8K 等常見的 Benchmark 來衡量其 LLM 的能力：

{{< image src="llama3.png" alt="表格「Meta Llama 3 Instruct model performance」，比較 Llama 3 8B 與 Gemma 7B-It、Mistral 7B Instruct，以及 Llama 3 70B 與 Gemini Pro 1.5、Claude 3 Sonnet 在 MMLU、GPQA、HumanEval、GSM-8K、MATH 上的表現；Llama 3 8B 分別得分 68.4、34.2、62.2、79.6、30.0，優於兩個較小的競爭模型，而 Llama 3 70B 分別得分 82.0、39.5、81.7、93.0、50.4，在多數項目上超越或持平 Gemini Pro 1.5 與 Claude 3 Sonnet" caption="Llama-3 使用的 Benchmark" >}}

GAIA 所想要解決的問題正是認為過去這些 Benchmark 雖然可以衡量 LLM 的知識量（或是說聰明程度），但是和 General AI Assistant 的能力卻不完全一致！ 舉例來說，以下是來自 MMLU Benchmark 的兩個 Sample 以及 GSM8K Benchmark 的一個 Sample：

```text {title="MMLU Example"}
# Question
Paper will burn at approximately what temperature in Fahrenheit?

# Answer
986 degrees

# Question
Which of the following heavenly bodies have never had a spacecraft landed on it?

# Answer
Jupiter
```

```text {title="GSM8K Example"}
# Question
Paddington has 40 more goats than Washington. If Washington has 140 goats, how many goats do they have in total?

# Answer
If Washington has 140 goats, Washington has 140+40 = <<140+40=180>>180 goats. In total, they have 140+180 = <<140+180=320>>320 goats #### 320
```

從上述的範例應該可以感受到，假如 LLM 可以在這些問題上回答的很好，我們可能會覺得它很聰明（什麼都懂），但是在這些問題上回答的很好，就是代表我們距離 General AI Assistant 又更靠近了嗎？我想答案絕對是否定的！

在 [GAIA 論文](https://arxiv.org/abs/2311.12983)中也有提到，現今我們在衡量 AI 模型（LLM） 的能力時，大多會用一些連人類也做不好的問題來衡量，這些問題大多是一些專業領域相關的問題。然而，從近幾年 AI 模型屢次在 MMLU 或 GSM8k 這些 Benchmark 上獲得好成績的趨勢來看，AI 已經愈來愈擅長這些特定艱難的任務。

此外，目前在衡量 AI 模型（LLM） 的 Benchmark 中，有些也是屬於 Open-Ended Generation 的類型，意思就是說這些問題並沒有一個標準的答案，或是說這些問題的答案通常需要透過比較多的文字來描述。那這樣就會導致我們在衡量某一個 AI 模型在這種 Benchmark 上的表現時，可能就必須透過其他 AI 模型或是 Human 作為裁判（Judge）而沒有辦法透過 Rule-Based 的方式來檢查 AI 模型的輸出。

然而，這些問題其實也有可能是既有的 AI 模型或是 Human 所回答不出來的，那又怎麼能夠請他們擔任裁判呢？

## GAIA Benchmark 介紹

理解了 GAIA Benchmark 想要解決的問題後，我們開始介紹 GAIA Benchmark 的獨特之處！GAIA Benchmark 中包含 466 個 Question/Answer Pair，每一個 Question 都是 Text-Based，有時候會有額外的檔案 （例如，圖像檔案或是 CSV 檔案）。

如下圖為 GAIA Benchmark 中各種檔案類型的統計：

{{< image src="file-type.png" alt="橫向長條圖「Distribution of File Types」，列出 GAIA Benchmark 中各檔案類型的數量：xlsx 29 個、png 18 個、pdf 15 個、txt 13 個、mp3 7 個、jpg 7 個、csv 6 個、docx 2 個、pptx 2 個、zip 2 個、xml 2 個，以及 py、json、m4a、pdb、MOV、jsonld 各 1 個" caption="GAIA Benchmark 中所包含的檔案類型" >}}

GAIA 中的 Question 可能是日常工作常見的文書任務、科學問題或是通用的知識性問題。而 GAIA 中最重要的特色就是每一個 **Answer 都是簡短、簡單、容易驗證的（避免模稜兩可的狀況出現）**，但都需要很多不同面向的基本能力，才有辦法得到這一個 Answer。 具體來說，GAIA 中的 Answer 要馬是一個 Number 或是一個 String 或是 A List of String，且正確答案只會有一個。

此外，我們又可以透過 System Prompt 告訴 Agent 應該輸出怎麼樣的 Answer Format，這對於 Automated Evaluation 會很有幫助。而 AI 模型如果要在 GAIA Benchmark 上得到高分，就必須具備以下幾種能力：

- Advanced Reasoning
- Multi-Modality Understanding
- Coding Capability
- Tool Use

如下圖（左）呈現的是每一種技能所包含的問題數量，可以發現大部分的問題都沒有辦法直接透過 AI 模型既有的知識來回答，AI 模型必須學習透過 Web Browsing 的方式來得到正確答案。下圖（右）呈現的是每一種難度的問題需要使用多少種不同的工具，以及多少個步驟才能得到答案。

{{< image src="difficulty.png" alt="兩張圖表：左側為橫向長條圖「Capabilities required to solve GAIA」，顯示需要網頁瀏覽能力的題目有 355 題、程式撰寫 154 題、多模態 138 題、多種檔案類型讀取 129 題、不需要特殊能力的有 32 題；右側為散佈圖「An overview of GAIA questions」，以問題難度 Level 1 至 3 上色，橫軸為所需步驟數（0 到 45）、縱軸為使用的工具種類數（0 到 6），大多數題目集中在步驟數少於 15、工具種類數 1 到 3 之間" caption="GAIA Benchmark 的問題難度" >}}

GAIA Benchmark 的使用方式也相當直觀，直接使用官方所提供的 System Prompt 對 AI 模型進行 Zero-Shot 的 Inference 即可。如下圖是官方所提供的 System Prompt 以及一個範例的問題：

{{< image src="system-prompt.png" alt="邊框中顯示用於評估模型在 GAIA 上表現的 System Prompt：要求助理以一般 AI 助理的身份回答，並以「FINAL ANSWER: [YOUR FINAL ANSWER]」結尾，格式規則包括數字不可加逗號或單位、字串不可使用冠詞或縮寫，以逗號分隔的清單則依各元素類型分別套用上述規則" caption="System Prompt of GAIA Benchmark" >}}

{{< image src="question.png" alt="以邊框呈現的 GAIA 範例問題：「The attached Excel file contains the sales of menu items for a local fast-food chain. What were the total sales that the chain made from food (not including drinks)? Express your answer in USD with two decimal places.」，旁邊附有一個標示為 uploaded.xlsx 的附加檔案圖示" caption="Sample Question in GAIA" >}}

最後，作者透過 GAIA Benchmark 來衡量多個 SOTA LLM 以及 Human 的表現：

{{< image src="exp.png" alt="兩部分長條圖「LLMs, Human and Search engine scores and time to answer for GAIA」：上方顯示 Search engine、GPT-4、GPT-4 Turbo、AutoGPT-4、GPT-4 Plugins 與人類在 Level 1、2、3 的答對率（%），人類在各難度都超過 85%，而表現最好的模型 GPT-4 Plugins 在 Level 1 僅約 30%、Level 2 僅約 10%；下方以對數座標顯示回答所需時間，AutoGPT-4 與人類所花時間最長" caption="多個 SOTA LLM 在 GAIA Benchmark 上的表現" >}}

可以發現連前陣子最強的 GPT-4 Turbo 模型在 Level 1 問題的表現也只有 10 ~ 20 分，透過 Human 的幫助頂多可以到 30 分。在 Level 2 和 3 的問題上，這些既有的 SOTA LLM 表現的又更差。但你發現到了嗎！不管在 Level 1、2 還是 3，Human 所得到的分數幾乎都在 90 分上下！

我覺得這正是 GAIA Benchmark 的有趣之處 —— 它設計了一些對於 Human 來說簡單但是對於現今的 AI 模型來說困難的任務！它不單單只是考驗 AI 模型到底知道（記住）了多少知識，而又更進一步衡量 AI 模型會不會使用工具、能不能理解多種不同的資料類型、有沒有更強的推理能力以及能不能自己撰寫一些程式碼來進行分析。當 AI 模型有能力在 GAIA Benchmark 上有好的表現時，也象徵著這個 AI 模型又更像 General AI Assistant 了。

## 結語

在本篇文章中，和大家分享了 [GAIA: A Benchmark for General AI Assistants](https://arxiv.org/abs/2311.12983) 這篇 ICLR 2024 的 Poster 論文。原本只是看到：「哦～是 ICLR 的論文」（感覺值得讀一下），後來又看到「哇，是 Meta 發的」（感覺蠻有趣的），最後又看到「Yann LeCun 也是作者之一」（那真的必須一定要讀了）！

本篇論文提出了一個 Benchmark 來更準確的衡量一個 AI 模型是否具備 General AI Assistant 的能力，同時巧妙的設計 Answer，避免有模棱兩可的狀況出現，讓我們更容易透過 Ruled Based 方式來衡量 AI 模型的輸出。最後，也透過實驗呈現現今的 SOTA AI 模型在這個 Benchmark 上的表現仍然很差，但是 Human 卻有相當好的表現。

---
# weight: 1
title: "[論文介紹] Synthesizing Text-to-SQL Data from Weak and Strong LLMs"
date: 2025-09-15
lastmod: 2025-09-16
draft: true
description: ""

featuredImage: "featured-image.jpg"

tags: ["Large Language Model", "Fine-Tuning", "LLM Alignment", "Synthetic Data Generation"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## 前言

本篇文章介紹 [SENSE: Synthesizing Text-to-SQL Data from Weak and Strong LLMs](https://arxiv.org/abs/2408.03256) 論文。本篇論文發表在 ACL 2024，論文的核心目標在於如何透過 Supervised Fine-Tuning (SFT) 訓練出一個厲害的 Text-to-SQL 模型。

本篇論文以 **Data** 的角度出發，提出一種基於 Weak 與 Strong LLM 各自產生不同性質的 Text-to-SQL Synthetic Data 方法，來提升開源模型 Fine-Tuning 後的表現。

作者最終 Fine-Tune 出來的模型稱為 **SENSE**，雖然有提供 [GitHub](https://github.com/Yangjiaxi/Sense)，但在我撰寫本篇文章時，作者尚未將程式碼以及模型推上去。 

## SENSE 想解決的問題

SENSE 的目標透過 SFT 來提升開源模型的 Text-to-SQL 表現。既然要做 SFT 那會遇到的首要問題就是訓練資料的準備。為了更有效率的準備訓練資料，SENSE 採取 Synthetic Data Generation 的方法。

因此，SENSE 所要處理的問題就會在於:

> **要生成什麼樣的 Synthetic Data** 才能讓模型在 Fine-Tune 後有更好的 Text-to-SQL 能力?

## SENSE 所提出的方法

作者認為良好的 Text-to-SQL 的訓練資料，需要教會模型以下 2 件事情:

- 模型需要足夠的泛化能力，在看到訓練資料中所沒有的 Table Schema 時，也要能夠產生正確的 SQL
- 模型需要認識常見的 SQL 的錯誤寫法，來減少自己也犯下同樣的錯誤

基於上述兩點，SENSE 的方法可以分為兩個階段:

- 第一階段
  - 目標: 讓模型具有足夠的 Text-to-SQL 泛化能力
  - 方法: 透過 Strong LLM 來生成高品質資料 (Strong Data)，再將模型以 SFT 訓練於此
- 第二階段
  - 目標: 讓模型認識 SQL 中的錯誤寫法
  - 方法: 透過 Weak LLM 來生成常見的 SQL 錯誤語法 (Weak Data)，再將模型以 DPO 訓練於此

{{< admonition tip >}}
如果你是第一次接觸到 [DPO: Direct Preference Optimization](https://arxiv.org/abs/2305.18290) 這個名詞，可以先閱讀[此篇文章](../dpo/)來掌握 DPO 的基本概念!
{{< /admonition >}}

### Strong Data: Supervised Fine-tuning

### Weak Data: Preference Learning

## SENSE 實驗結果

## 結語

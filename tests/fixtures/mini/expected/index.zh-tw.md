---
# weight: 1
title: "Mini：一個示範用的測試文章標題"
date: 2026-10-26
lastmod: 2026-10-26
draft: false
description: "這是測試用的描述，說明方法 A 如何把流程存成圖，並用驗證閘門決定改動要不要採用，長度足夠通過檢查。"
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

你有沒有看過 agent 一直重複同一個無效的動作？

先給結論：方法 A 在 24 格中有 23 格為正。

## 問題

ReAct 每一步都在摸索，容易重複無效的動作。

{{< image src="figure1.png" alt="左邊是知識圖譜，右邊是流程圖。" caption="圖 1 — 知識與流程。（來源：原始論文 Figure 1。）" >}}

## 方法

圖的形式是 \( G = (V, E) \)，其中 \( V \) 是節點集合。

可以把閘門想成一道檢查站：新版本要證明自己不比舊版本差，才放行。

$$
S(G) \ge S(G')
$$

{{< fold title="閘門的一個漏洞" tone="warning" >}}
驗證器不檢查工具名稱，只靠 prompt 約束。
{{< /fold >}}

---
# weight: 1
title: "[論文介紹] Coding Agents with Multimodal Browsing are Generalist Problem Solvers"
date: 2025-06-16
lastmod: 2025-06-16
draft: true
description: ""
featuredImage: "featured-image.jpg"

tags: []
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## 前言

本篇文章介紹 [Coding Agents with Multimodal Browsing are Generalist Problem Solvers](https://arxiv.org/abs/2506.03011) 論文，此論文由 Carnegie Mellon University, Independent 與 All Hands AI 於 2025 年 6 月發表至 arXiv。

本篇論文提出：**一個 Agent 如果具備 Coding, Multimodal Web Browsing 以及 Information Access 三種能力，那麼它將會是一個 General Agent (能夠處理多種領域的任務，而非侷限於單一領域)**。

{{< image src="openhands-versa.png" caption="OpenHands-Versa vs OpenHands" >}}

如上圖所示，本篇論文所提出的方法稱為 **OpenHands-Versa** 是一個 General (Versatile) Agent。在核心方法上主要是基於 OpenHands 這個專注於 Software Development 的 Specialist Agent 提供不同的 Tool。 OpenHands-Versa 本身也是一個開源專案，有興趣的讀者可以再研究其 [Codebase](https://github.com/adityasoni9998/OpenHands-Versa)。

## OpenHands-Versa 想解決的問題

簡單來說，OpenHands-Versa 想解決的問題為：
> 如何設計一個能夠處理不同領域任務的 General Agent?

近幾年有許多 Agent 的方法被提出，然而這些 Agent 都只有在特定的 Benchmark 或是任務上有好的表現，而無法泛化到其他領域的任務。舉例來說，[Agentless](https://arxiv.org/abs/2407.01489) 和 [SWE-Agent](https://arxiv.org/abs/2405.15793) 在 [SWE-Bench](https://www.swebench.com/) 上都達到了 State-of-the-Art 的表現，然而它們卻都無法從 Web 上取得資訊，也無法透過 Web-Based Chat 與其他 Agent 溝通，導致這兩個方法在 GAIA 以及 The Agent Company 兩個 Benchmark 上的表現較差。相反的，擅長 Web Navigation 的 Agent (EX. [AgentSymbiotic](https://arxiv.org/abs/2502.07942), [AgentOccam](https://arxiv.org/abs/2410.13825), [Agent Workflow Memory](https://arxiv.org/abs/2409.07429)) 卻不會寫 Code 或是執行 Code。

## OpenHands-Versa 方法介紹


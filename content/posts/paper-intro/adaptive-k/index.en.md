---
# weight: 1
title: "Beyond Top-k: How Adaptive-k Dynamically Selects the Best Context for RAG Without Latency"
date: 2025-09-22
lastmod: 2025-09-22
draft: false
description: "Struggling with choosing the right 'k' in your RAG system? Discover Adaptive-k, a novel, no-tuning method that dynamically selects the best context for LLMs, improving performance without sacrificing speed."
featuredImage: "featured-image.jpg"

tags: ["Large Language Model", "Retrieval-Augmented Generation"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## Introduction

This article introduces the paper "[Efficient Context Selection for Long-Context QA: No Tuning, No Iteration, Just Adaptive-k](https://arxiv.org/abs/2506.08479)," which was uploaded to arXiv in June 2025 and accepted by the EMNLP 2025 (Main) conference.

The authors have also open-sourced their code on [GitHub](https://github.com/megagonlabs/adaptive-k-retrieval). Interested readers are encouraged to try it out!

## The Problem Adaptive-k Aims to Solve

In the [Retrieval-Augmented Generation (RAG)](https://arxiv.org/abs/2312.10997) framework, we often use the "Top-k" method to select the k document chunks most similar to a query. These chunks are then fed into the Large Language Model's (LLM) context, enabling it to generate answers based on external knowledge and reduce hallucinations.

However, in practice, the Top-k approach is too simplistic. Sometimes, it retrieves too much irrelevant information, causing the LLM to hallucinate or perform poorly. Other times, it fails to retrieve enough information, preventing the LLM from generating a correct answer. Therefore, determining the optimal value for "k" in "Top-k" has always been a challenge in the RAG field.

To enhance retrieval flexibility, many Adaptive RAG methods have been proposed, such as [Self-RAG](https://arxiv.org/abs/2310.11511) and [Adaptive-RAG](https://arxiv.org/abs/2403.14403). These methods allow the LLM to choose different retrieval strategies based on the query itself or to decide when to retrieve, using an iterative process to gather sufficient information. Additionally, techniques for refining retrieved documents are common, with [CRAG](https://arxiv.org/abs/2401.15884) being a classic example.

However, a common thread among these approaches, whether from the Adaptive RAG or Corrective RAG families, is that **they invariably lead to longer inference latency, which in turn affects the user experience**.

This brings us to the core problem that this paper (hereafter referred to as "Adaptive-k") aims to address:

> How can we more dynamically and flexibly determine the value of k for each retrieval without sacrificing inference latency?

## Introducing the Adaptive-k Method

The essence of the Adaptive-k method can be summarized in a single sentence:

> For each set of retrieval results, the Adaptive-k method sorts the similarity scores between the query and each document chunk in descending order and then identifies the largest drop, or "gap," in these scores. Only the document chunks with higher similarity scores preceding this gap are retained.

{{< image src="approach.png" alt="Diagram of the Adaptive-k retrieval method: a query and context passages are embedded, similarity scores are sorted into a distribution, the largest gap sets the threshold k so only the top passages are retrieved into the prompt for the LLM" caption="Illustration of the Adaptive-k method" >}}

The image above illustrates the Adaptive-k method, while the one below shows its algorithm:

{{< image src="algo.png" alt="Pseudocode for Adaptive-k estimation via the largest similarity gap: embed the query and context, compute and sort similarities in descending order, take pairwise differences, and pick k at the index of the largest gap" caption="Algorithm of the Adaptive-k method" width="50%" >}}

The authors note that in practice, relying solely on the similarity score gap to select the top k document chunks might cause some relevant chunks distributed after the gap to be excluded. To address this, they introduced a Buffer Size "B." The total number of retrieved document chunks becomes "k+B." (In the paper, B is set to 5).

## Conclusion

This article reviewed the paper "[Efficient Context Selection for Long-Context QA: No Tuning, No Iteration, Just Adaptive-k](https://arxiv.org/abs/2506.08479)," explaining how it improves upon the traditional Top-k retrieval in RAG. By analyzing the distribution of similarity scores, the authors designed the Adaptive-k retrieval mechanism to overcome the shortcomings of conventional methods.

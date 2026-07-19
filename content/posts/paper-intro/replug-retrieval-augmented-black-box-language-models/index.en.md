---
# weight: 1
title: "REPLUG: Retrieval-Augmented Black-Box Language Models"
date: 2024-10-31
lastmod: 2024-10-31
draft: false
description: "Explore how Retrieval-Augmented Generation (RAG) enhances black-box LLMs. This article details the NAACL 2024 paper REPLUG, discussing its innovative methods for Inference and Training stages to improve LLM answer quality and effectively reduce hallucination."
featuredImage: "featured-image.png"

tags: ["Large Language Model", "Retrieval-Augmented Generation"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true
license: '<a rel="license external nofollow noopener noreffer" href="https://creativecommons.org/licenses/by-nc/4.0/" target="_blank">CC BY-NC 4.0</a>'

url: "paper-intro/:contentbasename"
---

<!--more-->

## Introduction

Retrieval-Augmented Generation (RAG) technology has been incredibly popular in recent years because it allows LLMs to answer user queries based on the latest data (not seen during the Pre-Training Stage), reducing the phenomenon of LLM hallucination.

This article aims to introduce a RAG paper from NAACL 2024 — [REPLUG: Retrieval-Augmented Black-Box Language Models](https://aclanthology.org/2024.naacl-long.463/). This paper was actually published on Arxiv as early as [January 2023](https://arxiv.org/abs/2301.12652), so it's not a very new paper. However, the method proposed in the paper has appeared in many subsequent RAG-related papers, making it still worth studying! Furthermore, the RAG method proposed by REPLUG is quite simple and easy to understand, making it very suitable for readers new to the RAG field!

## The Problem REPLUG Aims to Solve

A common problem with general LLMs is that when a user asks about knowledge that the LLM has not learned during the Pre-Training or Fine-Tuning stages, the LLM is likely to answer by making things up (Hallucination). It is quite difficult to teach an LLM to know what it doesn't know. Conversely, through RAG techniques, LLMs can obtain relevant information for the question from an external database, reducing hallucination.

{{< image src="replug.png" alt="Comparison diagram: the previous paradigm has a frozen retriever feeding documents into a trainable white-box language model under 10B parameters, whereas RE-PLUG keeps the large black-box language model over 100B parameters frozen and instead makes the retriever the frozen or trainable component" caption="[Figure 1] REPLUG augments black-box LMs with a frozen or tunable retriever, enabling use with large API-based LMs (>100B parameters)." >}}

As shown in Figure 1 above, most past RAG methods used a frozen (cannot be trained) Retriever paired with a trainable LLM, allowing the LLM to learn to generate output based on the documents provided by the Retriever. This approach has the following drawbacks:

- The Retriever does not learn how to retrieve good documents.
- Fine-tuning the LLM itself is a high-cost task. To reduce costs, one might have to use a smaller LLM, which in turn reduces performance.

Furthermore, most existing State-Of-The-Art LLMs are Black-Box Models, meaning we can only call them via API, providing input and getting output, let alone fine-tuning them. Therefore, the RAG method proposed in this paper primarily focuses on Block-Box LLMs!

## The Method Proposed by REPLUG (1): Inference Time

The method proposed by REPLUG can be divided into two parts: Inference Time and Training Time. This section will first introduce how Inference Time can improve the output quality of the LLM through Ensemble techniques.

{{< image src="replug-approach.png" alt="Diagram of the REPLUG inference process where a retriever fetches several documents for the test context Jobs is the CEO of, each document is separately prepended to the context and passed through the black-box LM to get next-token distributions, and these are ensembled into a final distribution that predicts Apple" caption="[Figure 2] REPLUG retrieves relevant documents, prepends them to the input, and ensembles output probabilities." >}}

As shown in Figure 2 above, given a Query (hoping the LLM answers "Job is the CEO of ???"), the Retriever will retrieve the documents most similar to this Query from the External Database. The specific method here is actually the standard RAG approach: pass both the Query and all Documents in the External Database individually through a Sentence Embedding Model to get their Embeddings. Then, calculate the Cosine Similarity between the Query's Embedding and all Document Embeddings. Select the Top-K most similar Documents!

With K documents related to the Query, a simple approach is to use all these documents as Context and input them along with the Query into the LLM. However, this approach might cause the input sequence length to exceed the LLM's Context Window Size.

Therefore, this paper proposes an Ensemble method: Concatenate each document individually with the Query and input them separately into the LLM. Each time, a Next Token Distribution is obtained. Finally, these K Next Token Distributions are Ensembled together.

During the Ensemble process, each Distribution must be assigned a Weight, and this Weight is calculated from the Similarity between that document and the Query.

In other words, if a document is more similar to the Query, its Weight will be higher. Through this method, the LLM's output no longer relies on just one document but can refer to multiple documents simultaneously without needing to provide a large context at once.

{{< admonition info >}}
My thought is that since the Context Window Limit of SOTA LLMs is constantly expanding, and various Inference Optimization techniques are being proposed, I think the effectiveness of this method might not be significant. Within an affordable Context Size, providing all documents at once can actually give the LLM more Global Information, potentially leading to better Reasoning and thus better output.
{{< /admonition >}}

## The Method Proposed by REPLUG (2): Training Time

The second method proposed by REPLUG is to train the Retriever during the Training Stage. In other words, because the focus is on Block-Box LLM, it's impossible to train the LLM, but the question is how to train the Retriever to retrieve documents that improve the output quality of the LLM.

{{< image src="replug-training.png" alt="Diagram of REPLUG LSR training where the retriever produces a retrieval likelihood distribution over documents, the frozen language model produces a target likelihood distribution based on how much each document lowers the perplexity of the answer, and the retriever is trained by minimizing the KL divergence between the two distributions" caption="[Figure 3] The retriever is trained using the output of a frozen language model as supervision signals." >}}

As seen in Figure 3 above, following the general RAG approach, first, based on the current Query ("Job is the CEO of ???"), the Retriever can retrieve K documents from the External Database. Through the Similarity between these K documents and the Query, the probability values of these K documents being selected can be calculated, which is called Retrieval Likelihood. The specific method is simply to apply Softmax to these K Similarities.

Next, concatenate these K documents separately with the Query and input them into the LLM. From the LLM's Output Distribution, extract the probability value of the correct Token. For example, according to the current Query, the correct Token the LLM should output next is "Apple".

In this step, we can obtain the probability of the LLM predicting the token "Apple" after reading each different document. If connecting Document #2 with the Query results in the highest probability for the LLM predicting the token "Apple", then we can imagine that Document #2 is the most suitable for the current Query!

Through this method, we can calculate the probability value of each document for the correct Token, called LM Likelihood. Our ultimate goal is to make the Retrieval Likelihood as close as possible to the LM Likelihood, so the KL Divergence between these two Likelihoods can be used as the Loss to update the Retriever.

Once the Retriever is updated, the Embeddings of all documents that we pre-calculated and stored in the External Database will become outdated. Therefore, the authors chose to update the Embeddings of all documents in the External Database after updating the Retriever T times!

{{< admonition info >}}
I think this training method is quite intuitive and effective. Since the training direction of the Retriever is determined by the LLM, subsequent RAG methods often refer to this training method as LLM-Supervised!
{{< /admonition >}}

## REPLUG Experimental Results

{{< image src="exp-1.png" alt="Language-modeling perplexity table for GPT-2 sizes and black-box GPT-3 models, showing that adding REPLUG and REPLUG LSR consistently lowers perplexity versus the original, with gains of several percent, for example 6.3 percent on GPT-3 Davinci with REPLUG LSR" caption="[Table 1] Both REPLUG and REPLUG LSR consistently enhanced the performance of different language models." >}}

From the experimental results in Table 1, it can be seen that regardless of which version of GPT2 or GPT3 is used, their performance improves when combined with REPLUG's Inference Time technique (+ REPLUG). If the Retriever is further trained, the performance improves even more (+ REPLUG LSR).
{{< image src="exp-2.png" alt="MMLU accuracy table by category (humanities, social, STEM, other and all) comparing Codex, PaLM, Flan-PaLM and Atlas against Codex plus REPLUG and Codex plus REPLUG LSR, where the REPLUG variants raise Codex's overall score from 68.3 to 71.4 and 71.8" caption="[Table 2] REPLUG and REPLUG LSR improve Codex performance on MMLU categories, with 4.5% and 5.1% gains respectively." >}}

In the experiment shown in Table 2, the authors used the MMLU Dataset, which is divided into 4 categories. Among them, Codex, PaLM, and Flan-PaLM are the three Baselines with the best performance on the MMLU Dataset Leaderboard. Atlas is used as a RAG method Baseline. It can be seen that adding the techniques proposed in this paper to Codex improves its performance.

## Conclusion

This article briefly introduced the NAACL 2024 RAG paper — [REPLUG: Retrieval-Augmented Black-Box Language Models](https://aclanthology.org/2024.naacl-long.463/). It mainly focuses on improving the output quality of Block-box LLMs by using the Ensemble Output Distribution technique during the Inference Stage, allowing the LLM's output to consider multiple different documents simultaneously. It also proposes an LLM-Supervised method during the Training Stage to train the Retriever to retrieve documents suitable for the LLM, thus improving the LLM's output quality.

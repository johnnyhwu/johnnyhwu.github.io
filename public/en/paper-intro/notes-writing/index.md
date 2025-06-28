# Augmenting LLM Reasoning with Dynamic Notes Writing for Complex QA


<!--more-->

## Introduction

This article introduces [NotesWriting: Augmenting LLM Reasoning with Dynamic Notes Writing for Complex QA](https://arxiv.org/abs/2505.16293), a paper published on arXiv in May 2025 by [ServiceNow](https://www.servicenow.com/).

{{< admonition warning >}}
This paper does not present a particularly novel method. Instead, it highlights a simple and common technique: using an LLM to filter and consolidate all retrieved documents into a final, relevant summary. This addresses a common issue in Multi-Hop RAG where multiple retrieval steps can either exceed the LLM's context size limit or introduce excessive irrelevant information.
{{< /admonition >}}

## The Problem NotesWriting Addresses

In Multi-Hop Retrieval-Augmented Generation (RAG), an LLM must interleave multiple steps of retrieval and reasoning to arrive at a final answer. For example, to answer the question, "How many people attended the last international baseball game held in Taiwan?", the LLM first needs to retrieve information for "What was the last international baseball game held in Taiwan?". Only after finding that answer can it proceed to retrieve information for "How many people attended that specific game?".

However, when answering each sub-question, the LLM might retrieve a large volume of related documents. Placing all this information into the LLM's context can lead to two problems: exceeding its context window limit or degrading its performance in subsequent reasoning steps due to noise from irrelevant information.

Therefore, the problem this paper aims to solve is a primary challenge in the field of RAG: **how to extract essential information from retrieved documents while avoiding the inclusion of excessive unimportant or irrelevant information in the LLM's input context.** The paper specifically emphasizes that this issue is exacerbated in Multi-Hop RAG, where new documents are retrieved at each step, making the problem more severe.

## The NotesWriting Solution

{{< image src="notes-writing.png" caption="[Figure 1] The NotesWriting Method" >}}

As shown in the figure above, the NotesWriting method is very straightforward. In each reasoning step of the LLM-based agent, if a search/retrieval tool is used to fetch the top-K documents, an LLM performs "Note Extraction" on each document to pull out the most relevant information for the current question. Finally, "Note Aggregation" is used to consolidate all the extracted information.

The prompt for Note Extraction is as follows:
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

## Experimental Results of NotesWriting

In the experimental phase, the authors applied the NotesWriting method to three common Multi-Hop RAG baselines: [ReAct](https://arxiv.org/abs/2210.03629), [IRCoT](https://arxiv.org/abs/2212.10509), and [FLARE](https://arxiv.org/abs/2305.06983). The results are shown in Tables 1, 2, and 3 below.

{{< image src="exp-1.png" caption="[Table 1] NotesWriting + ReAct" >}}

{{< image src="exp-2.png" caption="[Table 2] NotesWriting + IRCoT" >}}

{{< image src="exp-3.png" caption="[Table 3] NotesWriting + FLARE" >}}

Although NotesWriting is an intuitive and simple method, these experimental results once again demonstrate that **Retrieved Document Refinement** is a crucial and highly effective technique in RAG systems.

{{< admonition info "Further Reading" >}}
If you're looking for a more comprehensive approach after reading about NotesWriting, we recommend exploring the classic paper on **Retrieved Document Refinement** in RAG: [Corrective Retrieval Augmented Generation](https://arxiv.org/abs/2401.15884). It's sure to provide many valuable insights!
{{< /admonition >}}

## Conclusion

This article has introduced the paper [NotesWriting: Augmenting LLM Reasoning with Dynamic Notes Writing for Complex QA](https://arxiv.org/abs/2505.16293). The goal of NotesWriting is to mitigate the performance degradation in Multi-Hop RAG caused by excessive irrelevant information entering the LLM's context after multiple retrieval steps. The method involves extracting notes from each retrieved document and then aggregating them to produce a concise and essential summary. This enhances the quality of the LLM's context, thereby boosting its overall performance.


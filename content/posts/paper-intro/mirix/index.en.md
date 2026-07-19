---
# weight: 1
title: "MIRIX: Multi-Agent Memory System for LLM-Based Agents"
date: 2025-07-17
lastmod: 2025-07-21
draft: false
description: "Explore MIRIX, a powerful new memory system for LLM-based agents. Learn how its unique 6-component architecture and multi-agent design achieve state-of-the-art results, outperforming methods like LangMem, Mem0, and MemGPT."
featuredImage: "featured-image.jpg"

tags: ["Large Language Model", "Multi-Agent", "Retrieval-Augmented Generation", "Agent Memory"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true
license: '<a rel="license external nofollow noopener noreffer" href="https://creativecommons.org/licenses/by-nc/4.0/" target="_blank">CC BY-NC 4.0</a>'

url: "paper-intro/:contentbasename"
---

<!--more-->

## Introduction

This article introduces the paper [MIRIX: Multi-Agent Memory System for LLM-Based Agents](https://arxiv.org/abs/2507.07957). As the title suggests, MIRIX is a paper related to LLM Memory, similar to [LangMem](../../other/langmem-intro/), [Mem0](../mem0/), and [MemGPT](../memgpt/) which we have previously discussed. The MIRIX paper was published on arXiv in July 2025. The authors have open-sourced the code on [GitHub](https://github.com/Mirix-AI/MIRIX), and you can also download the software developed based on this paper directly from the [official MIRIX website](https://mirix.io/).

Interestingly, the [official MIRIX website](https://mirix.io/) not only provides software downloads but also displays the benchmark results of multiple methods on LOCOMO and ScreenshotVQA. It's clear that the method proposed by MIRIX not only surpasses popular methods like [LangMem](../../other/langmem-intro/), [Mem0](../mem0/), and [Zep](https://github.com/getzep/zep) but is also one of the few methods that can support images as LLM Memory.

## The MIRIX Method Design

The design of the MIRIX method can be broadly divided into the following three aspects:

- Memory Component Design
- Memory Update Workflow
- Conversation Workflow

### Memory Component Design

{{< image src="memory-component.png" alt="Row of six labeled icons for MIRIX's memory components: Core Memory for user information and preferences always in context, Episodic Memory for events about the user, Semantic Memory for new concepts and names, Procedural Memory for step-by-step guides, Resource Memory for files and documents, and Knowledge Vault for addresses, phone numbers and credentials" caption="[Figure 1] The 6 Memory Components defined in MIRIX" >}}

As shown in the figure above, MIRIX defines a total of 6 Memory Components. These components appear to be a synthesis of the memory components designed in [LangMem](../../other/langmem-intro/) and [MemGPT](../memgpt/). For instance, [LangMem](../../other/langmem-intro/) also includes Episodic, Semantic, and Procedural Memory, while Core Memory and Resource Memory correspond to Core Memory and Archival Memory in [MemGPT](../memgpt/).

Here is a breakdown of the information stored in each Memory Component:

- **Core Memory**: Stores the most crucial information. Following the approach of [MemGPT](../memgpt/), Core Memory contains two sections: `persona` and `human`. The `persona` section holds the agent's identity, tone, and expected behavior, while the `human` section stores information about the user's identity.
- **Episodic Memory**: Stores timestamped events. Each entry consists of the following:
  - `event_type`: e.g., `user_message`, `inferred_result`, or `system_notification`
  - `summary`: A brief description of the event
  - `details`: A detailed description of the event
  - `actor`: The initiator of the event, can be `user` or `assistant`
  - `timestamp`: e.g., `2025-03-05 10:15`
- **Semantic Memory**: Stores established facts or general information. For example, "Harry Potter is written by J.K. Rowling" or "John is a friend of the user who enjoys jogging and lives in San Francisco." Information in Semantic Memory does not expire unless specifically removed or modified. Each entry consists of:
  - `name`
  - `summary`
  - `details`
  - `source`
- **Procedural Memory**: Stores information that helps the agent solve complex and specific tasks. For example, few-shot demonstrations or step-by-step instructions provided to the agent. Each entry consists of:
  - `entry_type`: Can be `workflow`, `guide`, or `script`
  - `description`: A description of the task to be completed
  - `steps`: Step-by-step instructions to complete the task
- **Resource Memory**: Stores all information required by the user that does not fall into any of the above categories. Each entry consists of:
  - `title`
  - `summary`
  - `resource_type`: e.g., `doc`, `markdown`, `pdf_text`, `image`, `voice_transcript`
  - `full content`/`excerpted content`
- **Knowledge Vault**: Stores confidential and sensitive information, such as the user's address, contact information, and API keys. Each entry consists of:
  - `entry_type`: e.g., `credential`, `bookmark`, `contact_info`, `api_key`
  - `source`: e.g., `user_provided`, `github`
  - `sensitivity`: `low`, `medium`, `high`
  - `secret_value`

### Memory Update Workflow

{{< image src="memory-update.png" alt="Sequence diagram of the MIRIX memory update workflow where user input is sent to a Meta Memory Manager that analyzes the content type and routes it to the relevant Memory Managers, which process the information and update the Memory Base, then confirmations flow back and an acknowledgement returns to the user" caption="[Figure 2] The Memory Update Workflow in MIRIX" >}}

The figure above illustrates how memory is updated in the MIRIX method. Based on the user's input, relevant information is first retrieved from the 6 Memory Components. The Meta Memory Manager then determines which Memory Component the current user input belongs to and assigns the update task to the corresponding Memory Manager.

### Conversation Workflow

{{< image src="conversation.png" alt="Sequence diagram of the MIRIX conversation workflow where a user query goes to a Chat Agent that analyzes the question, calls search_in_memory over the Memory Base to retrieve relevant results, optionally triggers urgent memory updates via the Memory Managers, and then synthesizes and generates the response" caption="[Figure 3] The Conversation Workflow in MIRIX" >}}

Once the MIRIX Agent has collected sufficient memory, it can begin to answer the user's questions based on that memory. The actual conversation process of the MIRIX Agent is shown in the figure above. Based on the user's input, relevant (but concise, not all details) information is first retrieved from the Memory Base across the 6 Memory Components. The Chat Agent then determines which Memory Component should handle the current input and triggers a "Conduct Specific Search" to retrieve more detailed and complete information from that specific component. Finally, it generates the final response based on this retrieved information. If the Chat Agent determines that the user's input requires a memory update, it can directly trigger the specific Memory Manager to update the relevant Memory Component.

## Experimental Results

In the experimental phase, the MIRIX paper used two datasets—ScreenshotVQA and LOCOMO.

ScreenshotVQA is a multimodal LLM memory dataset created for this paper. This benchmark includes 5886, 18178, and 5349 screen captures collected from 3 users over 1 day, 20 days, and 1 month, respectively, along with 11, 21, and 55 corresponding questions. LOCOMO, on the other hand, is a text-only LLM memory dataset, containing 600 conversations, with each conversation averaging 26K tokens and 200 corresponding questions.

For the evaluation metric, the authors designed an LLM-as-a-Judge method based on `GPT-4.1`. Additionally, the MIRIX Agent used `gemini-2.5-flash-preview-04-17` and `gpt-4.1-mini` as its backbone models for the ScreenshotVQA and LOCOMO datasets, respectively.

{{< image src="exp-1.png" alt="Table on ScreenshotVQA reporting accuracy and storage for three students and overall, comparing Gemini, SigLIP@50 and MIRIX, where MIRIX has the highest overall accuracy at 0.5950 while using only 15.89 MB of storage versus SigLIP's 15.07 GB" caption="[Table 1] MIRIX experimental results on ScreenshotVQA" >}}

{{< image src="exp-2.png" alt="Table on the LOCOMO benchmark reporting single-hop, multi-hop, open-domain, temporal and overall scores for memory systems like A-Mem, LangMem, Mem0, Zep and MIRIX under gpt-4o-mini and gpt-4.1-mini, where MIRIX leads with an overall 85.38, approaching the full-context upper bound of 87.52" caption="[Table 2] MIRIX experimental results on LOCOMO" >}}

From the experimental results above, it is clear that the MIRIX Agent achieved outstanding performance on both datasets!

## Conclusion

This article has introduced the LLM Memory method proposed in the [MIRIX](https://arxiv.org/abs/2507.07957) paper. After reading this paper, what impressed me the most was the 6 Memory Components defined in MIRIX. They cover almost every conceivable usage scenario and address the shortcomings in memory component design found in [LangMem](../../other/langmem-intro/), [Mem0](../mem0/), and [MemGPT](../memgpt/). As for the Memory Update Workflow and Conversation Workflow, I found them to be less novel. However, MIRIX's approach of designing a specific Memory Agent for each component has led to better performance than other baseline methods, suggesting that its [prompt design](https://github.com/Mirix-AI/MIRIX/tree/main/mirix/prompts/system) is likely worth studying.
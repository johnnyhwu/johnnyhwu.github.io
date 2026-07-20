---
# weight: 1
title: "GAIA: A Benchmark for General AI Assistants"
date: 2024-06-27
lastmod: 2025-07-27
draft: false
description: "Why do powerful AIs like GPT-4 struggle with tasks humans find easy? Dive into GAIA, the game-changing benchmark from Yann LeCun's team, and discover how it redefines the true capabilities of a General AI Assistant beyond standard tests. A must-read for anyone in AI."
featuredImage: "featured-image.png"

tags: ["Large Language Model", "Vision Language Model", "Fine-Tuning"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true
license: '<a rel="license external nofollow noopener noreffer" href="https://creativecommons.org/licenses/by-nc/4.0/" target="_blank">CC BY-NC 4.0</a>'

url: "paper-intro/:contentbasename"
---

<!--more-->

## Introduction

In a previous article on [ChatEval](../chateval/), I introduced the concept of LLM Agents and how a multi-agent framework can be used to have multiple LLM Agents debate and evaluate the outputs of other LLMs.

> However, is there a benchmark to measure the capabilities of a single agent?

Today, I want to share a paper from ICLR 2024, presented as a poster, titled [GAIA: A Benchmark for General AI Assistants](https://arxiv.org/abs/2311.12983). This paper proposes a benchmark specifically designed to measure the capabilities of a General AI Assistant! The reason I'm excited to share this paper is not just because it's interesting, but also because one of its authors is none other than Yann LeCun! Anyone in the AI field has heard of Yann LeCun, who recently had a [major debate with Elon Musk on X](https://x.com/ylecun/status/1797270661192155427?lang=en)...

{{< image src="author.png" alt="Title slide of the GAIA paper, showing the title 'GAIA: A Benchmark for General AI Assistants' and its authors Gregoire Mialon, Clementine Fourrier, Craig Swift, Thomas Wolf, Yann LeCun, and Thomas Scialom, affiliated with Meta FAIR, HuggingFace, AutoGPT, and Meta GenAI" caption="The authors of GAIA" >}}

## The Problem GAIA Benchmark Aims to Solve

With so many benchmarks already available to evaluate LLM Agents, why do we need another one like GAIA? What makes it different from the benchmarks we've been using? For instance, when Meta announced Llama 3, they used common benchmarks like MMLU, HumanEval, and GSM-8K to measure its LLM's performance:

{{< image src="llama3.png" alt="Table titled 'Meta Llama 3 Instruct model performance' comparing Llama 3 8B against Gemma 7B-It and Mistral 7B Instruct, and Llama 3 70B against Gemini Pro 1.5 and Claude 3 Sonnet, on MMLU, GPQA, HumanEval, GSM-8K, and MATH; Llama 3 8B scores 68.4/34.2/62.2/79.6/30.0 respectively, outperforming both smaller competitors, while Llama 3 70B scores 82.0/39.5/81.7/93.0/50.4, beating or matching Gemini Pro 1.5 and Claude 3 Sonnet on most benchmarks" caption="Benchmarks used for Llama-3" >}}

The problem GAIA aims to solve is the belief that while these existing benchmarks can measure an LLM's knowledge (or how "smart" it is), they don't fully align with the capabilities of a General AI Assistant. For example, here are two samples from the MMLU benchmark and one from the GSM8K benchmark:

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

From these examples, you can probably sense that if an LLM answers these questions well, we might think it's very smart (it knows everything). But does performing well on these questions mean we are closer to achieving a General AI Assistant? I believe the answer is a firm no.

The [GAIA paper](https://arxiv.org/abs/2311.12983) also points out that we often evaluate AI models (LLMs) using problems that are difficult even for humans, typically in specialized domains. However, the trend in recent years shows AI models achieving high scores on benchmarks like MMLU and GSM-8K, indicating that AI is becoming increasingly proficient at these specific, difficult tasks.

Furthermore, some current benchmarks for evaluating AI models (LLMs) are of the open-ended generation type. This means the questions don't have a single standard answer, or the answers require extensive text to describe. This leads to a situation where evaluating a model's performance on such a benchmark might require other AI models or humans to act as judges, making it impossible to check the output through rule-based methods.

However, it's also possible that these questions are ones that existing AI models or even humans can't answer. If that's the case, how can they be qualified to be judges?

## Introducing the GAIA Benchmark

Now that we understand the problem GAIA aims to solve, let's dive into what makes the GAIA benchmark unique. The benchmark consists of 466 question/answer pairs. Each question is text-based and sometimes comes with additional files (like images or CSV files).

The chart below shows the distribution of file types in the GAIA benchmark:

{{< image src="file-type.png" alt="Horizontal bar chart titled 'Distribution of File Types' listing file counts in the GAIA benchmark: xlsx 29, png 18, pdf 15, txt 13, mp3 7, jpg 7, csv 6, docx 2, pptx 2, zip 2, xml 2, and 1 each for py, json, m4a, pdb, MOV, and jsonld" caption="File types included in the GAIA Benchmark" >}}

The questions in GAIA can range from common workplace administrative tasks and scientific problems to general knowledge questions. The most important feature of GAIA is that every **answer is short, simple, and easily verifiable (to avoid ambiguity)**, yet arriving at that answer requires a wide range of fundamental skills. Specifically, an answer in GAIA is either a number, a string, or a list of strings, and there is only one correct answer.

Additionally, we can use a system prompt to tell the agent what format the answer should be in, which is very helpful for automated evaluation. For an AI model to score high on the GAIA benchmark, it must possess several capabilities:

- Advanced Reasoning
- Multi-Modality Understanding
- Coding Capability
- Tool Use

The figure below (left) shows the number of questions corresponding to each skill. It's clear that most questions cannot be answered directly from the AI model's existing knowledge; the model must learn to use web browsing to find the correct answer. The figure on the right shows how many different tools and steps are needed to answer questions of varying difficulty.

{{< image src="difficulty.png" alt="Two charts: a horizontal bar chart on the left titled 'Capabilities required to solve GAIA' showing web browsing needed for 355 questions, coding for 154, multi-modality for 138, diverse filetype reading for 129, and none for 32; a scatter plot on the right titled 'An overview of GAIA questions' plotting number of tools used (0-6) against number of steps taken (0-45), color-coded by difficulty Level 1-3, with most questions clustering at fewer than 15 steps and 1-3 tools" caption="Question difficulty in the GAIA Benchmark" >}}

Using the GAIA benchmark is also quite straightforward: you just use the official system prompt to perform zero-shot inference on the AI model. Below are the official system prompt and a sample question:

{{< image src="system-prompt.png" alt="Bordered box showing the system prompt used to evaluate models on GAIA: it instructs the assistant to answer as a general AI assistant and end with 'FINAL ANSWER: [YOUR FINAL ANSWER],' with formatting rules requiring numbers without commas or units, strings without articles or abbreviations, and comma-separated lists following the same rules per element" caption="System Prompt of GAIA Benchmark" >}}

{{< image src="question.png" alt="Example GAIA question in a bordered box: 'The attached Excel file contains the sales of menu items for a local fast-food chain. What were the total sales that the chain made from food (not including drinks)? Express your answer in USD with two decimal places,' accompanied by an attached file icon labeled uploaded.xlsx" caption="Sample Question in GAIA" >}}

Finally, the authors used the GAIA benchmark to evaluate the performance of several SOTA LLMs and humans:

{{< image src="exp.png" alt="Two-part bar chart titled 'LLMs, Human and Search engine scores and time to answer for GAIA': the top chart shows accuracy scores (%) at Level 1, 2, and 3 for a search engine, GPT-4, GPT-4 Turbo, AutoGPT-4, GPT-4 Plugins, and humans, with humans scoring above 85% at every level while the best model (GPT-4 Plugins) only reaches about 30% at Level 1 and 10% at Level 2; the bottom chart shows time to answer on a log scale, with AutoGPT-4 and humans taking the longest" caption="Performance of multiple SOTA LLMs on the GAIA Benchmark" >}}

We can see that even the powerful GPT-4 Turbo model only scored between 10-20 on Level 1 questions, and with human assistance, it barely reached 30. On Level 2 and 3 questions, these SOTA LLMs performed even worse. But did you notice? For Levels 1, 2, and 3, humans scored around 90%!

I think this is what makes the GAIA benchmark so fascinating—it designs tasks that are simple for humans but difficult for current AI models. It doesn't just test how much knowledge an AI model has memorized. It goes a step further to measure if the AI model can use tools, understand different data types, possess stronger reasoning abilities, and write simple code for analysis. When an AI model can perform well on the GAIA benchmark, it signifies that it is one step closer to becoming a General AI Assistant.

## Conclusion

In this article, I shared insights from the ICLR 2024 poster paper, [GAIA: A Benchmark for General AI Assistants](https://arxiv.org/abs/2311.12983). My journey with this paper began with "Oh, it's an ICLR paper" (sounds worth reading), then "Wow, it's published by Meta" (seems very interesting), and finally, "Yann LeCun is one of the authors!" (then I absolutely must read it!).

This paper proposes a benchmark to more accurately measure whether an AI model possesses the capabilities of a General AI Assistant. It cleverly designs its answers to avoid ambiguity, making it easier for us to evaluate the model's output using rule-based methods. Lastly, the experiments show that current SOTA AI models still perform poorly on this benchmark, whereas humans perform exceptionally well.
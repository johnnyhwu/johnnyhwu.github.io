---
# weight: 1
title: "Steering Large Language Models Between Code Execution and Textual Reasoning"
date: 2025-05-25
lastmod: 2025-05-25
draft: false
description: "Explore an ICLR 2025 paper on guiding Large Language Models (LLMs) between code execution and textual reasoning. Learn why models like GPT-4o may prefer text-based approaches, sometimes leading to errors, and how combining both reasoning methods yields the best performance."
featuredImage: "featured-image.jpg"

tags: ["Large Language Model", "Single-Agent"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true
license: '<a rel="license external nofollow noopener noreffer" href="https://creativecommons.org/licenses/by-nc/4.0/" target="_blank">CC BY-NC 4.0</a>'

url: "paper-intro/:contentbasename"
---

<!--more-->

## Introduction

This article introduces the paper "[Steering Large Language Models Between Code Execution and Textual Reasoning](https://openreview.net/forum?id=5X5Z7Ffrjb)", published on arXiv in October 2024 by researchers from MIT, Harvard, Microsoft, and Google DeepMind, and accepted by the ICLR 2025 conference. The impressive list of authors and the prestigious conference suggest this is a high-quality paper!

## The Problem This Paper Aims to Solve

As the title suggests, this paper seeks to address/explore the question:

> For a Large Language Model (LLM), is it better to reason using Code Execution or Textual Output?

For some Natural Language Processing (NLP) tasks, like generating summaries or engaging in dialogue, Textual Output reasoning is clearly more natural and effective. However, for tasks involving mathematics or logical inference, Code Execution reasoning can often lead to the correct answer more efficiently.

{{< image src="code-exec-is-better.png" alt="Two side-by-side chat examples (a) and (b): answering directly in text is marked wrong with a red X, such as claiming 9.11 is bigger than 9.9 or miscounting the positions of the letter r in strawberry, while the same questions answered by writing and running code are marked correct with a green check, correctly finding 9.9 is bigger than 9.11 and that r appears at positions 2, 7, and 8" caption="Code Execution Reasoning is better." >}}

For example, consider the two tasks shown above: "Which is larger, 9.11 or 9.9?" and "How many 'r's are in 'strawberry' and what are their positions?" These tasks are quite simple, yet GPT-4o provides incorrect answers when using Textual Output reasoning. In contrast, it easily gets them right using Code Execution.

{{< image src="code-exec-is-better-2.png" alt="Line chart titled Number Multiplying, all text answer, plotting success rate (%) against digit-count combinations from 2_2 to 16_16 for O1-preview, GPT-4o, GPT-4o-mini, and GPT-3.5-turbo; all models except O1-preview collapse to near 0% success by the 4_4 combination, while O1-preview stays above 50% until 8_8 before also dropping toward 0% by 12_12" caption="Code Execution Reasoning is better." >}}

As shown above, or when performing multiplication of two numbers where "2_3" means a 2-digit number multiplied by a 3-digit number, we find that as the number of digits increases, even OpenAI's O1-type models cannot answer correctly through more Textual Output reasoning.

Clearly, for LLMs, no single reasoning method can solve all problems. Sometimes Textual Output is more suitable, while other times Code Execution is better. Therefore, another question this paper addresses is:

> How can we guide LLMs to use the appropriate reasoning method (Textual Output vs. Code Execution) for the right tasks?

Besides answering these two questions, the paper also analyzes the differences in performance when using Textual Output versus Code Execution for reasoning across six LLMs (O1-preview, GPT-4o, GPT-4o-mini, GPT-3.5, Claude-sonnet, Mixtral-8x7b) on various tasks.

## OpenAI GPT-4o: Code Execution vs. Textual Output

OpenAI's GPT-4o defaults to Textual Output reasoning, but it can use Code Execution through its Code Interpreter Tool when necessary. The authors analyzed three models—GPT-4o, GPT-4o-mini, and GPT-3.5-turbo—to see whether they would choose Code Execution or Textual Output reasoning for two different tasks: Number Multiplying (calculating the product of two numbers) and Game 24 (given some numbers, select and output an equation that results in 24).

This experiment revealed:

{{< admonition tip Insight >}}
Larger models (like GPT-4o) tend to use Textual Output reasoning for tasks of moderate difficulty (not too hard, not too easy), which can lead to incorrect answers. Conversely, smaller models (like GPT-3.5-turbo) tend to use Code Execution reasoning for tasks of all difficulty levels, resulting in higher accuracy.
{{< /admonition >}}

{{< image src="gpt-4o-fail.png" alt="Three stacked chat panels: a simple question (12*56) is answered correctly in plain text, a hard question (124354536*5607425632) is answered correctly using code analysis, but a medium-difficulty question (1243*5607) is answered incorrectly in plain text as 6,969,801 (highlighted in red) when the correct answer is 6969501, illustrating GPT-4o's inconsistent arithmetic without code" caption="Example of GPT-4o making a mistake." >}}

As shown above, GPT-4o **confidently** uses Textual Output reasoning to correctly answer simple 2-digit multiplication. For very difficult multi-digit multiplication (the second example), GPT-4o knows to use Code Execution. However, in the third example, faced with a moderately difficult 4-digit multiplication, GPT-4o **still confidently** uses Textual Output reasoning and gets the **wrong** answer.

{{< image src="gpt-4o-exp-1.png" alt="Bar chart titled Number multiplying, Code Interpreter with three panels for GPT-4o, GPT-4o-mini, and GPT-3.5-turbo, showing the percentage of correct and incorrect answers with and without code across increasing digit-combination counts; accuracy with code stays near 100% while accuracy without code drops sharply as digit count grows" caption="[Figure 3] Performance of different models on Number Multiplying." >}}

{{< image src="gpt-4o-exp-2.png" alt="Bar chart titled Game 24, Code Interpreter with three panels for GPT-4o, GPT-4o-mini, and GPT-3.5-turbo, comparing correct and incorrect rates with and without code as the number of combined terms increases from 2 to 5; GPT-4o's with-code accuracy declines as terms increase while GPT-3.5-turbo's with-code accuracy stays consistently high, between about 80% and 98%" caption="[Figure 4] Performance of different models on Game 24." >}}

The two images above correspond to Figures 3 and 4 in the paper. The quantitative analysis clearly shows that GPT-4o tends to use Textual Output reasoning for simple tasks and Code Execution for clearly difficult tasks. However, for moderately difficult tasks, it still opts for Textual Output reasoning, leading to a higher error rate. In contrast, GPT-3.5-turbo uses Code Execution reasoning for tasks ranging from simple to difficult.

Since Number Multiplying and Game 24 are tasks well-suited for Code Execution reasoning, the smaller model (GPT-3.5-turbo) actually outperformed the larger model (GPT-4o).

What if we directly instruct the model in the prompt to use Code Execution reasoning? Would all models perform equally well? The authors conducted this experiment but found that:

{{< admonition tip Insight >}}
Requiring the model to use Code for reasoning in the prompt doesn't guarantee good results. The model might generate inefficient **code that resembles Textual Output**, leading to incorrect answers.
{{< /admonition >}}

{{< image src="text-like-code.png" alt="Two side-by-side code panels: on the left, GPT-3.5 Code Interpreter writes a correct Python program that searches permutations of operators to solve a Game-24-style puzzle; on the right, GPT-4o-mini Code Interpreter writes arithmetic expressions as prose-like text and repeatedly self-corrects yet never finds a valid equation equal to 24" caption="GPT-4o generating code that resembles Textual Output." >}}

As shown above, even when GPT-4o is asked to use Code Execution reasoning, it might be inherently confident that the task can be solved with Textual Output reasoning. This can result in code that still mimics textual thought processes, leading to an incorrect final result.

## Larger-Scale Experimental Analysis

To more thoroughly analyze and compare the performance of existing LLMs on Code Execution and Textual Output reasoning, the authors used 7 baseline methods with 6 LLMs, tested on 14 different tasks.

### Task Types

The 14 tasks are listed below:

- **Math**
  - Number Multiplying
  - Game 24
  - GSM-Hard
  - MATH-Geometry
  - MATH-Count&Probability
- **Logical Reasoning**
  - Date Understanding
  - Web of Lies
  - Logical Deduction
  - Navigate
- **Robot Planning**
  - BoxNet
  - Path Plan
- **Symbolic Calculation**
  - Letters
  - BoxLift
  - Blocksworld

These tasks can all be handled by Code Execution reasoning but vary in difficulty. Each task has over 300 test samples, so random variations in LLM output can be largely ignored. For a description of each task and its source paper, please refer to Appendix D of the original paper.

### Method Types

The 7 baseline methods are as follows:

- **Only Question**: Only the input question is provided.
- **All Text**: The prompt includes hints to make the LLM reason only with Textual Output.
- **All Code**: The prompt includes hints to make the LLM reason only with Code Execution.
- **All Code + CoT**: The prompt includes hints to make the LLM reason only with Code Execution using [Chain-of-Thought](https://arxiv.org/abs/2201.11903).
- **AutoGen Conca.**: The input question is concatenated with the [AutoGen](https://arxiv.org/abs/2308.08155) system prompt. AutoGen's System Prompt:
    ```text
    You are a helpful AI assistant. Solve tasks using your coding and language skills. In the
    following cases, suggest python code (in a python coding block) or shell script (in a sh coding
    block) for the user to execute. 1. When you need to collect info, use the code to output the
    info you need, for example, browse or search the web, download/read a file, print the content
    of a webpage or a file, get the current date/time, check the operating system. After sufficient
    info is printed and the task is ready to be solved based on your language skill, you can solve
    the task by yourself. 2. When you need to perform some task with code, use the code to
    perform the task and output the result. Finish the task smartly. Solve the task step by step if
    you need to. If a plan is not provided, explain your plan first. Be clear which step uses code,
    and which step uses your language skill. When using code, you must indicate the script type
    in the code block. The user cannot provide any other feedback or perform any other action
    beyond executing the code you suggest. The user can’t modify your code. So do not suggest
    incomplete code which requires users to modify. Don’t use a code block if it’s not intended
    to be executed by the user. If you want the user to save the code in a file before executing it,
    put # filename: filename inside the code block as the first line. Don’t include multiple code
    blocks in one response. Do not ask users to copy and paste the result. Instead, use ’print’
    function for the output when relevant. Check the execution result returned by the user. If the
    result indicates there is an error, fix the error and output the code again. Suggest the full code
    instead of partial code or code changes. If the error can’t be fixed or if the task is not solved
    even after the code is executed successfully, analyze the problem, revisit your assumption,
    collect additional info you need, and think of a different approach to try. When you find an
    answer, verify the answer carefully. Include verifiable evidence in your response if possible.
    Reply ”TERMINATE” in the end when everything is done.
    ```
- **AutoGen System**: Uses AutoGen's system prompt as the LLM's system prompt (LLMs do not use a system prompt by default).
- **Code Interpreter**: Allows the LLM to use a Code Interpreter.

### LLM Model Types

The 6 LLMs are as follows:

- **O1-preview**
- **GPT-4o**
- **GPT-4o-mini**
- **GPT-3.5-turbo-16k-0613 (GPT-3.5)**
- **Claude-3-sonnet-20240229 (Claude-sonnet)**
- **Open-mixtral-8x7b (Mixtral-8x7b)**

Apart from the GPT series LLMs, which offer a **Code Interpreter** function, the other LLMs do not. Therefore, they were not tested with the **Code Interpreter** method. O1-preview cannot have its system prompt changed, so the **AutoGen System** method is not applicable to O1-preview.

### Evaluation Metric

{{< image src="metric.png" alt="Mathematical formula for the AveNorm evaluation metric, defined as the average over N tasks of each method's score s_ij divided by the maximum score achieved on that task, max(s_i)" caption="Evaluation Metric" >}}

The authors used the **Average Normalized Score** as the score for each method. AveNorm<sub>\(j\)</sub> represents the final score of the \(j\)-th method, \(s_{ij}\) is the score of the \(j\)-th method on the \(i\)-th task, and max(\(s_i\)) is the maximum possible score for the \(i\)-th task.

### Experimental Results

{{< image src="exp.png" alt="Table listing task success rates (%) across baseline methods (Only Question, All Text, All Code, All Code+CoT, AutoGen Conca., AutoGen System, Code Interpreter) and proposed methods (Code Interpreter+, Code+Text+Sum., Self-estimate Score) over 14 tasks, broken out by GPT-4o, GPT-4o-mini, and O1-preview; Code+Text+Sum. achieves the highest average normalized scores for GPT-4o (88.2) and GPT-4o-mini (85.0)" caption="[Table 1] Experimental Results" >}}

From the experimental results in the table above, the authors derived 2 insights:

1. Among the 7 baseline methods, there is no single best method applicable to all tasks; different tasks are suited to different reasoning methods.
2. Using Code Execution reasoning is not always best. For some tasks, Textual Output reasoning yields better performance, primarily because:
   - Some tasks require consideration of too many aspects, and the LLM-generated code doesn't fully account for them.
   - Code restricts the tokens an LLM can output, thereby limiting the LLM's thinking process.

## Methods Proposed by This Paper

The authors propose 3 methods to improve LLM performance when using Textual Output or Code Execution reasoning:

- **Code Interpreter+**: Similar to the baseline method "All Code," this encourages the LLM to use Code Execution for reasoning (the paper doesn't clearly distinguish this method from the "All Code" baseline).
- **Code + Text + Sum.**: First, results are obtained using the "All Code" and "All Text" methods (based on Code Execution and Textual Output reasoning, respectively). Then, another LLM summarizes these two answers to produce a final answer. The prompt is as follows:

    ```text
    You are a helpful AI assistant. Solve tasks using your coding and language skills.

    In the following cases, there are two different agents respond to the same problem. In some
    cases, they output the direct answer, while sometimes they output the code to calculate the
    answer.

    I will display you the initial question and the answers from two agents. The code execution
    results will also be given if the code exists. Your task is to analyze this question based on the
    analysis and answers from above two agents and then output your final answer.

    If you want to generate code to acquire the answer, suggest python code (in a python coding
    block) for the user to execute. Don’t include multiple code blocks in one response, only
    include one in the response. Do not ask users to copy and paste the result. Instead, use
    ’print’ function for the output when relevant.

    I hope you can perform better than other two agents. Hence, try to choose the best answer
    and propose a new one if you think their methods and answers are wrong.
    ```

-   **Self-estimate Score**: The LLM is first asked to give a score for both Textual Output and Code Execution reasoning methods based on the current problem, indicating which method is more suitable. Then, the LLM is asked to reason according to the method with the higher score. The prompt is as follows:

    ```text
    You will be presented with a task that can potentially be solved using either pure textual
    reasoning or coding (or a combination of both). Your goal is to determine which method
    will be most effective for solving the task and figure out the answer. Follow these steps:

    1. **Estimate your confidence level** in solving the task using both approaches:
    - **Coding score (0-10)**: How confident are you that you can solve this task correctly by
    writing code? Provide reasoning.
    - **Text score (0-10)**: How confident are you that you can solve this task correctly by
    using textual reasoning? Provide reasoning.

    2. **Choose the approach** that you believe has the highest chance of success:
    - If one score is significantly higher, start with that approach.
    - If both scores are close, start with textual reasoning first, then decide if coding is necessary
    after.

    3. **Solve the task** using the chosen method:
    - If you chose coding, write the necessary code, explain the logic behind it, and run it.
    - If you chose textual reasoning, use detailed explanation and logical steps to reach the
    answer.

    4. **Reflect** after attempting the task:
    - Did the chosen approach work well? If not, should you switch to the other method?

    Now, here is the task:
    ```

## Experimental Results

{{< image src="exp2.png" alt="Table summarizing average normalized scores (%) across six models (GPT-4o, GPT-4o-mini, GPT-3.5, O1-preview, Claude-sonnet, Mixtral-8x7b) for baseline and proposed methods, with overall average score and average rank columns; the proposed Code+Text+Sum. method achieves the highest average score (79.5) and best average rank (2.50) among all methods" caption="[Table 2] Experimental Results" >}}

Both Table 1 and Table 2 show that **Code + Text + Sum.** performs the best among all methods. This suggests that instead of forcing an LLM to choose only Textual Output or Code Execution reasoning, allowing it to consider the results of both reasoning methods leads to the best performance.

## Conclusion

This article introduced an ICLR 2025 paper — [Steering Large Language Models Between Code Execution and Textual Reasoning](https://openreview.net/forum?id=5X5Z7Ffrjb) — which primarily focuses on understanding LLM choices and performance between Textual Output and Code Execution reasoning methods.

Here are the key takeaways from this paper:

- Larger models (like GPT-4o) tend to use Textual Output reasoning for tasks of moderate difficulty, which can lead to incorrect answers. Conversely, smaller models (like GPT-3.5-turbo) tend to use Code Execution reasoning for tasks of all difficulty levels, resulting in higher accuracy.
- Requiring a model to use Code for reasoning in the prompt doesn't guarantee good results; the model might generate inefficient code that resembles Textual Output, leading to incorrect answers.
- Some tasks are better suited for Textual Output reasoning, while others are better for Code Execution; there's no absolute best method.
- When an LLM uses Code Execution for reasoning, it might perform poorly due to two reasons:
  - Some tasks involve too many aspects, and the LLM-generated code doesn't fully consider them.
  - Code restricts the tokens an LLM can output, thereby limiting its thinking process.
- Allowing an LLM to summarize a final answer based on the results of both reasoning methods yields the best performance.

For a concrete example of code execution outperforming pure textual reasoning on structured data, see [EHRAgent](../ehragent-code-empowers-large-language-models-for-few-shot-complex-tabular-reasoning-on-electronic-health-records/), which wraps database operations as Python functions so the LLM can reliably query tabular EHR data through code instead of reasoning about it in text.

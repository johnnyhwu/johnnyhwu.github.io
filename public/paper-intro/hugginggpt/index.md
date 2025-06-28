# [論文介紹] HuggingGPT: Solving AI Tasks with ChatGPT and its Friends in Hugging Face


<!--more-->

## 前言

最近 (2025/01) 由於 DeepSeek-R1 的模型 ([Paper](https://arxiv.org/abs/2501.12948), [GitHub](https://github.com/deepseek-ai/DeepSeek-R1)) 釋出，在 AI 學術與產業界都引發了很大的討論，竟然有辦法用如此低的訓練成本打造[媲美 OpenAI o1](https://github.com/deepseek-ai/DeepSeek-R1?tab=readme-ov-file#deepseek-r1-evaluation) 的模型。

許多 AI 公司巨頭 (ex. [OpenAI](https://www.youtube.com/watch?v=xXCBz_8hM9w), [Claude](https://hackernoon.com/whats-next-for-ai-interpreting-anthropic-ceos-vision)) 更是開始推測 AGI 可能會在最近 3 年到來！

AGI 具體什麼時間出現以及具備什麼樣的能力，現在想起來都還有點模糊。我們倒不如回過頭來看看前兩年的一篇 Single Agent 經典論文 — [HuggingGPT: Solving AI Tasks with ChatGPT and its Friends in Hugging Face](https://proceedings.neurips.cc/paper_files/paper/2023/file/77c33e6a367922d003ff102ffb92b658-Paper-Conference.pdf)，來想像未來 AGI 該有的樣子！

HuggingGPT 是由 Zhejiang University 以及 Microsoft Research Asia 共同發表，被 NeurIPS 2023 Poster 所接受。截至 2025/01/27，[HuggingGPT 的 Citation](https://scholar.google.com/scholar_lookup?arxiv_id=2303.17580) 來到了 1029 次。雖然沒有 Attention Is All You Need (150520 Citations) 以及 Chain-of-Thought (9831 Citations) 這麽誇張，但是 HuggingGPT 在 [LLM Agent 的研究領域也算是 Must-Read](https://github.com/WooooDyy/LLM-Agent-Paper-List#:~:text=%5B2023/03%5D%20HuggingGPT%3A%20Solving%20AI%20Tasks%20with%20ChatGPT%20and%20its%20Friends%20in%20Hugging%20Face.%20Yongliang%20Shen%20(Microsoft%20Research%20Asia)%20et%20al.%20arXiv.%20%5Bpaper%5D%20%5Bcode%5D) 呢！

## HuggingGPT 想解決的挑戰

本篇論文想處理的挑戰：

- LLM 只接受文字作為輸入和輸出，將會限制其處理視覺或語音相關的任務
- 有些比較複雜的任務底下還包含很多子任務，需要讓 LLM 作為 Coordinator  來支配其他 Model 才有辦法完成
- LLM 雖然在多數領域上都有 Zero-Shot Capabilities, 但是如果和 Domain Expert (ex. Specialized Model) 比起來, 能力上還是有落差

## HuggingGPT 的方法概念

{{< image src="hugginggpt-concept.png" caption="Figure 1: An LLM (e.g., ChatGPT) acts as a controller, coordinating expert models (e.g., Hugging Face) to solve complex AI tasks by planning, assigning, executing, and responding." >}}

本篇論文所提出的 HuggingGPT 方法，就是希望可以讓 LLM 作為 Coordinator (Controller)，使用其他外部的 Model/Tool/Domain Expert 來完成更複雜的任務。HuggingGPT 的概念如 Figure 1 所示，主要是把 LLM 作為 Controller，進行 Task Planning, Model Selection, Task Execution 和 Response Generation。

## HuggingGPT #1 Step: Task Planning

{{< image src="hugginggpt-prompt.png" caption="Table 1: Details of HuggingGPT's prompt design, featuring injectable slots like {{ Demonstrations }} and {{ Candidate Models }} replaced with corresponding text before input to the LLM." >}}

在 Task Planning 階段的重點就是要透過 LLM 分析 User 的 Query，將其拆解為多個 Structured Task，且包含這些 Task 的 Execution Order 或是 Dependency，最終輸出一個 Task List。為了使 LLM 能夠做好 Task Planning，在這個階段的 Prompt Design 也相當重要。

作者特別提到，使用了兩種技巧在這個階段的 Prompt 中：**Specification-based Instruction** 和 **Demonstration-based Parsing**。

如 Table 1 中 Task Planning 階段的 Prompt 所示，Specification-based Instruction 的概念就是告訴 LLM 應該要如何進行 Task Parsing：「每一個 Task 都會由一個 Json 來表示，這個 Json 包含了 4 個 Slot， 包含 "task", "id", "dep" 和 "args"。此外，Json 中還會有 "dep" 的欄位，來表示 Task 之間的 Dependency 關係」。而 Demonstration-Based Parsing 則是善用 In-Context Learning 的技巧，讓 LLM 根據 Demonstration 學習做 Task Parsing。

在整個 Task Planning 階段的 Prompt 中，讓我覺得最有趣的地方是 "Chat Logs" 的部分。可以發現到作者在 Prompt 中加入了 Chat Logs，讓 LLM 在進行 Task Planning 時可以參考過去 User 和 Assistant 之間的互動，而不只是直接針對 User 的最新 Query。

如此一來，我相信如果 LLM 本身的能力 (智商) 夠好的話，是有辦法透過考慮更多 Context，避免由於 User 單一個 Query 中所存在的的 Ambiguity 或是 Incompleteness，而做出不正確的 Task Planning。

{{< image src="prompt-slot.png" caption="Table 9: Definitions for each slot for parsed tasks in the task planning." >}}
{{< image src="tasks.png" caption="Table 13: Task list, arguments, examples, and model descriptions in HuggingGPT." >}}

在 Table 9 中也可以看到每一個 Slot 的意義；在 Table 13 中也有呈現所有 HuggingGPT  支援的 Task ("Available Task List")。

## HuggingGPT #2 Step: Model Selection

Model Selection 階段就是要針對 Task Planning 階段的輸出 (Task List) 中的每一個 Task 選擇「一個」 最適合的 Model。 從 Table 1 可以看到 Model Selection 階段的 Prompt 會包含 Model Candidates。由於 LLM 具有 Context Limitation，我們不可能把所有 Model Candidates 都塞到 Prompt 中 ，因此作者會事先根據目前的 Task Type 進行篩選，再根據篩選後的結果選擇 Top-K 放到 Prompt 中作為 Model Candidates。

## HuggingGPT #3 Step: Task Execution

在 Task Execution 階段中，最重要的問題就是 Resource Dependency，也就是在執行這個 Task 之前應該先執行哪一個 Task。為了處理這個問題，HuggingGPT 在 Task Planning 階段，就會讓 LLM 生成的 Task List 中的 "arg" 指定 `<resource>-task_id` (ex. `<resource>-0`)，用來表示目前這個 Task 的 Argument 要來自哪一個 Task 的輸出。

## HuggingGPT #4 Step: Response Generation

從 Table 1 中 Response Generation 階段的 Prompt，可以看到主要是讓 LLM 根據前面所有階段的資訊，來產生最後的 Final Answer。

我覺得在這個階段的 Prompt 寫法 (ex. "You must first answer the user’s request in a straightforward manner. Then describe the task process and show your analysis and model inference results to the user in the first person.") 就蠻值得學習的！在之前 Chat-like Agent 的開發經驗中，深刻體會到 Response Generation 階段的 Prompt，會大大的影響 Response 的 Style 而進而影響到 User 的體驗。

## 實驗結果

在實驗設定中，作者使用 3 種 LLM 作為 HuggingGPT 的 Backbone：gpt-3.5-turbo, text-davinci-003, gpt-4，並將 Temperature 設定為 0 來確保 LLM 的輸出穩定，此外，**為了確保 LLM 更能夠輸出 JSON Format，針對 "{" 和 "}" 這兩個 Token 的 logit\_bias 設定為 0.2**。

{{< admonition info >}}
logit\_bias 是什麼？其實它的原理也超簡單！

在 LLM 的 Decoding 階段，可以基於 LLM 對每一個 Token 的 Predicted Logit (在 Softmax 之前) 加上或減去一個特別的數值，來影響一個 Token 被 Sample 到的機率大小。而這個特別的數值可以因 Token 不同而有所不同，而且是作用在 Logit 上，因此又稱為 Logit Bias。

舉例來說，如果我們不希望 LLM 生成不好的 Token (ex. stupid)，那就可以針對這個 Token 設定一個負值 (ex. -0.5) 的 logit\_bias。那麼在 Decoding 階段時，就會針對 stupid 這個 Token 加上這個 Logit Bias (-0.5)，使其 Logit 變得更小，讓 Softmax 後的結果也變小，這個 Token 被 Sample 到的機率也就更小。
{{< /admonition >}}

理解完 HuggingGPT 的方法後，可想而知的是 Task Planning 階段是整個 HuggingGPT 方法是否有辦法表現好的關鍵。因此，我們先來看看 HuggingGPT 進行 Task Planning 的實際例子：

從 Figure 1 可以看到 User 的 Query 中包含了 2 個 Sub-Task (Describe the Image & Object Counting)，而 LLM 將其轉為 3 個 (Image Classification, Image Captioning & Object Detection) Sub-Task。

{{< image src="hugginggpt-demo.png" caption="Figure 2: Overview of HuggingGPT's workflow with an LLM as the controller and expert models as executors." >}}

而從 Figure 2 也可以看到 User 的 Query 包含了 3 個 Sub-Task：

- Detecting the pose of a person in an example image
- Generating a new image based on that pose and specified text
- Creating a speech describing the image

而 LLM 將其轉為了 6 個 Sub-Task：

- Pose detection -> Text-to-image conditional on pose
- Object detection
- Image classification
- Image captioning -> Text-to-speech

看完了實際的範例後，作者也透過 Quantitative Approach 來分析 HuggingGPT 在 Task Planning 的能力。

{{< image src="task-type.png" caption="Table 2: Evaluation for task planning in different task types." >}}

如 Table 2 所示，三種常見的 Planning Task 有 Single Task (Single-Hop), Sequential Task (Multi-Hop) 以及 Graph Task (Mulit-Hop)。

{{< image src="exp-1.png" caption="Table 3: Evaluation for the single task. “Acc” and “Pre” represents Accuracy and Precision." >}}

{{< image src="exp-2.png" caption="Table 4: Evaluation for the sequential task. “ED” means Edit Distance." >}}

{{< image src="exp-3.png" caption="Table 5: Evaluation for the graph task." >}}

Table 3, 4, 5 分別呈現 HuggingGPT 在這 3 種 Planning Task 上的表現。可以非常明顯地觀察到，在當時的時代 GPT-3.5 可以說是完勝其他 Open-Sourced Model。從 Table 3, 4, 5 的實驗中其實也可以發現到，在 HuggingGPT 的做法中，基本上是完全仰賴 LLM 本身的能力來進行 Task Planning，除了 Specification-based Instruction 和 Demonstration-based Parsing 技巧外，HuggingGPT 並沒有提出什麼特別的方法來提升 Task Planning 能力。

## 結語

在本篇文章中，我們介紹了一個 Single Agent 方法 — [HuggingGPT](https://arxiv.org/abs/2303.17580) (NeurIPS 2023 Poster)。

HuggingGPT 的核心概念是透過 LLM 本身強大的推理能力作為 Controller/Coordinator 來進行 Task Planning，每個 Task 中都會使用到相對應的 Model/Tool。再透過後續的 Model Selection, Task Execution 以及 Response Generation 來得到最終的答案。

我個人覺得 HuggingGPT 的方法雖然不難，但它的貢獻在於提出了一個 Single Agent Framework (ex. 應該包含哪寫 Step, 每個 Step 的 Output 要長怎樣, 每個 Step 的 Prompt/Instruction 該怎麼寫)。且還是在 ChatGPT 剛問世不久（ChatGPT 推出的時間為 2022/11/30，而 HuggingGPT 發布的時間在 2023/03），就成功地將 LLM 作為 Controller/Coordinator，來進行 Task Planning 與 Tool Usage 進而處理更複雜的任務!


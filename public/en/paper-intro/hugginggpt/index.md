# HuggingGPT: Solving AI Tasks with ChatGPT and its Friends in Hugging Face


<!--more-->

## Introduction

Recently (2025/01), the release of the DeepSeek-R1 model ([Paper](https://arxiv.org/abs/2501.12948), [GitHub](https://github.com/deepseek-ai/DeepSeek-R1)) sparked significant discussion in both the AI academic and industry fields. It demonstrated the feasibility of creating a model [comparable to OpenAI o1](https://github.com/deepseek-ai/DeepSeek-R1?tab=readme-ov-file#deepseek-r1-evaluation) with such low training costs.

Many AI industry giants (ex. [OpenAI](https://www.youtube.com/watch?v=xXCBz_8hM9w), [Claude](https://hackernoon.com/whats-next-for-ai-interpreting-anthropic-ceos-vision)) have even begun speculating that AGI might arrive in the next 3 years!

Exactly when AGI will appear and what capabilities it will possess still feel a bit vague at the moment. Instead, let's revisit a classic Single Agent paper from the past two years — [HuggingGPT: Solving AI Tasks with ChatGPT and its Friends in Hugging Face](https://proceedings.neurips.cc/paper_files/paper/2023/file/77c33e6a367922d003ff102ffb92b658-Paper-Conference.pdf), to envision what future AGI might look like!

HuggingGPT was jointly published by Zhejiang University and Microsoft Research Asia and was accepted as a NeurIPS 2023 Poster. As of 2025/01/27, [HuggingGPT's Citation count](https://scholar.google.com/scholar_lookup?arxiv_id=2303.17580) has reached 1029. While not as exaggerated as Attention Is All You Need (150520 Citations) or Chain-of-Thought (9831 Citations), HuggingGPT is considered a [Must-Read in the LLM Agent research field](https://github.com/WooooDyy/LLM-Agent-Paper-List#:~:text=%5B2023/03%5D%20HuggingGPT%3A%20Solving%20AI%20Tasks%20with%20ChatGPT%20and%20its%20Friends%20in%20Hugging%20Face.%20Yongliang%20Shen%20(Microsoft%20Research%20Asia)%20et%20al.%20arXiv.%20%5Bpaper%5D%20%5Bcode%5D)!

## Challenges HuggingGPT Aims to Solve

The challenges addressed in this paper:

*   LLMs only accept text as input and output, which limits their ability to handle vision or speech-related tasks.
*   Some more complex tasks include many subtasks, requiring the LLM to act as a Coordinator to manage other Models to complete them.
*   Although LLMs have Zero-Shot Capabilities in most domains, there is still a gap in capability compared to Domain Experts (ex. Specialized Models).

## HuggingGPT's Method Concept

{{< image src="hugginggpt-concept.png" caption="Figure 1: An LLM (e.g., ChatGPT) acts as a controller, coordinating expert models (e.g., Hugging Face) to solve complex AI tasks by planning, assigning, executing, and responding." >}}

The HuggingGPT method proposed in this paper aims to allow the LLM to act as a Coordinator (Controller), using other external Models/Tools/Domain Experts to complete more complex tasks. HuggingGPT's concept, as shown in Figure 1, primarily positions the LLM as the Controller responsible for Task Planning, Model Selection, Task Execution, and Response Generation.

## HuggingGPT #1 Step: Task Planning

{{< image src="hugginggpt-prompt.png" caption="Table 1: Details of HuggingGPT's prompt design, featuring injectable slots like {{ Demonstrations }} and {{ Candidate Models }} replaced with corresponding text before input to the LLM." >}}

The key in the Task Planning stage is to analyze the User's Query using the LLM, decompose it into multiple Structured Tasks, including their Execution Order or Dependency, and finally output a Task List. To enable the LLM to perform Task Planning effectively, the Prompt Design at this stage is also crucial.

The authors specifically mention using two techniques in the prompt for this stage: **Specification-based Instruction** and **Demonstration-based Parsing**.

As shown in the Task Planning stage Prompt in Table 1, the concept of Specification-based Instruction is to tell the LLM how to perform Task Parsing: "Each Task will be represented by a Json, which includes 4 slots: 'task', 'id', 'dep', and 'args'. In addition, the Json will have a 'dep' field to represent the Dependency relationship between Tasks." Demonstration-Based Parsing, on the other hand, leverages the technique of In-Context Learning, allowing the LLM to learn Task Parsing based on Demonstrations.

In the entire Task Planning stage Prompt, the part that I found most interesting is the "Chat Logs" section. It can be observed that the authors included Chat Logs in the Prompt, allowing the LLM to refer to past interactions between the User and the Assistant during Task Planning, instead of just responding directly to the User's latest Query.

This way, I believe if the LLM's own capability (intelligence) is good enough, it can make more accurate Task Planning by considering more Context, avoiding errors due to the Ambiguity or Incompleteness in a single User Query.

{{< image src="prompt-slot.png" caption="Table 9: Definitions for each slot for parsed tasks in the task planning." >}}
{{< image src="tasks.png" caption="Table 13: Task list, arguments, examples, and model descriptions in HuggingGPT." >}}

Table 9 also shows the meaning of each Slot; Table 13 presents all Tasks supported by HuggingGPT ("Available Task List").

## HuggingGPT #2 Step: Model Selection

The Model Selection stage is to select "one" most suitable Model for each Task in the output of the Task Planning stage (Task List). As seen in Table 1, the Prompt for the Model Selection stage will include Model Candidates. Due to LLM's Context Limitation, we cannot put all Model Candidates into the Prompt. Therefore, the authors will pre-filter based on the current Task Type and then select the Top-K based on the filtered results to include in the Prompt as Model Candidates.

## HuggingGPT #3 Step: Task Execution

In the Task Execution stage, the most critical problem is Resource Dependency, which means which Task should be executed before the current Task. To handle this problem, HuggingGPT designates `<resource>-task_id` (ex. `<resource>-0`) in the "arg" field of the Task List generated by the LLM during the Task Planning stage, indicating which Task's output should serve as the Argument for the current Task.

## HuggingGPT #4 Step: Response Generation

From the Prompt for the Response Generation stage in Table 1, it can be seen that it primarily asks the LLM to generate the final Answer based on information from all previous stages.

I think the way the Prompt is written in this stage (ex. "You must first answer the user’s request in a straightforward manner. Then describe the task process and show your analysis and model inference results to the user in the first person.") is quite worth learning! In my previous experience developing Chat-like Agents, I deeply realized that the Prompt in the Response Generation stage significantly affects the Response Style, thereby influencing the User's experience.

## Experimental Results

In the experimental setup, the authors used 3 LLMs as the Backbone for HuggingGPT: gpt-3.5-turbo, text-davinci-003, gpt-4, and set the Temperature to 0 to ensure stable output from the LLM. Furthermore, **to ensure the LLM is better able to output JSON Format, the logit\_bias for the tokens "{" and "}" was set to 0.2**.

{{< admonition info >}}
What is logit\_bias? Its principle is actually super simple!

During the Decoding stage of an LLM, a specific value can be added to or subtracted from the LLM's Predicted Logit for each Token (before Softmax) to influence the probability of a Token being Sampled. This specific value can differ for different Tokens and acts on the Logit, hence it is called Logit Bias.

For example, if we don't want the LLM to generate bad Tokens (ex. stupid), we can set a negative value (ex. -0.5) as the logit\_bias for this Token. Then, during the Decoding stage, this Logit Bias (-0.5) will be added to the logit for the "stupid" Token, making its Logit smaller. This also makes the result after Softmax smaller, and the probability of this Token being Sampled becomes smaller.
{{< /admonition >}}

After understanding HuggingGPT's method, it is conceivable that the Task Planning stage is the key to whether the entire HuggingGPT method can perform well. Therefore, let's first look at a practical example of HuggingGPT performing Task Planning:

Figure 1 shows that the User's Query includes 2 Sub-Tasks (Describe the Image & Object Counting), which the LLM converts into 3 Sub-Tasks (Image Classification, Image Captioning & Object Detection).

{{< image src="hugginggpt-demo.png" caption="Figure 2: Overview of HuggingGPT's workflow with an LLM as the controller and expert models as executors." >}}

Figure 2 also shows that the User's Query includes 3 Sub-Tasks:

*   Detecting the pose of a person in an example image
*   Generating a new image based on that pose and specified text
*   Creating a speech describing the image

The LLM then converts these into 6 Sub-Tasks:

*   Pose detection -> Text-to-image conditional on pose
*   Object detection
*   Image classification
*   Image captioning -> Text-to-speech

After reviewing the practical examples, the authors also used a Quantitative Approach to analyze HuggingGPT's Task Planning capability.

{{< image src="task-type.png" caption="Table 2: Evaluation for task planning in different task types." >}}

As shown in Table 2, three common Planning Tasks are Single Task (Single-Hop), Sequential Task (Multi-Hop), and Graph Task (Mulit-Hop).

{{< image src="exp-1.png" caption="Table 3: Evaluation for the single task. “Acc” and “Pre” represents Accuracy and Precision." >}}

{{< image src="exp-2.png" caption="Table 4: Evaluation for the sequential task. “ED” means Edit Distance." >}}

{{< image src="exp-3.png" caption="Table 5: Evaluation for the graph task." >}}

Tables 3, 4, and 5 respectively show HuggingGPT's performance on these 3 types of Planning Tasks. It is very evident that, at that time, GPT-3.5 completely outperformed other Open-Sourced Models. From the experiments in Tables 3, 4, and 5, it can also be observed that in HuggingGPT's approach, the Task Planning largely relies solely on the LLM's own capability. Besides Specification-based Instruction and Demonstration-based Parsing techniques, HuggingGPT did not propose any special method to enhance Task Planning capability.

## Conclusion

In this article, we introduced a Single Agent method — [HuggingGPT](https://arxiv.org/abs/2303.17580) (NeurIPS 2023 Poster).

The core concept of HuggingGPT is to use the LLM's powerful reasoning ability as a Controller/Coordinator for Task Planning, where each Task utilizes a corresponding Model/Tool. Then, through subsequent Model Selection, Task Execution, and Response Generation, the final answer is obtained.

Personally, I think HuggingGPT's method is not complex, but its contribution lies in proposing a Single Agent Framework (ex. what steps it should include, what the output of each step should look like, how to write the Prompt/Instruction for each step). Moreover, it successfully used the LLM as a Controller/Coordinator for Task Planning and Tool Usage to handle more complex tasks shortly after ChatGPT was released (ChatGPT was released on 2022/11/30, and HuggingGPT was published in 2023/03)!

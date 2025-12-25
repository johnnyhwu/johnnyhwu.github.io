---
# weight: 1
title: "rStar Deep Dive: How MCTS & Mutual Reasoning Boost LLaMA2-7B Accuracy from 12% to 64% Without Fine-tuning"
date: 2025-12-10
lastmod: 2025-12-25
draft: false
description: "Discover how Microsoft Research Asia's rStar architecture boosts Small Language Model (SLM) reasoning without fine-tuning or GPT-4. Learn about MCTS, Mutual Reasoning, and how LLaMA2-7B's math accuracy jumped to 63.91% in this deep dive into the ICLR 2025 paper."
featuredImage: "featured-image.jpg"

tags: ["Large Language Model", "Test-Time Scaling"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## Introduction

This article shares a fascinating paper resulting from a collaboration between Microsoft Research Asia and Harvard University: **[Mutual Reasoning Makes Smaller LLM Stronger Problem-Solvers (rStar)](https://arxiv.org/abs/2408.06195)**. Published in August 2024, this paper has been successfully accepted as an **ICLR 2025 Poster**!

In the evolution of Large Language Models (LLMs), we have often believed that to improve the reasoning capabilities of Small Language Models (SLMs, e.g., LLaMA2-7B), we must rely on data distillation from stronger models (like GPT-4) for Supervised Fine-Tuning (SFT). However, this paper proposes a disruptive perspective: **Small models actually possess sufficient potential; they simply lack the correct "guidance for thinking" and "self-verification" mechanisms.**

The authors propose an architecture called **rStar**, which combines **MCTS (Monte Carlo Tree Search)** with a unique **Mutual Reasoning** mechanism. Impressively, **without any fine-tuning and without relying on GPT-4**, simply through algorithmic enhancement during the inference phase, LLaMA2-7B's accuracy on the GSM8K math dataset skyrocketed from **12.51% to 63.91%**. It even allowed Mistral-7B to surpass many models that had undergone specialized fine-tuning.

Next, we will delve into how rStar unlocks the deep reasoning capabilities of small models by imitating human thinking actions (Action Space) and utilizing a peer-like checking mechanism (Discriminator).

## The Problem rStar Aims to Solve

Broadly speaking:

> How can Small Language Models (SLMs) significantly improve their reasoning capabilities without relying on data distillation from stronger models (like GPT-4)?

We can categorize the problems rStar aims to solve into three levels:

### Macro Challenge: The Reasoning Bottleneck of Small Models and Reliance on "Teachers"
*   **Current Status:** Small parameter language models (SLMs, e.g., Mistral-7B, LLaMA2-7B) perform far worse than large models on complex reasoning tasks (like GSM8K math problems). Even with Chain-of-Thought (CoT), accuracy remains limited (e.g., Mistral-7B is only at 36.5%).
*   **The Problem:** The current mainstream method for improving SLM reasoning is **Fine-tuning**, but this usually relies on "stronger models" (like GPT-4) to generate high-quality synthetic data or for knowledge distillation.
*   **The Goal:** The paper aims to break this dependency and achieve **"Reasoning improvements without a superior teacher LLM."** This means enabling the model to improve its capabilities through **Self-play** during **Inference-time**, without additional training or external supervision.

### Technical Challenge I: "Ineffective Exploration" during Generation
When models attempt self-improvement (e.g., using methods like RAP for tree search), they face the following difficulties:
*   **Search Space Traps:** SLMs have limited capabilities. If simply asked to "generate the next step," they often wander within a low-quality reasoning space. The paper mentions that even when LLaMA2-7B uses the RAP method to explore 32 rounds, only 24% of the trajectories are correct.
*   **Monotonous Action Space:** When traditional MCTS is applied to LLMs, the actions are often very singular (e.g., "propose the next sub-question"). This limits the model's ability to simulate diverse human reasoning strategies (such as decomposing problems, rephrasing questions, single-step vs. multi-step reasoning, etc.).

### Technical Challenge II: "Unreliable Verification" during Validation
Even if the model generates multiple reasoning paths, selecting the correct one is a major issue:
*   **Difficulty of Self-Verification:** Research shows that SLMs struggle to accurately assess whether their own generated answers are correct (Self-verification is hard). Models often cannot distinguish between high-quality and low-quality reasoning steps.
*   **Limitations of Majority Voting:** Traditional Self-Consistency (SC) relies on "Majority Voting," which assumes the model is correct most of the time. However, on difficult problems, an SLM might generate wrong answers the majority of the time, causing majority voting to fail.
*   **Cost of Reward Models:** Training a specialized Reward Model (RM) brings us back to the problem of needing labeled data or external supervision, and it is prone to overfitting specific tasks.

**In summary:**

The core pain point this paper addresses is:

> Small models can't come up with good ideas during "generation," and can't distinguish right from wrong during "checking."

rStar attempts to solve these two problems by improving the Action Space of MCTS (making generation more human-like) and introducing "Mutual Reasoning" (having another peer model verify).

## The Method Proposed by rStar

{{< image src="solution.png" caption="rStar's Self-Play Mutual Reasoning consists of Generation-Discrimination" >}}

The **rStar** method proposed in this paper can be summarized as follows:

> rStar is like letting a small model "play two roles." One role (called the **Generator**) uses diverse thinking strategies imitating humans (like decomposing problems, rephrasing) to generate solution paths. The other role (called the **Discriminator**) acts like a classmate, checking these paths through "fill-in-the-blank tests." Through mutual verification (Self-play), they significantly improve reasoning accuracy without retraining.

---

Understanding **MCTS (Monte Carlo Tree Search)** is key to understanding the technical details of this paper. The core skeleton of rStar is built upon MCTS. Therefore, we will start with the basic concepts of MCTS and then explain how rStar designs methods for each stage of MCTS.

---

### Basic Concepts of MCTS (Four Stages)

MCTS is a heuristic search algorithm that first shone in board games like Go (e.g., AlphaGo). Its core idea is:

> Since there are too many possible paths, I cannot calculate them all. So, I use "random simulations" to estimate winning rates and focus computational resources on the "most promising" paths.

In this paper, MCTS is used to help the **Generator** produce reasoning steps. The **Root** of the tree is the question, **Nodes** are intermediate reasoning steps, and **Edges** are the actions taken.

One Iteration of MCTS includes the following four standard stages:

1.  **Selection:**
    *   **What it does:** Starting from the root, traverse down the tree until reaching a node that hasn't been fully expanded (a Leaf node).
    *   **How to select:** This step isn't random; it uses a formula (usually **UCT**, Upper Confidence Bound for Trees). This formula balances two things:
        *   **Exploitation:** Going down the path that currently looks to have the highest score/winning rate.
        *   **Exploration:** Going down a path rarely traveled, as better answers might hide there.
    *   **Significance:** Ensures we focus on the current best solution without giving up on exploring unknown possibilities.

2.  **Expansion:**
    *   **What it does:** Once "Selection" reaches a leaf node, if the node can continue to be deduced, we create one or more new Child Nodes.
    *   **Significance:** In rStar, this means the model takes a new **reasoning action** (like decomposing the problem, generating the next step) based on the current reasoning state, growing new reasoning steps.

3.  **Simulation (Rollout):**
    *   **What it does:** Starting from the newly expanded node, quickly go to the end until the game is over or a complete answer is generated. This usually uses a simpler or random strategy (Default Policy).
    *   **Significance:** This is like a "trial run." Since generating only half the reasoning steps doesn't tell us if it's right or wrong, we let the model quickly finish the remaining steps to see if a reasonable answer can be reached.

4.  **Backpropagation:**
    *   **What it does:** Based on the result of the "Simulation" (e.g., whether the final answer passed a check, or the Reward score obtained), this score is **passed back** up to all parent nodes along the path.
    *   **Significance:** Updates the statistical data (Visit Count $N$ and Value $Q$) for all nodes on this path. If this simulation was successful, the scores of nodes on this path increase, making them more likely to be selected in the next "Selection" phase.

{{< admonition tip "Difference between MCTS and DFS / BFS" >}}

**DFS and BFS are essentially Exhaustive, while MCTS is Sampling/Non-exhaustive.**

*   **BFS (Breadth-First Search) & DFS (Depth-First Search):**
    *   They are **blind**. BFS must look at all possibilities in one layer before moving to the next; DFS must hit a dead end before turning back.
    *   They lack "learning" ability. They won't give up early just because a path looks bad, nor will they allocate more resources to dig deeper because a path looks good.
    *   **Downside:** When the problem is complex (like mathematical reasoning, where every step has countless phrasings), the search space explodes exponentially. Exhaustive methods quickly run out of memory or time and can often only search very shallow levels.

*   **MCTS (Monte Carlo Tree Search):**
    *   It is **asymmetric**. The tree grows unevenly. "Good" branches grow deep and lush; "bad" branches might be ignored shortly after sprouting.
    *   **Non-exhaustive:** It doesn't need to traverse all nodes. Through multiple simulations, it statistically determines which path is "probabilistically" the best.
    *   **Dynamic Adjustment:** As iterations increase, its understanding of the tree shape becomes clearer, and the search strategy becomes smarter.

{{< /admonition >}}

### The "Selection" Process in rStar

rStar doesn't design anything particularly special for Selection, mainly following the original MCTS approach:

1.  **Start from Root:** Begin at the question.
2.  **Face the Fork:** Assume the current node is expanded, having generated several candidate Child Nodes ($s_1, s_2, s_3...$).
3.  **Score:** Calculate the UCT score for each candidate Child Node.
4.  **Pick:** Select the Child Node with the highest UCT score and move there.
5.  **Repeat:** Continue repeating steps 2-4 in the new Node **until a "Leaf Node" is encountered**, which is a node that hasn't generated subsequent steps yet.

Once a leaf node is reached, the **Selection** phase ends, and the **Expansion** phase begins.

#### UCT (Upper Confidence Bounds for Trees)

How is the **UCT** score calculated during the Selection phase? Let's look directly at the formula in Section 3.2 (Solution Generation with MCTS Rollout) of the paper:

$$ \text{UCT}(s, a) = \frac{Q(s, a)}{N(s, a)} + c \sqrt{\frac{\ln N_{parent}(s)}{N(s, a)}} $$

This formula determines which next step (Child Node) MCTS should pick when facing multiple options. It consists of two parts: **Exploitation** and **Exploration**.

##### Part 1: Exploitation —— Picking the "Blue Chip Stock"

$$ \frac{Q(s, a)}{N(s, a)} $$

*   **Meaning:** This is the **average winning rate** (average reward) of node $s$.
*   **$Q(s, a)$:** The total accumulated score of the node.

    {{< admonition tip "Meaning of Q(s, a)" >}}

    So the precise meaning of $Q(s, a)$ is:

    **"The total reward accumulated by this specific reasoning step $s$ (which was generated by action $a$)."**

    *   **Scenario:** Suppose you are at "Step 1" and considering "Step 2 (Option A)".
    *   Here $s$ is "Step 2 (Option A)".
    *   $a$ is the action that produced Option A (e.g., "Propose a sub-question").
    *   $Q(s, a)$ is the total score we've awarded to this node $s$ in history after determining it helped solve the problem.

    {{< /admonition >}}

*   **$N(s, a)$:** The number of times this node has been visited.
*   **Intuition:** If we've walked this reasoning step 10 times before, and 9 times it led to the correct answer, its average score will be high. This term encourages the model to follow directions that **past experience proves are good paths**.

##### Part 2: Exploration —— Giving "Potential Stocks" a Chance

$$ c \sqrt{\frac{\ln N_{parent}(s)}{N(s, a)}} $$

*   **Meaning:** This adds points for **paths less traveled** (Exploration Bonus).
*   **$N_{parent}(s)$:** Total times the parent node (current location) has been visited.
*   **$N(s, a)$:** Times the child node $s$ (the candidate we are evaluating) has been visited.
*   **Mechanism:**
    *   Denominator is $N(s, a)$: If we've visited node $s$ many times, the denominator grows, and this value shrinks (Exploration Bonus drops).
    *   Numerator is $\ln N_{parent}(s)$: As we pass through the parent node more often, if a certain child node $s$'s visit count $N(s, a)$ hasn't increased (still 0 or very small), this value becomes very large.
*   **$c$ (Constant):** A hyperparameter to adjust the weight of exploration. Larger $c$ means the model likes trying fresh paths more.
*   **Intuition:** This term says: "Hey! Although the average score of that path (node $s$) next door might not be the highest, or is 0, that's because we haven't really walked it yet! Give it a chance!"

### The "Expansion" Process in rStar

{{< image src="expansion.png" caption="The 5 Actions used in rStar's Expansion Process" >}}

This is one of the most brilliant innovations of this paper! Traditional MCTS often uses only one way to "expand" (e.g., always asking "What is the next step?"). However, **rStar** observed that human thinking is very flexible when solving difficult problems.

In the Expansion phase, when MCTS reaches a leaf node (current reasoning state), it selects one of **5 Actions that imitate human reasoning** to execute, generating a new child node (new reasoning content).

I categorize these 5 Actions into three groups: **Linear Reasoning**, **Decomposition & Refinement**, and **Reformulation**.

#### Group 1: Linear Reasoning
These actions are most like standard Chain-of-Thought (CoT), suitable for handling parts where logic flows smoothly.

##### Action 1 (\(A_1\)): Propose a one-step thought
*   **What:** Based on the current context, generate only "this step's" reasoning, without rushing to write everything to the end.
*   **Why:** To avoid the "snowballing error" of CoT. Standard CoT is written in one go; if the middle is wrong, the rest is wrong.
*   **MCTS View:** Expands a child node containing only the "next sentence."

##### Action 2 (\(A_2\)): Propose the remaining thought steps
*   **What:** Based on the current state, write out all remaining reasoning steps in one go until the answer is reached.
*   **Why:** To simulate human "fast thinking." If the remaining problem has become simple, or the model is confident, solving it step-by-step is unnecessary; charging to the finish line is more efficient.
*   **MCTS View:** Expands a child node containing the full subsequent path (usually leading directly to a terminal node).

#### Group 2: Decomposition & Refinement
These actions are designed for complex, error-prone problems, inspired by "Least-to-Most Prompting."

##### Action 3 (\(A_3\)): Propose next sub-question along with its answer
*   **What:** The model doesn't solve the original problem directly but asks itself: "To solve this big problem, which small problem do I need to solve first?" and then answers that small problem.
*   **Why:** Complex problems (like multi-step math) are easy to get wrong if solved directly. Breaking them into sub-questions lowers the difficulty.
*   **MCTS View:** Expands a node containing a structure like "Q: Sub-problem... A: Sub-answer...".

##### Action 4 (\(A_4\)): Answer the sub-question again
*   **Constraint:** This action can only be used after $A_3$.
*   **What:** **Re-answer** the sub-question just proposed by $A_3$. But this time, force the model to use Few-shot CoT to answer in detail.
*   **Why:** Sometimes, although $A_3$ breaks down the right problem, the answer is sloppy or wrong. $A_4$ acts like a "check mechanism" or "serious solving mode," ensuring this key sub-step is calculated correctly.
*   **MCTS View:** A correction or reinforcement of the previous node.

#### Group 3: Reformulation
These actions address "misreading the question" or "tunnel vision."

##### Action 5 (\(A_5\)): Rephrase the question/sub-question
*   **Constraint:** Usually used after the Root (original question) or after sub-questions.
*   **What:** List the conditions in the question (List conditions) or rephrase the question to make it clearer.
*   **Why:** Often models err because they missed a hidden condition (e.g., "positive integer", "excluding"). This simulates a human saying when stuck: "Wait, let me re-read the question and list the known conditions..."
*   **MCTS View:** The expanded node isn't a reasoning step but a "clearer problem description," upon which subsequent reasoning will be based.

#### Which Action to Choose Each Time?

In advanced systems like AlphaGo, there is usually a Policy Network to predict the probability of each action (Prior Probability).

However, in **rStar**, to keep it lightweight and applicable to various SLMs, it does not train an additional Policy Network to decide which Action to choose. Instead, it uses **"Rule-based Constraints"** paired with an **"Exploration First"** mechanism. We can imagine it as a checklist with rules.

Specifically, the logic for determining the Expansion action is divided into two layers:

##### Layer 1 Filtering: Hard Constraints
Not all 5 Actions can be used at any time; they must fit the current "context logic." The paper clearly defines Dependencies:

*   **$A_4$ (Answer sub-question again):** Can only be used after **$A_3$ (Propose sub-question)**.
    *   *Logic:* You must have a sub-question before you can "re-answer" it.
*   **$A_5$ (Rephrase):** Can only be used after **Root** (or sometimes after sub-questions).
    *   *Logic:* Usually needed when the question is hard to read or conditions are complex.
*   **$A_1, A_2, A_3$:** These are general actions available in most Intermediate States.

##### Layer 2 Decision: UCT's "Unexplored Priority" Mechanism
This goes back to the core feature of MCTS. When Selection picks a node ready for Expansion:

*   **Initial State:** All untried Action types (the legal ones) have a visit count $N$ of 0.
*   **Mathematical Result:** According to the UCT formula, the denominator is 0 (or tiny), causing the calculated value to be **infinite**.
*   **Decision:** MCTS forces the model to **try those Action types "not yet tried."**

**In other words, rStar's strategy is "Egalitarian":**
It doesn't prejudge which action is good but tends to **try all legal action types once**. If $A_1$ hasn't been tried at this node, do $A_1$; next time, if $A_1$ is done, try $A_3$.

##### Supplement: Quantity Limit (Quota)
To prevent the search tree from becoming infinitely wide, the paper mentions an important limit in Section 4.1 (Implementation Details):

*   **$A_1$ (One-step) & $A_3$ (Sub-question):** These actions vary greatly, so up to **5** different child nodes are allowed under the same node (by sampling different content).
*   **Other Actions ($A_2, A_4, A_5$):** Default limit is **1**.

{{< admonition tip "Example" >}}

Suppose we are currently at the Root Node. The Root Node already has 2 Child Nodes, created via Action $A_2$ and $A_5$. According to the Quota, the Root Node cannot create new Child Nodes via $A_2$ and $A_5$. Also, based on Hard Constraints, Action $A_4$ cannot be used. Thus, the only remaining actions are $A_1$ and $A_3$.

Following the MCTS concept, it prioritizes unused actions, so it will attempt $A_1$ or $A_3$, **instead of** walking into the existing $A_2$ or $A_5$ nodes. Furthermore, since the Quota for $A_1$ and $A_3$ is 5 each, every time Expansion happens at the Root Node, it will choose $A_1$ or $A_3$ until eventually, the Root Node has **5 ($A_1$) + 5 ($A_3$) + 1 ($A_2$) + 1 ($A_5$) = 12** Child Nodes.

{{< /admonition >}}

##### Summary
So in the Expansion phase, the flow to decide the Action is:

1.  **List:** List all legal Action types based on the current node state (removing illogical ones).
2.  **Check Quota:** Check which Action types haven't reached the generation limit.
3.  **Random/Round-Robin:** Pick one from the remaining legal options (usually random or sequential) and let the LLM execute the generation.

**Conclusion:** rStar doesn't rely on the model to "judge" which move is best right now. Instead, it uses MCTS to force the model to **try various moves** over multiple Rollouts, and finally, the Reward mechanism tells the model which move was most effective.

### The "Simulation" Process in rStar

Suppose we are now at a **Child Node (let's call it $s_1$)**. This node was just generated via **Action $A_1$ (Propose a one-step thought)**, so it currently **only contains the "first step"** of reasoning (e.g., "Step 1: First calculate how many apples..."), without a final answer.

If we stop here, we have no idea if this step is good. The purpose of **Simulation (also called Rollout)** is to evaluate whether this node ($s_1$) can lead to a correct ending by "fast-forwarding the future."

Here are the detailed steps of the Simulation phase in the rStar paper:

#### Default Policy Rollout

At this stage, MCTS switches to a simpler, faster mode (Default Policy).

*   **Input:** Question + Current Node $s_1$ content.
*   **Instruction:** Tell the LLM: "Based on the written Step 1, **complete all remaining reasoning steps** until the answer is calculated."
*   **Action:** Usually, complex actions like $A_3, A_4, A_5$ are not used here. Instead, it's similar to the logic of **Action $A_2$ (Propose remaining steps)**, letting the model generate to the end in one breath.

#### Terminal State

After the LLM executes the command, it generates a **Full Trajectory**:
$$ \text{Trajectory} = \text{Root (Question)} \oplus s_1 (\text{Step 1}) \oplus s_{\text{rest}} (\text{Completed Remaining Steps}) \rightarrow \text{Final Answer} $$

At this point, we have a **final answer** (e.g., "The answer is 42").

#### Reward Calculation —— The Key Scoring Standard

Now that we have a final answer, how do we score $s_1$ (calculate $Q$ value)?

This paper faces a major challenge: **This is an Inference task, so there is no Ground Truth to check against.** Therefore, the method rStar adopts is **Self-Consistency Majority Voting Estimation**.

> In the Implementation Details of Section 4.1 Experiment Setup, it mentions **"In the trajectory self-generation stage, we augment each target SLM with our MCTS, performing 32 rollouts."** This means the 4-stage process of MCTS (Selection -> Expansion -> Simulation -> Backpropagation) runs 32 times, producing 32 Full Trajectories and final answers.

Thus, rStar compares the final answer obtained from each Simulation with the current answers in the MCTS answer pool (up to 32) to calculate the Reward:

1.  **Answer Pool:** During the MCTS search process, we generate many paths and get many answers.
2.  **Self-Consistency Majority Voting:** We see which answer appears most frequently. Suppose "42" appears most often; we tentatively assume "42" is the correct answer.
3.  **Reward:**
    *   If the answer from this Simulation is "42" (consistent with the majority), this simulation gets a **High Score (Reward = 1)**.
    *   If it calculates "15" (minority opinion), it gets a **Low Score (Reward = 0)**.

{{< admonition tip "Example" >}}

Suppose we are at a node doing the first Rollout of the entire MCTS (the answer pool is empty). I get "18". We add "18" to the pool. According to Self-Consistency Majority Voting, the Reward for this Rollout is 1 / 1 = 1.0. This Reward is updated back to every parent node leading to the current node in the next stage (Backpropagation).

In other words, suppose we are at the 5th Rollout of the MCTS. The answer pool has 4 answers: ["18", "18", "18", "20"]. If this 5th Rollout gives "20", the Reward is 2/5 = 0.4. This Reward is then updated back via Backpropagation.

{{< /admonition >}}

> In the early stages of MCTS (first few rounds), the answer pool is small, so this score might not be accurate. But as Rollouts increase (paper sets 32 rounds), the "correct answer" usually emerges due to probabilistic advantage, and scoring becomes more accurate.

### The "Backpropagation" Process in rStar

If Selection is "Decision," Expansion is "Action," and Simulation is "Evaluation," then Backpropagation is **"Learning and Induction."** This is the moment MCTS truly becomes smarter.

In rStar, the implementation of Backpropagation is intuitive, but there is a **key design choice** made to adapt to SLMs.

I break it down into three parts:

#### Core Task: What to Update?

When Simulation ends, we get a Reward (let's denote it as $R$). Now, we travel back up the path we just walked (from the current Leaf Node to the Root Node) and update two statistics for each node on the path:

1.  **$N(s, a)$ (Visited Count):**
    *   Tell this node: "Hey, we passed through you again!"
    *   Update: $N \leftarrow N + 1$
2.  **$Q(s, a)$ (Total Reward Value):**
    *   Tell this node: "After passing you this time, we got a result of $R$ points. Put it on the ledger!"
    *   Update: $Q \leftarrow Q + R$

#### rStar's Key Design: Outcome-based Reward

This is a highlight of the paper. Many advanced MCTS methods (like AlphaGo) or other Reasoning methods (like RAP) try to score every intermediate step (Intermediate Reward).

**In rStar, the authors deliberately avoided scoring intermediate steps.**

*   **Why?** Because SLMs are weak. Letting them assess "Is this reasoning step good?" (Self-rewarding) is usually inaccurate, often no better than random guessing (proven in the Appendix).
*   **How?** rStar uses a **Sparse Reward** strategy.
    *   The "intrinsic value" of intermediate nodes is set to 0.
    *   Their value depends entirely on the **result of the final Simulation**.

**Specific Operation:**

Suppose our path is:
**Root (Question) $\rightarrow$ Node A (Step 1) $\rightarrow$ Node B (Step 2) $\rightarrow$ [Simulation] $\rightarrow$ Final Answer**

Suppose Simulation gives a Reward $R = 0.8$ based on majority voting.

**Backpropagation Update:**

1.  **Update Node B:**
    *   $N_B \leftarrow N_B + 1$
    *   $Q_B \leftarrow Q_B + 0.8$
2.  **Update Node A:**
    *   $N_A \leftarrow N_A + 1$
    *   $Q_A \leftarrow Q_A + 0.8$
3.  **Update Root:**
    *   $N_{root} \leftarrow N_{root} + 1$
    *   $Q_{root} \leftarrow Q_{root} + 0.8$

**Meaning:** This implies Node A and Node B share **equal credit** for this "good result." This is a simplified but effective Credit Assignment.

#### Connection with UCT Formula

After this update, the tree's data changes.

*   Since $N$ increased, the **Exploration term** for nodes on this path in the next Selection phase decreases (denominator gets larger).
*   Since $Q$ increased (assuming $R$ is positive), the **Exploitation term (average win rate $Q/N$)** of this path might increase.

This forms a loop:
*   If the result is good ($R=1.0$) $\rightarrow$ $Q$ increases significantly $\rightarrow$ Average score rises $\rightarrow$ Easier to be selected next time (Exploitation).
*   If the result is bad ($R=0.0$) $\rightarrow$ $Q$ stays same but $N$ increases $\rightarrow$ Average score is pulled down $\rightarrow$ Likely to try other paths next time (Exploration).

### Mutual Reasoning for Final Answer in rStar

{{< image src="mutual-reasoning.png" caption="Example of Mutual Reasoning in rStar" >}}

After finishing 32 Rollouts (Selection -> Expansion -> Simulation -> Backpropagation), we currently have 32 Full Trajectories and final answers. The next question is: **How to decide the final answer?**

So, rStar introduces a second stage: **Mutual Reasoning with a Discriminator**. These 32 Trajectories go through a "strict filtering and verification" process:

#### Discriminator
*   **Who is it?** Another SLM of comparable capability, or even the same model playing a different role.
*   **Task:** Its job is **not** to score these 32 paths directly (e.g., "give this 80 points"), because small models are usually inaccurate graders.
*   **Method:** Its job is a **"Fill-in-the-blank Test."**

#### Mask-and-Complete
For **each** of the 32 Trajectories (let's call it $t$), the system performs:

1.  **Masking:**
    *   Suppose a Trajectory $t$ has 5 steps ($s_1, s_2, s_3, s_4, s_5$).
    *   The system randomly picks a cut point (paper mentions randomly retaining the first 20% to 80% of steps).
    *   For example, keep the first 3 steps ($s_1, s_2, s_3$) and **Mask** the rest ($s_4, s_5$).

2.  **Completion:**
    *   Feed the question and the kept first half ($s_1, s_2, s_3$) to the Discriminator.
    *   Instruction: "Based on the previous steps, complete the remaining reasoning steps and calculate the answer."
    *   The Discriminator generates a new ending and a new answer (denoted as $\hat{A}$).

#### Mutual Consistency Check
Now we have two answers:
*   **Original Answer ($A$):** From the complete Trajectory generated by the Generator.
*   **Rewritten Answer ($\hat{A}$):** From the completion by the Discriminator based on the first half.

**Criteria:**
*   **If $A == \hat{A}$:** Congratulations! This path is considered **Mutually Consistent**. This means the logic is robust; even another model seeing only half of it could derive the same result. The credibility of this path increases significantly.
*   **If $A \neq \hat{A}$:** Alert! This path might contain logical leaps or luck, causing another model to fail to follow it or reach a different result.

#### Final Selection
Through Mutual Reasoning and the Discriminator, we filter the 32 Trajectories generated. Based on the remaining Trajectories, we pick the sole "King" as the final response.

We calculate the score of the remaining Trajectories using the following formula and pick the highest one:

$$ \text{Final Score} = \text{MCTS Reward} \times \text{Confidence Score} $$

##### MCTS Reward
*   **Source:** Data from the **MCTS Search Tree (Generator)**.
*   **Meaning:** Refers to the **$Q$ value** (or normalized $Q$ value) of the terminal node corresponding to that Trajectory.
*   **Interpretation:** "How is the quality of this specific reasoning path?"
    *   If this path ($t$) was visited multiple times in MCTS and led to high-score answers every time, its $Q$ value is high.
    *   This implies the Generator thinks: "Following these steps, the logic is very smooth and stable."

##### Confidence Score
*   **Source:** Statistical data from the **32 Rollouts Answer Pool**.
*   **Meaning:** The frequency of "that answer" appearing in all 32 attempts (Self-Consistency Majority Voting probability).
*   **Interpretation:** "How credible is this final answer?"
    *   This is independent of the path, looking only at the result.
    *   Example: If "42" is calculated 28 out of 32 times, the Confidence Score for "42" is $28/32 = 0.875$.

##### Why Multiply?

Suppose we have two Trajectories (A and B) that passed the Discriminator check, both resulting in the correct answer "42." Which one should we output as the "Detailed Solution"?

*   **Trajectory A:**
    *   A common, stable path (MCTS went here often).
    *   **$Q$ Value (Reward) = 0.9** (High path quality)
    *   **Answer "42" Confidence = 0.875** (Popular answer)
    *   **Final Score** = $0.9 \times 0.875 = \mathbf{0.7875}$

*   **Trajectory B:**
    *   A rare path (MCTS rarely went here, or it sometimes led to errors), but got it right this time and passed the Discriminator.
    *   **$Q$ Value (Reward) = 0.4** (Low path quality, maybe lucky)
    *   **Answer "42" Confidence = 0.875** (Answer still popular)
    *   **Final Score** = $0.4 \times 0.875 = \mathbf{0.35}$

By multiplying, the system favors Trajectories that **"Lead to a high-consensus answer (High Confidence) AND whose reasoning process is verified by MCTS as high quality (High Reward)."** This avoids picking paths where "the answer is right, but the process was a fluke," ensuring the solution steps output to the user are the **most standard and robust**.

## rStar Experimental Results

{{< image src="exp.png" caption="Experimental Results of rStar" >}}

**rStar (generator @maj)** indicates determining the Final Answer purely via Majority Voting from the 32 Rollouts of the Generator (using no Discriminator).

From the table, we see that even without using the Discriminator for Mutual Reasoning, rStar performs better than Baseline methods, showing the Generator design is effective. Adding the Discriminator for Mutual Reasoning significantly boosts performance further.

---

Reading the experimental data, a question arose:

> Simple SC (Self-Consistency) @maj64 achieves decent performance. If rStar requires far more average LLM Calls per task than 64, and the performance gain isn't massive compared to SC@maj64, is the method really that efficient?

Actually, in **Appendix A.2, Table 7**, the paper honestly lists this data.

*   Specific LLM Calls (using GSM8K as example):
    *   **LLaMA2-7B:** Average **166.81 calls**.
    *   **Mistral-7B:** Average **148.90 calls**.

Where do these ~150-160 LLM Calls come from?
1.  **Generator (MCTS):** To generate 32 full Trajectories, although MCTS does only 32 Rollouts, the intermediate Expansion (generating Actions) and Simulation (completing paths), plus the branching structure, consume about **120-130 calls** on average.
2.  **Discriminator:** Verifying the 32 paths requires a fixed **32 calls**.
3.  **Total:** $120 + 32 \approx 150+$ calls.

rStar's cost is about **2.3 ~ 2.6 times that of SC@64** (close to SC@128 or SC@192 level).

Besides Call count, the paper mentions a striking figure: **Generated Tokens**.
*   rStar generates an average of **360k (367.1k)** Tokens per question.
*   This is because MCTS paths are often long (multi-step, sub-questions), and the Discriminator reads long Contexts.

In comparison, if SC@64 has 200 tokens per path, the total is only 12.8k tokens. **rStar's Token cost is about 20~30 times that of SC@64.**

However, we must look at **"Return on Investment (ROI)"**: how much accuracy gain do these costs buy? This depends on the **Model's Base Capability**.

*   Scenario A: Weak SLMs —— rStar Wins (e.g., **LLaMA2-7B**, see Table 2):
    *   **SC@64:** Accuracy **20.77%**
    *   **SC@128:** Accuracy **23.05%** (Doubling to 128 yields negligible gain)
    *   **rStar (~160 calls):** Accuracy **63.91%**

**Conclusion:** Here, rStar's benefit is **huge**.
Why? Because weak models have severe "systematic errors." SC@64 just repeats wrong logic 64 times (Garbage In, Garbage Out). rStar, through MCTS Action guidance, pushes the model's capability boundary, solving problems SC cannot solve by stacking numbers. The cost increase here is very worthwhile.

*   Scenario B: Stronger SLMs —— Gap Narrows (e.g., **LLaMA3-8B-Instruct**)
    *   **SC@64:** Accuracy **83.24%**
    *   **rStar:** Accuracy **91.13%**

**Conclusion:** Improvement of about **8%**.
It depends on the application. If you seek extreme accuracy (83 to 91), 2.5x cost is acceptable. If resources are limited, SC@64 is good enough.

Summary of choosing between rStar and Self-Consistency:

1.  **Solving "Impossible" Problems:** rStar's real value is "providing critical support." When the model lacks capability (like LLaMA2-7B on math), SC sampling is useless. rStar makes the model "smarter," which SC cannot do.
2.  **Solving "Careless" Problems:** When the model is already strong (like GPT-4 or LLaMA3) but occasionally careless, SC typically has better ROI.
3.  **Conclusion:** rStar's benefit lies in **mining the upper limit of SLM potential**, not just saving money. If the task is hard for the SLM (<50% accuracy), rStar is powerful; if simple, SC suffices.

---

{{< image src="exp-2.png" caption="Selection of Discriminator Model" >}}

This touches on a hot topic: **Weak-to-Strong Generalization**.
We discussed the Discriminator. Intuition suggests: "To check LLaMA3-8B's answer, shouldn't the discriminator be at least as strong?"

In the table above, the authors ran an interesting experiment:
*   **Generator:** LLaMA3-8B-Instruct
*   **Discriminator:** Different models.

**Surprising Result:**
*   Using **Phi-3-Mini (3.8B)** as Discriminator: Accuracy **91.13%**
*   Using **GPT-4 (Super Strong)** as Discriminator: Accuracy **92.57%**

**Interpretation:**
This shows rStar's Mutual Consistency mechanism is very robust. Even a Discriminator much weaker than the Generator (3.8B vs 8B) can effectively filter correct answers as long as it can perform basic logical completion. This is great news for **lowering deployment costs** (you can use a small model to monitor a larger one).

---

{{< image src="exp-3.png" caption="rStar performance on GSM8K with different Rollout quantities" >}}

We discussed rStar's high cost (32 rollouts). But looking at the table above, we see a great trend.

**Phenomenon:**
*   With only **2 Rollouts**, rStar significantly outperforms Baselines (like RAP and SC).
*   The curve saturates around **8~16 Rollouts**; further gains diminish.

This addresses the cost concern. Although the paper sets 32, in practice, we could cut Rollouts to **4 or 8**. This drastically reduces LLM Calls (maybe just slightly more than SC) while still enjoying MCTS's structured reasoning advantages. This proves that High-quality Trajectories generated by rStar can be found very early.

---

{{< image src="exp-4.png" caption="rStar performance on GSM8K with different Action Spaces" width="80%">}}

We spent a lot of time on the 5 Actions ($A_1 \sim A_5$). You might ask: "Is it necessary to be so complex? Does one move not work?"

The table answers (using LLaMA3-8B):
*   **Only $A_3$ (like RAP):** 70.5%
*   **Only $A_3 + A_5$:** 72.5%
*   **All ($A_1 \sim A_5$):** **75.0%**

This proves the value of a **"Rich set of human-like reasoning actions."** A single decomposition strategy (like RAP) is useful but inflexible for diverse problems. Adding "Rephrase ($A_5$)" and "Single/Multi-step toggling ($A_1/A_2$)" covers more reasoning blind spots. This suggests future research could focus on **designing even more diverse reasoning actions**.

## Conclusion

Finally, to summarize the three most important core concepts of this paper:

1.  **Inference Scaling Laws:** This paper proves that besides stacking compute at training (Pre-training/Fine-tuning), we can stack compute at **Inference-time** (via Search and Verification) to massively boost model capability. This is a path to getting stronger without retraining.
2.  **Mutual Reasoning:** "Self-verification" is hard, but "Mutual verification" (fill-in-the-blank) is effective. This method, relying on **Consistency** rather than direct Scoring, is a clever solution to the difficulty of training Reward Models.
3.  **MCTS as a Prompting Driver:** Traditional MCTS is for games; rStar turns it into a Prompt scheduler. This demonstrates the powerful potential of combining **Classic Algorithms** with **LLMs**.

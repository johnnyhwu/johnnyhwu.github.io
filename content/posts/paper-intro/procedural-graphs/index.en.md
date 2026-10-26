---
# weight: 1
title: "Do Workflow Graphs Help AI Agents? Procedural Graphs"
date: 2026-10-26
lastmod: 2026-10-26
draft: false
description: "Procedural Graphs store an LLM agent's workflow as an editable graph that a refiner improves offline. It beat ReAct in 23 of 24 cells, but a hand-written graph hurt."
featuredImage: "featured-image.png"

tags: ["Large Language Model", "Agent Memory", "Single-Agent"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## Introduction

This post walks through a Google paper, *Procedural Graphs: Self-Evolving Execution Structures for LLM Agents* (arXiv 2609.09153v1, September 2026). Its core move is to store an agent's "way of doing things" as an editable directed graph. At inference time, only a small piece of the graph near the agent's current position is taken, and a second LLM turns it into a prompt. Offline, an LLM edits the graph, and whether an edit helps is decided by a separate validation set (a set of problems that were not used for training).

The conclusion first. With the same model and the same solver (the LLM that picks actions), compared against a memoryless ReAct (explained in the next section), the gain is positive in 23 of 24 "model × benchmark" cells. HotpotQA, however, barely improves (at most +1.7). The price is one extra LLM call per step, which makes token usage roughly 1.33 to 1.85 times that of the no-graph setup. Hand-written expert graphs are also not reliably good: on MultiChallenge, one answered 16 fewer questions correctly than using no graph at all (out of 56), and only after evolution did it get back to 3 more than no graph.

What I find most worth taking away is not the graph but its improvement loop: propose an edit, gate it with a separate validation set, and feed the rejected ones back to the proposer. That loop can be applied to any editable text asset, and the second half of the post covers it on its own.

The post covers the problem, the method (in three parts), the experiments (three of them), and what is worth taking away. At the end there are five standalone concept notes; the main text points to them where relevant.

## The Problem: ReAct Figures Out Every Step on Its Own

ReAct is a common agent loop: think one step, call one tool, look at the result, think again. The problem is that every step has to infer the next move from an ever-longer log of actions and observations. On long tasks the agent easily forgets the goal, calls tools out of order, and repeats actions that do not work.

Existing remedies each miss something:

- **Text memory and reflection** (Reflexion, ExpeL): the content is free text, and the solver still has to judge for itself how that text constrains the steps that follow.
- **Conditional guidance** (AutoGuide): each piece of guidance is independent of the others, with nothing connecting them.
- **Hand-written workflows and state machines**: they require manual design.
- **Automatic workflow search** (AFlow): it only optimizes the structure offline and does not adapt to progress at inference time.

The paper wants four things at once: structure strong enough to block ineffective behavior, flexibility of reasoning preserved, adaptation to the current progress, and the ability to improve from experience.

For the core analogy, look at Figure 1. A knowledge graph organizes facts into triplets and answers "what is this"; a Procedural Graph organizes the task procedure into triplets and answers "what to do next".

{{< image src="figure1.png" alt="On the left, a knowledge graph organizes facts into triplets to answer what-is questions; on the right, a Procedural Graph organizes task procedures into triplets to answer what-to-do questions." caption="Figure 1 — From knowledge to procedure: a knowledge graph answers \"what is it\", a Procedural Graph answers \"what to do\". (Source: original paper, Figure 1.)" >}}

## Method 1: What the Graph Looks Like

A Procedural Graph (PG below) is a directed graph with attributes. Nodes are steps, and edges say "which step can follow this one". Each edge also carries three pieces of text explaining how to follow it (paper Section 3.1). Formally:

$$
G = (V,\, R,\, E,\, \Phi), \qquad E \subseteq V \times R \times V
$$

- \( V \): the set of nodes. Each node stands for a tool function, a skill, an internal reasoning step, or a task state.
- \( R \): the vocabulary of relation types. There are only four in practice: `LEADS_TO`, `TRIGGERS`, `PROVIDES_INPUT_FOR`, `CONVERGES_TO` (Appendix B.4). They are just labels; later we will see that they do not actually matter at inference time.
- \( E \): the set of edges. Each edge is \( (u, r, v) \), meaning "after \( u \), you may follow with \( v \) by relation \( r \)".
- \( \Phi \): maps each edge to a set of text fields. The paper uses three: condition (when to take this edge), guidance (how to do it), and pitfalls (what to avoid).

The paper's own example (Section 3.1) is this edge: `(cash_flow_forecast, LEADS_TO, fund_raising_request)`, meaning that after a cash-flow forecast you may go on to file a fundraising request. Its three pieces of text are:

| Field | Content |
| --- | --- |
| condition | when the projected cash runway falls below the safety buffer |
| guidance | file the request early, because funds arrive with a delay |
| pitfalls | do not stack a second request while one is still pending |

These three sentences are the raw material that gets translated for the solver at inference time.

The graphs actually used are small. Apart from BFCL v3, which has to map onto a huge function catalog and has 131 nodes and 265 edges, every graph has only 7 to 17 nodes and 7 to 27 edges; the numbers are in Table 1. The seven columns in Table 1 are the six benchmarks plus EnterpriseArena, a financial simulation environment where the agent plays a CFO managing a company's cash, with the goal of surviving 132 months without going bankrupt. It is not among the six benchmarks in the main comparison of Experiment 1, and is mainly used for the self-evolution case study.

{{< image src="table7.png" alt="The number of nodes and edges (triplets) in the Procedural Graph used in each of the seven evaluation environments: six benchmarks plus EnterpriseArena." caption="Table 1 — Procedural Graph sizes for each benchmark in the main experiments. (Source: original paper, Table 7.)" >}}

The graph can start from an expert's hand-written version, or from an empty graph with just two nodes, Start → End. The comparison of the two starting points is in Experiment 3.

## Method 2: Online Inference

At inference time, before each decision the system first works out which node of the graph the agent has just finished, takes only the subgraph reaching 2 hops forward from that node, and has another LLM turn it into a short piece of text saying "what to do now and what to avoid", which is appended to the solver's prompt. The graph is frozen during inference and is not updated (Section 3.2).

First, the two roles:

- **solver**: the LLM that actually picks the next action, i.e. the agent itself in the ReAct loop.
- **guidance model (\( \Psi \))**: another LLM that turns the subgraph into a prompt. The paper says it uses the same underlying model as the solver (Section 4).

One full step goes like this:

1. Get the previous action \( a_{t-1} \).
2. Match it to a node \( u_t \) on the graph and take the 2-hop subgraph \( G_t \).
3. \( \Psi \) reads \( G_t \), the question \( q \), and the last 3 steps of the trajectory, and writes the guidance \( g_t \).
4. \( g_t \) is filled into the `Procedural Graph Guidance:` field of the solver prompt.
5. The solver outputs a Thought and an Action.
6. The environment executes the action and returns an observation.
7. The new action and observation are appended to the trajectory, and the next step begins.

Figure 2 is an overview of the whole framework; focus on the middle column.

{{< image src="figure2.png" alt="Overview of the Procedural Graph framework: on the left triplets define the graph; in the middle the current node is located, a 2-hop subgraph is taken and handed to a guidance model that produces a prompt; on the right a refiner proposes edits from trajectories, guarded by a validation gate and rejection memory." caption="Figure 2 — Overview of the Procedural Graph framework. The middle is online inference and the right is offline evolution. (Source: original paper, Figure 2.)" >}}

### Part 1: Localizing and Taking the Subgraph

Part 1 answers "where on the graph is the agent right now":

$$
u_t = \mathrm{Match}(a_{t-1},\, V), \qquad G_t = \begin{cases} N_h(u_t), & u_t \neq \emptyset \\ G, & \text{otherwise} \end{cases}
$$

- \( t \): which decision step we are at. By convention \( a_0 = \text{Start} \), so the first step is always localized at the Start node.
- \( a_{t-1} \): the agent's previous action, for example one tool call.
- \( \mathrm{Match} \): matches \( a_{t-1} \) against the node set \( V \); the paper writes "exactly matching".
- \( u_t \): the matched node, i.e. the agent's position on the graph; if nothing matches it is the empty set.
- \( N_h(u_t) \): the subgraph obtained by expanding along outgoing edges from \( u_t \) for at most \( h \) steps. The experiments use \( h = 2 \).
- \( G_t \): the graph handed to \( \Psi \) at this step. When matching fails, it falls back to the whole graph \( G \).

Appendix B.5 has a serialized local graph from HotpotQA (an excerpt) that works as an example. The previous action is `first_hop_retrieve`, which is localized to `First_Hop_Retrieve`; hop 1 is `First_Hop_Retrieve → Scan_Index` and hop 2 is `Scan_Index → Bridge_Extract`. The two edges, together with their condition, guidance and pitfalls, are handed to \( \Psi \). The details of the matching mechanism are in the concept notes at the end.

### Part 2: Generating Guidance and Choosing an Action

Part 2 generates the guidance and picks the action:

$$
g_t = \Psi\big(G_t,\, q,\, T_{t-w:t}\big), \qquad a_t \sim P_{\text{solver}}\big(\cdot \mid q,\, T_t,\, g_t\big)
$$

- \( g_t \): the contextualized guidance at step \( t \), a piece of natural language.
- \( \Psi \): the guidance model.
- \( q \): the user's original question.
- \( T_{t-w:t} \): the trajectory of the last \( w \) steps; the experiments use \( w = 3 \).
- \( T_t \): the full trajectory so far, an interleaved sequence of actions and observations.
- \( a_t \): the action the solver takes at this step. All experiments use greedy decoding (always take the most probable option), so it is effectively deterministic.

\( \Psi \)'s instructions (the Guidance Generation Prompt in Appendix B.5) require it to say, based on the condition, guidance and pitfalls on the edges, what to do next, what to avoid, and how to recover after a recent failure, and to include the concrete command formats, tools and parameters that the graph mentions. What each of the two LLMs sees and outputs is laid out in the concept notes at the end.

### Four Properties to Remember

- **It only biases, it does not force.** The paper's abstract says the guidance biases the solver's next action but does not dictate it. The paper has no mechanism to check whether the solver's action actually follows the graph.
- **One extra LLM call per step (\( \Psi \) itself), so the cost is always higher than using no graph.** The numbers are in Experiment 2.
- **A failed match falls back to the whole graph, which is costly.** Experiment 2 shows that the whole graph plus generative guidance is the worst setting, but the paper does not report how often matching fails, so we do not know how often this path is actually taken.
- **The four relation types do nothing at inference time.** Appendix B.5 says the serializer does not print relation labels for \( \Psi \), so at least under this serialization \( \Psi \) sees only nodes, arrow directions and the three pieces of text.

## Method 3: Offline Self-Evolution

The offline part works like this: let the solver run a batch of training problems, leaving behind both successful and failed trajectories; the refiner (an LLM dedicated to editing the graph, using the same underlying model as the solver) reads the trajectories and outputs a list of edits, which are applied to a copy of the graph to get a candidate graph; the candidate is adopted only if it is no worse than the current graph on a separate validation set, and rejected ones are recorded and shown to the refiner in the next round (Section 3.3, Algorithm 1).

Round \( k \) goes as follows:

1. With the currently kept graph \( G_{k-1} \), run the solver on a batch of training problems, recording the trajectories and scores (0 to 1).
2. The refiner compares high-scoring and low-scoring trajectories: it looks for recurring error loops in failed trajectories and for shortcuts to borrow in successful ones.
3. The refiner outputs an edit list \( \Delta G_k \).
4. The edits are applied to a copy of the graph to get a candidate graph.
5. A structural check is run; if it fails, the candidate is dropped without running validation.
6. The score on the validation set is computed and compared with the old graph.
7. If it is no worse than the old graph, adopt it; otherwise fall back to the old graph and record this candidate in rejection memory.

### Proposing Edits: What the Refiner Outputs

$$
G_k^{cand} = G_{k-1} \oplus \Delta G_k
$$

- \( G_{k-1} \): the graph kept from the previous round. A rejected candidate never becomes the starting point of the next round.
- \( \Delta G_k \): the edit list proposed by the refiner.
- \( \oplus \): applies the edits to a copy of the graph; if the configuration asks for it, cycles are also removed automatically.
- \( G_k^{cand} \): the candidate graph.

There are only two kinds of edit: **Add** (add a node or edge, for example a verification step) and **Delete** (remove a node or edge that keeps leading trajectories into failure). Changing an edge's attributes means deleting it and adding it back with the new attributes.

The refiner's actual output is a JSON with four arrays: `add_nodes`, `delete_nodes`, `add_edges`, `delete_edges` (the Refiner Prompt in Appendix B.5). Deletions are applied before additions. There is a catch: `delete_edges` removes all edges between that start and end node regardless of relation type, so to keep some of them you have to add them again in `add_edges`.

Appendix E.3 has a worked example, using the EnterpriseArena CFO task. In Round 1, starting from an empty graph with only Start → End, a whole main line grows at once; Round 7 deletes the `pass_action` node (do nothing) and its edges; Round 8 replaces `fund_raising_request → book_closing` with a direct link to End. Figure 3 shows how the topology changes step by step.

{{< image src="figure5.png" alt="Topology changes of the CFO task's Procedural Graph across evolution rounds: green nodes and edges are additions, red dashed nodes and edges are deletions or pruning." caption="Figure 3 — Topological evolution of the CFO Procedural Graph. Green is added, red dashed is deleted. (Source: original paper, Figure 5.)" >}}

The structural check (Appendix B.6) looks at only three things: the endpoints of an edge must exist, node and relation types must be valid, and every node must have a path to a terminal node (a node with no outgoing edge counts as terminal). Candidates that fail are dropped outright.

> There is a loophole here: the refiner prompt requires ACTION nodes to be real tool names, but the validator does not check this, and only the prompt constrains it. If the refiner invents a tool node that does not exist, the structural check cannot stop it, and only the validation score of the next step can.

### The Validation Gate: Deciding Whether Edits Make the Graph Worse

The score on the validation set, and the rule for adopting a candidate:

$$
S_{val}(G) = \frac{1}{|D_{val}|} \sum_{(q,y) \in D_{val}} S\big(f_{solver}(q \mid G),\, y\big)
$$

$$
G_k = \begin{cases} G_k^{cand}, & S_{val}(G_k^{cand}) \ge S_{val}(G_{k-1}) \\ G_{k-1}, & \text{otherwise} \end{cases}
$$

- \( D_{val} \): the validation set, separate from both the training batches and the test set.
- \( (q, y) \): one question and its ground-truth answer.
- \( f_{solver}(q \mid G) \): the solver's output when using graph \( G \); \( S \) is the per-question score, so \( S_{val}(G) \) is the average score on the validation set.
- The comparison uses \( \ge \), so a tie is accepted. The old graph's score is cached and not rerun.

Why a separate validation set? Because the refiner proposed its edit after seeing the training trajectories, and working on the training batch does not mean it really works.

**A ten-round walkthrough.** Table 2 is Table 11 of Appendix E: self-evolution on EnterpriseArena with Gemini 3.5 Flash. The gate rule (the paper does not state the metric; below I explain why I infer it is the survival rate) is: accept the new graph if its validation survival rate is no lower than that of the currently kept graph, otherwise reject. The denominator is the 20 episodes of the validation set, so 1 episode equals 5 percentage points; the survival rate is the share of episodes that last the full 132 months without going bankrupt.

{{< image src="table11.png" alt="Training, validation and test metrics of PG across ten rounds of self-evolution; the Δ rows show the change against the previous best validation checkpoint, and grey rows mark rounds where no new graph was adopted." caption="Table 2 — Per-round metrics across ten rounds of self-evolution (Gemini 3.5 Flash, EnterpriseArena). (Source: original paper, Table 11.)" >}}

Here is the decision process from this table in one place:

| Round | New graph survival | Compared against (currently kept graph) | Result | Graph kept after this round |
| --- | --- | --- | --- | --- |
| R1 | 45.0% (9/20) | 0.0% (initial empty graph) | Accept | R1 |
| R2 | 80.0% (16/20) | 45.0% | Accept | R2 |
| R3 | 65.0% (13/20) | 80.0% | Reject | R2 |
| R4 | 75.0% (15/20) | 80.0% | Reject | R2 |
| R5 | Failed structural check, validation not run | 80.0% | Reject | R2 |
| R6 | 65.0% (13/20) | 80.0% | Reject | R2 |
| R7 | 80.0% (16/20) | 80.0% | Tie, accept | R7 |
| R8 | 90.0% (18/20) | 80.0% | Accept | R8 |
| R9 | 90.0% (18/20) | 90.0% | Tie, accept | R9 |
| R10 | 85.0% (17/20) | 90.0% | Reject | R9 |

The rightmost column is the point: the kept graph only moves forward and never goes backward. R3 through R6 were all rejected, so at the end of those four rounds the graph in hand was still R2. R10's training survival rate is 90.0% but its validation rate is only 85.0%; what got blocked was a change that worked only on the training batch (Appendix E.2).

Two things to flag:

- **The paper does not say which metric \( S_{val} \) uses in this experiment.** But the decisions in Table 2 only fit the survival rate: R4 has a higher mean score than R2 but a lower survival rate, and was rejected; R9 has a lower mean score than R8 but an equal survival rate, and was accepted. Appendix E.2 mentions a drop in mean score when explaining R10's rejection, but R9's mean score also dropped and it was still adopted, so it cannot be the mean score. **This is my inference: the gate actually looks at the survival rate.**
- **When the validation set is small, most accepts and rejects are noise.** With 20 episodes, a difference of one episode is 5 percentage points. The paper itself says a single decision hinges on one or two episodes and should be treated as a search trajectory, not a significance test (Section 5.4). Since ties are accepted, noise can also push the graph forward.

> A note with a general-knowledge analogy (not content from the paper): this whole mechanism is hill climbing. It only accepts changes that are no worse than the current one, so the score only goes up, but it also cannot reach a better design that requires getting worse first.

### Rejection Memory: Recording the Edits That Were Thrown Away

$$
\Delta G_{k+1} \sim P_{refiner}\big(\cdot \mid G_k,\, C_{k+1},\, H_{rejected}\big)
$$

- \( G_k \): the currently kept graph.
- \( C_{k+1} \): the training trajectories of the next round; if they exceed the length limit \( L_{max} \), the beginning is cut and the end is kept.
- \( H_{rejected} \): the history of rejected candidates, used as negative evidence meaning "do not propose this kind of thing again".

What happens after a rejection is simple: the graph stays the same, one record is made, the next round reruns on the next batch of training problems with the same graph, and the refiner is asked to propose edits again. The loop runs a fixed \( K \) rounds and does not stop early because of rejections. What each record contains and what the refiner actually sees are covered in the concept notes at the end.

Back to one round from Appendix E.2: R3 lowered the cash threshold that triggers fundraising. It worked on the training seeds, but on the validation set it caused premature dilution and cash shortfalls, the validation survival rate dropped from 80.0% to 65.0%, and the candidate was rejected.

## Method Summary Table

The whole method has seven components: three in the online stage, three in the offline stage, plus the graph itself, shared by both stages.

| Component | In one sentence | Input | Output | When |
| --- | --- | --- | --- | --- |
| Graph \( G \) | Steps and what can follow them, with condition / guidance / pitfalls on the edges | - | - | Shared by both stages |
| Localize + take subgraph | Find the current node, take the \( h=2 \)-hop subgraph | Previous action, \( G \) | Subgraph \( G_t \) | Online |
| \( \Psi \) (guidance model) | Translate the subgraph into guidance for right now | \( G_t \), \( q \), last 3 steps | \( g_t \) (text) | Online |
| solver | Pick the next action | \( q \), full trajectory, \( g_t \) | Thought + Action | Online |
| refiner | Read trajectories and propose a list of graph edits | Current graph, training trajectories, scores, \( H_{rejected} \) | Edit list \( \Delta G \) (JSON) | Offline |
| Validation gate | Accept the candidate only if its validation score is no lower than the old graph's | Candidate graph, validation set | Accept or reject | Offline |
| Rejection memory | Record the edits that were thrown away | Rejected candidate and its evidence | Reference for the next round's refiner | Offline |

## Experiment 1: Main Results and the Clean Comparison

The paper claims PG ranks first or ties for first in 21 of 24 "model × benchmark" cells. Comparing only against the memoryless ReAct (same model, same solver), 23 of 24 cells are positive, but HotpotQA barely improves.

**Setup (Section 4):** 4 LLMs (Claude Sonnet 4.6, Gemini 3.1 Pro, Gemini 3.5 Flash, Grok 4.1 Fast), 6 benchmarks, and 7 comparison methods (see the baseline concept note at the end). All methods share the same ReAct solver and differ only in how experience is stored and used. The guidance model and the refiner use the same LLM as the solver, and everything uses greedy decoding.

The seven comparison methods can be roughly grouped like this: Vanilla ReAct stores nothing; MemoryBank, RAP, ExpeL and AWM store text such as experience summaries, past trajectories, distilled lessons or workflows; AutoGuide stores conditional guidance of the form "in state X, do Y"; KnowAgent stores rules on "which action can follow which". A method-by-method comparison is in the baseline concept note at the end.

**The six metrics and test sizes:** the number of test questions determines how much one question is worth. GDPval has only 44, so one question is about 2.3 points, and a small gap can easily be noise.

| Benchmark and metric | What it tests | Test questions |
| --- | --- | --- |
| HotpotQA Acc. | Whether the answer to a multi-hop question is correct (an LLM judge decides equivalence with the ground truth) | 1,000 |
| MultiChallenge Acc. | Whether instructions given earlier in a multi-turn conversation are remembered and followed (overall success rate by an LLM judge) | 166 |
| GDPval Rubric Score | Average score of professional deliverables against each task's rubric | 44 |
| ALFWorld Success | Success rate on virtual household tasks, which demand a strict action order | 134 |
| \( \tau \)-bench Pass@1 | Customer-service scenarios: the share where the final database state equals the ground truth | 115 |
| BFCL v3 Acc. | Accuracy of multi-turn function calling | 100 |

**The paper's claim (Section 5.1):** against the strongest baseline in each cell, PG has 19 wins, 2 ties and 3 losses. The 3 losses are Claude on HotpotQA and Grok on ALFWorld and \( \tau \)-bench; the 2 ties are MultiChallenge for Claude and for Gemini 3.5 Flash. The three cells with the largest lead are BFCL v3 with Gemini 3.5 Flash (67.00 vs 58.00), GDPval with Gemini 3.1 Pro (78.78 vs 71.37), and \( \tau \)-bench with Gemini 3.1 Pro (80.00 vs 73.04). The full numbers are in Table 3.

{{< image src="table1.png" alt="Accuracy with 95% confidence intervals for PG and seven comparison methods across four LLMs and six benchmarks." caption="Table 3 — Main results for each LLM and benchmark; brackets give 95% confidence intervals. (Source: original paper, Table 1.)" >}}

**The clean comparison:** PG minus the memoryless ReAct, with the same model and the same solver, in points.

| Model | HotpotQA | MultiChallenge | GDPval | ALFWorld | \( \tau \)-bench | BFCL |
| --- | --- | --- | --- | --- | --- | --- |
| Claude Sonnet 4.6 | -0.10 | +6.03 | +5.26 | +6.71 | +7.82 | +6.00 |
| Gemini 3.1 Pro | +1.40 | +7.83 | +22.39 | +5.22 | +7.83 | +7.00 |
| Gemini 3.5 Flash | +1.40 | +10.24 | +5.09 | +11.19 | +13.05 | +11.00 |
| Grok 4.1 Fast | +1.70 | +18.68 | +13.96 | +13.43 | +3.48 | +8.00 |

A few things can be read from this table:

- 23 of 24 cells are positive; the only negative one is Claude on HotpotQA (-0.10).
- HotpotQA barely improves: the largest gain is only +1.7, smaller than the width of the confidence interval in that row. The other five benchmarks range from +3.48 to +22.39.
- "Beating the baselines" deserves a discount, because quite a few baselines are themselves worse than having no memory. For example, on ALFWorld with Gemini 3.1 Pro, no memory scores 94.78, MemoryBank 85.07 and RAP 80.60. So part of the 19 wins is opponents getting worse, and only comparing against no memory shows PG's own contribution.

> One more potential confound is my own inference, and the paper does not acknowledge it: the paper says all learning-based baselines consume the same training trajectories, but PG's validation gate additionally uses a validation set (1,000 questions for HotpotQA and 100 for MultiChallenge, Appendix B.1), and the paper does not say whether the baselines could use one.

## Experiment 2: Ablation on How the Graph Is Used

Local subgraph plus generative guidance is the highest on all three benchmarks; the whole graph hurts, especially on ALFWorld, which needs a strict action order. This is the only experiment that directly tests the core design (take a local subgraph, then have \( \Psi \) translate it into guidance) (Section 5.5).

**Setup:** the same graph and the same model (Gemini 3.5 Flash), changing only two things: whether the agent sees the whole graph or a local subgraph, and whether the graph is pasted in as raw text or first translated into guidance by \( \Psi \). Four combinations are compared:

- No graph: PG is not used.
- Whole graph + raw injection: the whole graph is serialized and put directly into the prompt, without going through \( \Psi \).
- Whole graph + generative: the whole graph is handed to \( \Psi \) to translate into guidance.
- Local subgraph + generative: the paper's full method.

Both cost metrics are lower-is-better: Avg. Tok is the average number of tokens used per question (including \( \Psi \)'s calls), and Avg. Step is the average number of solver steps per question.

{{< image src="table3.png" alt="Ablation on how PG is used: accuracy, average tokens and average steps on MultiChallenge, GDPval and ALFWorld for no graph, whole graph with raw injection, whole graph with generative guidance, and local subgraph with generative guidance." caption="Table 4 — Ablation on how the graph is used (Gemini 3.5 Flash). (Source: original paper, Table 3.)" >}}

**Accuracy (in points, higher is better):**

| Setting | MultiChallenge | GDPval | ALFWorld |
| --- | --- | --- | --- |
| No graph | 80.27 | 54.80 | 72.58 |
| Whole graph + raw injection | 86.60 | 57.17 | 70.34 |
| Whole graph + generative | 87.35 | 56.75 | 54.48 |
| Local subgraph + generative | 89.31 | 63.99 | 81.53 |

**Cost: tokens as a multiple of no graph** (computed from the raw token counts in Table 4):

| Setting | MultiChallenge | GDPval | ALFWorld |
| --- | --- | --- | --- |
| Whole graph + raw injection | 1.53x | 0.96x | 1.17x |
| Whole graph + generative | 2.18x | 1.63x | 5.34x |
| Local subgraph + generative | 1.85x | 1.33x | 1.55x |

Three things come out of these two tables:

1. **The local subgraph is the highest on all three benchmarks**, ahead of the runner-up in each by 1.96, 6.82 and 8.95 points.
2. **The whole graph hurts.** ALFWorld falls from 72.58 to 54.48, with tokens at 5.34 times the no-graph setting. My guess is that ALFWorld requires a strict action order, and \( \Psi \) still writes the irrelevant branches of the whole graph into the guidance. The paper gives only the result, not the mechanism.
3. **The local subgraph always costs more than no graph.** Its tokens are 1.33 to 1.85 times the no-graph setting. Steps drop on GDPval (28.20 to 18.57) and ALFWorld (21.84 to 18.80), but on MultiChallenge they go up, from 3.87 to 4.22.

## Experiment 3: Construction Modes

This experiment tests two things: whether self-evolution helps, and whether it can fix a broken expert graph. There is only one robust signal: on MultiChallenge the expert graph makes the score collapse, and evolution brings it back. Whether starting from an empty graph can catch up with the expert graph cannot be told from the MultiChallenge data (Section 5.3).

**Setup:** the same model (Gemini 3.5 Flash, Appendix D.3), varying "where the graph comes from and how it is updated", comparing five combinations (Appendix D.2):

| Mode | Starting point | Update method | Validation gate |
| --- | --- | --- | --- |
| 1 | Hand-written expert graph | No updates | None |
| 2 | Hand-written expert graph | One big rewrite after running the whole training set | None |
| 3 | Hand-written expert graph | Batch-wise evolution | Yes |
| 4 | Empty graph (Start → End) | One big rewrite | None |
| 5 | Empty graph | Batch-wise evolution | Yes |

The difference between "one big rewrite" and "batch-wise evolution" is:

| | One big rewrite | Batch-wise evolution |
| --- | --- | --- |
| Process | Run the whole training set with the starting graph, the refiner reads all trajectories and outputs one large edit that is adopted directly, then it ends | The training set is split into batches; for each batch in turn: run with the current graph, the refiner proposes edits, the validation set gates them (accept or discard), then run the next batch with the (possibly updated) graph, repeating until the last batch |
| Iterations | One round | Many rounds |
| Validation gate | None | Yes |

**Metrics and denominators:**

- **Ans EM (Exact Match):** an answer counts as correct only if the string is identical to the ground truth, and it measures only the final answer. The paper also reports Ans F1 (word overlap between the answer and the ground truth, more lenient than EM) with the same trend, so only EM is considered here.
- **MultiChallenge Overall:** the success rate, judged by an LLM judge, of following all instructions in the whole conversation. MultiChallenge has four more sub-metrics (Inference Memory, Instruction Retention, Reliable Versioned Editing, Self Coherence), but only Overall is considered here.
- **Denominators:** HotpotQA tests 1,000 questions, so 1 question equals 0.1 points. MultiChallenge uses only 56 questions in this table (Appendix B.1; the test set in Experiment 1 has 166 questions, and the paper does not say why only 56 are used here), so 1 question equals 1.79 points.

{{< image src="table2.png" alt="Metrics for the five PG construction modes and the no-graph baseline on HotpotQA and MultiChallenge." caption="Table 5 — Performance of the five construction modes on HotpotQA and MultiChallenge. (Source: original paper, Table 2.)" >}}

**Results:**

| Mode | HotpotQA EM | Difference vs no graph | MultiChallenge Overall | Difference vs no graph |
| --- | --- | --- | --- | --- |
| No graph | 58.8 | - | 87.50 (49/56) | - |
| 1 Hand-written expert graph | 62.8 | +4.0 | 58.93 (33/56) | -16 questions |
| 2 Expert graph + one big rewrite | 63.8 | +5.0 | 53.57 (30/56) | -19 questions |
| 3 Expert graph + batch-wise evolution | 63.1 | +4.3 | 92.86 (52/56) | +3 questions |
| 4 Empty graph + one big rewrite | 55.4 | -3.4 | 89.29 (50/56) | +1 question |
| 5 Empty graph + batch-wise evolution | 66.3 | +7.5 | 91.07 (51/56) | +2 questions |

**Why the baseline differs from Experiment 2:** with the same Gemini 3.5 Flash and no graph, the MultiChallenge baseline is 80.27 in Experiment 2 and 87.50 here, because the two experiments use different subsets of questions (the caption of Table 4 says they are fixed subsets), so the numbers cannot be compared across experiments.

Three conclusions:

1. **On HotpotQA only Mode 5 is clearly the best.** It answers 75 more questions correctly than no graph. Modes 4 and 5 both start from an empty graph and differ by 10.9 EM; Mode 4, which is worse than no graph, answers 34 fewer questions correctly.
2. **When starting from an expert graph, evolution adds nothing extra.** Mode 3 (63.1) is only 0.3 higher than the never-updated Mode 1 (62.8), and lower than Mode 2 (63.8).
3. **The robust signal on MultiChallenge is that "the expert graph makes the score collapse, and evolution can rescue it".** Modes 1 and 2 are 16 and 19 questions below no graph, and Mode 3 goes from Mode 1's 33 questions back to 52, a gap of 92.86 − 58.93 = +33.93, matching the paper's reported number. But Modes 3, 4 and 5 differ from each other by only 1 question and from no graph by only 1 to 3, so we cannot say which is better than which, nor that "starting from an empty graph catches up with the expert graph".

**The clean comparison (the method's own contribution):** same starting point, comparing only how much "adding evolution and the gate" adds.

| Starting point | Modes compared | HotpotQA EM | MultiChallenge |
| --- | --- | --- | --- |
| Expert graph | Mode 3 vs Mode 1 | +0.3 | 19 more questions |
| Empty graph | Mode 5 vs Mode 4 | +10.9 | 1 more question |

## What Is Worth Taking Away

### The Improvement Loop: Propose, Validate Independently, Feed Back the Rejected

Have an LLM propose an edit to a text asset (a prompt, rules, a [skill](../skillopt/), a graph), quantify old versus new on a set of data it has not seen, adopt the new one only if it is no worse, record the rejected ones, and show them to it with the next proposal. This approach has nothing to do with graphs; it applies to any editable text asset. The skeleton looks roughly like this:

```text
asset = initial version;  rejected = []
score_asset = evaluate(asset, VAL)            # score the initial version once, cache it
for round in 1..K:
    traces   = run(asset, TRAIN_BATCH[round]) # run the current version on a new batch of training data
    proposal = LLM_propose(asset, traces, rejected)
    cand     = apply(asset, proposal)
    if not valid(cand): rejected.append(proposal); continue
    score_cand = evaluate(cand, VAL)
    if score_cand >= score_asset: asset, score_asset = cand, score_cand
    else: rejected.append((proposal, cand, score_cand))
```

### Limits to Keep in Mind When Using It

The limits of this loop have all appeared above: hill climbing cannot escape a design that can only be reached by first getting worse, a gate on a small validation set mostly accepts noise, and a constraint written only in the prompt and not checked by the validator is no constraint at all (the refiner inventing a tool node that does not exist is an example). When applying it to your own asset, first check whether the validation set is large enough and whether the constraints are checked by code.

### How to Choose a Gate

This is general knowledge, not content from the paper: start with this kind of greedy gate; only when the validation score has not moved for several rounds and the validation data is large enough, consider approaches that can accept a worse version or keep several candidates at once.

## Extension: Five Standalone Concept Notes

The five notes below are each self-contained and readable apart from the paper's main thread. They explain the points that the main text above passed over in a sentence but that are the easiest to forget again.

### Localizing and the Subgraph: How the Previous Action Maps to a Node on the Graph

In one sentence: at each step, use "the agent's previous action" to find the current position on the graph, then expand along outgoing edges for a fixed number of steps, and hand only that small piece of the graph to what comes next. This note explains what \( \mathrm{Match} \) and \( N_h \) in Part 1 of Method 2 actually do.

**Where does the previous action \( a_{t-1} \) come from?** It is not computed separately; it is simply the Action line the solver itself wrote in the previous step. The solver prompt specifies that each step outputs exactly one Thought and one Action, in the format `Action: <tool_name>(arg1=val1, ...)` (Appendix B.5), and that line is recorded verbatim in the trajectory. So \( a_{t-1} \) is the last action in the trajectory, for example `fund_raising_request(type='equity', amount=50000000)`.

**What does "exactly matching" actually compare?** The paper only writes "exactly match" and gives no detail:

- Does it compare the whole line (with parameters) or only the tool name? Not stated.
- Nodes can also be reasoning steps or task states (Section 3.1), such as `Decide_Capital` and `Month_Start`, which do not correspond to any tool call. How are they matched? Not stated.
- **Inference:** what is compared should be the tool name, because the refiner prompt requires ACTION nodes to match the available tool names (Rule 1 in Appendix B.5). But in the Appendix B.5 example, the node is named `First_Hop_Retrieve` and the tool `first_hop_retrieve`, differing in case, so the "exact" match probably goes through normalization first.

The paper also shows only the result after matching (the Active Cognitive Node in the serialized example), not the matching step itself.

**What the paper actually says, versus common implementation names**

| Stated in the paper | Not stated (general knowledge or inference) |
| --- | --- |
| Exactly match the most recent action to one node on the graph, giving \( u_t \) | What data structure is used for matching. A common approach is a dictionary lookup: node name to node, and if found it is \( u_t \), otherwise empty |
| From \( u_t \), follow outgoing edges for at most \( h \) steps and collect the nodes and edges reached | This expansion is usually called breadth-first search (BFS): finish one level before going down to the next |
| If nothing matches, use the whole graph; the experiments use \( h=2 \) | How often matching fails |

Dictionary lookup and BFS are just the usual programming names, not content from the paper. Matching looks only at string equality, with no embeddings and no similarity computation, so the result is deterministic.

**Walking through it by hand.** The edge list is below; the first two edges come from the HotpotQA excerpt in Appendix B.5, and the last two are made up for the example:

1. `First_Hop_Retrieve → Scan_Index`
2. `Scan_Index → Bridge_Extract`
3. `Bridge_Extract → Second_Hop_Retrieve` (made up)
4. `Second_Hop_Retrieve → Answer` (made up)

Suppose the agent's previous action is `first_hop_retrieve` and \( h = 2 \):

1. Find the node: the name in the list that matches is `First_Hop_Retrieve`, and this is \( u_t \).
2. Step 1: find the edges whose start is \( u_t \), which gives edge 1, and add `Scan_Index`.
3. Step 2: find the edges whose start is `Scan_Index`, which gives edge 2, and add `Bridge_Extract`.
4. \( h = 2 \), so stop; edges 3 and 4 are not included.
5. \( G_t \) is edges 1 and 2, together with each one's condition, guidance and pitfalls.

When matching fails (the previous action cannot be found on the graph), \( G_t \) is all four edges. The serialized example in Appendix B.5 lists edges grouped as "Hop 1" and "Hop 2", which is consistent with this approach.

**Three details of the expansion:**

- **It follows outgoing edges only, i.e. along the arrow direction.** The nodes already walked through are not in the subgraph; that history is filled in by the window of the last \( w = 3 \) steps of the trajectory.
- **At a fork, all outgoing edges of the same level are collected together.** For example, in the later EnterpriseArena graph, `Decide_Capital` is followed by both `fund_raising_request` and `book_closing`, and both are in hop 1.
- **A made-up example:** the main line of EnterpriseArena is `Month_Start → check_cash_in_bank → cash_flow_forecast_calculation → save_note → check_market_data → Decide_Capital`. If \( u_t \) is `check_cash_in_bank` and \( h = 2 \), then `cash_flow_forecast_calculation` (hop 1) and `save_note` (hop 2) are collected, and it stops there; `check_market_data` is hop 3 and is not included.

**Why take the neighborhood by structure rather than by similarity?** This is the argument in Section 3.2: independent top-k similarity retrieval may miss the connections between steps. For example, it may retrieve the guidance for submit but not the transition from the preceding check_answer, and so miss the verification step that makes submitting reasonable. Taking the neighborhood along the structure brings out an action together with its procedural prerequisites.

### \( \Psi \) and the Solver: Inputs and Outputs Side by Side

At inference time two LLMs each have their own job. \( \Psi \) (the guidance model) reads the graph and writes a short piece of guidance; the solver cannot see the graph, reads only the guidance \( \Psi \) wrote, and then picks the action. The table below lists only what the paper actually gives (the two prompt templates in Appendix B.5), and marks separately what is not clearly stated.

| | \( \Psi \) (guidance model) | solver |
| --- | --- | --- |
| Role | Translate the subgraph into guidance \( g_t \) for right now | Pick the next action \( a_t \) |
| The graph it sees | The serialized local subgraph: node IDs, types and descriptions, plus each edge's condition / guidance / pitfalls, grouped by Hop 1 and Hop 2 | It cannot see the graph, only the \( g_t \) written by \( \Psi \) |
| The trajectory it sees | The last \( w=3 \) steps | The full trajectory \( T_t \) |
| Task description | Yes (the task_description field of the template) | In the system_prompt (inferred) |
| User question \( q \) | Yes (the query field of the template, see point 2 below) | The template has no separate field; inferred to be in the system prompt or the trajectory |
| Instruction | Following the three attributes on the edges, write clear, actionable advice: what to do next, what to avoid, how to recover after a failure, with the concrete command formats, tools and parameters mentioned in the graph | Fixed format: output exactly one Thought and one Action each time, and never write an Observation yourself |
| Output | \( g_t \): free text, with no format specified by the paper | `Thought: ...` followed by `Action: tool_name(arg=val, ...)` |

The overall data flow is the same as the seven-step process in Method 2, and is not repeated here.

Three points are easy to misunderstand:

1. **The solver cannot see the graph itself at all.** Information from the graph reaches it only through \( \Psi \)'s text, so how well \( \Psi \) writes directly determines whether the graph is of any use.
2. **\( \Psi \)'s query field can be read in two ways, and the paper does not settle it.** The prompt in Appendix B.5 describes it as the current active query / observation, while the paper's formula writes it as the user question \( q \). If it is the original question, \( \Psi \) sees the same sentence at every step; if it is the latest observation, \( \Psi \) reacts to what just happened. The latter better explains hints like "avoid: repeating search" in Figure 2, but this is an inference.
3. **The paper does not show the full text of \( \Psi \)'s actual output.** The \( g_t \) in the middle column of Figure 2 is only an illustration.

Below is a made-up example of \( g_t \), an imagined output based on the guidance and pitfalls of the two edges in Appendix B.5, not text from the paper:

> You have just retrieved the first batch of evidence. Next, scan these passages and find the bridge entity that connects to the goal of the question, such as a birth date or place. Do not skip details; missing the name of the bridge entity will make the second-hop search fail.

### One Graph per Benchmark: The Refiner Does Not Choose a Graph or Add a New One

This note tries to answer: if a benchmark contains many kinds of tasks, how can one graph serve them all? First the paper's approach: each benchmark has exactly one graph, and evolution means changing this one graph from \( G_0 \) to \( G_K \); the refiner's input is a single graph and its output is only four kinds of component edits, so there is no decision of "which graph to pick" or "whether to add a new graph".

**Why there is only one graph.** Each column of Table 1 is one benchmark, with one pair of node and edge counts. The refiner's input field is the currently kept graph (current_graph_json in Appendix B.5); its output format has only `add_nodes`, `delete_nodes`, `add_edges`, `delete_edges`, all of them edits to this one graph, with no operation that creates a new graph.

**What "starting from scratch" means.** It refers to a starting graph with just two nodes, Start → End (Modes 4 and 5 in Appendix D.2). The refiner still works by running add_nodes and add_edges on this empty graph; Round 1 of EnterpriseArena is exactly this, adding the whole main line at once (Appendix E.3). So "generating from scratch" is still, in essence, modifying an existing graph.

**What if a benchmark has very diverse tasks?** The paper uses the same graph for the whole benchmark. For example, GDPval covers tasks from different occupations and still has only one graph of 15 nodes, relying on the localization mechanism so that each step takes only a small piece. The paper does not discuss switching graphs by task type, and has not verified the case of multiple graphs or heterogeneous tasks.

**What if one graph holds unrelated subgraphs that should not be connected?** The paper does not discuss this scenario, and does not analyze what happens when one graph holds unrelated subgraphs. The left column of the table below is what the paper states, and the right column is what I infer from it:

| Stated in the paper | Inference |
| --- | --- |
| The structural check lists only endpoints existing, valid types, and every node reaching a terminal; it does not list whole-graph connectivity or reachability from Start (Appendix B.6) | Subgraphs that should not connect can stay separate, as long as the refiner does not add connecting edges |
| Step 1 always localizes at Start and takes the 2-hop subgraph | Start has to connect to the entrance of each subgraph, so the subgraph at step 1 mixes the first two levels of every task type, and \( \Psi \) (which sees the task description and the query) has to filter them itself |
| Localization looks only at which node the previous action maps to | The graph has no path memory: the same node produces the same neighborhood no matter which type of task it is |
| The gate compares the validation-set average and accepts if it is no lower than the old graph | If an edit helps type A but hurts type B, it is accepted as long as the average does not drop; the paper does not break the analysis down by task type |

**An example with a shared node (made up):** two types of tasks both call search. For type A, search is followed by verify; for type B, search is followed by summarize. The graph has only one search node, and both outgoing edges enter the neighborhood, so \( \Psi \) can only guess from \( q \) and the last 3 steps which one to use.

The paper does show that "irrelevant graph content is harmful": in Table 4 (Gemini 3.5 Flash), the whole graph with generative guidance is the worst setting, with an ALFWorld success rate of 54.48 against 81.53 for the local subgraph. Taking a local subgraph is its mitigation, but it works only when localization succeeds and the neighborhood itself is not mixed.

**Conclusion:** the paper does not handle heterogeneous tasks; there is one graph per benchmark, and how unrelated tasks coexist is not explained. It relies on the localization "previous action → node" plus the LLM filtering by \( \Psi \), with no routing by task type. **Inference:** it makes the most sense for tasks with similar procedures, such as EnterpriseArena, which runs the same main line every month; whether a heterogeneous mix on one graph works has not been verified.

### The Refiner's Inputs, the Training Trajectories, and \( H_{rejected} \)

What the refiner sees in each round is "the current graph, this batch of training trajectories, and the history of rejections", plus the task background; each entry of \( H_{rejected} \) records "what was changed last time, what graph it produced, and why it was rejected".

**First, a definition: what is a training trajectory?** It is the full record of the process the solver actually produced on the training problems: for each problem, every step from start to finish with its action and the observation returned by the environment, plus the final score (Section 3.3 Step 1).

$$
X_k = \{ (q_i,\, T_i^{(k)},\, S_i^{(k)}) \}_{i=1}^{|B_k|}
$$

- \( B_k \): the batch of problems drawn from the training set in round \( k \).
- \( q_i \): the question of problem \( i \).
- \( T_i^{(k)} \): the solver's trajectory on this problem, i.e. \( (a_1, o_1, a_2, o_2, \dots) \), actions and observations interleaved.
- \( S_i^{(k)} \): the final score of this problem, from 0 to 1; for binary tasks it is success or failure.

\( C_k \), which appeared in the rejection memory section, is the trajectories in this batch \( X_k \) concatenated and, if necessary, truncated.

In plain words: for a batch of problems, each leaves one record of "the problem, the solving process, and the score", and the refiner compares the processes of high and low scores in this batch of data. The paper's formula writes only actions and observations, but both the Current Trajectory field of the solver prompt and the trace in Appendix C.3 contain Thoughts, so I infer that \( T \) also includes Thoughts.

**The refiner's inputs**

| # | Input | Content |
| --- | --- | --- |
| 1 | The currently kept graph | \( G_{k-1} \), serialized as JSON |
| 2 | This round's training trajectories \( C_k \) | The trajectories produced by running the batch of training problems with \( G_{k-1} \), concatenated; if they exceed \( L_{max} \), the beginning is cut and the end kept |
| 3 | Score per problem | The final score \( S_i \) of each problem, so the refiner can compare high and low scoring trajectories |
| 4 | The rejection history | What \( H_{rejected} \) becomes after SerializeRejections |
| 5 | Task description | What this benchmark is about (appears only in the prompt template in Appendix B.5) |
| 6 | List of available tools | The names of tools the agent can execute, which ACTION nodes must match (appears only in the prompt template) |
| 7 | Mode | One of static_onetime, static_incremental, scratch_onetime, scratch_incremental (appears only in the prompt template) |

The formula in the paper's main text writes only items 1, 2 and 4, a simplified version; items 5 to 7 appear only in Appendix B.5.

**What each entry of \( H_{rejected} \) records**

Each entry records one rejected candidate, in two cases (Algorithm 1):

| Field | Failed validation | Failed structural check |
| --- | --- | --- |
| \( \Delta G_k \): the edit list (JSON) the refiner output that round | Yes | Yes |
| \( G_k^{cand} \): the candidate graph after applying the edits | Yes | May not exist (Appendix B.6) |
| \( X_k \): this round's training trajectories (produced with the graph from before the rejection, \( G_{k-1} \)) | Yes | Yes |
| Outcome | Validation score \( S_k^{cand} \) | Error diagnosis \( d_k \) (no score) |

\( H_{rejected} \) starts out empty and only grows afterwards. Note that the trajectories stored were produced with the graph from before the rejection, \( G_{k-1} \), and the refiner proposed the rejected edit after seeing exactly this batch; the trajectories the candidate graph itself produced on the validation set are not stored, only the score. So what is recorded is the evidence of "why it was changed that way".

**Which part is actually fed to the refiner? The paper gives two accounts and does not decide between them:**

| Location | Account |
| --- | --- |
| Section 3.3 Step 4 | The whole entry goes into \( H_{rejected} \), and the refiner receives \( H_{rejected} \) |
| Appendix B.6 | SerializeRejections hands over only "the candidate graph plus the validation score (or the structural error diagnosis)"; the training trajectories stay in the record, and \( \Delta G \) is not mentioned |

**Inference:** what is actually fed in is probably the B.6 version, because that is the implementation-level description. This way old trajectories do not take up context again, but \( \Delta G \) is not provided, so the refiner has to compare the rejected graph with the current one itself to see what was changed last time.

**Will the context blow up?** The paper does not address this, but at the scale of its experiments it probably will not. The only thing the paper length-limits is the training trajectories \( C_k \) (when they exceed \( L_{max} \), the beginning is cut; the value of \( L_{max} \) is not given); \( H_{rejected} \) itself has no cap, summarization or eviction mechanism, and the algorithm only appends and never clears.

How fast it grows depends on what each entry actually holds: if only the candidate graph and score are kept, an entry is about the size of one small graph (apart from BFCL, each graph has only 7 to 27 edges); if trajectories are fed in too, growth is much faster. The actual number of entries is also small: EnterpriseArena had accumulated only 4 before R10 started. **Inference:** growth is linear; with many rounds, or with a graph as large as BFCL's, you would need to add a cap yourself, for example keeping only the last \( N \) entries, or keeping only the edit list and not the whole graph; the paper has not verified this.

### Seven Baselines: What Each Stores and How It Is Used at Inference

Among the seven comparison methods, one is ReAct with no memory at all, and the other 6 are learning-based. They all use the same ReAct solver, and differ only in "what is stored from the training trajectories" and "how it is put into the prompt at inference time" (Section 4, Appendix B.3). The order follows the paper's "degree of structure" from low to high, and Table 6 has the full comparison.

{{< image src="table6.png" alt="A comparison table of the seven comparison methods, listing what each stores, how it is organized, and how it is used at inference." caption="Table 6 — Comparison of the memory mechanisms in the main experiments. (Source: original paper, Table 6.)" >}}

| Method | What it stores | How it is used at inference |
| --- | --- | --- |
| Vanilla ReAct | Nothing | None; this is the starting point |
| MemoryBank | A per-problem experience summary, with old ones evicted by a forgetting mechanism | Retrieved by relevance (favoring recent ones) and put at the very front of the prompt |
| RAP | Complete past trajectories | The few most similar trajectories are found and put in the prompt as examples |
| ExpeL | Natural-language lessons distilled by comparing successful and failed trajectories | The lessons go into the system prompt, with retrieved successful examples attached |
| AutoGuide | Conditional guidance of the form "in state X, do Y", also extracted by contrasting successes and failures | At each step it first summarizes the current state, then retrieves the matching guidance |
| AWM | Workflows (a text description plus an action sequence) induced from successful trajectories | The workflows are put in the prompt |
| KnowAgent | The available actions and text rules on "which action can follow which" | The whole thing is put in as a fixed prefix of the prompt and is the same at every step |

Two are closest to PG:

- **AutoGuide:** the paper itself says it is the closest (Appendix A.4). It is also "situation maps to action" and also retrieves at every step. The difference is that AutoGuide's pieces of guidance are independent of one another, while PG connects them into a graph.
- **KnowAgent:** the "action transition rules" it stores are conceptually PG's edges, but they are static text with no graph structure, and it does not take just a piece according to the current position.

If either of these beats PG, it is the one most worth a close look, because they are the closest to what PG claims is new.

## Conclusion

PG stores an agent's way of working as a graph with attributes. At inference time it takes only the subgraph reaching 2 hops forward from the current position and has another LLM turn it into guidance; offline, a refiner edits the graph and a separate validation set acts as the gate. Against a memoryless ReAct it wins 23 of 24 cells, but HotpotQA barely improves, and the cost is roughly 1.33 to 1.85 times the tokens.

A few key points to take away:

- A local subgraph plus generative guidance is the best way to use it; the whole graph hurts, especially on ALFWorld, which needs a strict action order.
- An expert graph can make the score collapse on MultiChallenge, and evolution plus the validation gate can rescue it; but when starting from an expert graph, evolution adds nothing extra, and whether starting from an empty graph can catch up with the expert graph cannot be told from the data.
- A small validation set, a gate that accepts ties, and constraints that only live in the prompt are the places that most need care when this mechanism is used in practice.
- What is most worth taking away is the improvement loop itself: propose, gate with a separate validation set, and feed the rejected ones back. It does not depend on the graph and can be applied to any editable text asset.

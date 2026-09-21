---
# weight: 1
title: "Dream-RSI: Replay History as a Free Simulator, Not a World Model"
date: 2026-09-21
lastmod: 2026-09-21
draft: false
description: "Dream-RSI replays discovery-agent history to cheaply test new exploration policies, but its 'World Model' framing overstates what a pure replay mechanism can do."
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

If you've ever built an agent system that iterates on its own improvement logic, you've probably hit this problem: the improvement logic itself should also get better over time, but figuring out "is this new version actually better" usually means spending real money to run a full round first. That's exactly the problem Dream-RSI (Tong Zheng et al., a collaboration between Google, University of Maryland, Google DeepMind, and University of Virginia) sets out to solve. When AI agents are used for scientific or algorithmic discovery — think AlphaEvolve-style systems — an **exploration policy** decides which direction to dig deeper into, when to branch out in parallel, and when to give up on a path. Can that policy improve itself cheaply?

The paper's answer is refreshingly direct: treat the discovery history that's already been generated as a replayable database. To test whether a new policy is good, you don't need to actually re-run any code — let the new policy read the history and ask "what would get revealed if I explored in a different order," and score it from that alone. This lets you screen thousands of candidate policies at near-zero cost. The mechanism is genuinely clever, and the paper's own ablation confirms it beats the more common alternative (summarizing history into a text prompt). But the paper frames the whole thing as using a "World Model" — a label that, on close inspection, doesn't quite match what the mechanism actually does. Beyond walking through the method itself, this post spends some space unpacking that gap, plus a few design habits that hold up even outside this specific paper.

{{< admonition abstract "Key Takeaways (TL;DR)" true >}}
- Dream-RSI treats a completed discovery history (a discovery tree) as a directly replayable database — testing a new exploration policy requires no re-execution at all.
- The ablation shows that treating history as an interactive, replayable simulator beats summarizing it into a text prompt.
- Gains across all three experimental domains are almost entirely about reaching the same quality with less compute, not a capability breakthrough.
- The paper's "World Model" label doesn't hold up: the replay mechanism has no generalization ability and can't evaluate branches that were never explored — it's more accurately described as a sophisticated off-policy replay evaluator.
{{< /admonition >}}

## Where exploration policies get stuck

Using an AI agent for scientific or algorithmic discovery means looping through "propose a candidate → execute and evaluate → revise based on feedback → propose again," and for hard tasks that loop can run thousands of times. Whoever decides how that loop is orchestrated — which direction to dig into, which candidates to expand in parallel, when to switch directions — directly determines efficiency. The paper calls this decision-maker the **exploration policy**.

Existing approaches mostly hard-code a fixed set of rules, so the discovery process never adapts and keeps dumping resources into directions already proven useless. Letting the policy learn online sounds like the fix, but it runs into two bottlenecks. First, evaluating "is one candidate solution good" is fast, but evaluating "is one exploration policy good" is not — you have to let it actually direct an entire discovery loop (potentially hundreds or thousands of iterations) before you know how well it performs. Second, the space of candidate policies is huge, and a new version might perform poorly, so you need to try many versions before finding a good one. Stack the two together, and every candidate policy needs a full, expensive online exploration run just to get feedback — which makes continuously improving the policy slow and costly.

## The core idea: turn exploration history into a replayable simulator

Dream-RSI's key observation is that every online exploration run already records, as a tree, exactly which node branched where, what result it produced, and what score it got. In principle, evaluating "would a different path produce a different outcome" only requires reading that tree — it doesn't require actually re-running any code.

The system alternates between "online exploring" and "offline dreaming" across three stages:

{{< image src="figure1.png" alt="A diagram of Dream-RSI's three-stage loop: online exploration, constructing the replay simulator, and dreaming-based policy improvement, cycling in sequence." caption="Figure 1 — Dream-RSI's recursive self-improvement loop. The current exploration policy first directs a coding agent through real exploration and logs the historical trajectory; the history is converted into a reusable simulator; the agent then \"dreams up\" a large pool of candidate policies inside the simulator, scores them rapidly, and redeploys the best one. (Source: original paper.)" >}}

Stage one (Online Explore) uses the current exploration policy to direct a coding agent through a real discovery loop, logging every attempt as a discovery tree. Stage two (Construct Replay Simulator) folds that tree into a growing history pool. Stage three (Dreaming-based Policy Improvement) imagines a large pool of candidate policies against the history pool, replays each candidate against the stored trees to compute a score, and picks the best-performing version to become the policy that actually gets deployed next round. Once the loop finishes, it returns to stage one and starts a new round with the improved policy.

Notably, only the exploration policy's code changes — the coding agent that actually solves problems, the evaluator that scores them, and the execution interface are all frozen. This "freeze most of the system, let only one small, controllable part self-improve" design is worth noticing as a pattern for dissecting self-improving systems in general, independent of this specific paper.

## The discovery tree: history you can replay but never rewrite

Every node in the discovery tree represents one "generate-and-evaluate" attempt. A node stores more than just a score — it includes a filesystem snapshot, the produced artifact, and evaluation diagnostics, making it a complete, replayable record of that attempt. At any point, only two kinds of nodes can be extended further: root nodes (opening an entirely new branch) or existing leaf nodes (continuing a branch already in progress).

{{< image src="figure2.png" alt="A discovery tree labeled with node scores and parent-child relationships, alongside an alternative exploration policy that replays it in a different expansion order." caption="Figure 2 — The complete history left behind by one online exploration run, which can be replayed by a different exploration policy. (Source: original paper.)" >}}

Online and offline use the same rules for "picking a node, forming a batch," but the underlying logic is completely different. **Online rollout** is genuinely executing, and it's stochastic: the coding agent generates candidates live, the evaluator scores them live, and the same starting point can produce different results run to run. **Offline replay** is deterministic replay: when a root node is selected, it always returns the "earliest-created, not-yet-revealed" child from history — the order is entirely fixed; when an already-expanded node is selected, it directly returns the child already stored in history. In other words, replay never generates anything new — the tree's content is fixed, and the only thing that's alive is "how you choose to walk this tree." That is exactly the one thing that varies between different exploration policies.

This also surfaces a limitation that falls directly out of the formal definition: replay cannot test "what would have happened if a different branch had been opened first," because the reveal order of a root node's children is locked to the order they were originally created — a path that was never taken simply cannot be recovered and evaluated inside replay.

## Avoiding "the winner is always whoever traverses the whole tree"

Looking at the highest score revealed during replay isn't enough on its own — traversing the entire tree always yields that tree's global best score, which fails to distinguish "efficiently finding a good result" from "brute-forcing the whole thing." The paper's replay score is therefore made up of three terms: the highest score among revealed nodes (quality), minus the number of revealed nodes times a coefficient (cost — the more you reveal, the more you're penalized), plus the average number of revealed nodes per round times another coefficient (a parallelism bonus, rewarding policies that know how to batch).

A concrete example makes the design's intent clearest. Suppose two policies operate on the same tree:

| | Nodes revealed | Highest score | Parallelism |
|---|---|---|---|
| Policy A (conservative, sequential) | 3 | 0.58 | 1 per round |
| Policy B (aggressive, batched) | 5 (all of them) | 0.60 | 2 per round, both rounds full |

Policy B has both a higher top score and higher parallelism, but because it revealed two more nodes, the cost term deducts more, and the final computed score actually favors the conservative Policy A. That is the core intent of this scoring formula: it's not simply about who scores highest, but a trade-off between "how good" and "how expensive," with the balance entirely determined by those two coefficients — the paper never states their actual values anywhere in the main text or appendix. Also, a candidate policy's final score is the average of scores computed separately across **all** historical trees, not a score from a single tree — otherwise the chosen policy might just happen to fit that one tree's particular structure.

## A "never gets worse" safety net

Each round of policy improvement works like this: first, let the currently deployed policy replay itself, unchanged, to get a baseline score. Then a policy-development agent (itself an LLM), whose job is to rewrite code, reads this replay record and produces a new version, which also gets replayed and scored. This process repeats for a number of rounds (a system-configured number). Finally, among all candidate versions, the one with the highest replay score is picked to become the policy that actually gets deployed next round.

The candidate pool always keeps the "completely unchanged" original version, so the picked score is never worse than the original — worst case, none of the rewrites improved anything, and you just keep using the original instead of regressing from a bad edit. This design is called **monotonic non-regression**, and it's a simple health-check that any "LLM edits its own logic" system can be checked against: does the candidate set always keep an "unchanged" option as a floor?

That said, this safety net only guarantees "replay score doesn't regress" — it does not guarantee "real online performance doesn't regress" either. That gap is discussed in detail later, in the "Is this really a 'World Model'?" section.

## Three experimental domains: what's saved is compute, not quality

The paper tests Dream-RSI across three domains: algorithm engineering (using the Lasso regularization path as an example), mathematical optimization (Sum-Difference, Autocorrelation, and Circle Packing), and GPU kernel engineering (four tasks from KernelBench). There's a common pattern across all three worth stating up front: nearly every dimension Dream-RSI wins on is "reaching the same quality with less compute," not "quality itself breaking new ground."

In algorithm engineering, Dream-RSI matches or beats the baseline's wall-clock runtime on six held-out downstream tasks, while using one to two orders of magnitude fewer discovery-agent calls:

{{< image src="figure3.png" alt="A table comparing final performance on the Lasso task, alongside a curve showing performance change against cumulative exploration compute." caption="Figure 3 — Lasso regularization-path discovery results. (a) Final wall-clock runtime on six held-out downstream tasks; lower is better. (b) Trajectory of performance as cumulative discovery-agent calls increase. (Source: original paper.)" >}}

Mathematical optimization is the domain where "almost no quality improvement" is most obvious:

{{< image src="table1.png" alt="A performance comparison table across multiple systems on mathematical discovery tasks, covering Sum Diff, Autocorrelation, and Circle Packing." caption="Table 1 — Performance comparison on mathematical discovery tasks. Higher is better for Sum Diff and Circle Packing, while lower is better for Autocorrelation. Best results are shown in bold. (Source: original paper.)" >}}

Dream-RSI reaches comparable scores with far fewer generations than SimpleTES (under 1,000, versus SimpleTES's 51,200), but the actual score gaps mostly sit three or four decimal places out, and on Circle Packing every method converges to the same value.

{{< admonition warning "Being honest: not every metric is a win" true >}}
On Autocorrelation, SimpleTES actually scores slightly better than Dream-RSI (1.453675 vs. 1.456375, lower is better) — the paper itself acknowledges this. This table also puts Gemini-2.0, Qwen3-8B, GPT-OSS-120B, and Gemini-3.0/3.1-Pro side by side in the same comparison, and raw model capability is itself a confounding variable — not a clean, controlled comparison.
{{< /admonition >}}

GPU kernel engineering is where the efficiency gain reads most directly:

{{< image src="figure4.png" alt="Curves showing performance evolving with number of generations across four GPU kernel tasks: VGG16, LayerNorm, ConvDiv, and ConvMax." caption="Figure 4 — GPU kernel engineering results. On VGG16 and LayerNorm, Dream-RSI reaches comparable performance with 2.43× and 1.79× fewer generations, respectively. On ConvDiv and ConvMax, it achieves 2.09× and 1.44× higher performance under comparable discovery budgets. (Source: original paper.)" >}}

Looking at all three domains together, there's a shared blind spot buried in the paper's own efficiency metric: the exploration prompt in the appendix explicitly requires the coding agent, before every proposal, to read through the content of every sibling attempt and every record in the complete history — not sampled, not just the most recent rounds. This blind spot applies across all three domains; it just happens that the Lasso task is the only place the paper reports concrete call counts, so it's worth using to estimate the scale. On Lasso, Gemini-3.7-Flash's online exploration used 32 parallel workspaces per round, each running up to 20 refinement steps, accumulating 1,879 discovery-agent calls across five rounds — and by the start of round five, the previous four rounds had already left thousands of records to read. As the number of rounds grows, in principle the context each API call needs to read only gets longer and more expensive, but the paper's efficiency metric throughout only counts "number of discovery-agent calls" and never accounts for this. Nowhere in the paper is there any summarization, retrieval-based reading, or a cap on how much history gets read. A plausible reason is that the Gemini models the paper uses already have very large context windows, and the experiment scale never actually forced this issue to the surface — but that doesn't mean the mechanism itself has no ceiling. Push the number of rounds further, or swap in a model with a smaller context window, and this "read the entire history" strategy will eventually hit a wall.

## The ablation is the most methodologically valuable part of the paper

More than the three main experiments, the ablation in §5.1 is worth a closer look: it compares "treating history as an interactive replay simulator to actively test against" versus "summarizing history into a text prompt to guide direction." Both paradigms tested (Dream-RSI and another baseline) got worse once the text-prompt guidance was added.

{{< image src="figure5.png" alt="Curves comparing performance on the ConvDiv task when using history as an interactive replay simulator versus using it only as text-based guidance." caption="Figure 5 — Ablation comparison on the ConvDiv task. Using history as an interactive replay simulator outperforms using it only as guidance. (Source: original paper.)" >}}

The paper's interpretation is that in long-horizon, multi-threaded exploration, hard-coding directional suggestions into the prompt actually over-constrains the search space and suppresses exploration diversity. This result is worth placing in a broader context: on the same underlying problem — how to make use of past experience — approaches like ReasoningBank and [WikiSkill](../wikiskill/) take the route of "summarize experience into text knowledge and inject it back in." This ablation points toward "structured, executable replay" outperforming "text-summary-style prompting" in the specific context of exploration policies — but that's a result from one setting, and it doesn't generalize into a claim that summary-based memory methods are broadly inferior to structured replay.

## How exploration behavior evolves across rounds

Another experiment tracks how the learned exploration policy's own behavior changes as recursive rounds accumulate.

{{< image src="figure6.png" alt="Two charts on the ConvDiv task: round-best performance and the number of evaluated attempts per round, both plotted across recursive rounds." caption="Figure 6 — Evolution of exploration behavior on ConvDiv. (a) Round-best performance across rounds. (b) Number of evaluated attempts per round. (Source: original paper.)" >}}

The paper observes a clear adaptive pattern: early on, while performance is still improving quickly, the policy tends to be conservative, spending resources digging deeper into a few promising-looking branches. As performance approaches a plateau and progress slows, the policy shifts toward more aggressively opening new branches and widening the search. This "early convergence, late divergence" behavior isn't a hard-coded rule — it's something the policy learns on its own from historical replay, echoing, to some degree, the `plan_grid()` logic in the paper's appendix that dynamically adjusts exploration width and depth based on history.

## Is this really a "World Model"?

The paper frames the whole mechanism as analogous to a "World Model," echoing Dreamer-style model-based RL systems. But that analogy is worth pulling apart.

A genuine world model is a trained function: input "current state plus action," output "next state plus reward." Take Dreamer as an example — it first compresses high-dimensional input (like game frames) into a low-dimensional latent state, then learns a function that predicts the next step inside that compressed space. The entire "dreaming" process rolls out an imagined future trajectory entirely within latent space, never touching the real environment. What makes this mechanism valuable is its ability to **generalize** to state-action combinations that have never actually been visited — otherwise it could only replay things that have already happened, which would be pointless.

Dream-RSI's "replay simulator" doesn't have this ability. It stores nodes that have already happened, verbatim, and replays them — there's no function doing generalization or interpolation anywhere. If a branch was never explored, replay is simply empty for it and produces no prediction to evaluate. A more accurate positioning: it's a sophisticated off-policy replay evaluation mechanism, not a world model capable of predicting unknown states.

{{< admonition tip "A portable habit of judgment" true >}}
The next time a paper claims to use a "simulator," "world model," or "imagination," the first question worth asking is: **can it evaluate possibilities that never actually happened?** If yes, it's a genuine model. If no, it's a replay mechanism — still valuable, but with a ceiling locked to "things that have already happened."
{{< /admonition >}}

This gap also connects directly to the safety net discussed earlier: monotonic non-regression guarantees that "replay score won't regress," but the replay-to-real gap has two independent sources. The first is whether the replay score formula's own weights (the cost and parallelism-bonus coefficients) are set correctly — even if replay could see every possible path in the universe, wrong coefficients would still push the chosen policy toward something that isn't actually optimal. The second is that a replay context is, after all, a historical context, not a real environment — even with perfectly tuned coefficients, replay can still only choose among branches that have already been walked, and cannot evaluate any possibility that was never explored; this limitation doesn't go away just by tuning parameters. The paper does attempt a fix for the first source (the appendix designs a mechanism that recalibrates the coefficient defaults based on the previous round's real performance), but it has no particular solution for the second — it can only rely on the overall Dream-RSI loop itself: every round adds another tree to the history pool, so the world the simulator can replay keeps growing. But that only expands the "known world" after the fact — it doesn't solve the in-the-moment limitation that, at the point of any given round's decision, the simulator simply cannot see possibilities that haven't happened yet.

## The engineering details hidden in the appendix are worth more than the main text

The paper's appendix includes an approximately 270-line prompt that guides the policy-development agent responsible for rewriting the exploration policy. A few of its design choices are, taken on their own, more practically useful than the formulas in the main text.

**The prefix-only constraint**: every decision the policy makes may only use "nodes this particular replay has itself actively revealed so far" — never the score of an unrevealed node, or any "god's-eye-view" information. This prevents cheating — scanning the whole tree upfront for the highest score and pretending exploration happened to find it — because real online deployment offers no such opportunity to cheat, since the online tree hasn't even grown yet. This restriction — decisions can only use what's currently known, never peek at the future or the global picture — is a standard requirement in reinforcement learning and online algorithms called the **causality constraint**. It isn't something Dream-RSI invented. Any mechanism that "offline-evaluates an online decision system using historical data" can be checked against this exact line.

**A three-way split for batch decisions**: each round selects up to W candidate nodes to form a batch, and the prompt requires composing it from three roles — exploitation (extending the currently most promising line normally), exploration (opening a new branch, or digging deeper into an under-explored one), and recovery (at most one, a genuinely repairable failed attempt). This is fundamentally the classic multi-armed bandit explore-exploit trade-off, but with an added recovery role that isn't part of the traditional bandit framework, because "failure" here might just be an implementation bug rather than the direction itself being bad. The rules explicitly require recovery to take at most one slot, never crowd out exploitation's slot, and never use a fixed quota — it has to be decided dynamically based on current evidence.

**A four-way failure taxonomy**: hard-unrecoverable (definitely can't be fixed), repairable implementation failure (the idea might be fine, it's an implementation bug), weak-but-underexplored (mediocre score but not yet tried deeply enough), and repeatedly unpromising (there's already enough evidence this direction genuinely doesn't work). One easily overlooked detail: code running to completion without throwing an error doesn't mean "success" — the produced solution might simply fail to satisfy correctness conditions, which is a normal evaluation that produced a weaker solution, not something that should be dumped into the "repairable failure" bucket and retried. And no classification is ever a permanent verdict — even if a branch is judged hard-unrecoverable, a single subsequent successful result reopens the possibility for that branch.

This four-way taxonomy resembles the classic transient (temporary failure, worth retrying) / permanent (permanent failure, retrying is pointless) dichotomy from distributed systems, but adds a state the traditional dichotomy doesn't have: weak-but-underexplored is neither a temporary error nor a permanent failure — it's "not enough samples yet to draw a conclusion," closer to the statistical notion of insufficient sample size than to any error type in traditional retry logic. This framework is directly reusable for designing an agent's tool-calling error handling: structural, rule-codifiable errors (rate limits, schema validation failures) are well-suited to automatic retry or interception at the harness level, with no need for LLM judgment; errors that require semantic judgment (this tool keeps failing — should I switch approaches?) are the ones worth passing to the LLM — and what the system prompt should provide there is judgment principles, not an exhaustive error-code lookup table. That's exactly how the B.2 prompt itself is written.

## Conclusion

Dream-RSI's core engineering insight is real: reframing a completed exploration history as a data structure that supports off-policy evaluation, used to cheaply screen improved versions of an exploration policy instead of expensive online trial and error — and the ablation genuinely confirms it beats simply summarizing history into a text prompt. But the contribution doesn't carry the weight the paper's framing suggests. Across all three experimental domains, the real gains almost entirely cluster around "reaching the same quality with less compute," not a capability breakthrough — and the "World Model" framing has a substantive gap from an actual world model that can generalize to unseen states. A more accurate description is a sophisticated off-policy replay evaluation mechanism.

More than the paper's own contribution, a few design patterns tucked away in the appendix's policy-improvement prompt are worth remembering: always keeping the "unchanged" original version in the candidate pool to guarantee monotonic non-regression; the causality constraint that decisions may only use currently-revealed information; a batch portfolio that adds a recovery role beyond plain explore/exploit; and a failure taxonomy that identifies a third state — "insufficient evidence" — beyond just "temporary failure" and "permanent failure." These design choices hold up independently of this specific paper, and are directly borrowable heuristics for anyone building a self-improving system or designing an agent's error-handling logic.

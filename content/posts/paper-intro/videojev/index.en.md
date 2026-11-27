---
# weight: 1
title: "VideoJev: Why Video LLMs Should Score, Not Write"
date: 2026-11-27
lastmod: 2026-11-27
draft: false
description: "VideoJev replaces token generation with candidate scoring for video timestamps and QA: 100x faster than Thinking models, only 1.2x-1.6x over Instruct."
featuredImage: "featured-image.png"

tags: ["Vision Language Model", "Inference Optimization", "Fine-Tuning", "Mixture of Experts"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## Video Models Don't Need to Write Answers Token by Token

On the same 1,549 LVBench multiple-choice video questions, Qwen3.5-4B Thinking spends 144.9 seconds per question on average, while VideoJev-4B takes 1.12 seconds. The gap comes from how answers are produced rather than model size: standard multimodal large language models (**MLLM**s) write answers one token at a time, whereas VideoJev turns both finding event timestamps and answering multiple-choice video questions into **candidate scoring**. In a single pass through the model, it reads internal representations at the candidate and decision markers and feeds them to one shared scoring layer, without generating any answer tokens.

- Event timestamps: slice the video into time bins as candidates, judge each bin independently, and pick the single continuous stretch of video with the highest combined score.
- Multiple-choice QA: treat the given answer options as candidates and use **softmax** (which turns raw scores into probabilities summing to 1) to pick the highest-probability choice.
- Shared prefix: compute the video **prefix** (the video frame data at the start of the input) once, then answer follow-up questions one by one (Cached) or all together (Joint).

{{< admonition warning "Two caveats before reading the numbers" >}}
Every experiment in the paper runs in a closed-world setup where questions, answer options, and event queries are supplied upfront; the paper's pitch of using VideoJev inside an agent workflow appears only in Future Work and is never tested. Also, the headline 'over 100× faster' compares against long-reasoning Thinking models; when we break down the tables below, the gap against direct-answer Instruct models is much smaller.
{{< /admonition >}}

Paper: [VideoJev (arXiv 2610.18615)](https://arxiv.org/abs/2610.18615) (2026/10).

## Why Small Decisions in Video Shouldn't Be Generated

[Video understanding](../video-deep-research/) relies heavily on two structured 'small decisions': **temporal grounding** takes an event description and finds its start and end timestamps in the video, while **multiple-choice Video QA** picks one answer from options like A through D.

Both answers are tiny, yet current MLLMs still generate them token by token. The paper highlights three bottlenecks with that approach:

1. Generation is expensive: producing a single option letter or a few timestamp digits can still take over a hundred seconds in long-reasoning mode (as in the opening LVBench comparison; full numbers in Table 2 below).
2. Discriminative classifiers are fast but rigid: traditional classifiers only handle fixed label sets and lack an LLM's ability to match arbitrary natural-language descriptions.
3. Videos are often queried repeatedly: recomputing the entire video's visual input for every single question wastes compute.

Temporal grounding adds a structural requirement: the output must be one **contiguous** time interval rather than scattered seconds. The next section's binning and decoding steps are built around that rule.

## How One Scoring Head Handles Both Grounding and QA

### Input Layout and Scoring Head: One Video Prefix, Two Readout Positions

Both tasks share the upper half of the pipeline: the model sends each candidate's hidden state into Eq. (1) to produce a raw score \( s \) (a **logit**, a real-valued score before probability conversion), and training and inference both branch from that same \( s \). Temporal grounding applies **sigmoid** (squashing each real score into a 0-to-1 probability) independently to each bin, trained with **BCE** (binary cross-entropy) and **Soft IoU** (a differentiable version of **IoU**, which measures overlap between predicted and ground-truth intervals). Multiple-choice QA applies softmax across all options and trains with **cross-entropy (CE)**.

| Stage | Temporal Grounding | Multiple-Choice QA |
| --- | --- | --- |
| Shared | Hidden state -> Eq. (1) -> score \( s \) | Hidden state -> Eq. (1) -> score \( s \) |
| Training | \( \sigma(s) \) -> BCE (Eq. 2) + Soft IoU (Eq. 3) | softmax -> cross-entropy (Eq. 5) |
| Inference | Subtract threshold -> max-sum segment (Eq. 4) | Pick highest-probability option |

{{< image src="figure2.png" alt="Three-panel overview: (a) time intervals represented as timestamps share the same input layout as text options; (b) Cached inference computes the video prefix once then processes each question suffix separately, while Joint inference processes the full batch in one forward pass; (c) time scores form event intervals and option scores select the answer." caption="Figure 2 — VideoJev architecture overview: candidate scoring and shared video computation (scores and reference intervals are illustrative) (Source: original paper, Figure 2.)" >}}

A single forward pass reads the whole sequence, yet the model only extracts hidden states at two special marker positions: `<|option_end|>` at the end of each candidate, and `<|decide|>` at the very end of the question. For example, a 20-second video sampled at 4 fps yields 40 time candidates; the video prefix is computed once, and each question appends its own suffix:

```text
[Video prefix: image tokens + timestamps] -> computed once
[Instruction] [Question] [Candidate 1 <|option_end|>] [Candidate 2 <|option_end|>] ... [Candidate 40 <|option_end|>] [<|decide|>] -> one per question
```

The scoring head's job is straightforward: map the question-level decision summary and each candidate into equal-length direction vectors, measure how closely their directions align (closer means higher score), scale the result, and add a baseline offset. Concretely, after reading `<|decide|>`'s hidden state \( h_d \) and the \( i \)-th `<|option_end|>` hidden state \( h_i \), Eq. (1) projects them to 512 dimensions with two separate linear projections \( W_q, b_q \) and \( W_k, b_k \), normalizes both to unit vectors \( u \) and \( v_i \), takes their dot product \( u^\top v_i \) (cosine similarity in \( [-1, 1] \)), multiplies by a fixed factor of 10, and adds one learnable scalar bias \( b \) to get candidate \( i \)'s logit \( s_i \):

$$
u=\frac{W_q h_d+b_q}{\|W_q h_d+b_q\|_2},\quad v_i=\frac{W_k h_i+b_k}{\|W_k h_i+b_k\|_2},\quad s_i=10\,u^\top v_i+b
$$

Take a 2-dimensional vector example: suppose \( u=(0.8, 0.6) \) and \( v=(0.6, 0.8) \); their directions align closely with a cosine similarity of 0.96, giving \( s=9.6 \) when \( b=0 \). The paper does not explain why the scale is fixed at 10 or why vectors are unit-normalized; my guess is that scaling sharpens the softmax distribution. The architecture also trims the tail of the language **backbone** (the core language model): VideoJev removes the final-layer **MLP** (multi-layer perceptron) and replaces the vocabulary output head with this scoring head, which **ablation** (removing a component to measure score impact) shows changes scores by under 0.2 points. The bias \( b \) only matters for temporal grounding's sigmoid and cancels out completely in QA's softmax (proof in Further Reading below).

{{< fold title="Details: why remove the final-layer MLP and swap the output head? (with Table 7)" tone="info" >}}
A standard LLM's final layer runs attention -> MLP -> hidden state \( h \) -> output head -> full-vocabulary logits -> next token. VideoJev instead reads \( h \) before the final MLP and replaces the output head with the Eq. (1) scorer. The paper cites FreeRet to state that pre-MLP features work better for semantic similarity without offering its own analysis; my guess is that the final MLP mainly serves next-token prediction and becomes redundant once generation is removed.

Table 7's ablation confirms the impact is tiny: removing the final MLP averages 65.3 (temporal grounding) and 74.3 (QA), compared to 65.1 and 74.1 when keeping it.

{{< image src="table7.png" alt="Ablation table comparing VideoJev-4B without the final-layer MLP (baseline) versus keeping it across three temporal grounding and four Video QA benchmarks, with deltas." caption="Table 7 — Effect of removing the final-layer MLP (VideoJev-4B) (Source: original paper, Table 7.)" >}}
{{< /fold >}}

{{< fold title="Details: how video tokens interleave with timestamps, from hidden states to seconds" tone="info" >}}
An LLM's input is just a sequence of vectors: text tokens look up embedding vectors and image tokens come from the vision encoder, and once inside the language model they are treated identically. Timestamps are text tokens interleaved beside every pair of frames to mark the seconds. Temporal grounding candidates are not chosen by the model; they are sliced sequentially from the video at two frames per candidate (\( K = \text{frames} \div 2 \)), independent of the query text. Each candidate label uses the two frames' midpoint rounded to one decimal place, such as \( (12.00 + 12.25) \div 2 = 12.125 \) formatted as `12.1s`, while labels and boundaries still use unrounded timestamps. The paper does not specify the exact prefix layout beyond saying candidate timestamp strings are copied from the video prefix; my guess is that VideoJev follows the Qwen convention of interleaving one timestamp per frame group.

After a forward pass, every position outputs a vector of the backbone's hidden dimension \( d \) (the paper does not report \( d \)), yet the model only reads `<|option_end|>` and `<|decide|>` positions and ignores video, instruction, and question outputs. Under causal attention, \( h_i \) sees the video, question, and earlier candidates, while \( h_d \) at the end sees everything. The paper does not explain how a candidate attends to its matching frames; my guess is that matching timestamp strings in the candidate and video prefix let attention align them.

| Step | Action | Illustrative Seventh-Bin Example |
| --- | --- | --- |
| 1 | Read hidden states | \( h_7 \) and \( h_d \) |
| 2 | Project to 512-dim unit vectors | \( v_7 \) and \( u \) (one \( u \) per question, one \( v \) per bin) |
| 3 | Dot product x 10 + \( b \) for logit | \( s_7 = 10\,u^\top v_7 + b \), assume 2.2 |
| 4 | Convert to probability via sigmoid | \( p_7 = \sigma(2.2) \approx 0.90 \) |
| 5 | Select one high contiguous segment via Eq. (4) | Assume bins six through 9 (independent of the main-text 10-bin decoding example) |
| 6 | Convert to seconds | Left edge of the sixth bin to right edge of the ninth bin |
{{< /fold >}}

### Temporal Grounding in Four Steps: Bins, BCE, Soft IoU, and Decoding

Temporal grounding turns a continuous video into scorable candidates in four steps: binning, per-bin yes/no classification, whole-interval overlap loss, and contiguous decoding. Step 1 is **binning and labeling**: the backbone merges every two adjacent frames (twofold temporal compression) into one bin. At evaluation, videos are sampled at 4 fps, making each bin about 0.5 seconds; a 20-second video has 80 frames, or \( K = 40 \) bins, named by their midpoint (e.g., `<12.1s>`). If bin \( i \)'s time \( t_i \) falls inside the union of annotated event intervals \( G \), its label \( y_i \) is 1, otherwise 0:

$$
y_i=\mathbb{1}\{t_i\in G\},\qquad K=\frac{\text{frames}}{2}
$$

Figure 2(a) confirms the 4 fps slicing: two adjacent frames sit at 00:12.00 and 00:12.25, 0.25 seconds apart. Part 3.1 of the paper leaves an unresolved ambiguity, stating that training videos are sampled at 2 fps without specifying per-task settings, which admits two readings:

- Reading (a): temporal grounding also trains at 2 fps, meaning ~1-second bins in training vs. 0.5-second bins at test time, a width mismatch the paper does not discuss.
- Reading (b): 2 fps refers to QA or general settings while grounding trains at 4 fps, keeping bin widths consistent.

Step 2 is **per-bin yes/no scoring (BCE, Eq. 2)**: because an event spans multiple bins that must all be able to say 'yes' at once, each bin gets its own independent sigmoid probability \( p_i = \sigma(s_i) \), and binary cross-entropy penalizes each bin before averaging across all \( K \) bins:

$$
\mathcal{L}_{BCE}=-\frac{1}{K}\sum_{i=1}^{K}\Big[y_i\log p_i+(1-y_i)\log(1-p_i)\Big],\qquad p_i=\sigma(s_i)
$$

BCE's blind spot is that it judges each bin in isolation and never sees whole-interval coverage (temporal grounding is evaluated by **IoU**, predicted-vs-ground-truth overlap divided by union, averaged across queries as **mIoU**). Step 3 therefore adds differentiable **Soft IoU (Eq. 3)**: \( d_i \) is bin \( i \)'s duration (canceling out when bins have equal width), the numerator is the intersection (only event bins with \( y_i=1 \) contribute), and the denominator is the union (event bins count in full, while non-event bins add whatever probability \( p_i \) the model over-predicted):

$$
\mathcal{L}_{IoU}=1-\frac{\sum_i d_i\,p_i\,y_i}{\sum_i d_i\,[\,y_i+p_i(1-y_i)\,]}
$$

Take a 10-bin illustrative example (we will reuse these summary figures for decoding and total loss without listing every individual bin): suppose ground truth spans the sixth through bin 9 (four bins), and the model assigns probabilities between 0.6 and 0.9 to those four bins (the last one is 0.6), summing to a numerator of 3.2. The denominator adds those four ground-truth bins to the over-predicted probabilities outside the event for a total of 5.0, giving Soft IoU 0.64 and loss 0.36 (the same 10 bins have a per-bin BCE loss of about 0.21). In practice this term matters: Table 6 shows adding Soft IoU lifts average mIoU across three grounding benchmarks from 60.7 to 65.3 (+4.6).

{{< image src="table6.png" alt="Ablation table comparing VideoJev-4B trained with BCE/CE only versus adding Soft IoU across three temporal grounding and four Video QA benchmarks, with deltas." caption="Table 6 — Effect of Soft IoU supervision (VideoJev-4B, deltas relative to BCE/CE baseline) (Source: original paper, Table 6.)" >}}

Step 4 is **decoding one contiguous interval (Eq. 4)**. The intuition is simple: bins above a threshold earn positive points, bins below lose points, and we pick the contiguous span with the highest total score. Concretely, convert the probability threshold \( \tau = 0.25 \) into logit space as \( \log\frac{\tau}{1-\tau} \approx -1.10 \), subtract it from each bin's logit to get weight \( w_i = s_i + 1.10 \) (\( w_i > 0 \) is equivalent to \( p_i > \tau \)), and run **Kadane's algorithm** (a single \( O(K) \) linear scan that finds the maximum-sum contiguous subarray) to obtain \( (a^\star, b^\star) \), outputting the left edge of bin \( a^\star \) to the right edge of bin \( b^\star \):

$$
w_i=s_i-\log\frac{\tau}{1-\tau},\qquad (a^\star,b^\star)=\arg\max_{1\le a\le b\le K}\sum_{i=a}^{b}w_i
$$

Continuing the 10-bin illustrative example (2 seconds per bin): ground truth is the sixth through bin 9 (10 to 18 seconds), but the adjacent fifth bin happens to exceed the 0.25 threshold (earning positive weight), so the maximum-sum subarray selects the fifth through bin 9 with a sum of about 10.83 and outputs 8 to 18 seconds. Against the 10 to 18 seconds ground truth, Hard IoU is 0.8.

{{< fold title="Details: how BCE penalizes bins, why non-event bins have probabilities in Soft IoU, and s vs. p" tone="info" >}}
Because the answer is a continuous span rather than a fixed set of options, discretizing into time bins lets the model score each bin. BCE grades a row of yes/no questions: when the label is 1, lower probability costs more (\( -\log p \)); when the label is 0, higher probability costs more (\( -\log(1-p) \)). Each bin must use an independent sigmoid so multiple event bins can be 'yes' together instead of competing under softmax. In the 10-bin example, the average penalty across all bins is BCE (~0.21), and the ninth bin — even though 0.6 is above 0.5 — lacks confidence and incurs a 0.51 penalty, the highest of any bin.

One common trap in Soft IoU: bins outside the event still have model probabilities \( p \); they only vanish from the intersection \( p \times y \) because \( y=0 \) multiplies them to 0. They remain in the union denominator as over-predicted mass that lowers IoU. Conversely, inside the event \( y=1 \) makes \( p \times y = p \), which can create the illusion that only event bins carry probabilities.

On the \( s \) in Eq. (4): the real model first computes an unbounded real logit \( s \) via Eq. (1), then converts it to a probability \( p \) in \( (0, 1) \) with sigmoid. Useful landmarks: \( s=0 \) gives \( p=0.5 \), \( s=2.20 \) gives \( p=0.90 \), and \( s=-1.10 \) corresponds to threshold \( \tau=0.25 \). Because Eq. (4)'s \( w = s - \log(\tau/(1-\tau)) = s + 1.10 \) already subtracts the threshold and \( p > \tau \) is equivalent to \( w > 0 \), decoding works directly on \( s \) without converting back to probabilities. Since the paper gives no real \( s \) values, our illustrative examples pick \( p \) first and invert via logit.
{{< /fold >}}

{{< fold title="Details: why not just threshold bins directly? Four interval-selection rules compared" tone="info" >}}
A plain threshold only tells you which bins pass; it does not say how to assemble them into one contiguous span. Eq. (4) also has a threshold \( \tau \); the real distinction is that threshold value and segment-selection rule are two separate choices.

Consider another illustrative set of probabilities (unrelated to the 10-bin decoding example, using point-sum summaries): all three rules use threshold 0.7, the fifth bin is a brief dip inside the event, and the tenth bin is a stray false positive far away.

- Rule A (leftmost to rightmost): stretched all the way to the tenth-bin false positive, dropping IoU to 0.75.
- Rule B (longest contiguous run): split in half by the fifth-bin dip so only half survives, dropping IoU to 0.50.
- Rule C (Eq. 4 maximum sum): convert each bin to \( w = s - \log(0.7/0.3) \). The fifth bin only loses 0.44 while both sides add 8.24 (the third bin and bin 4 add 3.45, the sixth through bin 8 add 4.80), so bridging the dip pays off for a third-through-bin-8 total of 7.80. The tenth bin adds only 0.25 after crossing the ninth bin's -3.04 penalty, so it is rejected. Result: exact match, IoU 1.00.

| Rule | Method | Weakness |
| --- | --- | --- |
| A: Leftmost to rightmost | Span from first to last bin above threshold | One distant false positive stretches the whole interval |
| B: Longest contiguous run | Take the longest unbroken run above threshold | A single mid-event dip splits the event in two |
| D: Expand from peak | Start at highest-probability bin and expand until below threshold | Stops at any dip; fails completely if the peak is a false positive |
| C: Maximum sum (Eq. 4) | Add/subtract weights and find max-sum contiguous span | Needs a threshold; too low a threshold lets barely-passing bins stretch the span |

This comparison of decoding rules is general modeling knowledge rather than paper content: when probabilities are clean and events are simple, Rules A or B are easy to debug; when scores jitter with dips or false positives, Rule C balances trade-offs (all four output a single interval). Note that the paper never benchmarks Eq. (4) against simple thresholding and never compares threshold 0.7 vs. 0.25, so its experiments alone do not prove this decoding rule beats simple thresholds on these benchmarks.
{{< /fold >}}

### Multiple-Choice QA and Task Comparison: Competing Options

Multiple-choice QA reuses the exact same input layout, readout positions, and Eq. (1) scoring head, simply swapping the suffix candidates for the question's option text (4 or 5 options per training question instead of video bins). Because exactly one option \( y \) is correct, Eq. (5) applies softmax so the \( K \) option probabilities sum to 1 and compete, then takes the negative log probability of the correct option as cross-entropy loss:

$$
p_i=\frac{\exp(s_i)}{\sum_{j=1}^{K}\exp(s_j)},\qquad \mathcal{L}_{CE}=-\log p_y
$$

Pushing up the right option's score automatically pushes down the others. Using Figure 2(c)'s three illustrative probabilities (0.72, 0.18, 0.10, with scores back-computed), the loss gap depending on which option is correct is stark; at inference time, options stay in their original order and the model picks the highest-probability choice:

| If Correct Answer Is | Assigned Probability | Cross-Entropy Loss |
| --- | --- | --- |
| A | 0.72 | 0.33 |
| B | 0.18 | 1.71 |
| C | 0.10 | 2.30 |

To keep the model from memorizing option positions, training applies a reproducible, label-independent shuffle to eligible questions and updates the target label accordingly. For example, if the answer was A and shuffling moves it to C, the label updates to C. Questions whose wording explicitly references option positions or prior conversation turns keep their original order to preserve meaning.

| Component | Temporal Grounding | Multiple-Choice QA |
| --- | --- | --- |
| Candidates | Time bins (sliced from video) | Option text from the question |
| Candidate count \( K \) | Frames \( \div 2 \) (e.g., 40) | 4 or 5 (training data) |
| Scoring | Eq. (1), shared head | Eq. (1), shared head |
| Probabilities | sigmoid (independent bins) | softmax (competing options) |
| Loss | BCE + Soft IoU | cross-entropy |
| Output | Contiguous segment via Eq. (4) | Highest-probability option |

## Multi-Question Inference and the Two-Stage Training Recipe

### Cached vs. Joint Inference: Sequential Arrival vs. All-at-Once

Since one video often fields many questions, VideoJev computes the video prefix \( V \) once; the difference lies in how question suffixes attach. **Cached** runs one forward pass (**[prefill](../../ai-concept/vllm-agentic-serving/)**) on the video prefix, caches it, and branches off to score each incoming question independently, fitting scenarios where questions arrive over time. **Joint** appends every question (prompt, candidates, and `<|decide|>`) behind the same prefix and scores them in one forward pass under standard **causal attention** (each position can only see itself and earlier tokens, never later ones). Joint requires all questions to be available upfront, and training uses this same concatenated layout.

| Currently Reading (Three-Question Example) | Cached Sees | Joint Sees |
| --- | --- | --- |
| \( Q_1 \) | \( V \), \( Q_1 \) | \( V \), \( Q_1 \) |
| \( Q_2 \) | \( V \), \( Q_2 \) | \( V \), \( Q_1 \), \( Q_2 \) |
| \( Q_3 \) | \( V \), \( Q_3 \) | \( V \), \( Q_1 \), \( Q_2 \), \( Q_3 \) |

In Joint mode, later questions can see earlier questions' prompts and options, but never any answers. The paper states it kept standard causal attention to preserve **FlashAttention** (a memory-saving, fast low-level attention kernel), without quantifying that trade-off; it also claims to have verified that no answer leakage occurs, without explaining how.

From basic systems intuition (the paper does not spell this out): Cached runs a new forward pass and re-reads the cached prefix for every additional question, whereas Joint amortizes that into one pass. More questions per video widen Joint's advantage, while a single question sees no difference. Figure 3's 4B curves show this split clearly.

{{< image src="figure3.png" alt="Two line plots with questions per video (1 to 10) on the x-axis and average model time on a log y-axis: (a) temporal grounding and (b) multiple-choice QA, comparing Cached (solid/dotted) versus Joint (dashed) with ten-question latency and accuracy labeled at the right ends." caption="Figure 3 — Multi-question efficiency of 4B models: average forward time for 1 to 10 questions per video (Source: original paper, Figure 3.)" >}}

### Two-Stage Training: Same Quality, Lower Backbone Update Cost

Training runs in two stages, one **epoch** (full pass through that stage's data) each; the **vision encoder** that reads frames and the **merger** (connector layer into the language model) stay **frozen** (weights never updated) throughout:

1. Stage One (30% of videos): train only the new scoring head, using BCE for temporal grounding and CE for QA.
2. Stage Two (70% of videos): unfreeze the language backbone and the **token embeddings** (input vectors) of the two new special tokens alongside the scoring head, adding Soft IoU with weight 2 for grounding while keeping CE for QA.

$$
\begin{aligned}\text{Stage 1:}\quad & \mathcal{L}_{TG}=\mathcal{L}_{BCE},\qquad \mathcal{L}_{QA}=\mathcal{L}_{CE}\\\text{Stage 2:}\quad & \mathcal{L}_{TG}=\mathcal{L}_{BCE}+2\,\mathcal{L}_{IoU},\qquad \mathcal{L}_{QA}=\mathcal{L}_{CE}\end{aligned}
$$

Plugging in the 10-bin illustrative example (BCE ~0.21, Soft IoU loss 0.36) gives a Stage Two grounding loss of \( 0.21 + 2 \times 0.36 \approx 0.93 \); the paper does not say how the weight of 2 was chosen.

The paper explains that warming up the scoring head first gives it a stable representation space (borrowing from multimodal projector alignment). My guess is that a randomly initialized head produces noisy gradients at first, which could disrupt pretrained weights if backpropagated straight into the backbone.

Table 8's ablation delivers a pragmatic verdict: two-stage training does not win on quality. Two-stage averages 65.3 (grounding) and 74.3 (QA), while single-stage training on all videos reaches 65.4 and 74.7. The real reason for two stages is training cost: Stage One skips backbone updates, so the backbone only updates on 70% of videos. As for 'potentially more stable', the paper never verifies it. Full hyperparameters live in part 3.1 of the paper.

{{< image src="table8.png" alt="Comparison table of VideoJev-4B two-stage training (baseline) versus single-stage training on all videos across three temporal grounding and four Video QA benchmarks, with deltas." caption="Table 8 — Two-stage vs. single-stage training (VideoJev-4B, baseline warms up the head on 30% of videos then jointly trains on 70%) (Source: original paper, Table 8.)" >}}

{{< fold title="Details: which parameters train in each stage, and is the backbone full fine-tuning or add-on weights?" tone="info" >}}
The paper never states whether the language backbone uses full-parameter fine-tuning or **LoRA** (low-rank adaptation, a memory-saving method that trains small add-on weights); neither 'LoRA' nor 'adapter' appears in the text. My guess is full fine-tuning based on three clues: first, backbone learning rates are 5e-6 (4B) and 2e-6 (35B-A3B), typical for full fine-tuning whereas LoRA usually runs one to two orders of magnitude higher (general practice); second, 4B uses DeepSpeed ZeRO-2 and 35B-A3B uses ZeRO-3, which shard optimizer states and gradients (with ZeRO-3 also sharding parameters) and are standard for full training; third, Appendix A.3's autoregressive baseline also fine-tunes Qwen3.5-4B at 5e-6 while freezing only the vision encoder and merger. The paper never tests LoRA and never reports head-only scores after Stage One; Table 8's single-stage run trains everything together.

| Component (Data-Flow Order) | Stage One | Stage Two |
| --- | --- | --- |
| Vision encoder, merger | Frozen | Frozen |
| Language backbone | Frozen | Trained |
| Token embeddings (`<\|option_end\|>`, `<\|decide\|>`) | Frozen | Trained |
| Scoring head | Trained | Trained |

- Language backbone: if full fine-tuning, all Transformer attention and MLP weights update (inference); whether the general vocabulary embedding table and 35B-A3B's **MoE** (Mixture of Experts) router and experts all update is unspecified (the appendix only notes the router stays FP32 at inference), and the removed final-layer MLP sits off the forward path with no gradient (inference).
- Token embeddings: `<|option_end|>` and `<|decide|>` each add one length-\( d \) input vector initialized from pretrained `<|im_end|>`, frozen in Stage One and trained in Stage Two with an unspecified learning rate; only input embeddings are needed because the output head was replaced by the scorer (inference).
- Scoring head: Eq. (1)'s \( W_q, b_q, W_k, b_k \) and scalar \( b \) (the fixed 10 is non-learnable), totaling about \( 2 \times (512d + 512) + 1 \approx 1024d \) parameters across two \( d \to 512 \) linear layers. The paper omits \( d \); if \( d \) is 2,000-4,000 (typical for multi-billion models), that is roughly 2M-4M parameters, three orders of magnitude smaller than the 4B backbone. Weights initialize from a 0.005-std Gaussian with bias 0, using learning rates 3e-4 in Stage One and 1e-4 in Stage Two.
{{< /fold >}}

## Results: Accuracy, Speed Breakdown, and Cached vs. Joint

### Accuracy: Sweeps Same-Backbone Instruct, Trails 4B Thinking Slightly

Accuracy spans 7 benchmarks: average mIoU across 3 grounding benchmarks (3,363, 4,500, and 1,541 test queries) and average accuracy across 4 multiple-choice QA benchmarks (1,549, 2,700, 1,337, and 2,174 questions). Baselines come in two modes: **Instruct** outputs the answer directly, while **Thinking** generates a long reasoning trace first. On both the 4B dense model and the 35B-A3B [Mixture-of-Experts (MoE)](../sparse-upcycling/) model, VideoJev beats same-backbone Instruct on both tasks; trailing 4B Thinking by 0.6 points on QA is the only loss, and Thinking pays over 100x the latency for it:

| Comparison | Grounding mIoU | QA Accuracy |
| --- | --- | --- |
| 4B: VideoJev vs. same-backbone Instruct | 65.3 vs. 58.6 (+6.7) | 74.3 vs. 66.3 (+8.0) |
| 4B: vs. strongest open 4B grounding baseline TimeLens2-4B | 65.3 vs. 62.0 (+3.3) | — |
| 4B: vs. same-backbone Thinking | — | 74.3 vs. 74.9 (-0.6) |
| 35B-A3B: vs. same-backbone Instruct | 67.7 vs. 56.9 (+10.8) | 79.5 vs. 73.8 (+5.7) |
| 35B-A3B: vs. same-backbone Thinking | — | 79.5 vs. 78.8 (+0.7) |

{{< fold title="Full benchmark tables: original Table 1 (Temporal Grounding) and Table 2 (Multiple-Choice Video QA)" tone="note" >}}
{{< image src="table1.png" alt="Full temporal grounding results table comparing proprietary models, 4B open models, and 30-35B MoE models on Charades, ActivityNet, and QVHighlights (R1@0.3/0.5/0.7, mIoU, average, and latency)." caption="Table 1 — Temporal grounding results (generative models default to Instruct mode, VideoJev uses Joint inference; click to zoom) (Source: original paper, Table 1.)" >}}

{{< image src="table2.png" alt="Full multiple-choice Video QA results table comparing proprietary models, 4B open models, and 30-35B MoE models on LVBench, Video-MME, LongVideoBench, and MLVU (accuracy, four-benchmark average, and latency)." caption="Table 2 — Multiple-choice Video QA results (Source: original paper, Table 2.)" >}}
{{< /fold >}}

### Speed: 'Over 100x Faster' Depends Entirely on the Baseline

The table below reports average forward time per question (in seconds): grounding is measured on Charades test (3,363 queries across 1,313 videos), and QA on LVBench (1,549 questions across 103 videos). VideoJev is timed in Joint mode, while baselines share the video prefix and generate each answer separately:

| Task & Scale | VideoJev | Same-Backbone Instruct | Same-Backbone Thinking |
| --- | --- | --- | --- |
| Grounding 4B | 0.276 | 0.763 (2.8×) | — |
| Grounding 35B-A3B | 0.336 | 1.054 (3.1×) | — |
| QA 4B | 1.123 | 1.355 (1.2×) | 144.929 (129×) |
| QA 35B-A3B | 1.493 | 2.379 (1.6×) | 149.777 (100×) |

- The headline 'over 100× faster' compares against Thinking mode (129× and 100×).
- Against direct-answer Instruct, multiple-choice QA is only 1.2× and 1.6× faster (computed from Table 2 latencies).
- The 2.8× to 3.1× gain on temporal grounding is a fairer comparison, since generating timestamp strings inherently takes longer than reading scores.

One more condition applies: those headline latencies use Joint mode, which assumes every question is known upfront. In an interactive agent loop where questions arrive one by one, Cached inference is the realistic regime.

### Cached vs. Joint: Batching Wins on 13 of 14 Test Pairs

Comparing Joint against Cached using the exact same trained model weights (**checkpoint**, Table 4): across 2 models × 7 benchmarks (14 pairs total), Joint actually scores higher on 13 of them. On 4B, Joint leads by 0.8 on grounding and 0.5 on QA; on 35B-A3B, it leads by 0.3 on grounding and 0.7 on QA. By contrast, an **autoregressive** (token-by-token) Direct baseline on LVBench (implementation details omitted here) drops from 60.0% under Cached to 58.7% under Joint, while VideoJev rises from 67.1% to 67.9%, showing Joint does not hurt accuracy.

{{< image src="table4.png" alt="Comparison table of VideoJev-4B and VideoJev-35B-A3B under Joint inference (baseline) versus Cached inference across three temporal grounding and four Video QA benchmarks, with deltas." caption="Table 4 — Cached inference vs. Joint inference (Source: original paper, Table 4.)" >}}

## Limitations and Unanswered Details in the Paper

Beyond the closed-world evaluation boundary noted earlier (pre-supplied questions, options, and queries, untested agent workflows in Future Work, and Joint-mode headline speeds), several implementation details remain unspecified:

- Grounding decoding edge cases: when every bin has a negative \( w_i \), the system falls back to the highest-probability bin, yet the paper never specifies what 'lightweight boundary post-processing' does, how 'smoothing window = 1' smooths anything (my guess is window 1 means no smoothing), how \( \tau = 0.25 \) was picked, or why simple thresholding was never compared.
- Multiple-choice shuffling details: the paper does not clarify whether option letters are re-indexed after shuffling (our A-to-C example assumes re-indexing, which is an inference) and does not report the pre-shuffle answer distribution.
- Other scattered gaps: why Eq. (1) fixes the scale at 10 and unit-normalizes, the trade-off of keeping standard causal attention (to preserve FlashAttention) and how non-leakage was verified, how Soft IoU weight 2 was chosen and whether two-stage training improves stability, the 2 fps training vs. 4 fps evaluation bin-width ambiguity, and whether backbone training is full fine-tuning or add-on low-rank weights (LoRA), the token-embedding learning rate, and whether 35B-A3B's MoE router updates.

## Three Takeaways You Can Reuse

Three portable lessons from VideoJev you can use when evaluating other video models or designing your own:

1. Skip token generation for structured small decisions: pack time bins or answer options into one sequence, score them in one forward pass with a shared head, and compute the video prefix once. When questions arrive in a batch, Joint is both cheaper and slightly more accurate than Cached on 13 of 14 test pairs.
2. Always ask 'compared to what, and in which mode?' on speed claims: VideoJev beats same-backbone Instruct across the board on accuracy, yet 'over 100× faster' is against Thinking mode; against Instruct QA it is 1.2× to 1.6×, and sequential agent queries must look at Cached rather than Joint.
3. Align the training loss with the evaluation metric: use softmax for exclusive choices and sigmoid for independent bins; per-bin BCE misses whole-interval overlap, so adding Soft IoU adds 4.6 mIoU, paired with logit-space maximum-sum decoding.

## Further Reading: Three Modeling Principles Beyond This Paper

### Logits, Sigmoid, and Softmax: Independent Checks vs. Competing Choices

A **logit** is the model's raw real-valued score; sigmoid and softmax both turn scores into probabilities, differing in whether candidates **compete with each other**. Viewed uniformly, sigmoid is just a two-class softmax with the second class fixed at 0: the first entry of \( \mathrm{softmax}([s, 0]) \) is \( e^s/(e^s+1) = \sigma(s) \):

$$
\sigma(s)=\frac{1}{1+e^{-s}},\qquad \mathrm{logit}(p)=\log\frac{p}{1-p},\qquad \mathrm{softmax}(s)_i=\frac{e^{s_i}}{\sum_j e^{s_j}}
$$

Because multiplying numerator and denominator by \( e^c \) cancels out, adding a constant \( b \) to every score leaves softmax completely unchanged, whereas for independent sigmoids it shifts the threshold. Suppose three options have base scores 9.00, 7.61, and 7.03 (score = base + \( b \)); changing \( b \) from 0 to \( -8 \) leaves the softmax column frozen while transforming the sigmoid column:

| \( b \) | Scores \( s \) | softmax | sigmoid |
| --- | --- | --- | --- |
| 0 | 9.00, 7.61, 7.03 | 72.0%, 17.9%, 10.0% (sum 100%) | 99.99%, 99.95%, 99.91% (sum ~300%) |
| -8 | 1.00, -0.39, -0.97 | 72.0%, 17.9%, 10.0% (sum 100%) | 73.1%, 40.4%, 27.5% (sum ~141%) |

The same holds in temporal grounding: suppose three bins have cosine similarities 0.9, 0.5, and 0.1 (base scores 9, 5, and 1). At \( b=0 \) all three exceed 0.5; shifting \( b \) to \( -6 \) moves their probabilities to 0.953, 0.269, and 0.007, leaving only the first bin above 0.5. Softmax implementations exploit this same shift invariance by subtracting the maximum score first to avoid exponential overflow:

```python
e = exp(s - max(s))
p = e / sum(e)
```

- Exactly one answer (single-label) -> softmax with cross-entropy; probabilities sum to 1 and compete.
- Independent yes/no per item (multi-label) -> sigmoid with BCE; probabilities need not sum to 1.
- Thresholding, summing, or fusing signals -> work directly in logit space, converting thresholds via \( \log\frac{\tau}{1-\tau} \).
- Bias or constant shift -> affects sigmoid only, never softmax.

The logit formula \( \log\frac{p}{1-p} \) is simply the inverse of sigmoid: \( p/(1-p) \) is the odds (ratio of happening to not happening), and taking its log gives log-odds. A model's raw output behaves like log-odds because training through sigmoid and BCE forces it onto that scale. The name comes from logistic regression in statistics, and machine learning broadened it to mean raw pre-probability scores (general knowledge):

$$
p=\frac{1}{1+e^{-s}}\ \Rightarrow\ e^{s}=\frac{p}{1-p}\ \Rightarrow\ s=\log\frac{p}{1-p}
$$

| Score \( s \) | Probability \( p=\sigma(s) \) | Odds \( p/(1-p) \) | Log-Odds |
| --- | --- | --- | --- |
| -1.10 | 0.25 | 0.333 (1 to 3) | -1.10 |
| 0 | 0.50 | 1 | 0 |
| 1.0 | 0.731 | 2.718 | 1.0 |
| 2.2 | 0.900 | 9 (9 to 1) | 2.20 |

Softmax follows a different relation: \( s_i = \log p_i + c \), where \( c = \log \sum_j e^{s_j} \). On the same illustrative scores \( (9.00, 7.61, 7.03) \), probabilities are about \( (0.72, 0.18, 0.10) \) and log probabilities are about \( (-0.33, -1.72, -2.30) \); subtracting log probability from each score yields about 9.33 everywhere, which is why softmax is shift-invariant.

### Why Per-Bin Correctness Does Not Equal Interval Quality

Summing per-bin penalties does not equal whole-interval quality. Suppose ground truth spans the third through bin 6 (4 bins): Model A misses 2 event bins (assigning 0.1), while Model B over-predicts 2 non-event bins (assigning 0.9), with identical penalties on all other bins. Both models have the exact same BCE of 0.54, yet their Hard IoU diverges:

| Metric | Model A: Misses 2 Bins | Model B: Over-Predicts 2 Bins |
| --- | --- | --- |
| Penalty per wrong bin | \( -\ln 0.1 = 2.30 \) | \( -\ln(1-0.9) = 2.30 \) |
| BCE | 0.54 | 0.54 |
| Hard IoU | \( (4-2)/4 = 0.50 \) | \( 4/(4+2) = 0.67 \) |

BCE ties because every wrong bin costs the same; IoU splits because for a \( g \)-bin event, missing \( m \) bins gives \( (g-m)/g \) while over-predicting \( m \) bins gives \( g/(g+m) \), which is strictly larger, meaning misses hurt IoU more than extra bins. The fix is adding a differentiable **surrogate loss** for the global metric alongside the per-bin loss. VideoJev's BCE + 2 x Soft IoU raises average mIoU from 60.7 to 65.3 (+4.6, Table 6 above).

### Hard IoU vs. Soft IoU: Training Signal vs. Evaluation Metric

**Hard IoU** operates on final binary decisions (each bin is either in or out of the predicted span), dividing overlap length by union length and averaging across queries to get mIoU. It cannot be differentiated directly for training (general knowledge) because thresholding is a step function with gradient 0 almost everywhere, giving no smooth signal between 0.49 and 0.51. **Soft IoU** replaces binary decisions with continuous probabilities \( p \); it matches Hard IoU whenever \( p \) is strictly 0 or 1 and takes four lines of Python:

```python
def soft_iou_loss(p, y, d):
    inter = sum(d * p * y)
    union = sum(d * (y + p * (1 - y)))
    return 1 - inter / union
```

Training Soft IoU and evaluation Hard IoU move in the same direction, yet their values can differ sharply. On the same 10-bin illustrative predictions (ground truth sixth through bin 9), three methods produce three distinct numbers:

| Method | Result | Meaning |
| --- | --- | --- |
| Soft IoU (training) | IoU 0.64, loss 0.36 | Blends overlap and confidence |
| Hard IoU, threshold 0.5 | 1.00 | Predicted sixth through bin 9 match ground truth exactly |
| Hard IoU, Eq. (4) decoding (\( \tau=0.25 \)) | 0.80 | Outputs fifth through bin 9 (8 to 18 seconds) |

In this example, a plain 0.5 threshold hits the exact span because of the threshold value (the fifth bin clears 0.25 but not 0.5) rather than the decoding rule; the paper does not compare thresholds. Soft IoU also penalizes correct bins whose confidence sits between 0.6 and 0.9, whereas Hard IoU only judges the final span, so the two correlate without being equal.

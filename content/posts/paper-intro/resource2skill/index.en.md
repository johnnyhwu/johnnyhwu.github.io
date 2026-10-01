---
# weight: 1
title: "Resource2Skill: Video Alone Beats Code, Articles, Artifacts Combined"
date: 2026-09-30
lastmod: 2026-09-30
draft: false
description: "Microsoft Research's Resource2Skill distills tutorial videos, code, articles and artifacts into a hierarchical skill library, gaining 11.9 points across seven domains."
featuredImage: "featured-image.png"

tags: ["Large Language Model", "Single-Agent", "Agent Memory"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

{{< admonition abstract "Key Takeaways (TL;DR)" >}}
1. **What it does**: Resource2Skill automatically distills four kinds of resources (tutorial videos, codebases, articles, reference artifacts) into a hierarchical skill library (the Skill Wiki), improving scores by 11.9 percentage points on average across 7 creative domains and 4 models.
2. **The most solid finding**: a skill library distilled from videos alone (66.8% on average) beats the other three resource types combined without video (59.4%). This resource-source ablation is the most cleanly controlled experiment in the paper.
3. **Two gaps**: the baselines in the main result have no skill library at all, so "a good method" cannot be told apart from "having a skill library"; and how raw resources are actually distilled into skills is described so thinly that it cannot be copied.
4. **The takeaways worth keeping**: look for confounders first, a skill library has a saturation point (about 200 skills in the paper), don't assume vector retrieval beats lexical retrieval, and layer your validation instead of discarding on a binary check.
{{< /admonition >}}

## Introduction

Ask an agent to make a slide deck, crunch an Excel sheet or build a 3D scene, and it usually gets stuck not on facts but on *how to do it*: which tool mode to use, how to break the task down, what to check along the way, how to recover from errors. Existing skill libraries mostly supply this procedural knowledge through hand-written skills, or by mining the agent's own operation logs (for example [SkillOpt](../skillopt/) and [WikiSkill](../wikiskill/)). Tutorial videos, the most natural material humans use to learn this kind of software, have barely been used in a systematic way.

Resource2Skill (Microsoft Research, arXiv 2606.29538) sets out to fix exactly that: it automatically distills four kinds of resources (tutorial videos, codebases, articles and reference artifacts) into a hierarchical skill library (the Skill Wiki) that an agent can retrieve from and execute efficiently. The paper reports an average gain of 11.9 percentage points across 7 creative domains and 4 models, and also beats off-the-shelf [harnesses](../../ai-concept/harness-engineering/) such as [Claude Code](../../ai-concept/claude-code/) and Codex.

My verdict up front: the paper's **research value is low**, because the core retrieval and selection mechanism is a combination of existing components rather than a new method. Its **engineering reference value is low-to-medium, with clear gaps**: the skeleton of the system (schema, acceptance pipeline, execution interface) is worth studying, but the paper says very little about how raw data is actually distilled into skills, which is the most critical technical detail, so you cannot copy a complete pipeline from it.

What is really worth keeping are a few intuitions the large-scale experiments verify: a skill library has a saturation point, pure vector retrieval is not necessarily better than lexical retrieval, and code executability should be validated in layers rather than as a binary discard. This article walks through the paper's method and results in order, then spends a full section on the lessons that hold independently of the paper itself, which are the part worth taking away after reading the whole paper.

## Problem Setup

Following the procedural-knowledge gap from the introduction, existing skill libraries come from roughly three sources: written by hand, accumulated from the agent's own operation logs, or mined from text or code resources. Resource2Skill points at a neglected source: **tutorial videos**. A video conveys the temporal order of operations, the visual effect of every step and design choices that are hard to put into words, none of which text carries completely; but stuffing a whole video into an agent's context is too expensive and too verbose.

The core problem the paper tackles is how to automatically distill a high-dimensional multimodal resource like a video into skills an agent can retrieve and execute efficiently, without losing the information unique to video.

## Core Method

{{< image src="figure1.png" alt="Resource2Skill distills four kinds of resources (tutorial videos, codebases, articles, reference artifacts) into a hierarchical Skill Wiki covering seven creative-software domains." caption="Figure 1 — The big picture of Resource2Skill: multimodal resources go in, a hierarchical skill library comes out, evaluated across seven creative domains. (Source: original paper.)" >}}

### The Skill Data Structure

Each skill is a four-element tuple plus metadata:

$$s = (p,\ x_{\text{text}},\ x_{\text{visual}},\ x_{\text{code}},\ m)$$

| Symbol | Meaning |
|---|---|
| \(p\) | The skill's path in the domain's taxonomy tree, e.g. `blender/lighting/jewelry` |
| \(x_{\text{text}}\) | Name, mechanism, applicability, inputs, expected effect |
| \(x_{\text{visual}}\) | Thumbnails, screenshots, render previews, charts (may be empty) |
| \(x_{\text{code}}\) | Executable or adaptable code snippets (may be empty, in which case it is a "reference-only" skill) |
| \(m\) | Metadata: category, tags, source type, validation status, used for filtering, auditing and tracing |

**Why visuals are a first-class citizen**: in common skill-library formats, such as Anthropic's Agent Skills specification (`SKILL.md` plus `scripts/`, `references/`, `assets/`), images and examples usually just go into the generic `assets/` folder, with no schema-level difference from any other attachment.

Resource2Skill writes \(x_{\text{visual}}\) explicitly into the core tuple of the skill definition because the paper's central thesis is that visual and temporal information cannot be replaced by text, a thesis that the resource-source ablation later on (Table 3 below) backs up. If your skill-library format does not treat visuals as first-class, it is by design assuming that visual information does not matter, and that assumption does not necessarily hold.

One practical detail worth noting: \(x_{\text{visual}}\) is resolved lazily. A thumbnail is normally just a path reference, and is only loaded as an actual image when the agent asks for the visual modality, so it does not count against the text-token budget. In other words, having visual content does not necessarily raise the cost of every call, which is why making visuals first-class is feasible in engineering terms rather than idealism.

### Comparison with Anthropic's Agent Skills Format

If your organization has already adopted Anthropic's Agent Skills standard (`SKILL.md` containing YAML frontmatter plus instructions, alongside `scripts/`, `references/` and `assets/`), note that it does not follow the same logic as Resource2Skill, and a forced conversion will break some things:

| Carries over directly | Breaks, and you have to rebuild it |
|---|---|
| \(x_{\text{code}}\) → `scripts/` | The mechanism where \(x_{\text{visual}}\) is "resolved on use and kept out of the text-token budget", which Anthropic's standard does not distinguish |
| \(x_{\text{text}}\) → the body of `SKILL.md` | The hierarchical taxonomy plus two-stage retrieval (covered below); Anthropic's standard has the model read each skill's description to judge relevance, which is an entirely different retrieval logic |
| `meta.json` → the YAML frontmatter of `SKILL.md` | The `exec_ok` acceptance gate, which is not part of the file format but a step in Resource2Skill's own pipeline, so it does not automatically exist after you switch formats |

The paper itself also makes this comparison in Related Work: Anthropic's Agent Skills are a skill library that is "hand-written, with no automated acquisition mechanism", while Resource2Skill's selling points are precisely automated distillation, video as a source and hierarchical classification. The two come from different design philosophies; neither replaces the other.

### The Four-Stage Pipeline

{{< image src="figure2.png" alt="Resource2Skill's four-stage pipeline: resource collection, distillation into skills, five acceptance gates, and storage in a hierarchical Wiki; at run time MetaBrowse retrieves candidates, the language model picks, skills are applied to the domain software via MCP, and the same pipeline is invoked online to fill gaps when the candidate pool falls short." caption="Figure 2 — The overall Resource2Skill pipeline, from resource collection to the skill library, then to run-time retrieval and online gap filling. (Source: original paper.)" >}}

The pipeline has four steps: resource collection → distillation with one vision-capable LM call (\(f_\theta\)) → five acceptance gates (\(A_D\)) → storage in the hierarchical Wiki by taxonomy path. At run time the agent picks skills with MetaBrowse's two-stage retrieval and applies them to the actual domain software through MCP; when the candidate pool cannot produce a usable skill, the same \((f_\theta, A_D)\) is triggered on the fly to fill the gap.

**The distillation step (\(f_\theta\))**: in essence one vision-capable LM call, with deterministic preprocessing in front (key frames extracted from videos, code blocks grabbed from codebases via AST, articles split into paragraphs) and deterministic postprocessing behind (output format normalized, a SHA1 computed as the skill ID). The paper stresses that this step is **not** a trained model, just prompt engineering plus structured output.

{{< admonition warning "What the paper doesn't make clear" >}}
How "key-frame sampling" works is not explained at all: is it fixed-interval, scene-change detection, or aligned with the narration? The paper itself argues in its introduction that the value of video lies in visual effects and temporal order, yet much of that information is actually spoken aloud by the instructor in the narration, and the pipeline description never mentions a speech-to-text (ASR) step. Whether speech is truly unused, or used but left out of the paper, cannot be determined from the text alone. In addition, the prompt template has never been released, there is no human spot-check of distillation quality, and the logic for splitting one video into multiple skills is likewise unexplained. If you want to apply this pipeline to your own data, this part, which is also the most technically demanding and the one that most needed to be spelled out, offers almost nothing to copy, and you would have to design it from scratch.
{{< /admonition >}}

**The five acceptance gates**: all are deterministic rule checks, not LLM-as-judge, each verifying a different element of the skill tuple:

| Gate | What it checks | How |
|---|---|---|
| Completeness | \(m\), \(x_{\text{text}}\) | Required frontmatter fields, minimum length of \(x_{\text{text}}\), at least one non-empty modality |
| Provenance | \(m\) | Whether `source_path` points to a resource actually recorded in the connector manifest |
| Deduplication | \(m\) | `SHA1(domain, source_path, node_index)` serves as the skill ID; a collision merges into the existing entry |
| Modality consistency | \(m\) vs. \(x_{\text{visual}}\), \(x_{\text{code}}\) | Whether each claimed modality really has a corresponding file on disk |
| Structural executability | \(x_{\text{code}}\) | Actually run the code once in a sandbox: does it execute, and does it produce a non-trivial result |

The design most worth remembering among these five gates is what happens when executability fails: **the skill is not discarded outright but downgraded to "reference-only"**. Code that has not been validated is never executed directly by the agent (to avoid running unverified code in production), yet the principles and effects described by \(x_{\text{text}}\) and \(x_{\text{visual}}\) remain usable, and the agent can rewrite the code from the description. This design splits "is this code trustworthy?" and "is this knowledge valuable?" into two independent judgments, instead of crudely handling both with a single binary switch (pass / discard).

If you want to add validation to your own skill library (for example the `scripts/` in the Anthropic Skills format), this is a cheap idea worth adopting directly: run a lightweight smoke test on each skill's script; scripts that pass run as usual, and for those that don't, note "reference only" in `SKILL.md` so the agent falls back to reading the description and rewriting the code itself, rather than having the whole skill discarded or forced to run with unreliable code.

{{< admonition warning "Two practical reservations" >}}
The paper's validation is done once when the library is built offline, and the result is hard-coded into the metadata. If your scenario involves internal tools whose versions keep changing, that validation result will go stale, and you need to decide yourself whether to re-run it periodically; this is a real difference between the paper's setting (relatively stable public tutorial resources) and an enterprise setting. In addition, the Modality consistency gate only checks "does the file exist" and not the **content quality** of \(x_{\text{visual}}\), meaning whether the image is actually relevant and clear; none of the five gates guards against that.
{{< /admonition >}}

**The execution stage**: `apply` is the only execution action. It sends the selected skill's code through MCP into domain software that is actually running (for example headless Blender), backed by a "capabilities manifest"; unsupported operations return a structured "cannot do this" message instead of a plain error. `render` turns whatever the domain software actually produced into a format the judge can understand: screenshots, rendered images, audio. The judge **only looks at the rendered output, never at the source files or code**, so even if the code logic is correct, the score is still docked if the rendered result looks poor.

**Online acquisition**: when retrieval cannot produce a usable candidate, the same \((f_\theta, A_D)\) is called on the fly to search for resources, distill and validate them, and the results go into a separate "online pool" that is **not** merged back into the offline wiki. This is a deliberate experimental control, so that online search does not make the offline library grow with use and confound the other experimental comparisons.

{{< image src="table2.png" alt="Table comparing offline-only and offline-plus-online skill acquisition: online gap filling makes almost no difference on the standard task set, but a large difference on the task set the offline library does not cover." caption="Table 2 — Offline vs. online skill acquisition (overall score, %). (Source: original paper.)" >}}

Quantitatively (Table 2): on the standard task set \(T_{\text{standard}}\), turning on online gap filling makes almost no difference (+0.7pp), but on \(T_{\text{novel}}\), a task set designed specifically to test what the offline library does not cover, the same 100 online skills lift the score from 41.2% to 62.8% (+21.6pp). The paper's conclusion is that online search is "for filling gaps", not "for everyday extra points": if your offline library already covers enough, expecting extra gains from online gap filling is unrealistic; but when users really hit a scenario the library lacks, this route can recover more than 20 percentage points of performance.

### Skill Retrieval and Selection: MetaBrowse in Two Stages

**Stage one (lexical filtering to narrow the candidate pool)**:

$$C_K(q) = \text{TopK}_{s \in \Sigma_D}\ \text{BM25}\big(q,\ \text{name}(s) \oplus \text{tags}(s) \oplus \text{applicability}(s) \oplus p(s)\big)$$

Here \(q\) is the user's task request, \(\Sigma_D\) is the domain's full skill library, and \(\oplus\) is string concatenation: a skill's name, tags, applicability and **taxonomy path \(p(s)\)** are all joined into one document and matched against \(q\), with \(K\) set to 20 in the paper.

The key design is to put the taxonomy path \(p(s)\) into the matched text as well, so that "where the skill sits in the taxonomy tree" directly affects the lexical score. In the paper's own words, the aim is for the library to "favour skills sitting in topically relevant subtrees", rather than treating the whole wiki as a heap of loose skills and matching against all of them. For example, if the query is "render a jewelry ring with dramatic lighting", a skill at `blender/lighting/jewelry-macro` already gets term overlap with the query, and thus score, from "lighting" and "jewelry" in its path alone; a skill at `blender/geometry/procedural-terrain` has almost no overlap, so its chance of even entering the candidate pool is low.

**Stage two (the language model selects a subset)**:

$$S(q) = \pi_\phi\big(q,\ \{\Phi(s) : s \in C_K(q)\}\big)$$

\(\pi_\phi\) is the language model itself, not a specially trained selector; \(\Phi(s)\) is what skill \(s\) exposes under the current configuration (metadata plus the opened text, visual and code views); the number of skills actually selected is \(n=5\). This step "selects a subset" rather than "ranks and takes the top-\(n\)", so the language model can select 0 skills and let the agent fall back to writing code itself. That differs from an ordinary recommender's top-K ranking: the selector has the power to "reject everything".

Behind this two-stage design sits a counterintuitive experimental result: the "Other Ablations" section below uses the actual numbers in Table 5 to show that pure vector retrieval does worse than pure lexical retrieval on this task.

## Main Results and a Key Blind Spot

{{< image src="table1.png" alt="Main comparison table: w Skills versus w/o Skills and two off-the-shelf harnesses, across seven domains and the average score." caption="Table 1 — Main comparison (overall score, %). The image covers four backbones; the text table below only excerpts the GPT-5.4 block. (Source: original paper, Table 1.)" >}}

| System | Web | Excel | Reaper | PPT | Blender | CAD | UE5 | Avg. |
|---|---|---|---|---|---|---|---|---|
| w Skills | 82.4 | 76.4 | 77.3 | 64.8 | 44.1 | 55.7 | 67.3 | 66.9 |
| w/o Skills | 68.7 | 58.6 | 73.2 | 55.4 | 29.5 | 48.7 | 29.1 | 51.9 |
| ClaudeCode-H | 81.6 | 69.2 | 75.8 | 61.6 | 36.7 | 53.3 | 35.7 | 59.1 |
| Codex-H | 79.8 | 70.4 | 76.1 | 62.3 | 35.9 | 53.0 | 36.3 | 59.1 |

Across 28 model-domain cells, w Skills beats w/o Skills in every one, and a paired Wilcoxon test gives \(p < 10^{-3}\) on all 9 sampled cells (mostly \(p < 10^{-8}\)), which is statistically solid. w Skills also beats the stronger of the two harnesses in 26 of 28 cells, with the largest gain in the UE5 domain (+30 to 40pp). The paper's reading is that a free-form code agent has a hard time assembling a passing scene from scratch through the UE5 Python API, and often falls below the minimum quality threshold and scores 0.

There is a very real blind spot here: **whether what wins is Resource2Skill's pipeline design itself or simply the coarser variable of "having a skill library or not", the paper's experimental design cannot separate**. For the two baselines `ClaudeCode-H` and `Codex-H`, the paper itself states in Appendix C that no Skill Wiki is mounted and web search is not allowed (Codex-H is even set to `web search to cached`, turning off live browsing too), so they just brute-force it with a general-purpose harness. In other words, Table 1 actually compares "has a skill library" against "has no skill library and isn't allowed to go find one", and the capability gap between the two other than the skill library is not separated out.

The paper has another set of experiments (Section 4.3.1, `Flat` vs. `Our Wiki` vs. `w/o Skills`) that responds to this question to some extent: the `Flat` condition turns skill content into a plain-text, unstructured flat list, removing taxonomy browsing, metadata filtering, visuals and code. The scores relate as follows:

- `w/o Skills`: 51.9% on average (see Table 1)
- `Flat` (plain-text flat list): a notch above `w/o Skills`, landing 2.5 to 8.2pp below `Our Wiki`, at roughly 58.7 to 64.4%
- `Our Wiki` (full hierarchical multimodal): 66.9% on average (see the "w Skills" row of Table 1)

This suggests that the contribution of the skill library's "form of organization" (hierarchical multimodal vs. flat text) is smaller than one might think, and most of the gain comes from the coarser variable of "having a skill library or not".

Note, though, that the skill content in the `Flat` condition is still produced by Resource2Skill's own distillation method, only with a different presentation. That is, the paper tested "the contribution of the form of organization" but never tested "the contribution of the distillation method's own quality": whether a cruder distillation, or even a hand-written skill library, would end up just as good is never touched, which is the paper's biggest validity gap methodologically.

## Ablation: The Resource-Source Mix (the Most Solid Experiment in the Paper)

{{< image src="table3.png" alt="Ablation table for the resource-source mix, comparing removing video, video only, and various source combinations." caption="Table 3 — Ablation on the resource-source mix (overall score, %). (Source: original paper.)" >}}

Holding everything else fixed and changing only which source families were used to collect resources:

| Source combination | Web | Excel | Reaper | PPT | Blender | Avg. |
|---|---|---|---|---|---|---|
| Code + Article + Artifact (no video) | 71.3 | 61.6 | 74.2 | 57.4 | 32.7 | 59.4 |
| Video only | 81.1 | 73.7 | 75.6 | 62.4 | 41.3 | 66.8 |
| Video + Code | 82.0 | 75.2 | 76.3 | 62.9 | 41.6 | 67.6 |
| Video + Article | 81.9 | 74.4 | 77.8 | 63.7 | 42.9 | 68.1 |
| Video + Artifact | 81.6 | 74.8 | 76.4 | 63.5 | 42.4 | 67.7 |
| All four | 82.8 | 75.8 | 78.1 | 64.2 | 43.8 | 68.9 |

Removing video drops the average from 68.9% to 59.4%, a fall of nearly 10 percentage points. More notable still, **video only** (without the other three sources) actually beats "the other three sources combined but without video" by 7.4 percentage points, so video alone contributes more than the other three sources together. The steepest drops are in Excel (−14.2pp) and Web (−11.5pp), and the paper's reading is that the order of operations and the on-screen changes in these domains are hard for text to carry completely. This is a fairly cleanly controlled set of experiments, changing a single variable (the resource source) and fixing everything else, and it is the most defensible finding in the paper.

{{< admonition question "Something the paper doesn't address but is worth doubting" >}}
Was the number of skills collected from video sources matched to the other three sources before comparing? If tutorial videos are simply easier to find in large quantities of high quality than articles or codebases, then "video wins" could be partly because "there is more data", and not entirely because "the video modality inherently carries more information". The paper does not control the variable of resource quantity. This is a reasonable doubt, but the paper itself offers no evidence that could confirm or refute it.
{{< /admonition >}}

## Skill Library Size: Diminishing Returns

Holding the agent, judge, brief and wiki interface fixed, the skill library is grown from 0 to full size and tested on 5 core domains, which gives a very clean curve: performance rises monotonically as the library grows and **saturates at around 200 skills**. The 0-to-200 stretch captures most of the gain (Reaper gains only +3.1pp, Excel gains the most at +14.2pp), the curve flattens after 200, and going from 400 to Full adds at most +0.8pp per domain. The final scores at full size (Full) for each domain: Web 82.4, Excel 76.4, Reaper 77.3, PPT 64.8, Blender 44.1.

This phenomenon of "a saturation point exists, with diminishing returns early on" is itself a judgment framework you can carry off directly: you don't need to start by collecting huge volumes of resources and distilling thousands of skills before going live, and covering the core, common operations first (the paper's number is "the first 200") is far more cost-effective than continually extending the long tail. But the specific number "200" **cannot be applied directly** to your own situation. It was measured in this paper's 7 specific creative-software domains with their own way of classifying skills, and on data of a different nature (for example internal enterprise knowledge) where the saturation point falls is entirely unknown, so you can borrow the qualitative idea that "diminishing returns exist" but not the specific number.

## Other Ablations

The paper runs two more ablations more briefly, but they are just as worth setting alongside the rest.

{{< image src="table4.png" alt="Matched-budget ablation table for multimodal representation, comparing text only, adding visual, adding code, and giving all three." caption="Table 4 — Matched-budget ablation on multimodal representation (overall score, %). (Source: original paper.)" >}}

**Table 4 (matched-budget representation ablation)**: the resource pool, skill IDs, metadata and retrieval budget are held fixed, and only "which modalities the agent sees after retrieval" changes. Text-only 65.0% → adding Visual 66.9% (+1.9pp) → Text + Code 67.0% (+2.0pp) → all three 68.9%. The conclusion is that multimodal content does contribute, but each single modality's increment is not dramatic (about 2pp each), and most of the base value still comes from text.

{{< image src="table5.png" alt="Ablation table for the skill-selection strategy, comparing six strategies including hierarchy plus language model, BM25 and vector retrieval." caption="Table 5 — Ablation on the skill-selection strategy (overall score, %). (Source: original paper.)" >}}

**Table 5 (selection strategy ablation)**: the skill library, agent, judge and candidate budget are held fixed, and only the strategy for picking skills changes: Ours (hierarchy-then-LM) 68.9% > BM25 66.0% > BM25+Embed 64.2% > Embed 60.0% > Random-FullPool 58.0% > No-Skill 57.3%. Pure vector retrieval (Embed) is among the weaker of the six strategies, and worse than pure BM25. This is the counterintuitive result mentioned earlier in the "Skill Retrieval and Selection" section: **don't assume dense retrieval is inherently better than lexical retrieval**. The fit between a skill and a task is sometimes not something pure semantic similarity can capture, and it takes an additional layer of judgment (a language model or rules) to guard composability and complementarity.

## What Holds Independently of the Paper

The paper's core method has little novelty, but reading it you keep running into a few judgment frameworks worth remembering. They do not depend on whether the Resource2Skill system itself succeeds, and they hold just the same for a different paper or a different setting. This section sets them out on their own, and it is the part of these notes that truly deserves close reading.

### The Paper's Own Contribution: Close to Zero

The core retrieval and selection mechanism is a combination of existing components, not a new method; the only thing that counts as a discovery, "video is irreplaceable" (Table 3 in the "Ablation: The Resource-Source Mix" section), is not cleanly controlled (resource quantity is not controlled), so its persuasiveness is limited. The paper's skeleton (the schema, the five acceptance gates, the MCP execution interface) has some value as a reference example for system design, but the most critical technical detail, "how to distill", is written extremely thinly and cannot be copied directly.

### Lesson 1: Ask First Whether the Confounders Are Controlled

When evaluating any "system A vs. system B" comparison, first ask whether anything other than the variable you care about has been left uncontrolled. Table 1 in the earlier "Main Results and a Key Blind Spot" section is a living example: `ClaudeCode-H` and `Codex-H` have no skill library at all, so that comparison does not answer "is Resource2Skill well designed?", only the coarser question of "is there a skill library?". Next time you see a similar system comparison, first confirm that the two sides being compared differ in only the one variable, "the design you care about".

### Lesson 2: A Skill Library Has a Saturation Point, with Diminishing Returns Early On

When building your own skill library, cover the core, common scenarios first, and don't chase broad, all-encompassing coverage from the start. The skill count at which saturation occurs varies by situation, so you can't copy the paper's "200", but the qualitative judgment that "returns diminish early and a saturation point exists" can be borrowed directly: cover the core operations first, then consider extending the long tail.

### Lesson 3: Don't Assume Vector Retrieval Is Inherently Smarter Than Lexical Retrieval

The paper compares six skill-selection strategies, and pure vector retrieval (Embed) turns out to be among the weaker ones, worse than pure BM25, while the paper's own two-stage hierarchy-then-LM method scores highest. The "fit" between a skill and a task is sometimes not something pure semantic similarity can capture, and it takes an extra layer of judgment (a language model or rules) to guard composability and complementarity. When designing a retrieval system, dense retrieval should not be the default right answer.

### Lesson 4: Layer Your Validation, Don't Discard on a Binary Check

"Is this code trustworthy?" and "does this knowledge have value in itself?" are two independent judgments. Code failing validation does not mean the whole skill entry is useless: it can be downgraded to "reference only", keeping its description and examples and letting the agent regenerate the code itself. This idea applies directly to the `scripts/` validation of any skill library (including the Anthropic Agent Skills format): run a lightweight smoke test, let what passes be used as normal, and mark what fails as "reference only" in the description file, instead of having the whole skill discarded or forced to run with unreliable code.

## Conclusion

The problem Resource2Skill tackles is very practical: software agents lack procedural knowledge, and tutorial videos are an information source that existing skill libraries have barely used. The paper proves through large-scale experiments that video really does make an irreplaceable contribution (Table 3), and it hands over a system skeleton (the four-element schema, five acceptance gates, two-stage retrieval), but the most critical technical detail, "how to distill", is written thinly, so a complete pipeline cannot be copied; the baseline design of the main result (Table 1) also leaves the blind spot of "is what wins the method, or just having a skill library?" unresolved.

What is really worth taking away is not the paper's method itself but the four judgment frameworks verified along the way: look for confounders first when evaluating system comparisons, a skill library has a saturation point so don't aim for all-encompassing coverage from the start, don't assume vector retrieval is inherently smarter than lexical retrieval, and layer your validation instead of discarding on a binary check. These hold independently of the Resource2Skill system itself, and besides "video is a useful resource", they are the most durable part of the paper.

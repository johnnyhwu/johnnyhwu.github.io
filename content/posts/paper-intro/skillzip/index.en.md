---
# weight: 1
title: "Skill Files Bloat as Agents Self-Evolve: Inside SkillZip's Fix"
date: 2026-10-21
lastmod: 2026-10-21
draft: false
description: "Self-evolving agents only ever append to their skill files. SkillZip merges the repetition with no task-based validation, shrinking them 31.2% on average, with caveats."
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

Self-evolving AI agents share one side effect: the skill file that records their rules of behavior keeps getting appended to and keeps growing. Exactly how it grows, and by how much, is the first thing the next section takes apart.

SkillZip, the paper this post covers, slims that file down, and it does so without running a single task to check whether the compressed version still works. The paper calls this property *evaluation-free*. The approach first parses the skill text into a "typed contract", then collapses the repeated parts with a "define once, reference many" logic, while a hard rule guarantees that the meaning of every original rule can still be found after compression.

The verdict first: **this paper's engineering value is higher than its research value.** Every underlying technique it uses (repeated-segment detection, lifting shared rules to a parent level, using a classifier to judge the logical relation between two sentences, dynamic programming, set packing, clustering) is a classic computer science technique, and none of them is original. The real contribution is assembling these techniques into a system that can actually be deployed: no task validation, compression 3.5 times faster than the competitor, an average compression rate of 31.2%, and no drop in overall accuracy. If you do practical work on skill evolution or agent memory management, the paper's architecture is worth studying; if you are looking for theoretical novelty, it has little to offer.

{{< admonition warning "Three reservations to keep in mind" >}}
Before getting into the details, here are three doubts that run through the whole post: the paper's fidelity guarantee only holds for what the parsing step caught, and anything missed earlier has no mechanism to be recovered; the paper says compression does "not sacrifice accuracy", yet four of its nine test settings actually got worse; and the competitor it compares against, SkillReducer, was designed for a completely different kind of redundancy, so the two are not quite racing on the same track. All three come up again below.
{{< /admonition >}}

## The Problem: Why Skill Files Keep Growing

### The Symptom: A Notebook That Only Grows

Self-evolving agents work in an intuitive way: a tool call fails, so add a warning; an output format is wrong, so add an example; a rare branch unexpectedly succeeds, so record the procedure. The catch is that every update is an *add*, and nobody goes back to *subtract*. The skill file ends up maintained like a notebook that only grows, not like a program that gets tidied.

The paper quantifies this with a longitudinal experiment.

{{< image src="figure1.png" alt="The orange line on the left is the skill file's total length, climbing steadily over self-evolution rounds; the blue line is the amount of genuinely unique, non-repeated contract content, which flattens out by the middle. The widening gap between the two lines is the repeated bloat." caption="Figure 1 — The gap between a skill's total length and its genuinely unique contract content as self-evolution rounds go by. (Source: original paper, Figure 1.)" width="50%" >}}

The chart has two lines, with self-evolution rounds on the horizontal axis. The orange line is the skill file's total length, which keeps climbing; the blue line is the amount of genuinely unique, non-repeated rule content, which flattens out after the middle. The widening gap between the two lines is exactly what this paper targets: the amount of text added far outpaces the amount of genuinely new knowledge added.

The paper's example is vivid. After enough rounds, the sentence "do not overwrite the original file" may appear in the opening intro, in three workflow branches, and in one example, so the same point is made four times. The authors measured the bloat rate on [SkillOpt](../skillopt/) (an existing skill self-evolution system): by round 5, skill length had grown to about 5.6 times, 3.1 times and 6.7 times the original on BFCL-V4, LiveMath and SpreadsheetBench respectively, about 5.2 times on average. Within five rounds, the skill file was already more than five times heavier than at the start.

### Two Kinds of "Long" Are Not the Same Problem

The paper distinguishes two situations that make a skill file longer, and the distinction decides which logic should be used to slim it down.

The first situation is the generic, community-written tutorial-style skill. These usually mix in background explanations, redundant examples and reference material that has nothing to do with execution:

```
## What is an API?
API is short for application programming interface, which lets different pieces of software talk to each other...

## Why choose OpenWeather over other services?
There are many weather APIs on the market. We chose this one because...

## Example 1: Look up the weather in Taipei
(example code)

## Example 2: Look up the weather in Tokyo
(almost identical code, only the city name changed)
```

"What is an API" and "why this service" have nothing to do with "how to carry out this task". Delete them and the agent can still look up the weather without missing any rule needed for execution. The basis for judging this kind of redundancy is relevance: whether it relates to execution.

The second situation is a skill evolved over many rounds, and it is completely different. Every addition to this kind of skill was accepted only after being validated by rollout feedback:

```
Round 3: when a city name contains a space (e.g. "New York") it was not encoded, and the API returned a 400 error
        -> the agent added a rule: "URL-encode the city name when it contains a space"

Round 7: when querying a city that does not exist, the API did not raise an error but returned an empty JSON,
         so the agent mistook it for "sunny"
        -> the agent added a rule: "after the query, check whether the returned JSON is empty"

Round 12: another branch (batch query) stepped on "city names must be URL-encoded" again,
         and added almost the same sentence once more, only worded differently
```

"City names must be URL-encoded" and "an empty JSON must be treated as a failure" are each true, necessary and highly relevant to execution on their own; neither is off-topic filler that can be cut. But the same point was made once in round 3 and again in round 12. Here you cannot decide what to delete by asking "does this passage relate to execution", because both passages do; what you can ask is "are these two passages saying the same thing, so that they can be merged". The basis for judging this kind of redundancy is redundancy itself, whether something is repeated, not relevance.

The baseline the paper compares against, "SkillReducer", is designed for the first situation: it uses delta debugging to strip away the chaff, together with task validation. SkillZip targets the second situation. Keep this difference in mind when looking at the experimental numbers later: the two were never aimed at the same kind of redundancy.

### Why Off-the-Shelf Prompt Compression Doesn't Work

A natural question is whether existing prompt compression tools (such as LLMLingua) can be used directly. The answer is no, for a simple reason: prompt compression decides what to keep by how relevant a passage is to the query at hand, but a skill has to stay valid for *every possible future query*. At the moment a skill is loaded, nobody knows what the agent will be asked next. With no "current query" to filter against, the logic of prompt compression simply has nothing to work with in the skill setting. This contrast is expanded in the extension part of the post, because it is a more general decision framework than the paper itself.

## Core Idea: Treat a Skill as a Typed Contract

SkillZip's basic claim is that a skill is not a flat piece of text but a contract. Different sentences in the contract govern entirely different things, and that directly determines which edits to them are safe.

{{< image src="figure3.png" alt="SkillZip architecture overview: the left half is one-shot compression, which starts from the full skill, scans and recovers the typed contract, and applies the explain-once-reference-many principle to remove repetition; the right half is continual compression (Zip-on-Write), which compares each new patch with its contract neighborhood and triggers a full repack only when needed." caption="Figure 2 — SkillZip's two modes of operation: one-shot compression (One-Shot) and continual compression (Zip-on-Write). (Source: original paper, Figure 3.)" >}}

Almost everything the paper does from here on is an unfolding of this figure. The left half takes a complete, already-bloated skill and compresses it in one shot; the right half handles every small patch as it arrives with a bit of local tidying, without waiting for bloat to build up. This section covers the core foundation both halves share, namely how the contract is defined and how to judge whether a merge pays off; the next section covers the full one-shot pipeline, and after that comes the continual mode.

### Six Types, One Contract

{{< image src="figure2.png" alt="Six color blocks stand for the six components of the contract: Interface, Workflow, Tool protocol, Scoped rules, Output contract and Evidence. Arrows in the middle form the main line of a user question triggering, execution in order, tool calls, rule checks and output checks, with Evidence attached on the side as supporting explanation." caption="Figure 3 — A skill decomposed into six typed contract components, each governing a different aspect of execution. (Source: original paper, Figure 2.)" width="75%" >}}

The paper writes the contract as \( C(S) = \langle I, G, T, C, O, E \rangle \) (paper Eq. 1), and the six components divide the work as follows:

| Symbol | Name | What it governs | Concrete example |
|---|---|---|---|
| \( I \) | Interface | What the skill is called, when it should be triggered, and when it should not | "Trigger: the user asks about the weather"; "Exclude: the user asks about the history of climate change" |
| \( G \) | Workflow | Execution order, branches, loops, what to do on failure, and when the work counts as done | "First look up the city code → then call the weather API → retry once on failure" |
| \( T \) | Tool protocol | Which tool to call, with which parameters, preconditions, return format and error handling | "Call get_weather(city_code); city_code must be URL-encoded first" |
| \( C \) | Scoped rules | What "must / must not / should" be done, and only within which scope or condition the rule holds | "(Scope: batch-query branch) must not query more than 10 cities at once" |
| \( O \) | Output contract | Response format, required fields, field order, validation, and when the output counts as complete | "Output must be JSON with two required fields, temperature and condition" |
| \( E \) | Evidence | Examples, templates, and reasons that make a decision clear | "Example: the full input and output of a Taipei weather query" |

{{< admonition tip "The two C's are not the same thing" >}}
The outermost \( C(S) \) here is the name of the whole contract function, and it is not the same thing as the component \( C \) (Scoped rules) in the fourth row of the table; the two just happen to use the letter C, with entirely different meanings, so when you see \( C \) later, watch which context it appears in.
{{< /admonition >}}

The division of labor among the six can be traced as a simple flow. Once a user question comes in, \( I \) first decides whether to trigger; then \( G \) runs the steps in order and calls the tools specified by \( T \); along the way \( C \) checks that no rule is violated; and after the tool returns, \( O \) checks the output format. \( E \) (examples and supporting evidence) is not on this main line; it is attached beside the other five as supporting explanation.

This breakdown is not for tidy filing. It is the safety basis for deciding whether two sentences can be merged. The paper gives three examples: two sentences about the same tool but with different required parameters cannot be merged, because forcing a merge would drop one of the requirements; a rule that every branch has can be lifted to the common parent (this is the scope lifting covered later); and a rule attached to only one branch cannot be lifted, because lifting it to the parent would widen its scope and turn it into a wrong rule.

### From Six Types to JSON: What the Extracted Structure Looks Like

After structured extraction, the contract is expressed as a JSON document with 8 top-level fields (paper Appendix C): `interface`, `scopes`, `workflow`, `rules`, `output`, `evidence`, `shared_procedures` and `residual`. The first six roughly correspond to the six types.

Of these, `scopes` is an auxiliary scope tree and does not count as a separate type; `shared_procedures` stores the shared procedures that have already been extracted; and `residual` stores the leftover content that was kept verbatim because extraction confidence was too low, which later subsections cover in detail.

Under each top-level field is an array, and every entry has its own schema and carries a `spans` (or `source_blocks`) field recording which block or blocks of the original text it was extracted from. This mapping is many-to-many: one extracted unit may cite several source blocks at once (say, the condition in one place and the rule itself in another), and one source block may be split into several different extracted units.

An element of the `rules` array looks like this:

```
{
  "id": "C1",
  "scope": "if-validation-fails",
  "modality": "must_not",
  "predicate": "overwrite the input file",
  "guard": "true",
  "spans": ["B5"],
  "locked": false,
  "confidence": 0.92
}
```

The `spans` field is the core of the provenance mechanism: in principle, every later compression decision can be traced back to "which block of the original text".

### The Formal Objective: Writing MDL (Minimum Description Length) as One Formula

MDL, the Minimum Description Length principle, means describing something in the shortest possible way.

SkillZip represents the compressed skill with a library \( K \) (reusable contract elements) plus a residual \( R \) (unique, exceptional, or uncertain content). The objective (paper Eq. 4) is:

\[ (K^*, R^*) = \arg\min_{(K,R)} L(K) + L(R \mid K) \]

subject to the constraint that for every \( a \in A_{req}(S) \), it must hold that \( a \preceq (K,R) \).

In plain words: **under the premise that no rule may be lost, find the representation with the shortest total length.** \( a \preceq (K,R) \) reads as "unit \( a \) is covered by \( (K,R) \)", and this is a hard constraint, not a weighted term that can be traded off. Even if a merge plan would save a large number of tokens, as soon as it leaves any originally extracted required unit uncovered, the plan is simply invalid.

How the length \( L(x) \) itself is computed is given by paper Eq. 6:

\[ L(x) = |\text{Render}(x)|_{tok} + \gamma_{def}(x) + \gamma_{ref}(x) + \gamma_{scope}(x) \]

Here \( |\text{Render}(x)|_{tok} \) is the token count after rendering \( x \) as text; \( \gamma_{def}(x) \) is the extra cost paid if \( x \) *defines* a new rule or procedure (naming it, writing its scope clearly); \( \gamma_{ref}(x) \) is the cost paid if \( x \) *references* an already-defined rule (cheaper than rewriting it, but not free); and \( \gamma_{scope}(x) \) is the cost of expressing the scope in which the rule applies. The point of summing these four terms is to stop the algorithm from being too clever: if "define plus reference" costs more than "just write it twice", then do not merge, and leaving things as they are is cheaper.

### Content the System Can't Classify: Locked Residual

Step 2 (covered in detail in the next chapter) uses a schema-constrained LLM to convert the original text into a structured contract. If it cannot tell the type or scope of a passage for certain, the system does not force it into one of the six types; it puts the whole passage into `residual` unchanged and marks it `locked=true`:

```
Original: "Behavior here is a bit special; adjust it based on experience"
-> not an explicit rule (no clear must/must_not)
-> not an explicit workflow step or output format requirement either
-> the LLM cannot decide which category it belongs to
-> the whole sentence goes into residual unchanged, locked
```

Locked content is never merged with anything else, never optimized and never deleted; it appears verbatim in the final output. This is the concrete implementation of the system's "fail conservatively" design philosophy: better to keep a passage of original text that is hard to understand than to risk forcing it into some type and losing or misjudging information through a wrong placement.

### Four Decisions: One Skeleton, Four Forms

The same skeleton as Eq. 4, applied to four different kinds of repeated structure, unfolds into four judgment formulas. The shared logic of each is: **a merge is worth it only if what it saves (the cost of keeping things separate) exceeds what it adds (definition cost plus reference cost plus residual cost).**

**Decision 1: merging equivalent statements (Eq. 7)**

\[ L(z) + L(x_1 \mid z) + L(x_2 \mid z) < L(x_1) + L(x_2) \]

\( x_1 \) and \( x_2 \) are two sentences with almost identical content, and \( z \) is the shared version kept as one copy after merging. \( x_1 \mid z \) and \( x_2 \mid z \) are the "extra differences each of \( x_1 \) and \( x_2 \) still needs to spell out" after the merge; if the two are nearly identical, both terms are close to 0.

The paper's own real example comes from Appendix E, a before-and-after of the LiveMath skill: before compression, this passage appeared twice word for word: "If the problem asks for a single specific value (e.g., maximum, minimum, unique solution) or implies a unique answer, output ONLY that single valid value. Strictly discard any extraneous candidates, negative roots, or intermediate results that do not satisfy all constraints..." After compression it appears only once, in tighter wording. What follows is an illustrative estimate (not exact numbers reported by the paper, which only gives the total for the whole skill, 936 down to 638 tokens; this is a rough estimate to show how the formula is used):

```
L(x1) ≈ 55 words, L(x2) ≈ 55 words -> total cost without merging ≈ 110
L(z) ≈ 45 words (tightened merged version), residual ≈ 0 (the two sentences are almost identical)
Verdict: 45 < 110 -> worth it, merge
```

**Decision 2: lifting a rule to a common parent, scope lifting (Eq. 8)**

\[ L(c@u) + r \cdot L(\text{scope-ref}) < \sum_{i=1}^{r} L(c@s_i) \]

\( c@s_i \) is rule \( c \) as attached under child branch \( s_i \), and \( c@u \) is rule \( c \) rewritten to attach under the common parent \( u \) (usually costing a few more tokens than attaching under a single branch, since it has to make clear it "holds for all child branches"). The scope-ref is a tiny inheritance marker each child branch keeps. Continuing with the weather-query skill example, illustrative numbers:

```
Before lifting (3 branches each write "URL-encode city names" once):
  Σ L(c@sᵢ) = 12+12+12 = 36

After lifting (moved to the common parent, each of the 3 branches keeps an inheritance marker):
  L(c@u) + 3·L(scope-ref) = 15 + 3×1 = 18

Verdict: 18 < 36 -> worth it, lift
```

The safety precondition is stated explicitly in the paper: lifting is allowed only when "every relevant child path really needs this rule" and "all local conflicts are encoded as exceptions". If some branch does not actually need the rule, forcing it upward would make the rule wrongly apply to that branch, and even if the arithmetic says it pays off, it must not be done. This formula follows the same logic as loop-invariant code motion in compilers (moving a computation that does not change inside a loop to outside the loop), covered in detail in the extension part.

**Decision 3: sharing a repeated procedure, workflow reuse (Eq. 9)**

\[ L(\text{def}(q)) + r \cdot L(\text{call}(q)) < r \cdot L(q) \]

\( q \) is an action sequence that repeats (for example "validate input → call API → retry on failure → parse result"), and \( r \) is how many times \( q \) appears without overlap in the whole skill. \( \text{def}(q) \) is the number of tokens needed to define \( q \) as a named shared procedure (the name plus the entry and exit conditions), and \( \text{call}(q) \) is the number of tokens needed each time it is used afterwards, just referencing the name. The paper only describes the phenomenon ("the same validate–repair–verify sequence is copied repeatedly with only minor differences") and gives no concrete token counts, so what follows is an illustration made up for this post:

```
Before (3 branches each write the full validate-repair procedure, 20 words each time):
  r · L(q) = 3×20 = 60

After (defined once for 24 words, referenced for 6 words each time):
  L(def(q)) + 3·L(call(q)) = 24 + 3×6 = 42

Verdict: 42 < 60 -> worth it, share
```

For a candidate to be nominated it must meet two constraints: no overlap (the same text cannot count as part of two different candidates), and consistent entry and exit behavior (the preconditions before the procedure runs, and the next step it connects to afterwards, must be the same across branches). The paper's render stage adds a practical judgment: "A shared workflow is named only when references save tokens; otherwise it remains inline." Even when Eq. 9 pays off mathematically, if \( r \) is too small and the procedure is short, the cost of naming can eat most of the saving, and the system then chooses not to name it and keeps it inline. The spirit of this formula is the same "define once, reference many" logic as grammar-based compression algorithms and the BPE algorithm used by LLM tokenizers, in a different application.

**Decision 4: a general rule plus exceptions, guarded variants (Eq. 10)**

\[ L(c) + \sum_i L(\delta_i) < \sum_i L(c_i@g_i) \]

\( c_i@g_i \) is the \( i \)-th conditional version of the rule (\( g_i \) is the condition under which it holds and \( c_i \) is the rule content), \( c \) is the common core of these versions, and \( \delta_i \) is the difference left between the \( i \)-th version and the general rule \( c \). This formula has exactly the same skeleton as Decision 1; the difference is that Decision 1 is a special case of Decision 4 (the difference \( \delta_i \) happens to be close to 0 because there was no difference in content), while Decision 4 is the more general case, allowing each copy to keep a real difference that cannot be erased. Illustrative numbers (the city-count limit rule in the weather-query skill):

```
Before merging (the city-count limit rule of 3 branches):
  Σ L(cᵢ@gᵢ) = 12+14+12 = 38

After merging (extract the common core "queries have a city-count limit", each keeps its difference):
  L(c) + Σ L(δᵢ) = 8 + 6+9+6 = 29

Verdict: 29 < 38 -> worth it, express as "general rule + exceptions"
```

There is something the paper leaves unexplained here: how to extract this common core \( c \) from multiple versions. The paper gives no concrete algorithm or prompt. It only mentions in step 3 of the method section that the relation checker judges this kind of pair as a conflict and sends it off to produce an exception candidate, but the mechanism for the step "how \( c \) is generated once the conflict is judged" is not spelled out. This is also the easiest of the four decisions to get wrong: if the rules in three branches in fact have hidden subtle differences, and the core-extraction step fails to catch them and wrongly merges them into one \( c \), a restriction that some branch should have had gets overridden by the general rule. This kind of error is not caught by the coverage constraint (from \( K \)'s point of view the rule is "covered"), yet the actual behavior is already different from the original.

The differences among the four decisions, put into one table for comparison:

| | Decision 1: equivalence merge | Decision 2: scope lifting | Decision 3: workflow reuse | Decision 4: general rule + exceptions |
|---|---|---|---|---|
| Paper formula | Eq.7 | Eq.8 | Eq.9 | Eq.10 |
| Shape of the formula | \( L(z) \) + residual < sum of the separate copies | \( L \)(lifted to parent) + \( r\cdot \)marker < sum over branches | \( L \)(definition) + \( r\cdot L \)(reference) < \( r\cdot L \)(original length) | \( L \)(common core) + sum of differences < sum of the versions |
| Triggering situation | Two sentences are fully equivalent | The same rule repeats in several child branches | The same action sequence repeats | Several versions are partly the same, partly different |
| Main contract type | Any (\( C \) is the most common) | \( C \) (scoped rules) | \( G \) (workflow) | \( C \) (scoped rules) |
| Is the residual 0 after merging | Almost 0 | Replaced by a scope-ref marker | Replaced by call(q) | Not 0; each copy keeps its difference |
| Safety precondition | modality/guard fully identical | Every relevant child path really needs the rule | Consistent entry/exit behavior + no overlap | The differences must be fully captured in \( \delta_i \), none missed |
| Algorithm for overlapping candidates | Union-Find clustering | Dynamic programming (on the scope tree) | Weighted set-packing | The paper gives no algorithm name |
| Most error-prone spot | Looks alike on the surface but modality differs, wrongly judged mergeable | Wrongly judging that some branch does not need the rule | Entry/exit looks consistent but hides a difference | Missing a restriction unique to one branch when extracting the common core |

### Two Gates: How the Six Types Connect to the Four Decisions

The six types are not "the classification basis for the decisions"; they are "the screening gate that decides whether a decision can be applied". **The six types decide "whether two things are even eligible to be compared", and the four decisions are "the math test of whether a merge pays off once compared".** They are two gates in sequence, not two parallel classification schemes: the original text is first scanned and extracted into six-type units, then passes the first gate (type-compatibility screening, where only units of the same type with compatible details can be paired), and only those that pass get the four decision formulas applied to see whether it pays off, after which the cheapest combination is selected.

Step 3 of the method section states five type-compatibility screening rules explicitly: \( I \) (interface) can be compared only if both play the same role, trigger or exclusion; \( C \) (rules) can be compared only if modality, predicate family and scope ancestry are all compatible; \( T \) (tools) can be compared only if the tool name is the same and the parameter signatures are compatible; \( O \) (output) can be compared only if it has the same response type and the same field namespace; and \( G \) (workflow) takes a completely independent route, searching among repeated action sequences with the same guard, without going through the comparison machinery above.

Candidates that pass the gate then have the corresponding decision formula applied:

| Type | Rule at gate 1 | Which decision can apply |
|---|---|---|
| \( I \) Interface | Same role | Decision 1 |
| \( C \) Rules | modality + compatible scope | Decisions 1, 2 and 4; the only type that gets all three |
| \( T \) Tools | Same tool + compatible parameters | Decision 1 (but with different parameters it cannot be merged) |
| \( O \) Output | Same type + same namespace | Decision 1 |
| \( G \) Workflow | Independent sequence matching | Decision 3 (does not go through the relation checker) |
| \( E \) Evidence | Not on the list above | No dedicated decision; a separate "coverage test" decides whether it can be deleted whole |

\( E \) (evidence) is a special case: the criterion is not "does it look like another example" but "has the thing this example says already been written clearly elsewhere (usually in \( O \) or \( C \))". This echoes the sentence in the caption of Figure 3 above, "an example is removable only when every requirement it uniquely expresses is represented elsewhere". It goes through the coverage test, not the four token-saving formulas of Eq.7 to Eq.10.

There is one more thing the paper does not make clear: Decision 2 (scope lifting) is not listed on its own among the five rules in step 3 of the method section. It is not a separate relation the relation checker judges; it is a "placement form" decided incidentally after candidate pool A (the equivalence groups) is processed by dynamic programming in step 4. In other words, the candidate identities generated directly by step 3 are only three kinds: equivalence/implication, conflict, and workflow repetition; Decision 2 is one possible presentation of an equivalence candidate in step 4, not a fourth kind of candidate already sorted out in step 3.

## One-Shot SkillZip: Walking Through the Full Pipeline

The method section splits the whole one-shot compression pipeline into 5 sub-steps, corresponding to the paper's Algorithm 1:

```
Algorithm 1 One-Shot SkillZip
Input: skill S, audit flag v
Output: compressed skill S̃

1: B ← Scan(S)                       step 1
2: (A, R) ← ExtractContract(B)       step 2
3: H ← ProposeReuse(A)               step 3
4: K ← MinCostCover(A, R, H)         step 4
5: S̃ ← Render(K)                     step 5
6: if v then
7:   K̂ ← Parse(S̃)
8:   M ← ContractDiff(K, K̂)
9:   S̃ ← RestoreMissingSpans(S, M)
10: return S̃
```

### Step 1: Scan (Rule-Based, No LLM)

The first step uses no LLM at all; it is a purely rule-based parser (paper Appendix B). What it does includes:

- Splitting the skill document into blocks that each carry an ID. The block ID is a hash of "the normalized text plus the heading path above it", not a line number. Line numbers shift when new content is inserted earlier; hashes do not.
- Turning the nested Markdown heading structure into a preliminary scope tree, where a scope path looks like this: `["root", "workflow", "if-validation-fails"]`.
- Picking up "numbered lists" and "temporal wording" (such as "first... then... after that...") as high-confidence workflow cues.
- Treating code blocks and tables as indivisible minimal units.

Why do this step first instead of handing everything to an LLM? Structure that rules can resolve, such as heading levels and numbered lists, should not waste the LLM's judgment on guessing; that saves cost, and it also means every later decision can be traced back to "which block of the original text". For a rule to be promoted from "attached under some small branch" to "attached under a larger scope", the text needs explicit cues: wording like "always" or "for every request" that explicitly claims global applicability, or the rule repeating under several related child nodes.

> This is a point inferred from how the paper is written, and the paper never addresses it head-on: the backbone of step 1 is "turn nested Markdown headings into a preliminary scope tree" and "turn numbered lists or temporal words into workflow cues". If the input is not Markdown but one undifferentiated block of plain text with no headings and no lists, neither source of cues exists, and step 1 would most likely catch little structure. That in turn affects the audit mechanism in step 5, because the audit depends on every extracted unit having spans to check back against; if plain-text input makes the blocks cut out by step 1 too coarse, the granularity of traceability drops.

### Step 2: Recover the Typed Contract

The numbered blocks cut out in step 1 are handed to a schema-constrained LLM, which is asked to output the contract described in the earlier "Six Types, One Contract" subsection. The output of this step is not text but structured JSON.

The paper explicitly names four kinds of errors that get rejected, and the check is done by deterministic host code, not by another LLM: unsupported citations (an extracted item cannot be matched to a source block ID); polarity mismatch (the direction of must versus must-not extracted backwards); unknown tool names (an extracted tool name that never appears in any source block); and invalid workflow references (a workflow node pointing to a next step that does not exist). For items 1, 3 and 4, the host can do it with pure ID or string matching, no semantic understanding needed: checking whether a cited block ID exists is a set lookup, checking whether a tool name appears in the source text is a string containment test, and checking whether the next step a workflow node points to exists is a graph node existence test. **For item 2 (polarity mismatch), the paper says nothing about how the check is done.** It involves understanding the meaning of that sentence in the original text and cannot be done with ID matching alone, and the paper also does not say whether this step is counted in the LLM calls reported in its cost table.

Why split "understanding" and "compression" into two independent steps? The extractor (step 2) is deliberately not asked to make compression judgments. That has two benefits: the quality of contract extraction can be tested independently, checked against human annotations; and once the extracted units are fixed, the optimization step is pure math, so the same input always gives the same output, unaffected by LLM randomness. The details of this "separate understanding from decision" principle come later.

### Step 3: Nominate Candidates

This step only "nominates" candidates; it does not yet decide whether to really merge them, and it has two small stages. The first stage is structural screening, applying the five type-compatibility rules from the "Two Gates" subsection above to filter out combinations that obviously cannot pair. The second stage is embedding retrieval plus a relation checker to judge the relation: first use hashing to find exact matches that are word-for-word identical after normalization; then use an embedding index to find semantically close approximate-match candidates (fast and rough), and then have a frozen relation checker (an NLI-like classifier) judge the relation more finely: equivalence goes into candidate pool A (possibly merged); implication also goes into pool A (the paper does not say how implication is actually used); conflict goes into pool B (possibly becoming a general rule plus exceptions, not discarded); and anything unrelated or low-confidence is discarded outright.

Workflow (type \( G \)) takes a completely separate route, going through neither type screening nor the relation checker; it relies on independent sequence matching over "repeated action sequences with the same guard", forming its own candidate pool C.

### Step 4: Pick the Shortest Covering Explanation

This step has three actions. Action one: each candidate first computes \( \text{save}(h) = L(\text{separate form}) - L(\text{form using } h) \) (Eq. 5, the general skeleton of Eq.7 through Eq.10), and candidates with \( \text{save}(h) \le 0 \) are discarded outright. This step only answers "does this candidate pay off on its own"; it does not mean "all these worthwhile candidates can be carried out together". Candidates may compete for the same batch of original units, and two of them cannot both be chosen.

Action two: different candidate pools use different algorithms to resolve "candidates crowding each other out". Pool A (equivalence/implication) first does conflict filtering, then uses Union-Find clustering to group, and if a group spans several scopes, uses dynamic programming to decide which level of the scope tree to put it on; pool B (conflict) applies Eq.10, but the paper gives no ranking algorithm for when candidates are mutually exclusive; pool C (workflow repetition) uses weighted set-packing, a greedy pass sorted by efficiency plus pairwise-exchange fine-tuning.

Action three: each time a candidate is selected, coverage is immediately rechecked, that is, can the meaning of every originally existing rule still be found in the currently selected \( K \)? If not, that candidate is revoked.

The paper itself gives a concrete example that puts three decisions into one running example: "The two branch-local copies of "never overwrite the input" are represented by one rule at their common parent because Eq. (8) is satisfied. The validate step is shared only if its definition and calls are shorter than the copies. The JSON example is removed only after its fields are covered by the output contract." Translated into a comparison: the two branches that each wrote "do not overwrite the input" go through Decision 2, scope lifting; the validate step goes through Decision 3, workflow reuse; and the JSON example being deleted goes through the coverage test for \( E \), on the condition that its fields are already covered by \( O \).

The table below strings the whole decision flow from step 3 to step 4 together, and is worth remembering:

| Step 3 candidate source | Step 3 judging mechanism | Step 4 presentation form | Formula | Algorithm for overlapping candidates |
|---|---|---|---|---|
| equivalence/implication candidates | structural screening + embedding retrieval + relation checker | plain merge | Eq.7 | Union-Find clustering |
| ↳ the same candidates, if the group spans scopes | (reuses the same judgment, not generated independently) | lifted to the common parent | Eq.8 | Dynamic Programming |
| conflict candidates | structural screening + embedding retrieval + relation checker | general rule + exceptions | Eq.10 | The paper gives no algorithm name |
| workflow repetition candidates | independent sequence repetition detection, no structural screening | workflow sharing | Eq.9 | Weighted set-packing |

### Step 5: Rendering and Structural Audit

The render step uses a fixed template (not an LLM) to convert the finally decided contract \( K \) back into a normal skill text, containing a concise purpose and triggers, global rules, a numbered workflow, nested guarded branches, explicit tool requirements and an output checklist. A shared workflow is given a name only when "a reference really saves tokens compared with inlining"; otherwise it stays inline.

The structural audit (optional) works in a clever way: take a "blind" audit parser, show it neither the original skill nor the selected contract \( K \), and show it only the final rendered text, asking it to re-parse independently into a fresh contract \( \hat{K} \). Then diff \( \hat{K} \) against the original \( K \). If \( \hat{K} \) is missing a trigger, guard, workflow edge, tool argument, polarity or output field, that information was lost during rendering or extraction; the shortest passage from the original text that covers the missing item is restored, put back into the final text, and locked against later deletion. The purpose of this step is to use an independent viewpoint that "never looks at the original and only sees the final render" to check backwards whether the final text really expresses everything \( K \) is meant to express.

## Zip-on-Write: Continual Compression Mode

### Why a "Continual" Mode Is Needed

A self-evolving agent in real operation receives a steady stream of small patches, a correction here, an addition there, not a whole rewrite. If the full one-shot pipeline were rerun every time, the cost would grow more and more expensive as the skill gets bigger. The problem Zip-on-Write solves is: process only the patch added this time, without re-analyzing the whole skill.

### The Sidecar Mechanism

From the paper: "SkillZip stores a sidecar, skillzip.json, containing the current contract, source provenance, scope tree, workflow graph, and candidate indices. The rendered SKILL.MD remains the only artifact loaded by the agent."

In other words, SkillZip maintains two things: the `skillzip.json` sidecar stores the structured internal state, including the current contract \( K \), source spans, the scope tree, the workflow graph and candidate indices; the agent itself never reads this file, and it is SkillZip's own working memory. `SKILL.md` is the final rendered text, the thing the agent actually loads and reads, and it has to be re-rendered after every sidecar update.

### Four Operations: ABSORB / REFINE / EXTEND / REFACTOR

Every new patch is classified as one of these four: ABSORB means the patch merely restates an existing rule and adds no new contract content; REFINE means the patch adds a guard, tool argument, validation or exception to an existing unit; EXTEND means the patch introduces a genuinely new rule; REFACTOR means the patch makes some older rule or procedure worth sharing "now".

Walking through each with the weather-query skill example: in the ABSORB case, the existing rule "city names must be URL-encoded" has a guard of `true` (applies in all cases), and a new patch says "city names in batch queries must also be URL-encoded"; the content was already covered by the existing rule, so it is ABSORB and the contract does not change at all. In the REFINE case, a new patch says "when a city name in a batch query contains a comma, extra handling is needed, beyond URL encoding"; the existing rule does not cover this new detail, but a guard can be added to the existing rule, so it is REFINE, adding the detail directly to the existing unit. In the EXTEND case, a new patch says "when querying historical weather, the date format must be YYYY-MM-DD"; this appears in no existing rule at all, so it is EXTEND, adding a new rule. In the REFACTOR case, branches A and B currently each write one "validate-repair" procedure (\( r=2 \), not yet worth sharing), and a new patch has branch C add exactly the same procedure, making \( r \) equal to 3; reapplying Eq.9 may now pay off, so it is REFACTOR, restructuring three separate procedures into one shared procedure.

REFACTOR is the only one of the four operations triggered "not by the new content itself, but because the new content changed whether the surroundings are worth sharing".

How does the host decide which operation to choose? The paper says: "The host selects the feasible operation with the smallest increase in Eq. (4)." In practice, infeasible operations are filtered out first (for example, ABSORB is feasible only when the patch introduces nothing the current contract does not already cover, and EXTEND requires a genuinely new required unit); among the remaining feasible operations, it picks the one that "increases the total cost of Eq.4 the least".

Note that the comparison is "smallest increase", not "which shrinks the most". Zip-on-Write deals with added content, so information in principle only stays level or grows and does not vanish into thin air; only when REFACTOR is triggered, turning something previously unshared into something shared, can the total length in theory actually end up shorter than before the patch. This differs in nature from One-Shot mode's Eq.5 (\( \text{save}(h) > 0 \), genuinely shrinking existing bloat): one compresses existing fat, the other tries to put on as little fat as possible when adding. The paper also stresses: "No operation is accepted because it improves a task score." The choice among the four operations relies purely on Eq.4 cost computation and never runs a task to see which operation makes the agent perform better, which is consistent with One-Shot and keeps the evaluation-free spirit.

### Narrowing the Candidate Search Scope

If every small patch had to be compared against all the rules in history, there would be no benefit at all from "processing only the increment". From the paper: "Candidate search is restricted to the matching type, current scope, ancestor scopes, and adjacent workflow nodes." That is, it compares only against things of the same type, only against things in the scope where the patch sits, plus all ancestor scopes from that scope up to the root; for workflow, it compares only with the immediately adjacent nodes before and after, not the whole workflow graph. The complexity is \( O(d \cdot k) \), where \( d \) is the number of units extracted from this patch and \( k \) is the number of retrieved candidates (a small constant), and it does not grow with the history length of the whole skill.

The price is that sharing opportunities that can only be discovered "across scopes" may be missed. For example, two originally unrelated branches each accumulate patches, and only now is there an identical procedure, but because each pass only looks at what is "nearby", a sharing opportunity spanning unrelated branches is not caught by a single local comparison.

### When a Global Repack Is Triggered

The sidecar additionally tracks "approximate counts" (not exact counts; the purpose is to avoid doing a full embedding plus relation checker comparison every time), and a repack is triggered when any one of three conditions is met. Condition one: the estimated recoverable saving exceeds a threshold \( \theta_{repack} \); the sidecar tracks approximate occurrence counts of rule families and action n-grams and roughly estimates "how many tokens a global tidy-up right now could probably save". Condition two: the contract has grown by more than \( \rho \) since the last repack. Condition three: \( B \) patches have accumulated.

Conditions one and three look similar on the surface but judge differently: condition three is a plain count and does not care whether the contents look alike; condition one looks at whether the patches have a "repetitive smell" among themselves: even if there are not many patches yet, as long as the repeated structure is dense enough to be worth tidying, it triggers early; even if the patch count has been reached, if the contents are all unrelated and the estimated saving is near 0, it does not trigger. Repack tidies only the "contract \( K \)" and does not re-analyze historical prose. In the paper's words: "Repacking operates on the compact contract rather than all historical prose."

### The Full Flow of Algorithm 2

```
Algorithm 2 Zip-on-Write Continual Compression
Input: state Z_(t-1), accepted patch Δt, repack policy η
Output: updated state Z_t and rendered skill S̃_t

1: Bt ← ScanPatch(Δt)                scan this patch (like step 1, much smaller scope)
2: (At, Rt) ← ExtractPatch(Bt)       extract the patch's contract units
3: Nt ← RetrieveCompatible(Z_(t-1), At)  retrieve only "nearby" compatible candidates
4: Ht ← ProposeOps(At, Nt)           propose ABSORB/REFINE/EXTEND/REFACTOR candidates
5: Z' ← LocalMinCostUpdate(...)      apply Eq.4, pick the operation with the smallest increase
6: AssertCoverage(Z', At)            check coverage
7: UpdateReuseStatistics(Z')         update the approximate counts in the sidecar
8: if RepackDue(Z', η) then          check whether a repack is triggered
9-12:   rerun a One-Shot-like candidate search + selection over the whole compact contract
13: S̃_t ← Render(Z')                 render to text
14: if AuditDue(Z') then             check whether a structural audit is due
15:     run the audit + restore what was missed
16: Zt ← AtomicCommit(...)           atomic commit
17: return (Zt, S̃t)
```

Two places deserve particular attention. First, "scope detection" (`RetrieveCompatible`) and "deciding the action" (`ProposeOps`) are two independent steps: scope detection only narrows the candidate pool, and even if retrieval finds nothing (`Nt` is empty), the action can still be decided; in that case the most reasonable outcome is usually EXTEND (nothing related exists nearby, so this patch is very likely a brand-new rule), and there is not even a need to compare how much Eq.4 increases, since there is only one feasible option. Second, `AtomicCommit` (atomic commit) ensures that if a crash happens midway, no half-written state is left behind; this is system-reliability engineering, a concern at a different level from the compression theory above.

## Experimental Results: What the Numbers Say

### RQ1: How Much Do Skills Bloat During Self-Evolution

The earlier subsection "The Symptom: A Notebook That Only Grows" already showed SkillOpt's bloat curve; here are the numbers for another comparison method, Memento-Skills.

{{< image src="figure4.png" alt="Left panel (a) is SkillOpt and right panel (b) is Memento-Skills. Both plot relative change curves for BFCL-v4, LiveMath and SpreadsheetBench plus an average line, with self-evolution rounds on the horizontal axis, and the curves of both methods keep climbing as rounds increase." caption="Figure 4 — The skill bloat trends of two existing self-evolution methods, SkillOpt and Memento-Skills, side by side. (Source: original paper, Figure 4.)" width="75%" >}}

With [SkillOpt](../skillopt/) run to round 5, skill length grew to about 5.6 times, 3.1 times and 6.7 times the original on BFCL-V4, LiveMath and SpreadsheetBench, about 5.2 times on average. The figure also draws the bloat curve of the Memento-Skills method for contrast, but the paper's main text gives concrete multiples only for SkillOpt. Overall, both existing self-evolution methods share the same bloat problem; it is not specific to SkillOpt.

### RQ2: Can SkillZip Preserve Fidelity (the Most Important Results Table)

The paper's Table I compares 3 models (Qwen-3.7-Max, Qwen-3.6-Plus, Kimi-K2.6) across 3 benchmarks (BFCL-V4, LiveMath, SpreadsheetBench), 9 settings in total. The overall numbers are:

| | Compression rate | Macro-average score | Task rollouts needed |
|---|---|---|---|
| SkillZip | 27.1%–36.9% (average 31.2%) | 0.577 (the uncompressed evolved skill is 0.570) | 0 |
| SkillReducer (baseline) | average 9.2% | 0.544 | 40–80 |

On the overall average alone, SkillZip's compression rate far exceeds SkillReducer's, and its macro-average score did not fall, even coming out slightly higher than the uncompressed version. But looking at the rise and fall setting by setting, the picture is not so consistent (compressed minus uncompressed):

| Model | BFCL-V4 | LiveMath | SpreadsheetBench |
|---|---|---|---|
| Qwen-3.7-Max | −0.006 | −0.002 | −0.006 |
| Qwen-3.6-Plus | +0.009 | +0.043 | +0.019 |
| Kimi-K2.6 | −0.025 | +0.024 | +0.007 |

The worst case is Kimi-K2.6 on BFCL-V4, dropping from 0.772 to 0.747, a fall of 0.025 in absolute terms, about 3.2% relative, and the paper does no additional analysis of this case anywhere. Four of the nine settings actually got worse, which is at odds with the paper's positive wording that there is "no systematic drop". To put it more strictly: "not consistently down, but there are definitely cases of regression".

There is a pattern worth noticing that the paper does not state: the three cases that dropped all occur on Qwen-3.7-Max, which happens to be the model whose evolved skill performs best of the three (0.869, 0.474 and 0.525, the highest on all three benchmarks). This hints that compression may carry higher risk when the original skill quality is already good. This is a pattern inferred from how the data is arranged, not a conclusion the paper states, and deserves a reserved attitude.

There is also a fairness concern about the comparison with SkillReducer. In its discussion section, the paper itself admits SkillReducer "is more naturally positioned as a first-pass debloating and quality-control method for general public skills". That is, SkillReducer is designed for the first kind of redundancy described in the earlier subsection "Two Kinds of 'Long' Are Not the Same Problem" (content unrelated to the topic), so SkillZip beating SkillReducer's compression rate by a wide margin may to some extent just reflect that the two were designed for different goals. The baseline is not on the same track, so the gap is not purely a difference in methodological merit.

### RQ3: Compression Cost, the Most Solid Advantage in the Paper

The paper's Table II reports the compression overhead of SkillZip and SkillReducer:

| | Average time | Task rollouts needed |
|---|---|---|
| SkillZip | 286 seconds | 0 |
| SkillReducer | about 1000 seconds | 40–80 (each at least one agent call) |

The speedup is about 3.5 times. Interestingly, the number of direct compression model calls SkillReducer uses is actually fewer than SkillZip's (3 versus SkillZip's 4 to 8), but it additionally has to run 40 to 80 task-validation rollouts, and that is the real main cause of the slowdown. This result is the most direct and verifiable demonstration of the paper's engineering value: "compress without running any task" directly saves the most expensive part of evaluation-guided compression.

### RQ5: The Effect of Zip-on-Write, Directly Validating the Continual Compression Mechanism

{{< image src="figure6.png" alt="Three side-by-side line charts for the Qwen3.6-plus, Qwen3.7-max and Kimi-k2.6 agent backbones, each with three lines: no compression, Zip-on-Write enabled from round 8, and Zip-on-Write enabled from round 1. The horizontal axis is self-evolution rounds, the vertical axis is skill length as a multiple, and the no-compression line always climbs highest." caption="Figure 5 — A 16-round self-evolution run on LiveMath, comparing skill length under no compression, Zip-on-Write started at round 8, and Zip-on-Write started at round 1. (Source: original paper, Figure 6.)" >}}

On LiveMath over 16 rounds of self-evolution, the three models gave these results: without compression, the skill bloated to 2.5 to 3.7 times; with Zip-on-Write on from round 1, it was held to 1.6 to 1.9 times, equivalent to a 38% to 50% reduction; with Zip-on-Write on only from round 8, it could win back only part of the bloat and could not catch up with the effect of "on from round 1", for example Kimi-K2.6 at 2.6 times versus 1.9 times. On accuracy, the configuration compressed from the start ended with final accuracy level with or slightly above the fully uncompressed version, adding no extra accuracy concern.

The one sentence most worth remembering from this RQ is the paper's own takeaway: "redundancy is cheaper to prevent than to remove". Preventing redundancy is cheaper than cleaning it up afterwards: the earlier continual compression is turned on, the better the effect, with no need to wait for bloat to set in before going back to deal with it. This matches the overall design spirit of Zip-on-Write exactly, tidying as you add rather than compressing after the bloat, and it is the most practically instructive conclusion in this set of experiments.

## What This Paper Actually Contributes

Taken apart, none of the underlying techniques the paper uses is original, a point already marked in every technical passage above. But a few things the paper genuinely assembled are of real value.

First, it combines the framing "a skill is a typed contract" with the MDL objective, and replaces task validation with a hard coverage constraint to guarantee fidelity. This is the only truly new theoretical contribution in the whole paper, corresponding to the paper's Proposition IV.1 and Corollary IV.2: whether a rare rule is retained depends not on how often it appears in the task distribution at compression time, but on whether the parsing step caught it. Second, the four decisions share one length-comparison skeleton (the four unfoldings of Eq.5), unifying four different kinds of repetition (equivalence, scope, workflow, exception) under one judgment logic; this is good engineering integration, not a new algorithm. Third, the local-update equivalence of Zip-on-Write (Proposition IV.2): when there are no new cross-scope reuse opportunities, local optimization equals a global rerun, and this proof gives "only look nearby" theoretical backing rather than leaving it a mere engineering shortcut. Fourth, empirically, the combination of a 31.2% compression rate, overall level accuracy, a 3.5 times speedup and zero rollouts is itself a solid engineering result, even with cases like the 3.2% regression of Kimi-K2.6 on BFCL-V4. Fifth, "redundancy is cheaper to prevent than to remove" is one of the few insights in RQ5 that is genuinely supported by data and has practical guidance value.

## Extension: Seven General Ideas Behind the Paper

The content of this part does not necessarily have anything to do with the SkillZip paper itself. It is general computer science or AI knowledge that was organized here because the paper happened to use it. The reason it is set apart as its own part is that these concepts outlast the paper: the paper's conclusions will go out of date, and these will not.

### Grammar-Based Compression and BPE

The origin is data compression and grammar induction, a classic theoretical CS topic from the 1990s to the 2000s. In the AI field you rarely see people directly use the names Re-Pair or SEQUITUR, but the spirit behind them is used by almost every LLM tokenizer, namely BPE (Byte Pair Encoding).

The core idea of Re-Pair is to repeatedly "find the most frequent pair of adjacent symbols and merge it into a new symbol", until no pair repeats. SEQUITUR is its online incremental version, reading in one symbol at a time and maintaining two invariants: no pair may appear more than once, and a repeat is immediately split off into a new rule; and every rule must be used at least twice, otherwise it is inlined and deleted. This naturally produces a nested, recursive grammar.

The simplest example: \( S = a\ b\ c\ a\ b\ c\ a\ b\ c \) (length 9, "abc" repeated 3 times). After finding the repeated segment "abc", define a new rule \( X \to a\ b\ c \) and rewrite as \( S \to X\ X\ X \). The size after rewriting is the rule body \( X \) (3 symbols) plus the main string (3 references to \( X \), 3 symbols), equal to 6 symbols, shorter than the original 9.

A full BPE walk-through (this example has nothing to do with the paper's content and is made up here). Suppose the corpus has only 4 words, with these occurrence counts: `cook_` 6 times, `cooker_` 2 times, `cookies_` 3 times, `look_` 1 time (the underscore stands for a special end-of-word symbol). Initially each word is split into single characters:

```
cook_    -> c o o k _
cooker_  -> c o o k e r _
cookies_ -> c o o k i e s _
look_    -> l o o k _
```

Round 1: count all adjacent character pairs multiplied by occurrence counts; the highest are (o,o) and (o,k), tied at 12, and (o,o) is chosen and merged into `OO`:

```
cook_    -> c OO k _
cooker_  -> c OO k e r _
cookies_ -> c OO k i e s _
look_    -> l OO k _
```

Round 2: (OO,k) is highest with a count of 12, merged into `OOK`. Round 3: (c,OOK) is highest with a count of 11, merged into `COOK`:

```
cook_    -> COOK _
cooker_  -> COOK e r _
cookies_ -> COOK i e s _
look_    -> l OOK _
```

In just 3 rounds, the 4 characters of "cook" are compressed into 1 token `COOK`, and this token is reused across 3 different words. That is what "define once, reference many" looks like concretely.

There is an easily misunderstood point to clarify here: the vocabulary is "cumulative", not "replacing". Each merge adds a new token to the vocabulary; it does not delete the old tokens and swap in the new one. After round 3, the vocabulary is `c, o, k, _, e, r, i, s, l, OO, OOK, COOK`, 12 tokens in all, not just `COOK` alone. The vocabulary (the list of all legal tokens, a fixed dictionary) and the encoding result (reassembling each sentence using tokens from the vocabulary) are two different concepts: the word `cook_` is encoded as `COOK _` (two tokens) and `cooker_` is encoded as `COOK e r _` (four tokens), so each word uses a different number of tokens. The dictionary gets thicker as it is built, but the dictionary itself does not delete other words just because you wrote a sentence.

Why doesn't merging go on until only one token is left? In practice a "vocabulary size" is set as a brake, for example stopping at 50 thousand tokens. But even with no brake, the benefit of continuing to merge keeps shrinking. The different words in the corpus differ from each other more and more, repeated adjacent pairs become rarer and rarer, and merging a pair that appears only once into a new token saves nothing (defining it costs something, yet it is used only once). This echoes SkillZip's Eq.9 exactly: when \( r=1 \), \( L(\text{def})+1 \times L(\text{call}) \) can hardly be smaller than \( L(q) \), so it does not pay off and the algorithm naturally does not choose it.

The three are related like this: Re-Pair merges arbitrary symbol sequences (general-purpose compression), BPE merges characters or subwords (building an LLM vocabulary), and SkillZip merges typed skill rules or workflow fragments.

### Loop-Invariant Code Motion

The origin is compiler optimization, general computer science background knowledge. An invariant (something unchanging), in the loop context, means that this computation gives the same result no matter which iteration the loop is on, has nothing to do with the loop variable, and just happens to be written inside the loop.

Before optimization:

```
a = 5
b = 3
for i in 0..1000000:
    x = a * b          # this line has nothing to do with i
    result[i] = x + i
```

`a * b` is recomputed on every iteration, but because `a` and `b` are never modified, computing it 1000000 times gives exactly the same result as computing it once, wasting 999999 computations. After a compiler detects this automatically, it moves it out:

```
a = 5
b = 3
x = a * b               # moved out, computed only once
for i in 0..1000000:
    result[i] = x + i
```

The behavior is completely unchanged, saving 999999 repeated computations. The conditions for deciding whether it can be moved are: the computation writes nothing that a loop variable would change, depends on no variable that changes only inside the loop, and moving it outside the loop does not change program behavior (it cannot have side effects). If `a` or `b` is modified midway through the loop, it is no longer invariant and cannot be moved.

This is the same logic as SkillZip's scope lifting (Eq.8): loop-invariant code motion in a loop is "this computation is the same in every iteration, so move it outside the loop and compute it only once"; SkillZip's scope lifting is "this rule is the same in every child branch, so move it to the common parent scope and write it only once". The conditions line up too: the compiler requires it to be unchanged every iteration, and SkillZip requires that every relevant child path needs the rule; the compiler cannot move it if it is modified midway, and SkillZip cannot lift the whole rule away if some branch has a conflict, and must leave an exception. This mental model applies not only to skills but to any system with nested structure, such as configuration inheritance and method overriding in object orientation; it is all the same logic.

### NLI and the Relation Checker

The origin is Natural Language Inference (NLI), a classic task in NLP and very common in the AI field. The standard definition is: given two sentences (premise and hypothesis), judge their logical relation, usually in three classes: entailment, where if the premise is true the hypothesis must be true too, for example "it is raining heavily today" entails "the weather is bad today"; contradiction, where the two sentences conflict and cannot both be true, for example "it is raining heavily today" and "the sky is cloudless today"; and neutral, where the two sentences have no necessary relation.

SkillZip's four-way classification belongs to the same family as the NLI three-way one, just cut with one extra class: entailment corresponds to implication (one-way entailment), and equivalence (two-way entailment) is a special case of entailment; contradiction corresponds to conflict; and neutral corresponds to unrelated.

"Frozen" means the classifier's parameters are never updated or fine-tuned during use; it is a trained off-the-shelf model used directly as a tool, frozen like the vector model used by the embedding index. The reason for emphasizing frozen is to echo "optimization is deterministic": if the classifier's parameters could change, the same input might give different answers on different runs, breaking the determinism guarantee.

The embedding index works by first turning each piece of text into a string of numbers (a vector), designed so that "texts with similar meanings get similar vectors", precomputing the vectors of a large amount of text and storing them in a data structure, so that given a new vector you can quickly find "which vectors are nearest to it" without comparing one by one. This step can only tell you "the two are semantically close"; it cannot tell you "close enough to merge, or close but contradicting each other", and that is why a relation checker is needed to judge once more.

Is the paper's use "light"? Not really. Standard NLI usually judges the logical relation of "two complete sentences", while SkillZip uses it to judge the relation between "two rules carrying scope, guard and modality labels", with an added "structural screening first, then ask" preliminary step. That is a reasonable extension, not decorative name-dropping.

### Three Combinatorial Optimization Tools: DP, Weighted Set-Packing, Clustering

**Dynamic Programming**: an example unrelated to the paper is climbing stairs — each time you can climb 1 or 2 steps, and the staircase has 5 steps; how many ways are there in total? The core idea is to compute the answer to "how many ways to reach step N" once and store it, then simply look it up when the same question comes up again, with no recomputation.

```
Reach step 1 = 1
Reach step 2 = 2
Reach step 3 = reach step 1 + reach step 2 = 1+2 = 3
Reach step 4 = reach step 2 + reach step 3 = 2+3 = 5
Reach step 5 = reach step 3 + reach step 4 = 3+5 = 8
```

It applies when a big problem can be split into many small problems, many of the small problems are actually the same (asked many times), and the big problem's answer can be assembled from the small problems' answers. Back to SkillZip: DP works "bottom-up" over the scope tree, first computing and storing the cost of placing a child node's own rules, and then, when computing the parent, using the answers already computed and stored for the children to judge "would moving the rule from both child nodes up to the parent make the total cost lower than keeping them separate", without rescanning the whole tree.

**Weighted Set-Packing**: an example unrelated to the paper is scheduling ad slots — in an evening slot from 8 pm to 11 pm, several advertisers want to run ads, but each ad has its own start and end time, ads with overlapping times cannot air together, and each ad bids a different amount; the task is to pick the combination with the greatest total revenue:

```
Ad A: 8:00-8:30, $100
Ad B: 8:15-9:00, $150   (overlaps A)
Ad C: 9:00-10:00, $200
Ad D: 8:30-9:30, $180   (overlaps C)
Ad E: 10:00-11:00, $120
```

Overlapping candidates allow only one to be picked, and the aim is to assemble the combination with the highest total value from limited, mutually exclusive options. The paper's approximate solution is greedy plus pairwise exchange: first sort by "how many tokens saved per unit of coverage" (not by total value), pick the best deal, and once picked, exclude the candidates that overlap with it, repeating until no new ones can be picked; then try swapping one already-picked candidate for an unpicked one and see whether the total value goes up, swapping if it does and leaving things as they are if not, repeating until no swap gives a better combination. Back to SkillZip: the workflow candidates' "no overlap" constraint is a concrete version of this problem. For example, in the sequence "[1] validate → [2] repair → [3] validate → [4] confirm → [5] output", candidate A covers [1][2][3] and candidate B covers [2][3][4]; the two overlap on [2][3], so only one can be picked, and the efficiency ratio "tokens saved divided by tokens covered" is used to sort and decide which.

**Clustering (Union-Find)**: an example unrelated to the paper is sorting fruit into piles — according to some similarity measure, automatically divide a heap of things into groups so that things in the same group are similar to each other. The chained-merge property of Union-Find is: initially every item is its own group; on seeing "C1 equivalence C2" they merge into {C1,C2}; on seeing "C3 equivalence C4" they merge into {C3,C4}; and on then seeing "C2 equivalence C4", since C2 is in {C1,C2} and C4 is in {C3,C4}, the two groups merge into one big group {C1,C2,C3,C4}. Even though the original relations are only pairwise, Union-Find handles the chain effect automatically. The reason to do conflict filtering before clustering is: if the relation checker also reported an incompatible relation such as "C1 conflict C5", that pair must first be excluded and kept out of the union-find merge list; only equivalence or implication pairs may enter union-find, while conflict pairs must go down the Decision 4 path and cannot be mixed in. Back to SkillZip: after Union-Find forms the groups, all the rules in the same group are eventually merged into one shared content (Decision 1), and if the group is spread across different scopes, DP then decides where on the scope tree the shared content should go (Decision 2).

A comparison of the three:

| | Dynamic Programming | Weighted Set-Packing | Clustering (Union-Find) |
|---|---|---|---|
| General problem shape | A big problem splits into small ones whose answers can be reused | Candidates are mutually exclusive; pick a conflict-free set with the highest total value | Items are related pairwise; automatically merge them into groups |
| Key feature | Later answers depend on earlier answers already computed | Candidates overlap/conflict; picking one crowds out another | Relations are chainable |
| Nature of the solution | Exact | Approximate (greedy + fine-tuning) | Exact |
| Corresponding sub-problem in the paper | Decision 2: scope placement | Decision 3: workflow candidate exclusion | Decision 1: grouping equivalence sets |
| Corresponding formula | Eq.8 | Eq.9 | Eq.7 |
| Everyday analogy | Climbing stairs | Ad slot scheduling | Sorting fruit into piles |

### MDL (Minimum Description Length)

The origin is information theory and statistics in the late 1970s, with Rissanen as the representative figure; it is a mathematical formalization of "Occam's razor" (the simpler the explanation, the better). Its very common relatives in machine learning include BIC from statistics, decision tree pruning and regularization (L1/L2 penalty terms), all different implementations of the same spirit.

The core intuition is explained with a classic example unrelated to the paper: a set of data points \( (1,1)(2,4)(3,9)(4,16)(5,25) \). Option A describes them with the simple formula \( y=x^2 \): the model itself is short and the residual is 0. Option B forces a degree-5 polynomial through them, which happens to pass through exactly these 5 points: the model itself is long (5 odd coefficients to remember) and the residual is also 0. The two have the same "accuracy", with residual 0 in both cases, but the total cost (model description length plus residual description length) differs, and Option A is shorter. MDL picks Option A. Even with accuracy tied, Option A captures the real structure in the data in a more concise way, while Option B just memorizes the answers.

The standard two-term form is:

\[ \text{total cost} = L(\text{model}) + L(\text{data} \mid \text{model}) \]

\( L(\text{model}) \) is how much space it takes to describe the model itself, and \( L(\text{data}\mid\text{model}) \) is how much more space is still needed to fully describe the data given the model, that is, the residual not explained by the model. Back to SkillZip's Eq.4: \( K \) (the contract library) corresponds to the "model", and \( R \) (the residual) corresponds to the "part of the data not explained by the model". \( K \) plays the role of "the formula \( y=x^2 \)", capturing the real structural regularity in the skill in the most concise way; \( R \) plays the role of the "residual", special content that the rule library cannot explain and that must be kept verbatim.

The paper does not borrow this concept lightly or say offhandedly "it's a bit like MDL"; it writes Eq.4 directly as the standard two-term form of MDL, with the four decisions (Eq.7 to Eq.10) all being concrete unfoldings of this formula in different situations, and the paper itself states this lineage explicitly in its related work section. Other common appearances of MDL in AI include decision tree pruning (prune a tree that is too complex without a significant accuracy gain), regularization (penalizing overly complex model parameters), Re-Pair/SEQUITUR (which the paper itself classifies as instances of the MDL spirit), and BIC (the criterion in statistics for comparing models, with a formula structure almost the same as MDL's).

### Relevance-Based vs. Redundancy-Based Compression

A typical prompt compression scenario (such as LLMLingua) is a long document plus a specific question for the LLM to answer:

```
Input: [a 5000-word Wikipedia article on diabetes] + question: "How is type 2 diabetes treated?"

Approach: estimate how important each piece of text is based on "this question"
     -> treatment-related passages: keep
     -> etiology and epidemiology passages: low relevance -> delete
```

This makes sense because there is a clear "current question" to use as the filtering basis. The skill situation is different: a skill is not written for a known question; it is written for "any future question belonging to this task category". At the moment a skill is loaded, nobody knows what will be asked next. If the logic of prompt compression were applied, deleting whatever has low relevance to the current query, then today when an algebra question is asked, the "rules about factorials" would be judged low-relevance and deleted, and tomorrow when a factorial question comes up, that rule is necessary but has already been wrongly deleted. The paper's wording corresponding to this logic: "Skills should be reusable for all queries of certain tasks... a reusable skill must retain requirements that no compression-time query activates."

This distinction can be used to decide which approach fits any situation of "should this document be compressed or trimmed": is there a clear, current usage situation to serve as the filtering basis? If yes, use the relevance approach; if no, meaning it must hold for all future situations, only the redundancy approach will do.

### The Architectural Principle of Separating "Understanding" from "Decision"

The division of labor across SkillZip's whole system is: semantic judgment (which category something belongs to) goes to the LLM, that is, the extractor in step 2 and the relation checker; mathematical judgment (does it pay off, which to pick) goes to deterministic code, that is, the host validation, the cost computations of Eq.5 to Eq.10, DP, weighted packing and clustering.

The paper states the intent of this division of labor explicitly: "The extractor is deliberately not asked to compress. Separating interpretation from optimization has two benefits: contract recovery can be evaluated against human annotations, and the optimization is deterministic once the extracted units are fixed." In plain words there are two benefits: the quality of extraction can be tested independently, checked against human annotations, without interference from the later compression logic; and once the extracted units are fixed, "whether to merge" is pure math, the same input always gives the same output, and LLM randomness cannot make every compression result different.

This principle applies not only to skill compression. Any scenario that wants to use an LLM's semantic understanding while requiring the system's final behavior to be reproducible and verifiable is worth adopting this division of labor: hand the part that needs semantic judgment, such as "what is this, and what is the relation between these two", to the model, and hand the part that can be expressed with explicit rules, such as "given this judgment, what should be done", to deterministic code.

## Conclusion

The problem SkillZip wants to solve is very concrete: a self-evolving agent's skill file keeps growing because of an append-only maintenance style, while the amount of genuinely new knowledge in that growth flattened out long ago. Its solution is to first break the skill into a typed contract (six types: interface, workflow, tool protocol, rules, output and evidence), then use four decisions under the MDL objective (equivalence merging, scope lifting, workflow reuse, general rule plus exceptions) to collapse the repetition, with a hard coverage constraint throughout guaranteeing that the meaning of the original rules does not vanish into thin air, which is also why no task needs to be run to validate the compression result.

The measured numbers are solid: an average compression rate of 31.2%, overall accuracy level or slightly up, compression 3.5 times faster than the competitor, and no task rollouts at all. The continual mode, Zip-on-Write, further validates "redundancy is cheaper to prevent than to remove": the earlier you start continual compression, the better bloat is controlled. But every technique the paper itself uses is unoriginal, and its real contribution lies in system integration and in the design choice of replacing "validating with tasks" by "guaranteeing with structured hard constraints" as the source of fidelity.

The three reservations raised at the start are worth pulling together once more: the fidelity guarantee only holds for what the parsing step caught, and whatever the parsing step misses has no remedy afterwards; four of the nine test settings actually regressed, the worst dropping 3.2%, and the paper does no further analysis; and the comparison with SkillReducer is to some extent a comparison across different tracks, because the kind of redundancy each was designed to target is different to begin with. If you do practical work on skill evolution or agent memory management, the paper's architectural thinking, especially "separate understanding from decision" and "replace task validation with hard constraints", is worth borrowing directly; as for the general computer science tools the paper touches on, what the extension part collected is just as useful away from this paper.

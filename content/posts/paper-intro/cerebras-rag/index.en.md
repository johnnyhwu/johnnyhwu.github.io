---
# weight: 1
title: "Cerebras's Enterprise RAG: Narrow-Waist Design, Decoupled Retrieval"
date: 2026-07-23
lastmod: 2026-07-23
draft: false
description: "How Cerebras's enterprise RAG uses narrow-waist design to decouple ingestion from retrieval, fuses rankings with RRF, and why it's a pipeline, not an agentic loop."
featuredImage: "featured-image.png"

tags: ["Large Language Model", "Retrieval-Augmented Generation"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## Introduction

In July 2026, Cerebras published a blog post describing the architecture of their internal knowledge base, "Cerebras Knowledge" — a system that handles over 15,000 queries a day, spans data from Slack, Wiki, code repositories, and Jira, and serves not just humans but automated workflows and AI agents as well.

This note is what I came away with after reading the article and holding it up against my own hands-on experience building an enterprise RAG system. It's organized around a single mental model — "narrow-waist design" — and works through the data abstraction layer, hybrid retrieval and reranking, query planning, and organizational scoping in turn. It closes with two judgments the article never states outright, but that fell out of the discussion anyway: **retrieval and reasoning must be decoupled**, and **this architecture is fundamentally a single-round pipeline, not an agentic loop**.

{{< admonition abstract "Key Takeaways (TL;DR)" >}}
- **Narrow-waist design**: heterogeneous data (Slack, Wiki, code, Jira) converges on the write path into a single embeddings table with only five columns; the read path then re-expands from that one narrow interface into whatever retrieval and orchestration strategies it needs — so ingestion and retrieval can evolve independently.
- **Hybrid retrieval is fused with RRF, not score normalization**: Reciprocal Rank Fusion compares ranks, not scores, which sidesteps the incomparable-score-scales problem entirely, and the constant `k=60` tunes the system to favor cross-retriever consensus over any single strong signal.
- **The Planner routes, it doesn't judge sufficiency**: an LLM dynamically decides which tools to use for a given query, but the whole pipeline runs one planning decision, one parallel execution, one synthesis — there's no "evidence wasn't enough, go retrieve again" feedback loop. It's a single-round pipeline, not an agentic loop.
{{< /admonition >}}

## The mental model that runs through the whole article: narrow-waist design

If I had to explain this entire article with a single concept, I'd pick "narrow-waist design."

Picture an hourglass: the top half is a collection of heterogeneous write sources — Slack threads, Wiki pages, code, Jira tickets, even custom databases; the middle narrows down to one simple interface; the bottom half re-expands into whatever retrieval and orchestration strategies are needed. In Cerebras's system, that "narrow waist" is a single embeddings table with just five columns: `document` (the searchable text), `embedding` (the vector), `metadata` (an opaque JSON blob), `source` (where it came from), and `timestamp`.

The value of the narrow waist isn't that "unification" looks tidy — it's that **everything above the waist and everything below it can evolve independently, without interfering with each other**. Adding a new data source only means writing a connector that pushes data into those five columns; the read side doesn't need to change a single line. Switching retrieval strategies only touches the read side; the write side feels nothing. The article puts it bluntly: whether it's Slack chatter or a chip schematic table, once it's in that same embeddings table, it can be queried through the same interface — which is exactly the effect narrow-waist design is meant to produce.

It's worth noting this "narrow waist" shape recurs at least three times in the article, not just once at the data-ingestion layer:

| Where it appears | Before convergence (wide) | After convergence (narrow waist) |
|---|---|---|
| Data ingestion layer | Heterogeneous sources: Slack, Wiki, code, Jira | A single embeddings table |
| Read-side fusion layer | Each retriever's own ranking | Fused into one ranking via RRF |
| Multi-tool output layer | Each tool returns results in its own format | Normalized by the executor into a shared evidence schema |

All three occurrences are really the same move: **let diversity converge to a single, simple, unified shape at some point, then re-expand from that point.** This tension — "unify on the write side, embrace divergence on the read side" — is close to the shared theme underlying nearly every technical detail in the article; every subsequent section is really just a concrete implementation of this same tension at a different layer.

The system's infrastructure choices echo this same principle: embeddings, raw summaries, metadata, and sync state all live in the same Postgres instance (via pgvector, 3072 dimensions, HNSW index). This choice has a compounding payoff that's especially visible in code embeddings — because sync state lives in the same database as the embeddings, each commit only needs to reprocess the handful of chunks that actually changed, instead of recomputing the whole repo.

## Unifying the data abstraction layer: even connectors have to narrow

There's a trap worth naming: "unified in form but fragmented in meaning." If the embeddings table grows source-specific columns like `slack_channel`, `code_repo`, or `jira_ticket_id` just to accommodate each source, downstream retrieval logic still ends up full of source-type if-else branches — and that's not really a narrow waist. Cerebras's approach narrows all the way down: downstream logic never needs to know where a row came from in order to process it; the `source` column only matters at the very end, when results are presented to the user.

There's a simple test for whether the narrow waist has actually been narrowed cleanly: if downstream retrieval or ranking logic contains an `if source == 'X' then...` branch, the waist hasn't been narrowed enough yet.

Each connector only has to answer three questions, and **only these three**: how to turn source data into a document plus metadata (a transform function), how to pull data from the source system (a fetch function), and how often to sync (which can even vary per channel, as with Slack). The connector doesn't need to know how the downstream side will use this data at all — none of these three questions touches "how to retrieve it," which is exactly how "decoupling ingestion from retrieval" gets implemented concretely at the data layer.

A sufficiently narrow contract pays an organizational dividend: adding a new data source can be fully delegated to a team that has no familiarity with the core system. Open a PR, attach a small Python module, and as long as its output conforms to the shared schema, everything else wires up automatically — no core-team involvement required. This is actually a useful litmus test: if adding a new data source requires the core team to step in, that's usually a sign the abstraction layer itself is leaking.

One easily overlooked detail: the `metadata` column isn't just decorative information for display — it's also the carrier for retrieval ranking signals. For example, the age decay mechanism discussed later reads its timestamp directly from `metadata`. This means metadata design has to anticipate, at connector-writing time, what ranking signals might be needed later (timestamps, source type, author or team information) — because retrofitting them afterward means reprocessing the entire corpus.

## Why pure vector search can't handle Slack conversations

The article spends considerable space on how Slack messages get processed, because pure vector search has three very specific failure modes on this kind of data.

### Three failure modes

First: embedding compression is insensitive to "how much actual information this text carries" — it only captures semantic direction. That means a throwaway remark and a substantive one can score nearly identically if their semantic direction is both close to the query — vector search can't distinguish "this is semantically related" from "this actually has content."

Second is a subtler geometric property: short messages systematically win on cosine similarity. Short messages have vector directions that are more concentrated and clear-cut, while long messages, containing multiple sub-topics, end up as a weighted average of several semantic directions — their direction gets diluted. This isn't something a different embedding model fixes; it's a property of the representation itself.

Third is context dependency — a standalone message like "that fixed it" is meaningless outside its conversational context, which is also why the unit of processing needs to be the entire thread, not a single message.

Facing these three failure modes, Cerebras didn't just stack a few common signals together — it first diagnosed the precise root cause of each failure, then found a signal whose mathematical properties happen to be immune to that specific root cause:

| Failure mode | Corresponding signal | Why it's immune |
|---|---|---|
| Semantic direction masks content value | IDF (term rarity) | Computes term rarity directly, independent of vector geometry |
| Short messages win unfairly | Full-text search | Exact token matching, unaffected by length |
| Context dependency | Thread-level chunking | Preserves the full conversational context |
| Answers go stale | Age decay | Reads timestamp directly, independent of semantics |

There's an easily overlooked but crucial precondition here: stacking two signals only makes sense if their failure modes are "orthogonal." If two signals fail on the same kind of input, stacking them solves nothing — it just counts the same weakness twice.

### Distillation: normalize before you embed

Before text ever gets fed into a vector model, the system does one more step called distillation: instead of embedding the raw thread text directly, it first has an LLM read the entire thread and extract four pieces of structured data — a one-line question, a summary, the solution, and system/code references — normalized into a consistent format before embedding. The raw text separately goes into Postgres full-text indexing, staying literally searchable, but never entering the vector space.

Why this step matters comes down to a property of embeddings themselves: embedding quality depends heavily on the formal consistency of the input text. A thread might be 2 people saying 3 sentences, or 10 people arguing across 50 off-topic messages — if you embed raw text with such wildly varying length and participant count directly, the resulting vectors become fundamentally incomparable on the question of "what does this document represent." The article notes that after threads are normalized into a consistent format, accuracy shows a measurable improvement — no specific numbers are given, but the direction itself has been validated empirically, not chosen as an arbitrary design preference. Notably, the article's own word choice is "normalized," not "summarized" — the emphasis is on making vectors semantically consistent within the same representation space, not merely shortening the text. This also gives a fairly general rule of thumb: when raw data varies wildly in form, the question isn't "should we summarize," but "is there a fixed schema that can converge this heterogeneous data into a consistent format."

### Bursting: recovering valuable outlier content

Distillation is lossy compression, though, and important side information can get dropped by the summary if it wasn't part of the main question-answer thread. The system compensates with a mechanism called bursting: it pulls out "consecutive messages from the same author" on their own, prepends the thread's topic as context, and embeds them separately. But not every burst is worth keeping — it must clear three quality gates: IDF ≥ 4.0 (ensuring it contains rare terms, not pure filler), length ≥ 200 characters (ensuring there's enough content to support a meaningful vector), and a bonus for having a reaction (using social signal as an indirect validation of value).

A concrete example: a thread with 4 speakers and 5 messages might end up producing "1 thread-level distillation artifact, plus N bursts that cleared the quality gates," all written into the same embeddings table, with metadata marking the type as `slack_thread` or `slack_burst`. Bursts that don't clear the gate (pure social filler, for instance) never get embedded at all.

There's an engineering principle worth writing down here: rather than letting garbage data slip into the system and relying on expensive downstream reranking to fix its position, it's cheaper to filter with low-cost rules at write time. Filtering at write time is a one-time cost; reranking is a cost paid on every single query — the earlier noise gets blocked, the more it saves over the long run.

Anyone familiar with Anthropic's Contextual Retrieval might find bursting a bit familiar. Contextual Retrieval's core idea is generating a custom context prefix for each chunk, to avoid isolated fragments losing their surrounding context. Bursting is essentially a lightweight version of the same principle: instead of running an LLM to generate context for every single burst, it just pastes the thread's overall topic on as a prefix — achieving a similar effect at a much lower cost.

## Turning multiple retrieval rankings into one ranking

The system fires several retrievers at the same query simultaneously (vector search, full-text search, IDF-weighted search, and so on), which creates an immediate headache: scores from different retrievers simply aren't directly comparable. BM25's score range is unbounded, while cosine similarity falls between -1 and 1 — the units, scales, and distribution shapes are all different, so adding them together is meaningless. The common fix is normalizing each score to a 0–1 range before combining with weights, but that has its own trap: normalization depends on "what the max and min are within this particular result batch," so the same document's relative weight can drift unpredictably from one query batch to the next.

### RRF: only looks at rank, never at score

Cerebras's solution is RRF (Reciprocal Rank Fusion), with a formula that looks like this:

```
RRFscore(d) = Σ  weight_i / (k + rank_i(d))
              i∈retrievers
```

Where k = 60 (this smoothing constant comes from the recommended value in Cormack et al.'s 2009 paper), and weight defaults to 1.0. If a given retriever doesn't surface the document at all, that term's contribution is simply 0 — no bonus, no penalty.

RRF's core insight is that it only uses "rank," never "score." Rank is an integer every retriever naturally has, and one that's naturally comparable across retrievers — this single move sidesteps the "incomparable score scales" problem entirely, with no normalization needed, and therefore none of the drift that normalization introduces.

The constant k is really a dial for a design philosophy. The larger k is, the more it flattens the score gap between top ranks, and the more the system favors "shows up across multiple retrievers, scores accumulate gradually" winning over "shoots to #1 in a single retriever" — in other words, it prefers consensus over a single strong signal. The smaller k is, the more disproportionate the reward for landing #1, and the more the system trusts a single retriever's strong signal. Choosing k=60 means Cerebras chose to "trust the consensus of multiple independent signals rather than be led astray by a lucky hit in a single retriever."

Working through an actual example makes the effect concrete: if document A ranks 3rd in both retrievers, while document B ranks 1st in one but only 8th in the other, the computed RRF score often favors A — a document that's "reasonably solid on both sides" can beat one that's "very strong on one side but mediocre on the other." That's the concrete mathematical effect of RRF rewarding consensus and penalizing single-retriever strength.

### The relationship between IDF and BM25

Here's a point that's easy to conflate: what's the actual relationship between IDF and BM25? The two are often treated as the same thing, but their roles are actually different:

| | BM25 | IDF as used in the article |
|---|---|---|
| Role | A complete sparse ranking function | A single weighting signal / quality gate |
| Output | A ranking | A multiplier used to adjust other signals |
| Purpose | The entire sparse retrieval leg | Extra suppression of results that are "semantically close but pure filler" |

Put simply, IDF is already a component inside BM25; Cerebras pulls this component out and uses it separately as an independent signal. What the article calls "full-text search" corresponds to the sparse retrieval (BM25) leg everyone's familiar with; IDF is an additional, cross-cutting quality signal usable across every leg.

{{< admonition tip "A practical takeaway: pulling IDF out as an independent signal is especially useful for conversational data" >}}
If a system is already doing hybrid retrieval with BM25 plus vectors, IDF is technically already implicit inside BM25 — but pulling IDF out separately as an independent filtering or weighting signal, specifically to suppress results that are "semantically close to the query but pure filler," turns out to be especially useful for conversational data. Something like Slack, full of social filler, doesn't get filtered by BM25 ranking alone — filler that floats up in vector retrieval won't be caught there — but an independent IDF gate can do exactly that. The two aren't in conflict and can be stacked together.
{{< /admonition >}}

### Wrapping up the fused ranking: dedup, rerank, context recovery

Once fusion is computed, there are three finishing steps. First is dedup and capping: a single document is often chunked into several pieces, and if multiple chunks from the same document all rank near the top of the candidate set, they crowd out slots and reduce source diversity — the fix is capping how many candidates any single document can contribute. Second is bringing in a reranker (a cross-encoder model): RRF ranking is purely statistical fusion and doesn't understand the actual semantics of the query, while a reranker pairs the query against each candidate document one at a time and outputs a direct relevance score, capable of the semantic-level judgment RRF can't do.

{{< admonition info "Clarification: what a 'single call' to the reranker actually means" >}}
There's a technical detail worth clarifying here, to avoid misunderstanding how the reranker works. A "single call" to the reranker means it's packaged as one batched API call, but internally it still runs one "query-paired-with-document" inference per candidate — 20 candidates means 20 separate pairings, not all candidates stuffed into a single shared context at once. This is fundamentally different from the LLM call in the later synthesis stage:

| | Reranker | Synthesis LLM |
|---|---|---|
| Input format | Sees (query, single document) each time | Sees (query, all candidates) at once |
| Model's job | Scoring (classification/regression) | Generating coherent text |
| Compute scale | Small model, fast | Large model, long context, slower |

The whole pipeline is "progressively more expensive": the later the step, the higher the cost of each individual call. So the earlier, cheap steps (RRF fusion, dedup and capping) shrink the candidate set as much as possible, leaving the most expensive computation (synthesis) for a small number of high-confidence candidates.
{{< /admonition >}}

The last finishing step is recovering context: once the final top 10 is set, if the winner is a section from within some document, the system pulls back the two adjacent sections to present alongside it, so that chunking doesn't accidentally slice off a precondition or caveat into the neighboring chunk and lose it. This step only happens after reranking, and only for the small final set of results to present — avoiding wasted resources at the candidate stage.

{{< admonition warning "A structural weakness in RRF: lessons from slide retrieval" >}}
RRF has a structural weakness that shows up with enough use — I ran into it myself while building slide retrieval. The setup was: each slide first gets a text summary from a VLM (vision-language model), which is then embedded, paired with hybrid retrieval. A recurring failure looked like this: the correct slide ranked #1 in vector search, but full-text search never surfaced it at all (and the reverse happened too). After fusion, the correct answer's rank actually got worse. The stopgap fix was "always keep the #1 result from vector search and #1 from full-text search, regardless of fusion."

Tracing the root cause: RRF's "reward consensus" mechanism implicitly assumes every retriever at least "sees" the correct answer, just ranks it differently. Once the correct answer is completely absent from one retriever's leg (not even a candidate), RRF's contribution from that leg is 0 — and "consensus" flips into "penalty": the correct answer is propped up by a single leg's score alone, and can lose to a noisy document that ranks mediocre on both legs but appears in both. The slide-retrieval scenario is especially prone to this because vector search and full-text search **share the same unstable intermediate source** — the VLM's summary wording is inconsistent, so the same chart might be described as "revenue growth" in one pass and "sales increase" in another, causing full-text search — which is sensitive to literal wording — to score zero purely because of unlucky word choice. Sharing a single signal source between the two legs breaks exactly the "signals must be orthogonal" precondition mentioned earlier.

The fix can be layered from shallow to deep: first, deepen the recall depth of each leg (say, to top 50–100) — a lot of "absent from one leg" cases are really candidates cut off just past the truncation line, and deepening recall recovers them, while RRF's contribution from deep ranks is naturally small, so it doesn't introduce much extra noise. Going further, you can fix the representation layer so the two legs no longer share the same source: full-text search shouldn't index only the VLM summary — it should also index the slide's raw text (titles, bullets, and chart labels extracted via OCR), whose wording is stable and unaffected by the VLM's inconsistent word choices. The most fundamental fix is letting the reranker patch RRF's structural weakness: take the union of each leg's deepened recall (not just trusting RRF scores), and hand it to a cross-encoder to score each candidate individually — a reranker evaluates the query and document as a direct pair, indifferent to which leg it came from, so as long as the correct answer made it into the union, it has a chance to rank at the top, naturally immune to the "absent from one leg" problem.
{{< /admonition >}}

## Making the LLM route, not do grunt work: Planner and agent orchestration

If every query blindly calls every tool, it brings two direct downsides: unneeded tools still get triggered, adding latency and wasting cost; and noisy results from irrelevant tools can drag down overall ranking quality. The Planner's first-principle reason for existing is to turn "which tools should be used this time" from a fixed rule into a dynamic decision, so cost and latency scale with what the query actually needs. This idea of dynamically deciding the routing path per query is, at its core, the same move as [UniversalRAG](../universal-rag/)'s Router dynamically choosing a path by modality and granularity — just applied to a different axis.

### The Planner is deliberately made cheaper than the tools it serves

The Planner takes three inputs: a tool catalog (needing only concise capability descriptions, not full technical documentation or internal implementation details), the user's query itself, and the currently locked query scope (corresponding to the Projects concept discussed later). Its output is a list of selected tools, handed to the executor for parallel execution.

The Planner is deliberately designed to be cheaper than the tools it serves — it performs a classification task (choosing one or a few options from a finite set), not a generation task, so it can use a small model with structured output, keeping inference cost and latency low — making it the cheapest link in the whole pipeline. This is actually an important architectural principle: the decision layer must be deliberately cheaper than the execution layer, or else "a decision meant to save money" being expensive itself would be self-defeating.

To the Planner, a tool is always a black box — it only needs to know a tool's capability description, not whether internally it's a simple lookup or requires an extra round of reasoning to produce a result. This lets tools of very different natures be treated equally under the same planner logic.

{{< admonition tip "A question this resolved for me: does SQL querying violate single-round synthesis?" >}}
This point resolved something I'd been stuck on for a while. When handling questions that need SQL queries, the common flow is "first retrieve the table schema, then run one LLM call to do SQL reasoning and pull the relevant data, then run a second LLM call to generate a text answer based on that data." At first glance this seems to contradict the article's "single synthesis call produces the final answer" approach — if the retrieval tool itself needs internal reasoning to obtain evidence, does the single-round synthesis architecture still hold up?

The key is distinguishing "lookup" from "compute." The tools the article lists — search, search Slack, search code, find who knows this domain, and so on — all retrieve from data that's already been embedded or indexed, precomputed and sitting there waiting to be picked up; the retrieval action is fundamentally read-only, and what comes out is already evidence in its final form, ready to go straight into fusion ranking with no extra reasoning needed. The SQL scenario is fundamentally different: "pulling out the relevant data" itself requires generating and executing SQL on the spot to get an answer — that's an irreducible reasoning step, not a read-only fetch.

The test is what kind of output that LLM call produces. If the output is "evidence" (something downstream will further process), the step can stay — but it must be **hidden inside the retrieval tool**: SQL generation should live inside the `search_sql` tool as a necessary step to obtain the query's result rows, exposing only those rows to the outside. If the output is "a partial answer aimed at the user's question" (say, a summary pre-generated for a single data source), that step should be cut and deferred to the single synthesis call at the very end of the pipeline. To the Planner, `search_sql` is, like every other tool, just a black box selected based on its capability description — it doesn't need to know whether the inside is lookup or compute.
{{< /admonition >}}

### Two external interfaces: MCP and Web UI

The system exposes two interfaces to the outside world, sharing the same underlying primitives but built for entirely different purposes. The MCP interface deliberately excludes the planner and exposes only the most basic retrieval primitives — tools are designed to be as simple as possible and to avoid depending on an LLM, leaving an external agent (such as Claude Code) to decide the calling order and how to combine results on its own. The Web UI interface is the opposite: it wraps up the planner, executor, and synthesizer entirely, presenting the user with a simple question-answering interface.

The reasoning behind this split is direct: MCP's user is another agent with its own reasoning capability, and it shouldn't have decisions made for it in advance — if a hidden planner layer sits behind the tools, the external agent's expectations about tool behavior would break down, because tool behavior would no longer be a deterministic function of its input, but would instead depend on a hidden decision layer it can't see. The Web UI's user is a human, and humans don't compose tool calls themselves — the system has to package the entire flow for them.

This suggests a judgment worth keeping in mind: if a system may need to be called by other agents in the future, it must split "retrieval primitives" from "orchestration decisions" into two independently exposable layers — this is really the "decouple retrieval from reasoning" principle replaying itself one layer up, at the orchestration layer, in the same spirit as [HiRA](../hira/) and [Plan-and-Act](../plan-and-act/) splitting Planner and Executor into distinct roles.

The Executor carries two responsibilities: executing selected tools in parallel (assuming the tools have no dependencies between them and are themselves stateless retrieval primitives), and normalizing the raw output formats from different tools into a shared evidence schema (including score, freshness, and source hints). This is the narrow-waist design's third appearance, this time at the multi-tool output integration layer on the read side.

## Once the knowledge base gets large: Projects and scoping

The assumption of "search everything globally" degrades systematically as scale grows. The larger the corpus, the worse noise erodes ranking quality — a document that used to be irrelevant only needs to brush against a query on some semantic or literal edge to have a shot at crowding into the top of the candidate set, pushing the actually correct answer further down. This isn't the retrieval algorithm getting worse; it's that the assumption of "search everything" itself systematically degrades the signal-to-noise ratio as data volume grows. What makes this tricky is that the phenomenon is quite invisible: everything looks fine at small-scale testing, and it quietly degrades in production as data grows, making it hard to pin down which technical piece is actually at fault.

Cerebras's solution is Projects: a project is a named bundle of data sources. The key word is "reference," not "copy" — the same data source can be referenced by multiple projects without ever being physically duplicated. This means a project is essentially a logical filter condition applied at query time (for example, a range restriction on the `source` field in metadata), not a new data container. This design avoids the risk of data-update consistency and avoids storage cost growing linearly with the number of projects — again embodying the principle of "ingestion and retrieval evolving independently": adding a new project touches zero data-ingestion logic.

Scoping interacts directly with the two mechanisms discussed earlier. Its relationship with reranking: scope filtering should happen before RRF fusion, not after fusion and reranking are both done — otherwise ranking compute gets wasted on out-of-scope data, and out-of-scope documents could even occupy top-K slots. Its relationship with the planner: the currently locked scope is one of the planner's decision inputs, not just a downstream retrieval filter — it constrains both "where to look" and "whether a tool should even be considered," e.g. if a given project has no custom database attached, a tool like `search_sql` almost certainly shouldn't be considered.

As for how new users know which scope to pick, Cerebras's approach is to bind a default project directly to the user's profile. Requiring users to choose their own scope would mean offloading "organizational knowledge the system should already know" onto the user — which is putting the cart before the horse. A new user shouldn't need to first understand how the company's data sources are grouped internally just to automatically get high-signal answers. This is the principle of "keep system complexity inside the system, don't leak it to the user," concretely realized at the user-experience layer.

## What the article doesn't say: the boundary between a single-round pipeline and an agentic loop

All these technical details are solid, but after reading the whole article, I noticed a boundary it never touches at all — and one important enough to call out on its own: this architecture is, at its core, a **single-round pipeline**, not an agentic loop.

### Two structural limitations of a single-round architecture

The complete flow the article describes is: a query comes in, the planner decides once, execution runs in parallel once, synthesis happens once, done. This is structurally incapable of supporting two very common complex requirements. The first is "discovering the evidence isn't enough and another round is needed": synthesis, or some intermediate step, would need to be able to judge "there isn't enough evidence" and then issue another round of retrieval — but the article's executor is done the moment it fan-outs, with no feedback path to "assess whether it's enough, do another round if not." The second is sequential dependency — "look something up first, then look up something else based on the result." The article explicitly uses parallel execution, and parallelism's precondition is precisely that tools are independent of each other — if tool B's input depends on tool A's output, that simply cannot be expressed under a "parallel fan-out" model.

On the surface these look like two separate issues, but tracing them to the root, they're really the same thing: **the system lacks "state" and "multi-step reasoning."** The implicit assumption of a single-round architecture is that all the evidence a query needs can be fully determined right at the start — the moment the planner makes its decision. But the reality is often that "what I still need to look up" only becomes clear after seeing the first round's results — this is a fundamental issue of cognitive ordering, not a missed engineering detail.

Laying the two paradigms side by side in a table makes the difference clearer:

| | The article's architecture (RAG pipeline) | Architecture needed for iteration/sequencing (agentic loop) |
|---|---|---|
| Number of decisions | Once, fixed after that | Multiple, each round's result can trigger the next decision |
| Relationship between tools | Independent, can run in parallel | May have dependencies, needs sequencing |
| When it stops | Stops once the fixed flow completes | Dynamically decided by a judgment step: "is this enough?" |
| Essence | A process (pipeline) | An agent that decides its own next step |

Strictly speaking, what this article does isn't "agentic RAG" — it's "a traditional RAG pipeline that uses an LLM for dynamic routing." The Planner uses an LLM, but its intelligence stops at "which tools to use this time"; it doesn't extend to "was this enough, should we go another round." There's a distinction worth emphasizing here, one that's easy to conflate: **using an LLM to make a decision does not equal agentic.** The defining feature of "agentic" is a loop and state, not whether an LLM happens to be involved in the decision process.

None of this means the article's content isn't useful. What it offers isn't the answer to "how to do iteration" — it's the answer to "how to do each round well, inside an iterative loop." If you were to build a system that supports iteration and sequential dependencies, the shape would roughly look like this:

```
while there isn't enough information or there's a next step to query:
    agent decides what to query next, which tool to use    ← the article doesn't cover this
    execute retrieval                                       ← the article teaches how to do this well
    assess "was this enough, what to query next"           ← the article doesn't cover this
    merge into the accumulated evidence pool
synthesis reads the entire accumulated evidence pool to produce the answer  ← the article covers this (single-round version)
```

The outer while loop, and the reasoning behind "deciding the next step," belong to the domain of agentic system design, which the article never touches. But the technique for "doing a single round of retrieval well" inside that loop — data processing, multi-signal fusion ranking, planner tool selection within a single round — remains fully applicable and doesn't expire. The quality of the single-round architecture determines the quality of every iteration inside the loop; whether the loop exists at all determines whether the system can handle problems that need multi-step reasoning. These two layers are orthogonal to each other.

### Two questions to figure out which direction to strengthen

If you need to decide which direction to reinforce, there are two questions worth asking. First: at which layer is "not enough information" actually detected? If it's synthesis discovering insufficiency after reading the evidence, you need a self-critique or sufficiency-check step after synthesis that outputs "what's still missing" and feeds it back to the planner to trigger another round; if it's triggered by a user's follow-up question instead, that belongs to conversation management, not an iteration problem requiring a loop — a single-round pipeline re-running once per follow-up is enough. Second: is the sequential dependency "a limited number of fixed patterns," or does it "genuinely need an agent to plan on the fly"? If the patterns are limited (say, a fixed two-step flow of "look up a person, then look up that person's PRs"), you don't need a full agentic loop — you can write that sequence as a single composite tool with a fixed internal execution order, still appearing to the planner as one black-box tool. If the sequential dependency is open-ended, has no fixed pattern, and genuinely needs an agent to decide the next step on the fly, that's the case that truly needs an agentic loop — and at that point, the article's entire planner/executor/synthesis architecture can, at best, be demoted to a single sub-module handling "one round of execution" inside the agent loop.

## Looking back at my own system's pitfalls: retrieval and reasoning must be decoupled

The biggest value I got from reading this article wasn't any single technical detail listed above — it was an architectural problem I only saw clearly after holding the article up against my own system.

### The original system's problem: retrieval and reasoning were coupled

My original system used "domain/customer" as its axis of differentiation, with each domain bound to a fixed set of retrieval methods — say, a given domain always uses three fixed retrieval methods against three fixed databases, then merges the results. This design exposes two problems once it scales. First, even domains sharing the same type of data or questions can barely share retrieval methods, because the methods are hardwired to the domain axis. Second, adding a single new data type within one domain requires developing a brand-new retrieval method — the granularity of differentiation is bound at the domain level, with no way to dynamically adjust based on a single query's actual intent.

Tracing the root cause, both problems share the same underlying pathology: "retrieval and reasoning are coupled." The original fusion flow worked like this: each of the three retrieval legs calls its own corresponding reasoning method (say, SQL reasoning, or vision-and-text reasoning), each produces its own summary, and finally one LLM call merges the three summaries. In effect, every retrieval leg has a complete reasoning-and-summarization pipeline baked in — retrieval and reasoning are architecturally inseparable. This means it can't be shared across domains (the reasoning logic is welded onto retrieval), and it can't be replaced with a dynamic planner instead of domain binding either (because each leg isn't a pure retrieval primitive, but an entire, self-contained question-answering suite).

The direction of refactoring the article suggests is clear: decouple retrieval from reasoning. Retrieval tools should only emit raw evidence — no reasoning, no summarizing — with reasoning happening only once, in the single synthesis step at the very end of the pipeline. Drawn as a diagram, it looks roughly like this:

```
Original architecture:
  Retrieval A → Reasoning A(e.g. SQL) → Summary A ┐
  Retrieval B → Reasoning B(e.g. vision+text) → Summary B ┼─→ LLM merge → Final answer
  Retrieval C → Reasoning C                → Summary C ┘

The article's architecture:
  Retrieval A (read-only fetch) ┐
  Retrieval B (read-only fetch) ┼→ Fusion ranking (RRF, pure math) → rerank (1 small model call) → single synthesis → Answer
  Retrieval C (read-only fetch) ┘
```

### The concrete gains from decoupling

This shift brings several concrete benefits. The cross-domain sharing problem gets solved, because once decoupled, retrieval tools become clean, stateless primitives with no reasoning bound to them, and are inherently shareable across domains. The problem of needing to develop a new retrieval method for every new data type also gets solved: paired with the planner mechanism, adding a new data type only requires adding one retrieval tool and updating its capability description — the planner automatically learns to select it for the right queries, with no need to touch existing reasoning logic.

More fundamentally, it repairs the ability to reason across sources. In the original architecture's "each leg reasons and summarizes fully on its own" approach, no single LLM ever sees all the evidence at once — so if the correct answer requires cross-source reasoning (say, "a sentence from A plus a chart from B"), the original architecture is structurally incapable of that. The article's architecture, with its single synthesis step laying all the evidence out in the same context for one reasoning pass, inherently supports cross-source reasoning. Additionally, the original architecture's "summary of summaries" (each leg summarizes first, then a final merge summarizes again) stacks two layers of lossy compression, and downstream has no way to detect what detail was lost upstream; the article's architecture compresses only once, at the very end, keeping evidence in its original form up until that point, so error doesn't compound across two layers.

Of course, not all "reasoning before retrieval" should be eliminated. The lookup-versus-compute test mentioned earlier still applies here: if a certain kind of retrieval is fundamentally computation rather than lookup (like SQL generation needing on-the-spot reasoning to obtain data), that reasoning step should be kept — but hidden inside the retrieval tool, exposing only "the evidence it fetched" to the outside, not "a partial answer aimed at the user's question."

## Conclusion

This article demonstrates how "narrow-waist design" solves both write-side scalability and read-side retrieval quality simultaneously, in a heterogeneous enterprise-data setting — this principle recurs four times, across the data abstraction layer, the read-side fusion layer, the multi-tool orchestration layer, and the organizational scoping layer, making it the single mental model most worth internalizing.

Holding it up against my own existing system, the biggest payoff was two judgments the article never states directly. First, retrieval and reasoning must be decoupled: moving reasoning entirely out of the retrieval path, letting it happen only in the single synthesis step at the pipeline's end, is what simultaneously solves both "hard to share across domains" and "new data types require redundant development." Second, this entire planner-executor-synthesis architecture is fundamentally a single-round pipeline — it can make "one round of retrieval solid," but it can't handle problems like "evidence is insufficient and needs iteration" or "queries have sequential dependencies," which require state and multi-step reasoning. That's the territory of agentic RAG, which the article never touches at all.

One closing methodological note: the value of technical details isn't in copying them verbatim, but in testing the first principles behind them, one by one, against your own real-world scenarios — like the case of RRF failing in slide retrieval because its signal sources weren't orthogonal. This kind of comparative reading, more than simply understanding the article on its own terms, is what actually builds architectural judgment you can put to direct use.

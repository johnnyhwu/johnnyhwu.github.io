---
# weight: 1
title: "SAG: Multi-Hop RAG via Query-Time SQL, Not Offline Graphs"
date: 2026-08-19
lastmod: 2026-08-19
draft: false
description: "SAG skips the offline knowledge graph, storing events and entities in SQL, joined at query time -- beating HippoRAG 2 on multi-hop benchmarks like MuSiQue."
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

Multi-hop reasoning has always been the hardest part of getting a RAG system to work in production. Pure dense retrieval only looks at semantic similarity, and the reasoning chain routinely snaps halfway through. GraphRAG-style approaches build explicit associations, but building them means splitting text into triples offline, aligning entities, and computing global scores -- expensive to build, and a maintenance headache once data keeps flowing in.

**SAG (SQL-Retrieval Augmented Generation)** proposes a direct compromise: **don't build a graph offline at all. Turn each chunk into one semantically-complete "event" plus a set of entity tags, and write both into a standard SQL database. At query time, use SQL `JOIN`s to dynamically stitch together events that share an entity.** The graph only exists for the instant of a query, then it's discarded.

- [Paper (arXiv)](https://arxiv.org/abs/2606.15971v1)

Across nine Recall@K metrics on three multi-hop benchmarks -- HotpotQA, 2WikiMultiHop, and MuSiQue -- SAG takes first place on eight, reaching 80.0% Recall@5 on MuSiQue, the benchmark with the longest reasoning chains. But the interesting part of this paper isn't the numbers. SAG reframes something that used to be treated as an "algorithm problem" -- multi-hop retrieval -- as a **"database schema design problem"** instead, and the engineering dividends that reframing pays out (painless incremental writes, an auditable retrieval trace, and insensitivity to embedding quality) are worth more than the recall gains themselves.

{{< image src="figure1.png" alt="Process and performance comparison of three RAG paradigms: NaiveRAG, GraphRAG, and SAG, showing scalability, cost, speed, and precision tradeoffs" caption="Figure 1 — Process and performance comparison of three RAG paradigms. (Source: original paper)" >}}

## Two Existing Approaches, Two Different Kinds of Pain

### Vector Retrieval: No Logical Constraints, and It Breaks Chains

Traditional dense retrieval is, at its core, semantic similarity matching: chunk the text, embed it, return the Top-K at query time. Applied to multi-hop reasoning, it has three fundamental limits.

First, it can't establish explicit entity associations. Once a query involves a temporal constraint, a specific role, or a multi-step dependency, vector similarity can only find passages that "read similarly" -- it can't recover the explicit logical chain between entities.

Second, errors amplify along the reasoning chain. When an agent does sequential retrieval, if the first hop drifts even slightly because similarity wasn't quite high enough, every subsequent hop builds on that wrong foundation, and the whole path eventually breaks.

Third, and most damning: **the intermediate evidence that bridges a reasoning chain is often, both literally and semantically, nothing like the original question.** Ask "where did the founder of some company go to school," and the passage describing the founder's education may never mention the company's name at all. Pure vector distance filters out exactly this kind of critical stepping-stone at the very first hop.

### GraphRAG: Structure, at a Real Cost

To add structure back in, methods like GraphRAG and HippoRAG use an LLM offline to extract triples and build a global knowledge graph. The problem is that this path has a real cost:

- **Semantic fragmentation**: a knowledge graph restricts relations to `(subject, relation, object)` binary tuples, but real-world events are mostly N-ary -- involving multiple parties, times, and places. Forcing them into a handful of independent triples destroys the original context.
- **Incremental updates are an engineering disaster**: real systems ingest data continuously. Keeping a graph correct as new documents arrive often means re-running entity extraction, entity alignment, and relation normalization, or even recomputing global node weights (e.g. PageRank). That cost makes real-time incremental updates nearly infeasible.
- **Online/offline disconnect**: the paper points out an ironic pattern -- the elaborate graph structure built at great offline expense often degenerates, at query time, right back into flat vector similarity matching over "graph nodes" or "community summaries." The structure never gets to do its job.
- **Score decay and noise amplification**: methods like HippoRAG propagate scores over the graph with Personalized PageRank. As hop count grows, the damping factor crushes the scores of distant target nodes so deep answers can't rank highly, while high-degree hub nodes in the graph spread the signal toward irrelevant places, actually raising noise.

## SAG's Design Philosophy: Let Every Component Do What It's Best At

SAG's core idea isn't a stronger model -- it's **reassigning responsibilities across the retrieval pipeline**. Three components, each with a hard boundary:

| Component | Responsible for | Why it's the right fit |
|---|---|---|
| SQL database | Deterministic association (filtering & joining) | It doesn't understand semantics, but "is A equal to B" is a millisecond-level, 100%-certain comparison that doesn't decay when chained and naturally supports concurrency and append-only writes |
| Vector database | Fuzzy semantic expansion | Purpose-built for aliases, synonyms, typos, and paraphrasing -- the fault-tolerant safety net for entities and events |
| LLM | High-value joint judgment | Used only to extract events and entities offline, and to do joint assessment over an already-compressed candidate set online |

The key trade-off here: **vector retrieval is not used for multi-hop reasoning, and the LLM never walks a graph.** Multi-hop reasoning is handed to SQL, and the LLM only appears once the candidate set has already shrunk to under 100 -- which keeps the whole system's token consumption and API cost low.

### What Is a "Latent Hyperedge"

In classical graph theory, an edge connects exactly two nodes. What SAG borrows is the **hyperedge** from hypergraph theory -- an edge that can connect any number of nodes at once.

In SAG, one chunk maps to one semantically-complete event `e`, plus a set of entities bound to it. **That "event ↔ entity set" binding is itself a hyperedge.**

The word "latent" is the important part. At index-build time, the system never computes global connections between entities, and never draws any explicit graph. These hyperedges simply lie dormant in SQL, in the form of a many-to-many "event-entity" table. Only when a user asks a question, and the system issues a SQL `JOIN`, do events sharing an entity get stitched together in memory into a local hypergraph -- which is then released once the query is answered.

In short: **a hyperedge is just a database table with no lines drawn on it, materialized only for the instant of a query.** The overhead of maintaining a global static graph never exists at all.

### Why a 4-Hop Reasoning Chain Only Needs 1 Hop of Retrieval

Some MuSiQue questions require 4 hops on a binary graph to reach the answer, yet SAG achieves leading recall in practice using only `H=1` (one hop of expansion). This seemingly unreasonable gap comes down to information density.

In a traditional graph, nodes are split extremely fine, so a single hop can only cross a very short logical distance. But one SAG event is a sentence that preserves full context -- **a single event already compresses multiple entities internally**. So when a query hits its first seed event, the time, place, and people already embedded inside it have effectively covered the first hop or two already; using those entities as the next stepping stone for a SQL `JOIN` pulls back another event that has, again, already compressed the next stretch of the chain internally.

The information coverage of one hop of SQL expansion can therefore rival three or four hops on a traditional graph -- and it fundamentally skips the error accumulation and score decay that come with multi-hop propagation.

## The Offline Phase: Turning Documents into a Joinable Index

{{< image src="figure2.png" alt="SAG's overall architecture, with the offline chunk-to-event transformation and triple-index write in the top half, and the online seed recall, query-time expansion, and candidate selection in the bottom half" caption="Figure 2 — SAG's overall architecture. The top half is offline ingestion, the bottom half is online retrieval. (Source: original paper)" >}}

The offline phase is entirely batch processing, and documents are independent of each other, so writes can be highly concurrent.

### One-Chunk-to-One-Event

After a document is split into chunks, a lightweight LLM (the paper uses Qwen3.6-Flash) generates two things in parallel: one condensed but not fragmented event narrative, and a set of entity tags for indexing (covering 11 preset types including time, person, organization, product, and more).

Concretely, it looks like this:

```
Input Chunk (C001):
  "In 2014, Facebook announced it would acquire the popular messaging
   app WhatsApp for a staggering $19 billion. The deal was driven
   personally by Mark Zuckerberg. WhatsApp co-founder Jan Koum
   subsequently joined Facebook's board of directors."

LLM-generated Event (e1):
  "Facebook acquired WhatsApp for $19 billion in 2014, driven by
   Mark Zuckerberg; WhatsApp co-founder Jan Koum then joined
   Facebook's board of directors."

LLM-generated Entities:
  ['Facebook', '2014', 'WhatsApp', 'Mark Zuckerberg', 'Jan Koum']
```

Notice that the event sentence binds five entities at once -- this is exactly the "a single hyperedge already compresses multiple entities internally" point from above.

### Deliberately Skipping Entity Alignment

The heaviest offline burden for a traditional knowledge graph is entity alignment and disambiguation: deciding whether "Mark Zuckerberg," "Zuckerberg," and "馬克·祖克柏" all refer to the same person. When alignment fails, the graph breaks.

SAG's choice is pragmatic -- **it does zero global entity alignment offline**, doing only extremely lightweight literal cleanup like whitespace trimming and case normalization.

It can afford to do this because, in SAG, the event carries the semantic value; entities are just "connection hints." The pressure of alias resolution is deferred to query time, handed off to fuzzy vector matching. This trade-off pays off big: offline processing is entirely free of any global-graph lock, so writes are independent, high-throughput, and genuinely painless append-only operations.

### Three Indices, Triple Redundancy

Extracted data is written synchronously into three complementary stores.

The **SQL relational database** stores the structure and hyperedge relationships, centered on a many-to-many `Event_Entity_Mapping` table:

| Event_ID | Chunk_ID | Entity_Text | Entity_Type |
| :--- | :--- | :--- | :--- |
| e1 | C001 | Facebook | Organization |
| e1 | C001 | 2014 | Time |
| e1 | C001 | WhatsApp | Product |
| e1 | C001 | Mark Zuckerberg | Person |
| e1 | C001 | Jan Koum | Person |

The **vector database** stores two kinds of vectors: event vectors (for direct semantic matching against a question at query time) and entity vectors (for fuzzy alias expansion at query time).

The **full-text search engine** (the paper uses Elasticsearch) builds an inverted index. Where a forward index maps "document → which words it contains," an inverted index does the reverse: "word → which documents contain it." Its role here is a fallback for exact string matching: production RAG systems routinely stumble on rare proper nouns, product model numbers, and part numbers -- search for "chip model M3-Max" and vector retrieval may not recover it, but an inverted index locates it in milliseconds. Note that the three online steps in the next section don't actually use it at all; it's a fallback channel reserved for real-world deployment, not part of the main retrieval flow.

## The Online Phase: Dual-Track Seeding, SQL Expansion, LLM Selection

Online, SAG never touches a global graph -- three steps and it has an answer.

### Step 1: Dual-Track Seed Retrieval

Seed retrieval needs to pin down the first thread of reasoning precisely and broadly at the same time, so SAG runs two paths in parallel:

- **Path A (entity-guided SQL retrieval)**: a lightweight LLM first extracts entities from the question, looks them up in the entity vector index (threshold 0.9+) to expand an alias set -- e.g. `{WhatsApp}` expands to `{WhatsApp, whatsapp messenger}` -- then uses SQL `OR` logic to precisely pull every event linked to any of those entities.
- **Path B (pure event vector retrieval)**: in parallel, the question itself is embedded and matched directly against the event vector store, pulling back events above similarity threshold τ (default 0.4).

The two paths are unioned and deduplicated. Path B exists purely as a safety net, in case Path A's entity extraction misses something.

After merging, there's one master valve: a **seed budget `K_seed = 50`**. Anything over 50 is ranked by vector similarity and only the top 50 pass to the next step. Think of this as a reservoir's spillway -- however much water arrives upstream, the gate opening is fixed, which keeps downstream processing under control.

### Step 2: Query-Time Dynamic Expansion

With seed events in hand, the next step is to hop outward for indirect evidence. SAG uses a "reverse-collect entities, then forward-recover events" batched SQL pattern:

```
[Seed Events] --(SQL reverse lookup)--> [Entity Frontier] --(SQL JOIN)--> [Expanded Events]
```

Three actions make up the flow:

1. **Collect the entity frontier**: pull out every entity bound to a seed event to form an entity frontier set.
2. **Global pruning (budget 50)**: if a high-frequency, generic entity like "2014" leaks into the frontier, the next step pulls back a flood of irrelevant events. So the system enforces a **pruning budget of 50** -- when the frontier exceeds 50 entities, it computes each one's vector similarity to the query and forcibly keeps only the top 50. This same "50" resurfaces later when discussing limitations -- it's the direct cause of SAG's loss on 2Wiki.
3. **Batched SQL expansion**: run one batched `WHERE Entity_Text IN (...)` `JOIN` over these 50 selected entities, pulling back every newly-associated event, and merge it with the seed events into a candidate pool.

The network that this batch of events forms in the moment is exactly that temporary local hypergraph.

### Step 3: Coarse Filtering Plus Dual-Track LLM Selection

The candidate pool can hold several hundred events; this step needs to refine it into the final 10 chunks handed to the generation module.

First, coarse vector filtering: compute every candidate event's similarity to the query and take the top 100. This is an engineering compromise -- a cheap way to shrink what the LLM has to look at down to an affordable amount.

Then two paths run in parallel for final selection:

- **Path A (LLM structured selection)**: feed all 100 events into a reasoning LLM together, and have it perform a **joint assessment** -- holistically considering which events, in combination, form a multi-hop reasoning chain -- picking out the 5 most critical ones and mapping them back to their original chunks. This differs fundamentally from a cheap pointwise reranker: pointwise scoring rates each event one at a time and can't see complementary relationships between events; joint assessment can.
- **Path B (direct semantic retrieval)**: embed the question and pull the 5 highest-similarity chunks directly from the raw chunk vector store.

The two paths are unioned and deduplicated to output the final Top 10. The point of this dual-track design is complementarity: the structural path recalls the logical evidence that "needs to be pieced together across documents and reads nothing like the question," while the semantic path recalls the evidence that's "directly, obviously relevant to the question."

## Experimental Results: Where It Wins, and Where It Slips

### Main Results: The Harder the Dataset, the Bigger the Lead

{{< image src="table1.png" alt="Table comparing Recall@2/5 of SAG against Simple Baselines, Large Embedding Models, and Graph-based Methods across three multi-hop datasets" caption="Table 1 — Recall@2/5 of SAG against baselines under a unified underlying configuration (BGE-Large-EN-v1.5 + Qwen3.6-Flash). (Source: original paper)" >}}

Across the three datasets, the comparison that matters most is against HippoRAG 2 (both use the same BGE-Large embedding):

| Dataset | Reasoning difficulty | SAG (R@2/R@5) | HippoRAG 2 (R@2/R@5) |
|---|---|---|---|
| MuSiQue | Hardest -- 4 hops, counterfactually filtered | **64.1 / 80.0** | 49.5 / 65.1 |
| HotpotQA | 2 hops -- bridge and comparison questions | **91.6 / 96.5** | 78.4 / 94.4 |
| 2WikiMultiHopQA | Long entity chains, rare bridges | **82.3** / 88.0 | 76.6 / **90.4** |

On MuSiQue, SAG leads by nearly 15 percentage points, and this is the group that most stress-tests linking ability -- it has a 4-step logical chain and is counterfactually filtered to prevent single-hop semantic cheating. That supports the paper's mechanistic claim: using SQL for deterministic local hyperedge linking preserves deep evidence better than propagating scores with PageRank over a global graph.

HotpotQA only has 2 hops, so the decay effect from graph propagation is already weak, which is why the Recall@5 gap narrows to 2.1 points. But SAG still leads by 13.2 points on Recall@2 -- it's more consistent at ranking the most critical evidence first.

**2Wiki is the one column SAG loses, and it loses in an interesting way.** SAG leads on Recall@2 (82.3 vs. 76.6), but trails on Recall@5 (88.0 vs. 90.4). The cause is that same fixed pruning budget of 50: 2Wiki contains extremely long, extremely low-frequency entity chains, and when a bridging entity is both rare in the corpus and has low semantic relevance to the original question, it's easily crowded out of the 50 slots during expansion by high-frequency generic entities, breaking the chain. HippoRAG's global PageRank, by contrast, can reach these low-frequency nodes precisely because it propagates over the whole graph.

### Ablation 1: What Is Event Structure Actually Worth?

{{< image src="table2.png" alt="Table comparing event-level indexing versus triple-decomposition indexing on Recall@1/2/5/10 on MuSiQue" caption="Table 2 — Ablation comparing event-level indexing vs. triple-decomposition indexing (MuSiQue). (Source: original paper)" >}}

The authors forced SAG's events apart into triples and re-ran it; Recall@5 dropped from 80.0% to 77.1%.

That number needs to be read on two levels. First: **even decomposed into triples, 77.1% still handily beats HippoRAG 2's 65.1%** -- meaning SAG's SQL retrieval pipeline has a systemic advantage on its own, independent of whether hyperedges are used. Second: keeping the full event intact adds another 2.9 points, because one event records an N-ary relation and doesn't need to traverse multiple `JOIN`s the way triples do, avoiding the pruning loss incurred at every extra hop.

In other words, the paper's headline idea is the hyperedge, but most of the performance actually comes from the pipeline design.

### Ablation 2: What Does Dynamic Expansion Actually Capture?

{{< image src="table3.png" alt="Table comparing recall with query-time expansion enabled (H=1) versus disabled (H=0) on MuSiQue" caption="Table 3 — Ablation on expansion hop count in dynamic hyperedge construction (MuSiQue). (Source: original paper)" >}}

This is, in my opinion, the single most striking result in the whole paper:

| Setting | Recall@1 | Recall@5 |
|---|---|---|
| No expansion (H=0) | 35.7 | 69.4 |
| With expansion (H=1, default) | 36.2 | **80.0** |

The expansion mechanism produces **essentially no gain in Recall@1** (35.7 → 36.2, basically unchanged), yet it boosts Recall@5 by 10.6 points.

That tells you expansion isn't "ranking the seed events you already found better" -- it's rescuing the case that matters most: it recovers exactly the intermediate evidence that's semantically unrelated to the question, unreachable by vector retrieval alone, but critical to the reasoning chain. This is the quantified answer to the earlier pain point about "bridge evidence that reads nothing like the original question."

### Dependence on Embedding Quality

{{< image src="table4.png" alt="Table comparing SAG and HippoRAG 2 retrieval results on MuSiQue when switched to the NV-Embed-v2 embedding model" caption="Table 4 — SAG vs. HippoRAG 2 on MuSiQue after switching to NV-Embed-v2. (Source: original paper)" >}}

Switching the embedding from BGE-Large to the stronger NV-Embed-v2:

| System | Original Recall@5 | After switch | Change |
|---|---|---|---|
| HippoRAG 2 | 65.1 | 74.6 | +9.5 |
| SAG | 80.0 | 81.7 | +1.7 |

The difference is telling. HippoRAG's multi-hop performance depends heavily on vector scoring -- a node's initial score on the graph comes directly from vector similarity -- so a weaker model lets errors amplify along the propagation path. SAG's structural gains, on the other hand, mostly come from exact string-matching SQL `JOIN`s, which are largely independent of embedding quality.

The practical implication: **with a weaker, cheaper embedding model, SAG holds onto its multi-hop retrieval quality.** For a cost-sensitive production environment, that matters more than a 15-point recall lead.

## Where This Architecture Bites You

The paper is fairly honest about its own limitations -- here are three that would actually show up in practice.

**The pruning budget drops rare entities.** This is the direct cause of the loss on 2Wiki. The current pruning strategy ranks by vector similarity to the query, but the critical bridging entities in deep reasoning chains often combine "rare in the corpus" with "low semantic relevance to the original question" -- exactly the profile most likely to get crowded out of the 50-slot budget. A possible fix is introducing an IDF-like (inverse document frequency) weighting, or stratifying entities by frequency and giving low-frequency entities their own dedicated expansion allowance.

**Skipping entity alignment is a double-edged sword.** Not aligning offline buys lock-free, high-throughput writes, but if the same entity is written differently across chunks ("Meta" vs. "Facebook," "Zuckerberg" vs. "祖克柏") and those spellings aren't close enough in vector space to clear the 0.9 threshold, SQL treats them as two completely unrelated index points, artificially lowering cross-document link density. This is architecturally similar to the trade-off graph-based memory systems like [Mem0](../mem0/)'s graph variant face when extracting entities and relations from conversations -- SAG's compromise would be a lightweight entity-alias table that aggregates slowly in the background, without breaking offline independence.

**Currently append-only only, no support for updates.** SAG is designed for incremental append to a read-only document store, but an agent's long-term memory changes: user preferences shift, a task moves from "in progress" to "done," historical facts get corrected. When the database ends up holding conflicting old and new events, the current index has no native mechanism to determine which one is actually valid now. Moving in this direction would need the schema to add timestamps, validity flags, and event dependency chains, so the retrieval path can automatically filter out superseded information.

## Conclusion

The most valuable takeaway from SAG isn't the recall numbers -- it's the shift in thinking it demonstrates: **robust multi-hop reasoning at retrieval time doesn't require building an expensive, fragile, hard-to-maintain global knowledge graph offline.** Storing knowledge as a relational table of "events + entity tags," deferring graph materialization to query time, and replacing graph traversal with SQL `JOIN`s gets you there just as well -- and does it better.

For engineers, the core insight is a reassignment of responsibility. It doesn't ask the LLM to shoulder expensive graph traversal, and it doesn't ask vector search to guess at strict logical relationships -- it hands deterministic association to the SQL engine, a piece of technology that's been running and optimized for decades. In return you get low API cost, incremental writes that actually work, and a retrieval trace that's auditable at every step because it can be reproduced with a SQL query -- and that last point matters for online debugging almost as much as recall does.

The costs are equally clear: a fixed pruning budget drops long-tail rare entities, skipping alias merging dilutes cross-document link density, and the system currently can't handle knowledge updates or invalidation. These are the bill you pay for system simplicity and write throughput -- and knowing what's on that bill is how you decide whether this architecture actually fits your use case.

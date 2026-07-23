---
# weight: 1
title: "Adaptive Chunking: A Smarter, Per-Document Way to Split Text for RAG"
date: 2026-07-22
lastmod: 2026-07-23
draft: false
description: "One-size-fits-all text splitting quietly wrecks RAG pipelines. See how Adaptive Chunking scores candidate splits with five metrics and keeps the best per document."
featuredImage: "featured-image.png"

tags: ["Large Language Model", "Retrieval-Augmented Generation", "Evaluation"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## Introduction

Anyone who has built a RAG (Retrieval-Augmented Generation) system has probably had this experience: you spend a lot of time and money upgrading to a pricier embedding model, tweaking prompts, or even bolting on a reranker — and the system still gives wrong answers half the time.

The problem is often not in retrieval or generation at all. It's in the very first, most easily overlooked step: splitting a document into chunks before it ever reaches the vector database.

That is exactly what this paper is about. If document chunking is done badly, nothing downstream can fix it. A bad split means the knowledge granularity stored in the vector database is wrong from the start — the retriever can't pull a complete, precise context, and no matter how strong the downstream LLM is, it's still "garbage in, garbage out."

### Three old chunking problems that were never really solved

The authors lay out three pain points in current chunking practice that remain unresolved.

The first is the **context-preservation dilemma**. Traditional splitting relies on fixed character counts or hard punctuation cuts, which can easily slice a logically coherent passage in half — or worse, separate a pronoun ("it") from the entity it refers to, breaking the semantic link between them.

The second is the myth of "one method fits everything." For convenience, most engineering pipelines apply a single splitting strategy to the entire corpus — for example, LangChain's Recursive Splitter capped at 1,000 tokens, applied uniformly. But real-world knowledge bases are highly heterogeneous — tightly formatted legal contracts, technical manuals stuffed with tables, and purely narrative academic papers all mixed together, the same kind of text-and-table heterogeneity that [Mixture-of-RAG](../mixture-of-rag/) tackles on the retrieval side. No single splitting method handles every structure well.

The third problem is more fundamental: the industry lacks an independent ruler for measuring whether a chunk was split well. Developers typically have to run the entire RAG pipeline end to end and judge chunking quality by whether the final answer is correct — but that conflates retriever noise and generation-model noise with the effect of chunking itself, making it impossible to isolate chunking's actual impact.

The **Adaptive Chunking** framework this paper proposes centers on replacing "static, blind splitting" with "dynamic evaluation and selection": instead of chasing one universal splitting method, it runs several splitting methods on the same document in parallel.

It then scores each result with a set of "intrinsic evaluation metrics" that don't require actually running RAG at all, and automatically picks the highest-scoring version to write to the database — in short, letting the system "teach each document according to its nature."

{{< admonition abstract "Key Takeaways (TL;DR)" >}}
1. **The Adaptive Chunking framework**: instead of hunting for one "best" splitting method, it runs several splitting algorithms on every document in parallel, scores each with five intrinsic metrics that don't require running RAG at all, and automatically keeps the highest-scoring version for the vector database.
2. **Two new algorithms**: the LLM-guided Regex Splitter (the LLM only generates a regex rule; Python does the actual splitting) and the Split-then-Merge Recursive Splitter (shred everything first, then greedily merge with structure-aware backtracking overlap) — both backed by mandatory "oversized re-split" and "tiny-chunk merge" post-processing.
3. **Five intrinsic metrics** — RC, ICC, DCC, BI, SC — respectively check pronoun-reference integrity, intra-chunk topical purity, contextual coherence, structural integrity, and size compliance; an equal-weight average of the five decides which splitting method wins.
4. **Real-world payoff**: across 33 cross-domain document corpora, no single method dominates; downstream Retrieval Completeness improves by 9.6 percentage points and correctly-answered questions rise 32.7% in relative terms — evidence that chunking quality has an "amplification" effect on overall RAG performance.
{{< /admonition >}}

## Pre-processing: turning the PDF into clean Markdown first

Before any splitting happens, the authors add a pre-processing layer: converting the PDF into more structured Markdown rather than handing raw plain text to the splitting algorithms. This step matters because plain text flattens all the structural cues — tables, headings, paragraph boundaries — leaving the splitting algorithm groping in the dark.

This custom conversion pipeline hides a few engineering details:

- **Splitting oversized tables while preserving headers**: prevents later rows from losing their column mapping when a table is cut mid-way.
- **Filtering and grouping headers/footers**: reduces irrelevant noise that would otherwise leak into retrieval later.
- **Binding headings, footnotes, and their corresponding body text into indivisible blocks**: prevents splitting from tearing apart content that belongs together.

These seemingly minor pre-processing touches are actually the foundation that lets every downstream splitting algorithm be "structure-aware" at all.

## The chunking toolbox: two newly designed algorithms

To keep the pool of candidate splitting methods diverse, the authors add two new algorithms — beyond the common baselines (page-based, sentence-based) — that balance "structure awareness" with "execution efficiency."

### Algorithm 1: LLM-guided Regex Splitter

For documents with strongly regular structure, such as contracts and regulations, traditional recursive character-count splitting easily breaks the integrity of a clause; but asking an LLM to split the entire document directly blows up compute time and API cost.

This algorithm takes a middle path: it demotes the LLM to a "rule generator." The system only lets the LLM read the first portion of the document (roughly 8,000 tokens) to infer the regular-expression (regex) delimiter best suited to that document. The rest of the full text is then handed off to Python's native `re.split()`, which finishes splitting in milliseconds.

To get the LLM to reliably output a usable regex, the prompt design includes several safeguards:

- **Forced output format**: only a single regex compatible with Python's `re` engine is allowed, wrapped in `<regex>...</regex>` so the program can parse it directly.
- **Structure-protection guidelines**: explicitly instructs the model not to split tables wrapped in `<Table>` tags — dovetailing perfectly with the structured text built in the pre-processing stage.
- **Few-shot examples**: demonstrates "input text → expected regex" pairs to stabilize the model's reasoning.

{{< image src="figure3.png" alt="LLM-assisted regex splitting pipeline and prompt design: the left side shows the flow from sampling text to generating a prompt to applying the regex split, and the right side shows the actual prompt content" caption="Figure 3: LLM Regex splitter pipeline. The system only shows the LLM a small text sample to generate a rule, then uses the native regex engine to split the full document — balancing the LLM's understanding with the execution speed of native code. (Source: original paper, Figure 3)" >}}

### Algorithm 2: Split-then-Merge Recursive Splitter

This algorithm is a deep refinement of the industry-standard LangChain `RecursiveCharacterTextSplitter`, mainly addressing the old problems traditional recursive splitting has with boundary control and overlap.

Traditional recursive splitting follows **top-down** logic: whenever a block exceeds the upper limit (say, 1,000 tokens), it looks for a higher-priority delimiter (like a double line break) to split on; once a resulting piece is at or below the limit, splitting stops and it becomes the final chunk.

The fatal flaw in this logic is the complete absence of a lower bound — if a resulting piece is only 50 tokens, the algorithm accepts it as-is, producing a pile of "tiny fragments" that lack context and waste retrieval space.

This paper's approach flips the order, using a **bottom-up** two-stage strategy:

- **Stage one, "shred everything"**: following a pre-ranked list of Markdown delimiters, recursively split everything down until every piece is smaller than the target size S — the text becomes a pile of tiny structural units.
- **Stage two, "greedy merge"**: sweep through these tiny pieces top to bottom, merging as long as the accumulated token count doesn't exceed the upper bound S, continuing until it approaches the limit.

This ordering nearly eliminates meaningless tiny fragments entirely.

The overlap mechanism was also reworked. Traditional approaches mostly truncate passively by character count, which easily chops sentences apart.

During merging, whenever adding the next piece would exceed the upper bound, this algorithm starts a new chunk and triggers a "backtracking" mechanism — the new chunk copies the "complete structural fragment" (such as a full sentence) from the end of the previous chunk as its opening, so overlap is measured in semantic units rather than raw character counts.

{{< image src="figure5.png" alt="Two-stage split-then-merge flow diagram: text is first recursively split down to extremely fine pieces by delimiter priority, then merged top-down; when a merge would exceed the limit, backtracking brings in the complete trailing fragment of the previous chunk as overlap" caption="Figure 5: Split-then-merge recursive splitter pipeline. Shred first, merge second, and backtrack for overlap when needed — this two-stage design solves the fragmentation problem of traditional top-down recursion. (Source: original paper, Figure 5)" >}}

{{< image src="figure4.png" alt="A high-to-low priority list of delimiters, including the regular expressions corresponding to each level of Markdown heading" caption="Figure 4: The delimiter priority list used during splitting. The algorithm prioritizes Markdown headings at each level (e.g., the regex rule for a level-1 heading), ensuring content under the same heading gets grouped together preferentially during the merge stage. (Source: original paper, Figure 4)" >}}

Here's how the two recursive splitting approaches compare:

| Comparison | Traditional Recursive Splitter (native LangChain) | Split-then-Merge Recursive (this paper's refinement) |
| --- | --- | --- |
| Direction | Top-down; stops once below the upper limit | Bottom-up; shreds to the extreme first, then greedily merges up to the limit |
| Fragment control | Weak — produces many 0–50 token throwaway fragments | Strong — the merge mechanism greatly improves space utilization |
| Overlap mechanism | Passive character-count truncation, easily breaks sentences | Actively backtracks by complete structural fragment |
| Structure awareness | Weak — relies only on native line breaks and whitespace | Strong — deeply integrates Markdown heading and list regex rules |
| Size compliance | Unstable, high variance | High — strong Size Compliance (SC) metric performance |

## Quality assurance: a mandatory post-processing safety net

No matter how carefully the splitting algorithms are designed, documents with especially unusual formatting will inevitably produce "outlier chunks" that don't meet spec. These extreme values don't just distort the embedding's semantic representation — they can become noise that pollutes retrieval results. So after all splitting algorithms finish running, the authors attach a mandatory two-stage quality-control mechanism that only touches extreme values, leaving normally sized chunks untouched.

The first line of defense is **oversized re-splitting**. If a splitting result (say, when the LLM Regex misjudges) produces a chunk far exceeding the upper limit (the paper sets 1,100 tokens), it often mixes several unrelated topics together — technical specs bundled with a disclaimer is a common case.

When an embedding model is forced to compress these sprawling concepts into a single vector, the key semantic signal gets severely diluted, making it hard to match a user's specific query at retrieval time.

The system's fix: once a chunk over 1,100 tokens is detected, it's cut apart using the delimiter priority rules mentioned earlier (paragraph, then line break, then period, in that order) to pull it back into a reasonable range.

The second line of defense is **tiny-chunk merging**. During splitting, broken tables, isolated numbers, and orphan headings easily produce micro-fragments below a few dozen tokens. These fragments have no real content, but if they happen to contain a user's query keywords (especially with lexical-matching algorithms like BM25), they can steal a precious Top-k retrieval slot, feeding the LLM meaningless background text that leads to hallucination or an outright refusal to answer.

The system sets a lower bound (100 tokens in the paper); when it detects an undersized fragment, it tries merging it with an adjacent passage before or after — but first checks that the merged length won't exceed a relaxed upper bound (1,150 tokens) before actually executing the merge, to avoid creating a different kind of oversized chunk.

These two defenses look simple and blunt, but they're solidly effective. After post-processing, algorithms whose Size Compliance (SC) had been extremely unstable (like raw semantic splitters or LLM Regex) jump to near-perfect scores.

Extreme values are nearly wiped out entirely: before post-processing, several traditional baseline methods produced throwaway fragments of just 0 to 4 tokens; after post-processing, every method's minimum length was stably pulled up into a healthy range of 69 to 104 tokens.

{{< image src="table2.png" alt="A table comparing chunk-size statistics and runtime across chunking methods" caption="Table 2: Chunk-size and runtime statistics across chunking methods. Methods marked with a dagger (†) are unprocessed traditional baselines — notice their minimum-length columns frequently show 0-to-4-token meaningless fragments. (Source: original paper, Table 2)" >}}

The concrete magnitude of the improvement: before post-processing, LLM Regex and the semantic splitter had Size Compliance rates of only around 58% and 48% respectively; after both "oversized re-split" and "tiny-chunk merge" are applied, both rates jump above 99%.

## The core innovation: five metrics that score chunks without ever running RAG

Traditionally, evaluating whether a chunking method is good requires writing chunks to the database and running a full end-to-end test through the retriever and LLM. This kind of "extrinsic evaluation" is not only computationally expensive, it's also hard to tell whether a poor result comes from bad chunking, embedding drift, or the LLM's own limited comprehension — the errors from all three stages get tangled together.

This paper's solution is "intrinsic evaluation": skip retrieval and generation entirely, and score the split chunks directly using lightweight specialized NLP models, vector cosine similarity, and layout structure boundaries, across five dimensions, each scored between 0 and 1.

### RC (References Completeness)

This metric targets "failed pronoun resolution" — a classic RAG killer. If an entity (say, "Tesla") and the pronoun that refers to it ("it") get split into different chunks, and retrieval only pulls the chunk with the pronoun, the LLM ends up unable to answer because the information is incomplete.

The calculation works by first running the coreference-resolution model **Maverick** (ACL 2024) over the full text to find every entity–pronoun pair, recording the character-position range each pair spans in the original text.

Then it checks whether any split point falls inside the range of a given pair — if a single cut lands inside the range, that pair counts as "broken"; only if no cut falls inside is it considered fully preserved. RC is the proportion of pairs preserved intact.

{{< admonition tip "Worked example: how one cut can 'break' a pronoun" >}}
A concrete example makes this easier to grasp. Suppose the input text is:

```
"Elon Musk founded SpaceX. He wants to land on Mars with his rockets."
```

The Maverick model would output coreference-cluster data roughly like this:

```json
[
  {
    "cluster_id": 0,
    "entity": "Elon Musk",
    "mentions": [
      {"start": 0, "end": 9, "text": "Elon Musk", "type": "PROPER"},
      {"start": 26, "end": 28, "text": "He", "type": "PRONOUN"},
      {"start": 54, "end": 57, "text": "his", "type": "PRONOUN"}
    ]
  }
]
```

The system extracts two key ranges from this data: "Elon Musk → He" spans character positions 0 to 28, and "Elon Musk → his" spans 0 to 57.

If the splitter happens to cut right after "founded" (around character position 15), that cut lands inside both ranges — RC would mark both pairs as "broken." A cut that looks perfectly unremarkable in position actually damages two pronoun references at once.
{{< /admonition >}}

### ICC (Intrachunk Cohesion)

This metric checks whether a single chunk has "gone off-topic." It splits a chunk into several sentences, computes each sentence's embedding vector as well as an overall vector for the whole chunk (using Jina AI v3 in the paper).

It then computes the average cosine similarity between each sentence and the overall vector: the higher the similarity, the more concentrated the chunk's sentences are on a single topic, and the higher the ICC score.

### DCC (Document Contextual Coherence)

DCC pulls in the opposite direction from ICC: it ensures a chunk doesn't become an island cut off from its surrounding context.

It opens a sliding window of up to 3,000 tokens over the full text, spanning several neighboring chunks, computes an overall vector for the window, then checks how close each chunk inside the window is to that broader-context vector. A higher score means the chunk retains a stronger connection to its surrounding context.

### BI (Block Integrity)

BI protects "natural structures" — tables, captions, paragraphs — from being broken by a hard cut. The system records the start and end character positions of every table or paragraph in advance as "protected zones," then checks whether any cut falls inside a zone's interior (allowing a 5-character tolerance to exclude line-break noise).

As long as no cut lands inside, that block counts as intact; BI is the average of "intact or not" across all blocks. A BI of 1 means every table and paragraph stayed 100% intact after splitting.

### SC (Size Compliance)

The most intuitive metric: the proportion of chunks whose length falls within the 100-to-1,100 token range, directly reflecting how many chunks are neither too large nor too small.

## Dynamic decision-making: how the system picks a splitting method for each document

With the candidate algorithms and scoring metrics in place, the system enters its final integration and decision stage: for every input document, it automatically runs the full pipeline of "parallel splitting → five-dimensional scoring → weighted selection → write to vector store."

Concretely, that breaks into four steps:

1. **Parallel candidate generation**: the system simultaneously processes the same document with several splitting methods of different characteristics (each already carrying the post-processing quality control described above). The paper's candidate pool includes post-processed page splitting, recursive splitting (s=1100), recursive splitting (s=600), and LLM Regex (using GPT-5).
2. **Five-dimensional scoring**: each of the four resulting sets is scored on RC, ICC, DCC, BI, and SC.
3. **Weighted selection**: to keep the framework general-purpose and avoid overfitting to any particular dataset, the authors use the simplest, most straightforward approach — an equal-weight arithmetic mean — as the final score, with each of the five metrics contributing one-fifth.
4. **Dynamic write**: the system compares the four methods' final scores and keeps only the highest-scoring set for embedding and writing to the vector database; everything else is discarded.

Running this mechanism across 33 real-world, cross-domain document corpora directly confirms that a single strategy was never going to work.

{{< image src="table4.png" alt="A table showing the selection distribution across the four candidate chunking methods across the whole document corpus" caption="Table 4: Selection distribution of the Adaptive framework across a heterogeneous document corpus. Page splitting was selected 48% of the time, recursive splitting (s=1100) 42%, and LLM Regex plus the small-size recursive splitter accounted for the remaining 9% combined (rounding brings the total slightly below 100%). No single splitting method dominates every document type — this distribution is itself the most direct rebuttal to the idea of a single 'best' splitting method. (Source: original paper, Table 4)" >}}

There's an interesting detail here: taken on its own, recursive splitting (s=1100) actually has the highest average intrinsic score of any method — yet in practice, page splitting still wins on nearly half of all documents.

This shows that "best on average" and "best for every specific document" are two completely different things — which is exactly the point of the Adaptive framework, in the same spirit as [Adaptive-k](../adaptive-k/)'s move away from a single fixed retrieval size: not to find one globally optimal solution, but to match every document (or query) with whatever suits its own structure.

Of course, this mechanism isn't free. According to the paper's runtime data:

- Computing DCC is the most time-consuming step, taking 15 minutes 58 seconds, because it repeatedly computes vectors over the sliding window.
- Extracting entity-pronoun pairs with Maverick took 13 minutes 13 seconds, mostly bottlenecked on serial clustering on CPU.
- LLM Regex, because it has to call an LLM, averages 146.85 seconds per run.

Running the full Adaptive pipeline over the entire corpus took an average of about 210.66 seconds total.

Whether this overhead is worth it depends on where it's spent. Splitting and metric evaluation only happen during the "offline" index-building stage — once chunks are written to the database, online retrieval and generation latency is completely unaffected. In other words, this trades a few minutes of offline compute for stable, long-term answer quality online — for most enterprise applications, that's a favorable trade.

## Does this scoring actually work? Let the downstream numbers speak

All these intrinsic metrics are interesting, but what engineers actually care about is: does a higher-scoring chunk really translate into a more accurate answer? To verify this, the authors ran a controlled experiment — the retriever (Hybrid Search), reranker, and generation model (GPT-4.1) were all held fixed, with only the chunking strategy used to populate the vector database changed.

{{< image src="table5.png" alt="A table comparing Adaptive Chunking against other baseline methods on downstream metrics like retrieval completeness and answer correctness" caption="Table 5: Downstream RAG performance comparison. Chunks selected by Adaptive Chunking reach 67.68% Retrieval Completeness, 9.6 percentage points above the common LangChain recursive baseline (58.08%); Answer Correctness (G-Eval) reaches 78.01%, 7.9 points above the baseline. Out of 99 total test questions, the Adaptive method answered 65 correctly versus 49 for the baseline. (Source: original paper, Table 5)" >}}

This data is solid proof that the intrinsic metrics are meaningful: chunking results that score higher really do translate into measurably better downstream answer quality.

That said, tuning a single parameter can't max out all five metrics at once in practice. The authors computed Spearman correlation coefficients between every pair of metrics, and the results generally fall in the weak-to-moderate range (between -0.44 and 0.31), showing that these five metrics each capture a different facet of chunking quality — they complement rather than duplicate each other.

{{< image src="figure1.png" alt="A matrix of Spearman correlation coefficients between each pair of the five intrinsic metrics" caption="Figure 1: Correlation matrix between intrinsic metrics. ICC and DCC show a significant negative correlation (ρ = -0.44), and ICC and BI are also negatively correlated (ρ = -0.34). (Source: original paper, Figure 1)" >}}

{{< admonition warning "You can't max out all five metrics at once" >}}
Both of these negative correlations have a physical explanation:

- **ICC vs. DCC**: reflects the inherent limits of chunk size. The smaller a chunk gets, the purer its topic (higher ICC) — but the more it loses connection with its surrounding text (lower DCC).
- **ICC vs. BI**: is a different trade-off. If you keep an entire table or paragraph bundled together to protect a high BI score, you often end up dragging in irrelevant lead-ins or transition sentences into the same chunk, which drags topical purity (ICC) down.
{{< /admonition >}}

Rather than chasing a mythical parameter that maxes out all five metrics, engineers should accept that these trade-offs are structural, and lean toward whichever side actually matters for their use case.

There's one more phenomenon worth paying close attention to: Adaptive Chunking's average intrinsic score is 91.07%, versus 88.62% for traditional LangChain recursive splitting (default parameters) — a gap of only 2.45 percentage points, which doesn't look like much.

But once that small gap flows through a full RAG pipeline, it gets amplified several times over by the time it reaches the downstream output: Retrieval Completeness differs by 9.6 percentage points, and the relative gain in correctly answered questions reaches 32.7% (the 65-versus-49 figure mentioned earlier).

This is a textbook error-accumulation-and-amplification effect. RAG is fundamentally a multi-step, chained pipeline — a seemingly tiny semantic shift at the chunking stage (say, a pronoun's referent getting cut off, nudging the vector slightly) gets amplified step by step down the chain:

1. Retrieval stage: that chunk's cosine similarity falls out of the Top-k list.
2. Reranking stage: it gets ranked lower due to incomplete information.
3. Generation stage: the LLM reads incomplete context and plays it safe by answering "I don't know."

Optimization at the pre-processing and chunking stage isn't linear inside a RAG system — it gets amplified stage by stage as it flows downstream. This is exactly why the return on investment from cleaning up your data is often much higher than complex fine-tuning at the tail end of the pipeline.

## Practical advice for AI engineers, and where this framework still falls short

The paper's experimental results can be distilled into three directly actionable recommendations for engineers actually building RAG systems.

First, stop chasing a single splitting parameter. Documents with different structures clearly prefer different splitting methods — rather than spending time tuning one "universal" parameter set, build a candidate pool that includes page splitting, recursive splitting, and rule-based splitting, and let the system dynamically pick based on each document's characteristics.

Second, post-processing is the highest-ROI optimization. Implementing the "oversized re-split" and "tiny-chunk merge" defenses costs very little, but effectively clears out the two most annoying sources of retrieval noise — micro-fragments and semantically diluted oversized chunks — noticeably stabilizing vector database quality.

Third, invest resources at the data ingestion layer. Converting a PDF into high-quality Markdown that protects table headers, entity relationships, and heading-body bindings usually contributes more to final answer accuracy than blindly swapping in a bigger LLM.

Of course, this framework isn't free of costs and limitations either:

- **High offline build-time compute overhead**: computing DCC and running Maverick for entity-pronoun extraction are both especially time-consuming. At million- or tens-of-millions-of-token production scale, Maverick's lack of batch processing would become a clear performance bottleneck; future work may need a lighter, GPU-batch-accelerated alternative.
- **Weight allocation is still a rough arithmetic mean**: the five metrics currently use a simple 1:1:1:1:1 arithmetic mean, but different application scenarios clearly have different sensitivities to each metric — a finance use case that values precise data might care more about Block Integrity, while a customer-service use case that values fluent conversation might lean more heavily on DCC. How to automatically learn scenario-appropriate weights remains an open question for future research.
- **Limited multilingual support**: the RC metric relies heavily on the Maverick coreference-resolution model, which currently only supports English. Porting this framework to a Chinese or other-language RAG system would first require finding and validating a coreference-resolution tool for that language, adding meaningful engineering complexity.

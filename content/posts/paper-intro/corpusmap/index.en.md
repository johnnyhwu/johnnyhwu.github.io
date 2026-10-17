---
# weight: 1
title: "Do Agents Need a Map to Search Documents? Inside CorpusMap"
date: 2026-10-17
lastmod: 2026-10-17
draft: false
description: "CorpusMap precomputes an entity-document map so search agents follow links, not rediscover them: +6.4 to 11.7 Overall Quality points and 34% to 57% fewer input tokens."
featuredImage: "featured-image.png"

tags: ["Large Language Model", "Retrieval-Augmented Generation", "Single-Agent"]
categories: ["paper-intro"]
# series: ["getting-start"]
# series_weight: 1
lightgallery: true

url: "paper-intro/:contentbasename"
---

<!--more-->

## Introduction

Letting an agent answer questions over a large document collection with find and grep is a very common setup today. The problem is that the collection is just a pile of flat files. Even when the agent finds one relevant document, it gets no hint about which other documents that one is related to, so every question has to be explored from scratch.

CorpusMap (the paper *Follow the Entities: A Corpus Map for Agentic Search*, KAIST and Microsoft, arXiv 2609.37226) precomputes offline which documents are related to which. It resolves the people, projects, and events that recur across documents into entities, writes each entity up as an Entity Page, and links the page to every document that mentions it. At query time the agent hops along these links instead of rediscovering the same relationships for every question. This post covers the problem, the method, and the experiments in that order, and ends with a few concepts worth taking away on their own.

{{< admonition abstract "Key Takeaways (TL;DR)" >}}
- **Problem**: Key documents often cannot be found by literal search (for example, meeting notes that only use a project's internal codename), and the same exploration is redone for every question.
- **Approach**: Offline, resolve the entities that recur across documents, turn each one into an Entity Page (every fact cited to its source), and link it to all the documents that mention it, forming an "entity-document" bipartite graph. At query time the agent reads pages and follows links with the same shell commands it uses on the raw documents, and the system also hands it a starting list of candidate document paths picked by the keyword-ranking formula BM25.
- **Results** (3 benchmarks, 397 questions, four GPT models): Overall Quality is 6.4 to 11.7 points higher than Raw Corpus (no navigation layer, the agent searches the raw documents directly), with 34% to 57% fewer input tokens. The other four navigation layers do not consistently beat Raw Corpus. The gain is concentrated in "finding the evidence": clear on EnterpriseRAG-Bench and WixQA, small on HERB.
- **Engineering value**: Everything is built offline, can be updated incrementally, and can be built once with a cheap model and reused by an expensive one. The Extraction, Resolution, and Rendering stages can also be swapped for off-the-shelf tools with no LLM.
- **Limitations**: The experimental corpora hold only about 2.8k to 6.4k documents (scaled up to about 20k at most), and most follow-up experiments run only on EnterpriseRAG-Bench.
- **Concepts to take away**: Multi-document and multi-hop are two different kinds of problem, and a bipartite graph expresses relationships between nodes of the same kind through "common neighbors".
{{< /admonition >}}

{{< admonition info "Reading Markers" >}}
**[Inference]** marks the note author's inference, which the paper does not state. **[Background]** marks general knowledge from outside the paper. "Constructed" means the example was made up for illustration and is not from the paper. Unmarked content comes from the paper, or is a fact that can be computed directly from the paper's numbers.
{{< /admonition >}}


## Problem and Challenges

The paper targets multi-document question answering: the answer must combine evidence from at least two documents. It lists two challenges:

1. Between the key documents and the question lies a relationship that only this particular company knows. For example, meeting notes use only a project's internal codename, so searching by the literal words of the question cannot find them.
2. Each question is handled independently, so the agent repeatedly spends tokens rediscovering the same relationships. But a relationship such as "which documents are about the same project" does not depend on what is asked. It is stable and can be computed in advance and reused.

So the paper reframes the problem as corpus navigation: keep access to the full corpus, and add a persistent navigation layer that lays out the cross-document structure in advance.

### Which Kind of Relationship the Navigation Layer Should Hold

A navigation layer could hold many kinds of relationships. The paper gives two conditions.

1. **It can take you to documents that the question's literal words cannot find.**
2. **It can be compiled in advance, without knowing what users will ask.**

These are exactly the two properties a back-of-the-book index should have. Here is a constructed analogy: suppose you want everything related to "J. Chen" in a thick book. Flipping through page by page (the flat document collection) always starts from page one, and only turns up pages that literally say "J. Chen". A back-of-the-book index instead says directly "J. Chen -> pages 12, 47, 203".

An index entry points to "this person", not to "this string". Even if page 203 says "Manager Chen's infrastructure review", you can still reach it as long as the indexer decided it is the same person; that is condition one. The index was finished before the book was published and does not depend on what readers ask later, so it is built once and usable by every reader; that is condition two.

Counterexamples show that neither condition can be dropped (constructed):

| If the navigation layer is... | Which condition fails |
| --- | --- |
| Full-text keyword search | Condition one: it still only finds what literally appears |
| A summary written for this one question | Condition two: it can only be written after seeing the question, and must be rewritten for the next one |
| An entity index | Both hold, which is why the paper chooses it |

> **[Inference]** **[Background]** The underlying principle is to move query-time work offline and precompute it, the same idea as a database index or a search engine's inverted index. What is special about CorpusMap is that the index unit becomes the "resolved entity" rather than the word. The paper's own reasoning is that documents are written around entities such as people, projects, and products, and that entities can be recognized from the corpus alone, so the whole layer can be built offline.


## Method

The core of the method is to build an "entity-document" bipartite graph offline, write each entity up as an Entity Page, and let the agent walk along the links at query time. The sections below cover what the map looks like, how it is built offline, how it is used at query time, and finally why the map deliberately has no entity-entity edges.

### The Structure of the Map

The map is a bipartite graph: entities on one side, documents on the other, and edges only between an entity and a document. The concept of a bipartite graph itself is expanded at the end, in "Concepts Worth Taking Away". The formal definition is:

$$
G = (E \cup D,\ L), \qquad L = \{(e, d) \mid e \in E,\ d \in N(e)\}
$$

- \(D\): the set of documents.
- \(E\): the set of retained entities. Only entities linked to at least two documents are kept, because an entity that appears in only one document cannot string together any path.
- \(N(e)\): the document neighborhood of entity \(e\), that is, the documents that offline resolution decided mention \(e\).
- \(L\): the set of all "entity-document" links, each with an entity at one end and a document at the other.
- \(G\): the bipartite graph itself. If two documents share an entity, they are connected through it, and one document can belong to the neighborhoods of several entities at once.

Documents that are not linked to any retained entity stay in \(D\) and can still be found with ordinary keyword search.

**Walking through the content of Figure 1.**

| Entity \(e\) | Document neighborhood \(N(e)\) |
| --- | --- |
| Project Atlas | Oct 28 Email, Q3 Status Report, Acme MSA |
| J. Chen | Q3 Status Report, Nov 6 Standup |

{{< image src="figure2.png" alt="Overview of CorpusMap. The left half is offline graph construction, which resolves the same subject recurring across different folders into a shared entity and links entities and documents into a map. The right half is query time, where the agent starts from the entities mentioned in the question and collects evidence along the links, with the path it walked highlighted in green." caption="Figure 1 — CorpusMap overview: build the entity-document map offline, then walk its links at query time. (Source: original paper, Figure 2.)" >}}

Q3 Status Report belongs to both neighborhoods, so it is the bridge: Atlas -> Status Report -> J. Chen -> Nov 6 Standup. The agent walks it like this:

1. The question mentions Atlas, so it first opens the Project Atlas page.
2. From the page it goes to the Status Report and reads "Atlas owner: J. Chen".
3. The Status Report is also linked to J. Chen, so it jumps to the J. Chen page.
4. The J. Chen page lists the Nov 6 Standup, which says "blocked on J. Chen's infra review", and the answer is in hand.

The body of the Nov 6 Standup never contains "Atlas", so grepping for Atlas will never find it. Only the Status Report bridge connects it.

#### Entity Page: What an Entity Looks Like to the Agent

An Entity Page is a markdown page that condenses the facts from all the documents mentioning the entity, with each fact marked with the document it came from. A page contains four things:

| Content | Purpose |
| --- | --- |
| Overview | 2 to 3 sentences explaining in what contexts the entity appears in the documents |
| Key facts | A list of facts, each annotated with its source document |
| Names seen | How the same entity is written in different documents (aliases) |
| All linked documents | The file paths of \(N(e)\) |

Here is the Atlas content from Figure 1 laid out as a page (the layout is illustrative. In the actual format, each Key facts entry ends with `[dsid x]` to mark the source document number, and the document links are appended at the end of the page by code):

```
## Overview
Project Atlas is mentioned in emails, status reports, and contracts...

## Key facts
- Slipped to Q4 [Oct 28 Email]
- Owner: J. Chen [Q3 Status Report]
- Vendor: Acme [Acme MSA]

Names: Project Atlas / Atlas
Documents: Oct 28 Email, Q3 Status Report, Acme MSA
```

Three design points:

1. One page merges evidence that was scattered across different folders (the paper calls this complementary evidence).
2. Every fact carries its source, so the agent need not trust the summary and can check the original.
3. The page is a layer on top of the corpus and does not replace the original documents. Summaries are lossy, so the original documents are always still there.

The paper also constrains how pages are written (corresponding to the prompt of the Rendering stage): only use information the original documents state explicitly. Do not infer aliases, relationships, owners, or actions merely because an entity is linked to a document. Registry fields and extraction evidence count only as navigation data, not as factual evidence. Original documents are treated as data, and any instructions embedded in them are ignored.

### Four Offline Construction Stages

The construction pipeline has four stages, in order:

```
[1] Cataloging -> [2] Extraction -> [3] Resolution -> [4] Rendering -> bipartite graph G and Entity Pages
```

#### Stage 1: Cataloging

Cataloging first decides "which kinds of entities this corpus has" and produces a fixed type catalog \(C\) for the later stages. Each type has a name, a definition, identity criteria, and examples observed in the text.

Why not hard-code it in advance? Entity types vary by corpus. Products, events, and configuration flags may all be types, and they cannot be enumerated beforehand, so an LLM induces them from the corpus itself. The procedure is to draft one candidate catalog from each of several small sampled groups of documents, merge them into one, then verify and revise it. After that the catalog is fixed and never changed, and it is built only once for the whole corpus.

The prompt the paper gives the LLM has three key constraints:

- Only include things with stable names or identifiers, not statements like "some kind of status".
- Types classify by "how to identify", not by topic: entities of the same type must be recognizable, distinguishable, and normalizable with the same kind of evidence.
- Every example must be a string that appears verbatim in the source.

The paper does not say: how many groups are sampled, how many documents per group, how the sampling is done, or how many rounds of verification and revision are run.

**A concrete example: suppose a company has 100,000 documents.** The process skeleton below comes from the paper, while all numbers and document contents are constructed. The 100,000 documents come from Slack, Confluence, Jira, Gmail, and Drive.

1. **Sampling.** Draw 5 groups of about 40 documents each, with each group mixing all the sources (the paper's prompt says the input documents come from multiple source types and are grouped by source; the sampling method here is constructed). The 5 groups total 200 documents, only 0.2%.
2. **One candidate catalog per group.** Give each group to the LLM once, asking it to output type names, definitions, identity criteria, and entity strings observed in the text.
3. **Merge.** Combine the groups' catalogs into one.
4. **Verify.** A second LLM acts as an adversarial verifier whose only job is to look for counterexamples.
5. **Revise.** Change only the flagged defects to get the final catalog, say with 8 types. The catalog is fixed here, and the later Extraction stage uses these 8 types across all 100,000 documents.

The types proposed by each group in step 2 look like this (constructed):

| Group | Proposed types |
| --- | --- |
| Group A | Project (Atlas), Person (J. Chen), Jira ticket (RRB-17) |
| Group B | Initiative (Atlas), Customer (Acme), Incident (INC-2147), plus one wrongly included example "latency is high" |
| Group C | Project (Redwood), Config flag (installer-rollback-lock), and a type that mixes a product (Redwood Private) with a ticket (RRB-17) |

During merging, A's Project and B's Initiative refer to the same kind of thing, so they are merged into Project. One of C's types mixes products with tickets, which are identified differently, so it must be split.

> **[Inference]** Cataloging looks at only 200 sampled documents, so its cost is almost independent of corpus size. What truly grows linearly with the number of documents is the Extraction and Resolution that run on every document afterward. The paper gives no per-stage cost numbers.

##### Side note: with so many sampled documents, does the context fit?

The first step of Cataloging feeds an entire group of sampled documents to the LLM at once. This carries risk, especially for long documents, and the paper does not address it. A constructed token estimate follows (assuming 40 documents per group):

| Average length per document | Total for 40 documents |
| --- | --- |
| 1k tokens (Slack messages, short emails) | about 40k |
| 3k tokens (typical Confluence page) | about 120k |
| 10k tokens (meeting transcripts, long specs) | about 400k |

Short documents are fine. A group of long documents may not fit in the window, and even if it fits, details in a long context are easily overlooked. The paper says only "several small sampled groups of documents". It does not state how many documents per group, whether long documents are truncated, or run any experiment on this sensitivity.

> **[Inference]** The design is still relatively tolerant, for two reasons. First, the goal of Cataloging is to "find the common entity types", not to "understand every document", so if one document is overlooked, the same type usually appears in other documents and other groups. Second, only the proposal step consumes documents. The later merge, verify, and revise steps consume catalog JSON, which is small. Also, if a group is too large, the most direct adjustment is to shrink each group to 10 to 15 documents and increase the number of groups, or to truncate the early part of each document. The cost is more candidate catalogs and more work in the merge step, but the merge handles small JSON and is cheap. Reducing the per-group size is the most natural lever.

##### Side note: how merge, verify, and revise work

Each of these three steps is one LLM call whose input and output are JSON catalogs. They no longer read the original documents, so the cost is small.

| Step | Input | What the LLM does | Output |
| --- | --- | --- | --- |
| Merge | All candidate catalogs (each type numbered) | Every source type must take a stance: map to one final type, split into several, or be rejected | The final catalog, plus a mapping table of "where each source type went" |
| Verify | The original candidates and the merged draft | A second LLM acts as an adversarial verifier, only looking for defects and counterexamples, not rewriting | A defect list; it passes only if there are no defects |
| Revise | The draft and the defect list | Fix only the flagged defects and leave the rest alone | A complete revised catalog |

When merging, each source type is handled in a fixed order, moving to the next option only if the previous one does not work:

```
[1] Drop individual invalid instances -> [2] Narrow an overly broad type -> [3] Split a mixed type -> [4] Merge into an existing final type -> [5] Reject
```

Rejection is the last resort and must leave a record (the paper calls it a tombstone) stating why narrowing, splitting, and merging all failed. Every source type must be accounted for exactly once: mapped (corresponds to one final type), split (divided into two or more), or rejected (corresponds to no final type). Another hard constraint is that each final type's examples must come verbatim from the source catalogs, and the LLM may not invent any.

The verifier looks at seven kinds of problems: whether the reason for a rejection holds up, whether two types collect the same thing (a counterexample string must be attached), inconsistent granularity, self-contradictory criteria, instances of the same type that cannot be recognized with the same kind of evidence, examples that do not belong to the type, and types that appear out of nowhere. If any category has a defect, the verdict is fail. Revision touches only the flagged parts, and overlap problems are resolved either by merging or by adding a distinguishing criterion that is visible at run time.

Continuing with the example above (constructed):

1. Merge: A's Project and B's Initiative are both things like Atlas, so they are merged into Project. C's type that mixes a product (Redwood Private) with a ticket (RRB-17) is split into Product and Ticket. One of B's examples is "latency is high", which is a status statement rather than a name, so it is dropped.
2. Verify: The verifier points out that "Redwood Private" fits both Project and Product, so the two types have no reliable distinction, and the verdict is fail.
3. Revise: Resolve the overlap in one of two ways: merge them, or add a distinguishing criterion visible at run time (for example, requiring that a Product have a version number). The other types are left untouched.

The paper does not say: whether verification and revision loop for multiple rounds (it only says "verify and revise"), the rules for the deterministic policy decision mentioned in the revision prompt (using program rules to decide which defects count as blocking), and a note in the verification output called a "soft warning".

> **[Inference]** The soft warning is probably used to tolerate overlaps that run-time rules can resolve, but the details are not given. The whole procedure is essentially "one LLM as generator and another LLM as checker", guarding against LLM fabrication and over-merging. The paper does not run an ablation that removes the verification step to show it is necessary.

#### Stage 2: Extraction

Extraction takes one document in and produces one list out: it marks the entities in the document and attaches types from the catalog. Think of the catalog as a "table of sticker kinds", and Extraction as going through each document with it to place stickers. It is not responsible for deciding whether entities in two documents are the same.

The paper's prompt takes just one document plus the fixed type catalog at a time, and outputs two lists:

```
local entities:
  - surface forms: ["Project Atlas", "Atlas"]  type: Project
  - surface forms: ["J. Chen"]                  type: Person
unresolved entities:
  - surface forms: ["Q4"]  reason: no suitable type in the catalog
```

- local entities (in-document entities): each contains the surface forms (which must appear verbatim in this document) and a type name. Different spellings that refer to the same thing within one document are merged into one.
- unresolved: items that fit no type, or where the evidence is not enough to choose a type, are listed here with the reason and are not forced into a type.

Three rules decide what can be marked:

1. Every entity must be an identifiable individual. Standalone facts, rules, suggested actions, and generic descriptions without a name (for example "that migration project") do not create entities.
2. Every surface form must appear verbatim in this document and cannot be a name the LLM rewrote.
3. The "observed examples" in the catalog are only a reference, not a list of entities that already exist.

Walkthrough (document content constructed, with the sentence drawn from the Status Report in Figure 1): "Project Atlas is expected to slip to Q4. Atlas owner: J. Chen."

| Step | What happens |
| --- | --- |
| Mark | "Project Atlas", "Atlas", "J. Chen", "Q4" |
| Merge within the same document | "Project Atlas" and "Atlas" refer to the same thing and are merged into one entity, keeping both surface forms |
| Attach types | Atlas gets Project, J. Chen gets Person |
| No type fits | "Q4" is a time, the catalog has no suitable type, so it goes to unresolved |

Extraction looks at a single document only: the J. Chen in two documents are, for now, two in-document entities that do not know each other. Recognizing them as the same person is the next stage's job.

> **[Inference]** Extraction and Resolution are deliberately split into two steps because Extraction looks at a single document, so each document can be processed independently and the cost grows linearly with the number of documents. The cross-document decisions are left to the next step, which works against the registry. The paper does not state the reason for the split.

#### Stage 3: Resolution

Resolution is the most central step of the whole method: recognizing "the same thing in different documents" as one. For each in-document entity, it is compared against a "registry" (which starts empty), and one of three decisions is chosen:

| Decision | Meaning | Result |
| --- | --- | --- |
| LINK | It is the same thing as some entity in the registry | Update that entity and record one entity-document link |
| ADD | It is not in the registry; it is new | Add an entity and record one link |
| UNRESOLVED | Not enough evidence to tell | Record no link |

Walkthrough (processing order and document contents constructed, entities taken from Figure 1):

| Processing order | In-document entity | Decision | Registry becomes |
| --- | --- | --- | --- |
| 1. Oct 28 Email | Project Atlas | ADD (the registry is empty) | Atlas |
| 2. Status Report | Atlas | LINK (recognized as Atlas) | Atlas (one more link) |
| 2. Status Report | J. Chen | ADD | Atlas, J. Chen |
| 3. Nov 6 Standup | J. Chen | LINK | Atlas, J. Chen (one more link) |

The result is that Atlas links to the Email and the Status Report, and J. Chen links to the Status Report and the Standup, exactly the links of the bipartite graph above.

The paper's prompt for this step sets down several key rules:

- Name similarity or a high retrieval rank is not evidence that two things are the same. Judge using the full document context.
- Before deciding, compare the chosen candidate against the "strongest competing candidate" once. If the document context still cannot tell them apart, answer UNRESOLVED.
- The registry itself is incomplete, so do not force a match. The canonical name of a new entity must be one of the in-document entity's surface forms, and an existing entity's id must come from the candidate list.

A constructed example: the company has both J. Chen and Jenny Chen, and one document says only "Chen", with no context to tell which. Here it is better not to link (UNRESOLVED) than to link wrongly.

##### The Difference Between LINK and ADD

There is only one difference between them: whether the registry already contains this entity. LINK means "it already exists, and this document mentions it too", while ADD means "it does not exist yet, this is its first appearance, so create a new record".

| | LINK | ADD |
| --- | --- | --- |
| Basis for the decision | Same thing as some candidate in the registry | Nothing in the registry matches |
| What it does to the registry | Updates the existing record (UPDATEENTITY) | Adds a new record (ADDENTITY) |
| Where the entity id comes from | Must be an existing id from the candidate list | Newly created; the canonical name must be one of this in-document entity's surface forms |
| Effect on the links \(L\) | Adds one \((e, d)\) | Adds one \((e, d)\) |

Both record one entity-document link; only UNRESOLVED records none. This distinction determines what the map looks like: only entities linked to at least two documents are retained. An entity has just one link when it is first ADDed, and rises to two or more only when another document later LINKs to it. An entity that is never LINKed is eventually discarded.

The consequences of the two kinds of mistakes, and the default when unsure, are:

- ADD when it should LINK: one thing becomes two records in the registry, its links are cut in half, and the bridge breaks. For example, if the J. Chen in the Standup is treated as a new entity, there is no path between the Status Report and the Standup.
- LINK when it should not: two different things are merged into one record, and the page mixes in unrelated facts.
- When unsure, answer UNRESOLVED; the paper's prompt favors this conservative choice.

> **[Inference]** The paper does not say what retrieval method is used to fetch candidates from the registry, nor which fields UPDATEENTITY updates; presumably it adds the new surface form to the entity's name list. The paper also does not quantify how often each of the two mistakes above happens. In addition, Resolution processes items in sequence against a registry that keeps growing, so unlike Extraction it cannot be parallelized directly, and the processing order may affect the result. The paper does not analyze this.

#### Stage 4: Rendering

Rendering first filters out entities linked to only one document, then asks the LLM to write each retained entity as a page.

- **Filter**: Keep only entities linked to at least two documents. A constructed walkthrough: Project Atlas links to 3 documents and J. Chen to 2, so both are kept. The staging keys link to only 1 and are dropped.
- **Write pages**: One LLM call per retained entity. The input is the entity name, type, the surface forms seen, and the original documents in \(N(e)\). The output has a fixed two sections, Overview (2 to 3 sentences) and Key facts (each with its source). See the "Entity Page" section above for the constraints.
- **Links**: The links to each document are appended to the end of the page by code, not written by the LLM.

> Deployment reminder (the paper's Ethics Statement): Concentrating scattered information on one page may let people without permission to see the original documents see a summary through the entity page. The paper recommends building separate maps by permission level, without experimental validation.

#### The Four Stages Together

| Stage | Input | What it does | Output | Scope of execution | Replaceable by off-the-shelf tools |
| --- | --- | --- | --- | --- | --- |
| 1 Cataloging | Sampled documents | Induces entity types | Type catalog \(C\) | Once for the whole corpus | Paper does not say it can be replaced |
| 2 Extraction | One document plus \(C\) | Marks entities, attaches types, merges within a document | In-document entities; those with no fitting type go to unresolved | Once per document | Yes |
| 3 Resolution | In-document entities plus the registry | Decides LINK, ADD, or UNRESOLVED | The registry, and the entity-document links \(L\) | In-document entities processed one by one in order | Yes |
| 4 Rendering | The registry plus the original documents | Drops entities linked to only 1 document, and the LLM writes pages for the rest | Entity Pages | Once per retained entity | Yes |

Stage 2 uses the type catalog \(C\) built in Stage 1, and Stage 4 uses the registry produced by Stage 3 and also reads back the original documents. The type catalog is produced once, while the registry grows steadily as Stage 3 processes items one by one: the former is a fixed input, the latter is changing state.

These terms are easy to mix up, so here is a comparison:

| Term A | Term B | Difference |
| --- | --- | --- |
| Type catalog | Registry | The catalog is "which kinds there are" and stays fixed once built. The registry is "which ones actually exist" and grows as Resolution proceeds |
| In-document entity | Entity | The former is a temporary product inside a single document, the latter is a formal cross-document record in the registry |
| Links \(L\) | Entity Page | Links are produced during Resolution and are structure. Pages are produced during Rendering and are content |
| UNRESOLVED | A filtered-out entity | The former means "can't tell, so don't link"; the latter means "linked to fewer than 2 documents, so not retained" |
| The unresolved list in Extraction | The UNRESOLVED decision in Resolution | The former holds strings that cannot be given a type (such as "Q4"); the latter is a decision that "it is unclear whether this is the same entity". The names are similar but they occur in different stages |

The Extraction, Resolution, and Rendering stages can also use off-the-shelf tools instead (existing entity linking and recognition tools such as GLinker with the open-source GLiNER model, with pages generated directly from extraction evidence and no LLM). The later corpus scale-up experiment shows similar results to the LLM version at lower cost, and the paper does not describe the details.

### How It Is Used at Query Time

At query time the agent has no new tools; it reads Entity Pages with the same shell commands it uses on the raw documents. Each page is a file stored next to the original documents, and the page lists the paths of the documents it links to.

The commands available to the agent include ls, tree, find, grep, rg, cat, head, tail, sed, awk, cut, sort, uniq, wc, xargs, and jq, and it can also add documents to or remove them from its own supporting set (the set of documents the agent itself picks as supporting the answer). Each question has a fixed execution budget, following the setup of the EnterpriseRAG-Bench paper.

Alternating between two kinds of hops lets the agent keep walking the bipartite graph:

| From | To | How |
| --- | --- | --- |
| Entity Page | Document | Read the file path listed in the page and open that document |
| Document | Entity Page | Search for "which pages list this document", or search the pages with words from the document, then open the match |

#### The Candidate Document List: The Agent's Starting Point

Before the agent starts, the system attaches a list of "suggested documents to look at first". The list contains only each document's title (if any), file path, and document ID, with no body text. The agent may follow it or not, and can still grep the whole corpus itself. CorpusMap in its default setting comes with this list.

It is produced as follows:

```
[1] Question -> [2] BM25 scores all Entity Pages, take the top few -> [3] Gather the documents those pages link to
    -> [4] BM25 re-scores those documents by title and content, take the top few -> [5] Attach the list next to the question and hand it to the agent
```

BM25 is a classic keyword-ranking formula that scores by how the words of the question occur in the text. It measures only literal relevance and does not understand semantics. What step 2 matches are the page's name, type, overview, key facts, and the surface forms seen. The role of the entity page here is to widen the scope of keyword matching from "does a single document contain this word" to "all the documents this entity links to". The paper's main text does not say how many candidate pages and documents are given to the agent by default, and only the appendix's parameter sweep experiment covers a range of 1 to 100.

A constructed walkthrough (assuming only the Atlas page ranks first):

| Step | Result |
| --- | --- |
| Question | "Why was the Atlas migration delayed?" |
| Page ranking | The Project Atlas page ranks first, because both its name and key facts contain Atlas |
| Gather documents | Oct 28 Email, Acme MSA, Q3 Status Report |
| Re-rank documents | Sorted by matching title and content against the question |
| Handed to the agent | A path list of the top few, with no body text |

The Nov 6 Standup is not in this list, because it is not in Atlas's neighborhood. It can only be found when the agent later hops over through J. Chen.

#### How the Agent Walks the Map: A Case from the Paper

The paper includes a real side-by-side case. The question is: in Deterministic Playback Manifest v1, how are the signature and integrity fields represented? The answer is scattered across two documents from different sources: an early draft D1 (Google Drive) and the revised v1 spec D2 (Confluence). The gold answer is that v1 does not embed a signature, with integrity expressed through an optional integrity field and an integrity ref URI, while the early draft listed an embedded signature field.

{{< image src="table10.png" alt="A case comparison table comparing the exploration paths of the CorpusMap agent and the Corpus2Skill agent on the same question. CorpusMap finds both documents via a ticket page and a Serving Runtime page, while Corpus2Skill does not find them." caption="Table 1 — Case study: CorpusMap versus Corpus2Skill on the same EnterpriseRAG-Bench question. Blue boxes are documents and orange boxes are Entity Pages, with the same notation as Figure 1. (Source: original paper, Table 10.)" >}}

The CorpusMap agent walked it like this:

| Step | What the CorpusMap agent did |
| --- | --- |
| 1 | Searched Entity Pages for "playback", opened the ticket page ENG-8192, which links to draft D1 |
| 2 | Read D1 and saw that the draft has an embedded signature field |
| 3 | Searched Entity Pages again with keywords from D1, opened the Serving Runtime page, which links to D2 |
| 4 | Read D2 and answered that v1 uses the integrity field plus the integrity ref URI and no longer embeds a signature |

For the comparison method Corpus2Skill (which clusters documents into a tree structure), D1 and D2 sit under the same cluster. The agent explored other branches but never opened that cluster, and searching "Deterministic Playback", "manifest", and "integrity" found nothing, so it finally answered that it could not find the documents. The point is that in CorpusMap, D1 and D2 hang under different entity pages, so there are multiple routes to the same evidence, while a tree structure mostly attaches each document to a single branch.

> The paper does not say how the agent decides at each step what to search for or where to hop. The path is entirely decided by the LLM itself, limited only by the fixed per-question execution budget, with no guidance or restriction rules. **[Inference]** The quality of navigation will vary with the capability of the agent model.

### Why the Map Has No Entity-Entity Edges

At this point you might wonder: are there links between entities in the registry? The answer is no. The registry is a flat roster of entities, not a graph. It records the entity id, canonical name, type, and surface forms seen, plus the extraction evidence for each link (the fields listed in the rendering prompt; the paper does not enumerate the complete fields). There is no relationship field such as "the owner of Atlas is J. Chen".

Two entities are indirectly related only through shared documents: the intersection of \(N(\text{Atlas})\) and \(N(\text{J. Chen})\) is {Q3 Status Report}, so there is a path Atlas -> Status Report -> J. Chen.

The paper deliberately did not add entity-entity edges, and tested this (Appendix B.4). They tried two ways of adding them and listed these edges on the Entity Page: one is relations extracted by an LLM (for example "the workaround for RRB-17 deletes installer-rollback-lock"), and the other is pairs of entities that share the same document. The results were:

- Such edges do not make any new page reachable. Two entities already share a document, and the edge only shortens \(e \to d \to e'\) to \(e \to e'\).
- Without edges, 86% to 90% of the Entity Pages the agent newly opened were found through search, because the page text itself mentions other entities.
- With edges available, the agent followed an edge in only 11% to 19% of questions, and 71% of those moves did not bring in a gold document not yet found (gold documents are those the benchmark annotates as truly needed to answer the question). Of the gold documents first reached through an edge, 79% were also found on the same question without edges.
- Document recall changed by only -2.6 to +0.2 percentage points, yet Entity Pages grew 27% to 52% larger and input tokens rose by up to 28%. (All of the above is from EnterpriseRAG-Bench, and that passage does not state which model was used.)

In summary: the edges bring almost no new paths, yet make pages larger and use more tokens, so the paper does not add them.

The paper's conclusion is that the bipartite graph already covers the connections these edges would bring. The paper contrasts this with the following question: list all the internal discussion threads about RRB-17. The Entity Page for RRB-17 links to four of the five gold documents, and the remaining one is a meeting transcript reached through another link. The table lists both the entity-document paths and the entity-entity paths, so the two ways of walking can be compared directly.

{{< image src="table9.png" alt="A case table: the question, the five gold documents, and a comparison of entity-document paths and entity-entity paths." caption="Table 2 — Case study of entity-entity edges; blue boxes are documents and orange boxes are Entity Pages. (Source: original paper, Table 9.)" >}}

> **[Inference]** Relationships between entities are left in the page text (for example the Atlas page says Owner: J. Chen), and when the agent wants to jump there it can just grep, with no need for structured edges.


## Experiments

The setup and metrics come first (without understanding the metrics you cannot read any table), then the main results, with the remaining experiments condensed into bullets.

### Setup

#### Three Benchmarks and Corpora

First, two terms: gold documents are the documents a benchmark annotates as truly needed to answer a question. Distractor documents are documents unrelated to the question that are mixed into the corpus to make search harder.

| Benchmark | Questions used | Corpus | Contents |
| --- | --- | --- | --- |
| EnterpriseRAG-Bench | 80 questions (Project Related 40, Conflicting Info 20, Completeness 20) | 2,819 documents | The gold documents of all the benchmark's questions, plus one-hop distractor documents linked to the gold ones |
| WixQA | 79 questions (ExpertWritten 52, Simulated 27) | 6,221 articles | The complete customer-support knowledge base articles |
| HERB | 238 questions (content-type questions) | 6,365 documents | A simulated software company's Slack, meeting transcripts, documents, PRs, and so on: 6,362 documents cited as evidence by these questions, plus 3 metadata files |

The selection criterion is to take only questions whose answer annotates at least two gold documents. The other categories of EnterpriseRAG-Bench have a single gold document or none, and for WixQA, questions grounded in a single article are excluded, giving 397 questions in total. All methods use the same fixed corpus.

> **[Inference]** The paper is motivated by enterprise corpora of hundreds of thousands of documents, yet the experimental corpora hold only 2.8k to 6.4k documents (the corpus scale-up experiment reaches about 20k). The distractors in EnterpriseRAG-Bench are drawn from the ring linked to gold documents, which should be harder than random distractors, but still smaller and cleaner than a real company corpus. The paper does not discuss this.

#### Metrics

The metrics fall into three kinds, measuring "how good is the final answer", "how complete is the evidence found", and "how many tokens were spent".

| Abbreviation and full name | Benchmark | What it measures | Which stage it tests |
| --- | --- | --- | --- |
| Correct. (Correctness) | EnterpriseRAG-Bench | An LLM judge decides whether the answer roughly matches the gold answer with no conflict; only right or wrong | Final answer |
| Complete. (Completeness) | EnterpriseRAG-Bench | The percentage of the atomic facts the gold answer breaks into that the answer covers | Final answer |
| Fact. (Factuality) | WixQA | Using the official judge prompt, rates how much of the gold answer's key information the answer contains | Final answer |
| Content (content score) | HERB | Using the official judge, scores against the reference answer on three aspects: factual correctness, completeness, and relevance | Final answer |
| Doc. Rec. (Document Recall) | EnterpriseRAG-Bench | The percentage of gold documents that were put into the supporting set; no LLM is used to compute it | Finding evidence |
| Ctx. Rec. (Context Recall) | WixQA | How much of the key information appears in the context the agent gathered (tool outputs plus the candidate list given with the question) | Finding evidence |
| Tokens | All | The sum of input tokens over all the agent's LLM calls for one question | Cost |

Doc. Rec. and Ctx. Rec. have similar names but are not the same quantity: the former counts "whether gold documents were chosen into the supporting set", while the latter asks "whether the key information appeared in the content that was read", so the numbers cannot be compared directly across benchmarks. For all metrics that use an LLM judge, the judge model is GPT-5.6 Sol.

#### How Overall Quality and Rel. Tok. Are Computed

The two summary metrics are defined as:

$$
\text{Overall Quality} = \frac{Q_{\text{ERB}} + Q_{\text{Wix}} + Q_{\text{HERB}}}{3}, \qquad \text{Rel. Tok.} = \left( r_{\text{ERB}} \cdot r_{\text{Wix}} \cdot r_{\text{HERB}} \right)^{1/3}
$$

Here \(Q_b\) is the average of all the quality metrics of benchmark \(b\) (including the two recall metrics; see the note below). \(r_b\) is the method's tokens on benchmark \(b\) divided by Raw Corpus's tokens on \(b\) under the same model. The geometric mean gives the three benchmarks equal weight so that HERB, which uses the most tokens, does not dominate. (**[Inference]** This is the note author's explanation; the paper gives no reason.)

Computing it once (using GPT-5.5, Raw Corpus from the main results table):

| Benchmark | Metrics used | Formula | Result |
| --- | --- | --- | --- |
| EnterpriseRAG-Bench | Doc. Rec., Correct., Complete. | (61.62 + 62.08 + 73.11) / 3 | 65.60 |
| WixQA | Ctx. Rec., Fact. | (73.31 + 67.51) / 2 | 70.41 |
| HERB | Content | 62.31 | 62.31 |

Overall is (65.60 + 70.41 + 62.31) / 3 = 66.11, matching the table. For Rel. Tok., take CorpusMap (GPT-5.5) as an example: 88.1k / 206.5k = 0.43, 74.5k / 337.2k = 0.22, 494.7k / 598.4k = 0.83, and the geometric mean of the three is about 0.43, matching the table.

**Note:** The paper only says "quality metrics", but Overall Quality actually includes the two recall metrics too (this is the only way to make the numbers match when backed out from the main results table). Looking only at the answer metrics (Correct., Complete., Fact., Content), the gain shrinks by about a quarter. In other words, part of the headline gain comes from "finding the evidence" rather than "answering well". The table below is computed from the main results table's GPT-5.5 numbers:

| | With recall (the paper's Overall) | Answer metrics only |
| --- | --- | --- |
| Raw Corpus | 66.11 | 65.81 |
| CorpusMap | 72.55 | 70.62 |
| Gap | +6.44 | +4.82 |

#### Comparison Methods (baselines)

The six methods differ in only one thing: the unit the navigation layer uses to organize the corpus. The original documents are kept in every method, and the agent uses the same shell commands in all of them.

| Method | Organizing unit | Approach |
| --- | --- | --- |
| Raw Corpus | None | No navigation layer; the agent searches the raw documents directly |
| Document Page | Each document | An LLM writes a page of key facts for each document |
| Group Page | The corpus's own grouping (for example folders) | Merges the documents of the same group into one page |
| LLM Wiki (Karpathy, 2026) | Decided by the LLM itself | The LLM freely writes pages that link to each other |
| Corpus2Skill (Sun et al., 2026a) | Topic hierarchy | Clusters documents, with an LLM summarizing each cluster, forming a tree for the agent to walk down |
| CorpusMap (this paper) | Entity | Entity Pages plus entity-document links |
| Gold Documents (Oracle) | Not applicable | Gives only the gold documents directly to the model, representing the ceiling under ideal retrieval |

The same LLM is used for building the navigation layer and for answering (a map built by GPT-5.5 is answered by GPT-5.5), and cross-model reuse is tested separately. The Oracle is not an opponent; the paper itself calls it an "incomparable" upper bound, used to measure how far each method is from the ceiling.

> **[Inference]** LLM Wiki was originally only a conceptual gist with no standard implementation, so the one in the table is the authors' own version. Losing to CorpusMap only shows that "this version" loses. As for the prompt details of the other baselines, the note author did not see them in the appendix.

### Main Results

First, the models: the four models used in the experiments are GPT-5.5 and the Luna, Terra, and Sol versions of GPT-5.6. Luna is the cheapest, and GPT-5.5 and Sol are the two most expensive.

CorpusMap has the highest overall quality on all four GPT models while also using fewer tokens on average. But the lead is "consistent" rather than "crushing", and concentrated on two benchmarks.

{{< image src="figure1.png" alt="Scatter plot with estimated answering cost on the horizontal axis and Overall Quality on the vertical axis, comparing CorpusMap with the three strongest baselines. CorpusMap has higher quality at lower cost." caption="Figure 2 — Overall Quality versus estimated answering cost: CorpusMap and the three strongest baselines, averaged over the three benchmarks. (Source: original paper, Figure 1.)" >}}

{{< image src="table1.png" alt="The paper's main results table: metrics aggregated over the three benchmarks, covering GPT-5.5 and the Luna, Terra, and Sol versions of GPT-5.6, with the mean and standard deviation of each method." caption="Table 3 — Main results: metrics for each method across three benchmarks and four models, as the mean and standard deviation over three runs. (Source: original paper, Table 1.)" >}}

The table below shows Overall Quality from the main results table (the average of the three benchmarks' averages, with 80, 79, and 238 questions, and each benchmark's score being the mean of three runs):

| Model | Raw Corpus | Document Page | LLM Wiki | Group Page | Corpus2Skill | CorpusMap | Oracle |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GPT-5.5 | 66.11 | 66.41 | 64.49 | 61.07 | 45.49 | 72.55 | 79.62 |
| Luna | 53.85 | 55.73 | 54.39 | 47.55 | 37.27 | 65.58 | 80.00 |
| Terra | 65.75 | 62.91 | 58.71 | 43.84 | 43.86 | 72.51 | 79.90 |
| Sol | 67.69 | 66.31 | 65.15 | 31.23 | 44.44 | 74.68 | 79.69 |

- **Gain**: CorpusMap has the highest Overall Quality on all four models. The gains over Raw Corpus are +6.44, +11.73, +6.76, and +6.99 (subtracting the numbers in the table). The paper's significance test table (paired bootstrap, resampling by question 100,000 times, with Holm–Bonferroni correction) gives +6.45, +11.74, +6.76, and +7.00, with all 95% confidence intervals above 0, for example [4.30, 8.62] for GPT-5.5.
- **Cell-by-cell check**: Across four models times six metrics, 24 cells in total, CorpusMap is highest in all of them (except Oracle).
- **Other navigation layers**: None consistently beat Raw Corpus. Document Page wins on only two of the four models (GPT-5.5, Luna), LLM Wiki on only one (Luna, +0.54), and Group Page and Corpus2Skill lose on all four. The paper's own conclusion is that adding a navigation layer is not guaranteed to help.
- **Cost**: Rel. Tok. is 0.43, 0.65, 0.66, and 0.43, that is, 34% to 57% fewer input tokens, with the biggest savings on the two most expensive models (GPT-5.5 and Sol).
- **Not a crushing win**: The lead over each model's strongest baseline is about 6 to 10 points (+6.14, +9.85, +6.76, +6.99), and the gap to the Oracle ceiling is still 5 to 14 points (7.07, 14.42, 7.39, 5.01). Looking cell by cell, cost is not lower across the board either: Corpus2Skill is cheaper on GPT-5.5 (0.31× versus 0.43×, but with quality of only 45.49), and CorpusMap uses more tokens than Raw Corpus on Luna's HERB (254.2k versus 219.4k).

The gain is concentrated in two benchmarks (GPT-5.5; each cell is the average of all the quality metrics for that benchmark, with 80, 79, and 238 questions):

| Benchmark | Raw Corpus | CorpusMap | Gain | Oracle | Gap to ceiling |
| --- | --- | --- | --- | --- | --- |
| EnterpriseRAG-Bench | 65.60 | 76.60 | +11.00 | 89.36 | 12.76 |
| WixQA | 70.41 | 76.69 | +6.28 | 82.60 | 5.91 |
| HERB | 62.31 | 64.37 | +2.06 | 66.90 | 2.53 |

> **[Inference]** HERB's ceiling is itself low (even the Oracle, given the gold documents directly, gets only 66.90), so on this benchmark the bottleneck does not seem to be "finding the evidence", and a navigation layer has little room to help. The paper does not analyze this. The paper's own phrasing is "narrows the gap to the Oracle", which is accurate: it does not surpass it.

### Other Experiments

- **Map reuse across models** (Table 4; all the numbers below are on EnterpriseRAG-Bench, and gains are relative to Raw Corpus):
  - The map built by the cheapest model, Luna, beats Raw Corpus for all four answering models (+7.99, +5.14, +9.89, +2.88).
  - The construction cost upper bound is 74.65 USD, about 1.6% of building the map with GPT-5.5 (upper bound 4,732.14 USD).
  - GPT-5.5 scores 73.59 with Luna's map and 76.60 with its own, a gap of 3.01.
  - The conclusion is that the map can be built once with a cheap model and reused by expensive ones. This table has no standard deviations and the gaps between cells are often around 1 point, so do not read much into the ranking of "who builds best".

{{< image src="table4.png" alt="Map reuse table: rows are the models that built the map, columns are the models that answered, cells are Overall Quality, and the rightmost column is the one-time construction cost." caption="Table 4 — Map reuse across models (EnterpriseRAG-Bench only): rows are the map-building models, columns are the answering models, and cost is the one-time construction cost. (Source: original paper, Table 4.)" >}}

- **Incremental updates** (Figure 3): New documents are added in chronological order, and only the Entity Pages whose linked documents changed are re-rendered. The three incremental updates save 34%, 69%, and 71% of the full rebuild's construction tokens respectively, with final quality comparable to a full rebuild. Questions covered by the updates improved after the update, even though these documents could already be found by searching the raw corpus. Tested only with GPT-5.5 on EnterpriseRAG-Bench.

{{< image src="figure3.png" alt="Three subplots: (a) the fraction of tokens each incremental update saves relative to a full rebuild, (b) quality at each map state, (c) accuracy before and after the update on newly covered questions." caption="Figure 3 — Incremental updates (GPT-5.5, EnterpriseRAG-Bench): (a) tokens saved, (b) quality at each state, (c) accuracy on newly covered questions. (Source: original paper, Figure 3.)" >}}

- **Corpus scale-up** (Figure 4): Adding distractor documents while keeping all gold documents, the corpus is scaled to 2.8k, 10k, and 20k documents, and CorpusMap beats Raw Corpus at every size while using fewer tokens. The open-source Qwen3.8-27B using the same map (built by GLinker) also improves on every metric and size.

{{< image src="figure4.png" alt="Corpus scale-up experiment plot, showing the performance of CorpusMap and Raw Corpus on GPT-5.6 Luna and Qwen3.8-27B as the corpus grows from 2.8k and 10k to 20k documents." caption="Figure 4 — Corpus scale-up: results with GPT-5.6 Luna and Qwen3.8-27B on EnterpriseRAG-Bench. (Source: original paper, Figure 4.)" >}}

- **Other model families** (the paper's cross-model-family table): DeepSeek-V4-Pro goes from 68.02 to 71.11 and MAI-Thinking-1 from 34.06 to 45.07, both the highest. MAI-Thinking-1's tokens actually increase (129.6k to 158.8k), so "fewer tokens" does not hold for every model.
- **Versus traditional retrieval methods** (the paper's retrieval-method comparison table): BM25, dense, HippoRAG, and [GraphRAG](../ragu/) are all lower than CorpusMap. On GPT-5.5 the strongest retrieval method gets 65.05 against CorpusMap's 76.60, and on Luna the strongest gets 61.74 against CorpusMap's 73.20. The paper's explanation is that retrieval-based methods can only answer from "what was retrieved that one time", while an agent can keep gathering more evidence.
- **Significance** (the paper's significance test table): For every baseline and every model, the 95% confidence interval is above 0. The resampling unit is the question, not independent reruns of the whole experiment.
- **Re-evaluation with a different judge** (the paper's judge-swap table): With DeepSeek-V4-Pro as the judge, CorpusMap is still the highest on the five LLM-scored metrics. Kendall's \(\tau\) is the correlation coefficient between two rankings, with 1 meaning identical ordering: Correct., Complete., and Content are 1.00, Fact. is 0.83, and WixQA's Ctx. Rec. is only 0.47.
- **Remaining single-document questions** (the paper's remaining-questions table): On the remaining EnterpriseRAG-Bench questions, which mostly depend on a single document, CorpusMap still wins (GPT-5.5: Correct. 89.05 to 94.76, Tokens 250.7k to 171.7k). The paper does not give the size of this question set.
- **Shared limitation**: Almost all follow-up experiments run only on EnterpriseRAG-Bench.


## Concepts Worth Taking Away

The two concepts below hold independently of this paper.

### Multi-Document and Multi-Hop Are Two Different Kinds of Problem

One-sentence version: multi-document asks "how many documents the answer must combine", while multi-hop asks "must you finish reading the previous document before you know what to look for in the next".

| | multi-hop (chained) | multi-document (this paper's scope) |
| --- | --- | --- |
| Between pieces of evidence | Dependent: read A first to know to look for B | Not necessarily dependent; only requires combining at least two |
| Example (this post) | Atlas -> J. Chen -> Standup | "List all discussion threads about RRB-17" (the question in Table 2) |
| Relationship | A kind of multi-document | Broader scope, covering both chained and parallel |

The paper itself uses the term multi-document. The selection criterion shows this too: EnterpriseRAG-Bench takes only the categories that annotate at least two gold documents per question, among which Conflicting Info (version comparison) and Completeness (gathering everything) are not necessarily chained reasoning.

> **[Inference]** The rule of thumb is to ask yourself "before reading the first document, can I already know what to look for in the second?" If not, it is chained and you must find things step by step. If yes, it is parallel gathering, and the point is to pull everything in one go.
>
> This affects method choice: chained problems need an agent loop (decide the next step after reading), while the bottleneck of parallel gathering is recall, and a good enough index or entity links can grab a whole group at once. In this post, the Atlas example uses an entity as a bridge to shorten a chain, and the RRB-17 example uses an entity to link to a whole group of documents at once; both kinds are handled by the same structure.
>
> It also affects evaluation: when assessing a method, first confirm which kind of question the benchmark contains, or you will conflate the two abilities of "gathering it all" and "reasoning it through".

### Bipartite Graph

One-sentence version: nodes are split into two kinds (two "parts"), and edges appear only between nodes of different kinds. Two nodes of the same kind cannot be connected directly; they are indirectly related through the other-kind nodes they both connect to.

Formally it is the same as the definition in "The Structure of the Map" above, and the more general way to write it is \(L \subseteq E \times D\):

- \(E\): the first kind of node (entities in this post).
- \(D\): the second kind of node (documents in this post).
- \(L\): the set of edges, each with one end in \(E\) and one end in \(D\).

A constructed analogy: students and clubs.

| Node kind | Example |
| --- | --- |
| First kind | Students (Ming, Hua) |
| Second kind | Clubs (Photography Club, Board Game Club) |
| Edge | "Joined": Ming — Photography Club |

There is no "Ming — Hua" edge and no "Photography Club — Board Game Club" edge. But if Ming and Hua both join the Photography Club, they are indirectly connected through it. Mapping to CorpusMap: students are entities (Atlas, J. Chen), clubs are documents (Status Report, Standup), and "joined" means "this document mentions this entity". A quick check: look at any edge, and its two ends must be "one entity and one document". If an "entity — entity" edge appears, it is not a bipartite graph.

Why it is worth learning on its own:

1. **The relationship between two nodes of the same kind can be expressed with "common neighbors".** Two entities are related when their document neighborhoods \(N(e)\) and \(N(e')\) intersect. The earlier entity-entity edge experiment supports this: adding direct edges changed document recall almost not at all while making pages noticeably larger.
2. **It is actually very common in retrieval.** **[Inference]** An inverted index is a "word ↔ document" bipartite graph, a recommender system is "user ↔ item", and authors and papers are "author ↔ paper". CorpusMap's novelty is replacing "word" with "resolved entity", so that different spellings of the same thing are merged.
3. **A rule for choosing.** **[Inference]** If the relationship is only a membership relationship like "mentions" or "belongs to", the details can be written in the page text, a bipartite graph is enough, and the cost is lowest. Only if you need to filter queries by a typed relationship such as "who is the owner" would typed edges be worth considering, and that would have to be separately shown to be worthwhile. This post validated only the first half.


## Conclusion

CorpusMap moves the question of "which documents are related to which" from query-time work redone for every question into a reusable entity-document bipartite graph built once offline. On three benchmarks and four GPT models, its overall quality is the highest with 34% to 57% fewer input tokens, while the other navigation layers do not consistently beat searching the raw documents directly.

A few things to remember when adopting it. Part of the gain comes from "finding the evidence" rather than "answering well", and on benchmarks like HERB whose bottleneck is not retrieval, the benefit is almost nil. The experimental corpora are much smaller than real enterprise corpora, and the follow-up experiments are mostly on EnterpriseRAG-Bench only. Concentrating scattered information on a single page also calls for thinking through the permission question first. The more practical engineering message is that the map can be updated incrementally, built once by a cheap model and reused by an expensive one, and even built with off-the-shelf tools for Extraction, Resolution, and Rendering instead of an LLM.

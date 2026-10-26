# A6: English title truncation audit: 2026-10-23

Plan item A6 (fix one title) plus the request to check every other English title.

## Where the truncation happens (measured, not assumed)

Google cuts titles by pixel width, not by character count. Observed on the live Taiwan results page
(`site:datasciocean.com/en/paper-intro`, 20 results read, 2026-10-23):

| Displayed on Google | Characters | Truncated? |
|---|---|---|
| `Skill Files Bloat as Agents Self-Evolve: Inside SkillZip's Fix` | 62 | no (narrow letters) |
| `WikiSkill: A Skill Memory That Never Gets Rolled Back` | 53 | no |
| `MIRIX: Multi-Agent Memory System for LLM-Based Agents` | 53 | no |
| `SAG: Multi-Hop RAG via Query-Time SQL, Not Offline Graphs` | 57 | no |
| `Cheap LLM Judge First, GPT-6 Only When Unsure` | 45 | no |
| `Can an LLM Write Its Own Playbook From a Manual ...` | 47 shown | yes |
| `Do Agents Need a Map to Search Documents? Inside ...` | 49 shown | yes |
| `HuggingGPT: Solving AI Tasks with ChatGPT and its ...` | 50 shown | yes |
| `Mem0: Building Production-Ready AI Agents with Scalable ...` | 55 shown | yes (loses "Long-Term Memory") |
| `Resource2Skill: Video Alone Beats Code, Articles, Artifacts ...` | 59 shown | yes |

So the visible limit is roughly 47-62 characters depending on the letters. At about 52 characters or
fewer a title is safe; above about 60 it is cut almost always. The site name is not part of what
is shown: the `<title>` tag is "<title> - DataSci Ocean", but Google displays the site name separately.

Consequence: Google cuts at the end, which for these titles is usually the part after the colon.

## Scope of the problem (all 142 English posts, front-matter titles)

| Title length | Posts |
|---|---|
| up to 45 | 14 |
| 46-55 | 31 |
| 56-60 | 16 |
| 61-70 | 33 |
| 71 or more | 48 |

Median 64, longest 125. About 97 of 142 are above 55. The repo's own rule (`hugo-conventions.md`,
"about 50-60 characters where practical") is not being met for most older posts.

Descriptions: median 169 characters; 108 of 142 are above 160. The architecture post's is 255.
Google shows roughly the first 155-160. Not changed here.

## Where it matters (traffic-weighted)

Among the 135 English article pages with impressions in the 90-day data, 94 have titles longer than 55
characters and they carry 65% of those pages' impressions. Pages with at least 800 impressions, average
position 14 or better, and a title above 55 characters (most to least impressions):

| Impr | Clk | Pos | Len | Page | Current title |
|---|---|---|---|---|---|
| 7,948 | 34 | 13.2 | 73 | `other/what-is-computer-architecture` | Computer Architecture Explained: The Bridge Between Software and Hardware |
| 7,035 | 7 | 10.0 | 72 | `paper-intro/mem0` | Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory |
| 5,126 | 38 | 7.8 | 88 | `other/fastapi-race-condition` | The Concurrency Trap in FastAPI: From Race Conditions to Deadlocks with Global Variables |
| 3,741 | 2 | 12.2 | 66 | `other/yarn` | A Beginner's Guide to Yarn: The Fast and Secure Alternative to NPM |
| 3,577 | 15 | 8.3 | 66 | `ai-concept/claude-code` | Claude Code Concepts: Agentic Loop, Tools, Skills, and Permissions |
| 3,469 | 2 | 7.4 | 68 | `paper-intro/sparse-upcycling` | Sparse Upcycling: Training Mixture-of-Experts from Dense Checkpoints |
| 3,192 | 2 | 8.4 | 88 | `paper-intro/mem-rl` | Beyond Fine-Tuning: How MemRL Enables Self-Evolving AI Agents via Reinforcement Learning |
| 3,059 | 25 | 7.3 | 58 | `other/pytorch-apple-silicon-m1-gpu` | Running PyTorch on Apple Silicon: Enabling M1 GPU Training |
| 3,019 | 13 | 9.4 | 96 | `ai-concept/llm-fine-tuning-rlhf` | The 3 Stages of LLM Training: A Deep Dive into Reinforcement Learning from Human Feedback (RLHF) |
| 2,336 | 14 | 8.4 | 89 | `paper-intro/adaptive-k` | Beyond Top-k: How Adaptive-k Dynamically Selects the Best Context for RAG Without Latency |

(Ten more pages with 844-2,253 impressions follow the same pattern: `onnx-profile-shape-inference`,
`dynamic-cheatsheet`, `plan-and-act`, `universal-rag`, `agentopt`, `cerebras-rag`, `hugginggpt`, `dream-rsi`,
`octo-tools`, `verbalized-sampling`.)

## What was changed

Only the first row: `content/posts/other/what-is-computer-architecture/index.en.md`

- `title`: `Computer Architecture Explained: The Bridge Between Software and Hardware`
  -> `Computer Architecture vs Computer Organization` (46 characters, fits).
- `lastmod`: 2025-10-16 -> 2026-10-23 (convention for touch-ups to a live post).
- Why this wording: it still starts with the head term, and it is the exact phrase of the query where we
  rank #1 in Taiwan (A7). The "bridge between software and hardware" angle stays in the description.
- Verified: `verify_post.py` passes (only pre-existing warnings); a local Hugo build renders
  `<title>Computer Architecture vs Computer Organization - DataSci Ocean</title>`; canonical and
  hreflang unchanged.

## Draft rewrites for the next five (NOT applied; check each against its article first)

| Page | Draft | Len |
|---|---|---|
| `paper-intro/mem0` | Mem0: Scalable Long-Term Memory for AI Agents | 45 |
| `other/fastapi-race-condition` | FastAPI Race Conditions with Global Variables | 45 |
| `other/yarn` | Yarn Beginner's Guide: A Fast Alternative to NPM | 48 |
| `paper-intro/sparse-upcycling` | Sparse Upcycling: MoE from Dense Checkpoints | 44 |
| `paper-intro/mem-rl` | MemRL: Self-Evolving AI Agents with Episodic Memory | 51 |

## Caveats

- Expected lift is modest. Pages ranking 7-13 gain a clearer snippet, but the English pages in the
  US sit near position 23 where title width hardly matters. The bigger gain is where position is good:
  `fastapi-race-condition` (7.8), `claude-code` (8.3), `pytorch-apple-silicon-m1-gpu` (7.3).
- A changed title can move rankings in either direction. Change a few, record dates in `log.md`, and
  compare 28 days against the previous 28 before changing more.
- The pixel measurement comes from one results page in one locale; treat 52 as a safe target, not a law.

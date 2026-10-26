# A2: what the Taiwan search results page actually looks like: 2026-10-23

Plan item A2, step 1. Question: why do generic concept queries rank in the top 5-8 but convert at 0.4-3%
(`dpo`, `dropout`, `計算機結構`, English `computer architecture`)? Is it the title/description?

## Method and limits

- Opened Google with `gl=tw&hl=zh-TW` in the author's own Chrome (Claude in Chrome), read the full page
  text of each results page. No captcha. One visit per query, 2026-10-23.
- The browser was signed in to Google, so results may be lightly personalized, and Google showed the
  author's own Search Console panel on the page (private to them). Treat positions here as a snapshot,
  not as the GSC average.
- "Organic position" below counts organic blue links; blocks above them (AI Overview, video carousel,
  image pack) push the result lower on screen than its number suggests.

## Findings per query

### `dpo`: intent is split, and an AI Overview sits on top
- AI Overview first, covering **two meanings**: Direct Preference Optimization and Data Protection Officer.
- Organic order: arXiv, **us (#2)**, Zhihu, Wikipedia (Data protection officer), HackMD, a Taiwanese
  data-protection firm article, CSDN, Substack. Two of the first seven results are not about AI.
- Related searches: `dpo 是什麼`, `dpo llm`, `dpo rl`, `dpo trainer`, `dpo github`, `DPO dataset`, `dpo 醫學`.
- Reading: the 1.4% CTR at position 4.0 is explained mostly by the ambiguous query plus the AI Overview,
  not by our snippet. Our result looks healthy: full title, dated snippet, and four jump-link sitelinks.
- Google's panel for the site on this query (last 7 days): 3 clicks, 139 impressions, position 6.8.

### `dpo 是什麼`: we are #2 and the field is easy
- No AI Overview, no intent split. Results are all AI-related Chinese pages.
- Order: AITerms.tw, **us (#2)**, Zhihu, Threads, XTuner docs, a blog, qianwenai, AWS docs, HackMD.
- Related searches: `dpo 算法`, `dpo 和 ppo 的区别`, `dpo rlhf`, `dpo ppo`, `grpo vs dpo`, `ppo dpo grpo 详解`.

### `dropout`: ordinary, fine
- Order: Medium, Wikipedia, **us (#3)**, dropout.tv (a comedy network), another Medium post, AITerms.tw, iT 邦幫忙, d2l.
- Some intent noise (`dropout anime`, `dropout 動畫` in related searches), but mostly the ML meaning.
- Our snippet shows an updated date (2026-07-20) and four sitelinks. Google's panel (28 days): 8 clicks,
  196 impressions, position 7.5 (about 4% CTR). No copy problem visible.

### `計算機結構`: course-notes intent
- Order: HackMD notes, NTHU OCW course, **us (#3)**, Dcard, HackMD, then a YouTube video carousel,
  a YouTube course, a bookstore.
- The searcher is mostly a student looking for a university course or lecture notes. Our article is a
  concept comparison, a partial match. 2.3% CTR at position 5.0 is reasonable here.

### English `computer architecture`: structurally crowded
- Order: Wikipedia, **a YouTube carousel with "key moments"**, more videos, then **us**, NTU course page,
  an **image pack**, a bookstore, NCKU wiki, NTHU OCW. Textbook/PDF intent dominates the related searches.
- Our English title is **truncated on the page**: "Computer Architecture Explained: The Bridge ...".
- 0.4% CTR at an average position near 4.7 follows from the videos and images above it. Last 7 days
  impressions for this query on the site: 454, down 82% (Google's panel).

### `computer organization vs computer architecture`: the winnable one
- **Our Chinese article is #1**, ahead of GeeksforGeeks, University of Vermont, CompilerSutra, Scribd, Reddit.
  The result carries sitelinks for "Computer Architecture vs...". The English version does not appear;
  Google shows the Chinese page for this English query.
- Related searches: `difference between computer organization and computer Architecture with example`,
  `computer architecture and organization notes`, `what is computer architecture`.

## Conclusions

1. The low CTR on generic head queries is mostly **SERP structure and intent**, not weak copy:
   AI Overview and a second meaning (`dpo`), video and image blocks (`computer architecture`),
   course-notes intent (`計算機結構`). Rewriting titles for these is unlikely to move much.
2. Our snippets are in good shape. One concrete defect: the English `what-is-computer-architecture`
   title is cut off.
3. The better targets are the **long-tail and comparison queries Google itself suggests**, where we
   already rank #1-2 and the field is weaker (`dpo 是什麼`, `computer organization vs computer architecture`).
4. Content gap, checked in the repo: `paper-intro/dpo` (zh) is about 3,800 characters with five sections
   (前言, 為什麼需要 RLHF, RLHF 有什麼問題, DPO, 結語). It mentions PPO once, GRPO and TRL zero times,
   and has no section on the loss/derivation. Google's related searches for DPO are exactly
   `dpo ppo 區別`, `grpo vs dpo`, `dpo 算法`, `dpo trainer`. We rank #2 despite a short article, so extending
   it is the cheapest content win found so far.

## Not answered

- Whether the AI Overview for `dpo` cites us. Not visible in the page text.
- Whether the English page for `computer architecture` would gain from a shorter title; CTR is likely
  capped by the blocks above it either way.

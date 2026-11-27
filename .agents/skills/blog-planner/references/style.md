# Style: prose that does not read as generated

`planner-guide.md` says what a post must do for a newcomer; this file says what to keep out of its sentences. A
reader who spots the tells below stops trusting the writing, even when every fact is right. The categories are
adapted from the `unslop` skill (github.com/theclaymethod/unslop, MIT), rewritten for Taiwan Traditional Chinese
and for this site's readers. `scripts/style_scan.py` flags the countable ones (`validate_plan.py` prints them as
warnings); the rest are for your own pass and for the Reader Reviewer.

## How to use this (read first)

- **A hit is a reason to look, not a reason to change.** Fix a sentence only when you can say what the pattern
  hides, repeats or inflates. A literal use is fine ("先看 A 再看 B" inside a worked procedure is a procedure).
- **Cut repetition, not explanation.** Our readers are newcomers (`planner-guide.md` §1). A term explained on first
  use is not over-explaining; the same term explained three times is.
- **Style never outranks substance** (`SKILL.md` rule 2). A hedge, a 「我的推論」 label or a caveat can be moved
  and merged, never deleted or weakened to make a sentence crisper.
- **Edit only what is wrong.** Rewriting a fine paragraph for style is how new tells get in.

## 1. Structure: preview, recap, repeat

The most visible tell is a post that announces what it will say, says it, then says what it said, at every level.

- **No route paragraph that mirrors the headings** (「接下來先看…，再看…，最後…」). The headings and the TOC already
  show the route. If the reader needs orientation, give a *reason* for the order ("the result only makes sense
  once you know who built the baseline"), not a list of it.
- **No section recap by default, and never a 「小結：」/"In short:" label.** Close a section with a recap only when the
  section is long (more than about six blocks) or turns on a subtle point, and the recap *adds* something: the
  consequence, the link to the next section, what to doubt. A recap that restates the section's first sentence is
  cut.
- **Say the verdict twice at most**: once on the first screen, once in the closing section in new words. In between,
  sections may build on it with new evidence; they do not restate it. (The Is-Bash post said 「方向可信、幅度要打折」
  four times, plus a callout titled the same.)
- **Headings state the section's own point**, not a slice of the intro's outline.
- **Not every paragraph opens with a connective** (「另外」「此外」「接著」「因此」/"Also", "Next", "However").
  Open on the claim.

## 2. Sentences: scaffolding, meta-commentary, false drama

Cut the phrase and lead with the content.

| Pattern | zh examples | en examples |
|---|---|---|
| Announcing instead of saying | 先講結論、一句話總結、簡單來說、換句話說、說白了、總的來說、綜上所述 | In summary, In other words, Simply put, The bottom line |
| Throat-clearing / steering | 先退一步看、值得注意的是、值得一提的是、順帶一提、不難發現、讓我們來看看 | It's worth noting, Let's take a step back, Here's the thing |
| Narrating the reading | 看完數字，回頭評估、如前所述、正如前面提到 | As mentioned, Now that we've seen, We'll look at |
| Inflation | 至關重要、扮演著關鍵角色、劃時代、革命性、顛覆、無縫 | pivotal, crucial, landscape, game-changer, a testament to |
| Manufactured contrast | 不是 X，而是 Y (more than about twice a post) | not X, but Y; isn't X; it's Y |
| Colon reveal / slogan | 結果：一句話。代價：一句話。 | The result: alignment. The cost: trust. |
| Dash glue | —— between clauses | — between clauses |
| Question then instant answer | **統計上站得住嗎？** 下表… (once is a signpost; as a habit it is a template) | So does it hold up? Yes. |
| Parenthetical hedge | （原文語氣為「可能」） after every sentence | (arguably…), (and, increasingly, …) |

A paper's hedge must survive, but say it inside the sentence once ("論文作者推測…", "the authors suggest…") instead
of a trailing parenthesis.

## 3. Lists, tables and bold

- **Do not announce a count** (「優點有四個：」「缺點有三個，第一個最…」/"Three key takeaways:"). Let the list show its
  length. A count is fine when it is itself information ("five interfaces", the paper's own number).
- **Bold-lead lists** (`- **控制變因乾淨**：…`) are for genuinely parallel categories a reader will scan. A post where
  most lists are bold-lead reads as a slide deck. The scan warns above 40% of list items.
- **A table compares**: rows of the same kind across the same columns. A two-column "名詞 / 意思" table that repeats
  definitions the prose already gives, or a table of one row, is prose in disguise.
- **One home per piece of data and per definition.** A number set shown as a paper image is not retyped next to it
  (`planner-guide.md` §5 has the rule and the validator enforces it). A term defined in the opening is not defined
  again in a glossary table and again in a later table; re-anchor it in a few words instead.
- **Bold in prose** marks the one phrase a skimmer must not miss in that paragraph, not every term.

## 4. Voice and source labels

The labels that say who is speaking (「論文作者」「我的推論」「論文未說明」「一般知識」「自編例子」) are substance and stay.
How often they appear is expression:

- **Label once per block.** If a whole paragraph is the Writer's inference, open it with 「我的推論是」 and do not tag
  each sentence. The scan warns at three or more labels in one block.
- **Gather related inferences** into one labelled callout instead of scattering them (`planner-guide.md` §3).
- **A legend of the labels** ("文中的來源標示") is meta-commentary: if the post needs one, it is a short note at the
  end, not a callout before the argument starts.

## 5. Rhythm and register

- Vary sentence length. Three sentences of the same shape in a row (「X 是…。Y 是…。Z 是…。」) is a template.
- The post may have a stance; the review section usually does. State it plainly once, with its reason, instead of
  every paragraph landing at the same polished confidence.
- Concrete verbs and actors: 「agent 把 500 筆結果全讀進上下文」, not 「造成上下文負擔」.

## 6. Before and after (from the Is-Bash-All-You-Need post)

| Before | Why | After |
|---|---|---|
| 小結：Q1 的答案是「贏，四組都贏」；但贏最多的那一邊，正好是基準線由論文作者自製的那一邊。 | label; restates the section, but the second half is new, so keep that half as the closing sentence | 贏最多的那一邊，正好是基準線由論文作者自製的那一邊。 |
| 看完數字，回頭評估這份證據。整體來說，這是一篇有用但結論要打折的實證比較… | narrating the reading, then the fourth restatement of the verdict | open on the first concrete strength or weakness |
| 優點有四個： | count announced | (drop; the list follows) |
| 一句話總結：**這是一份「方向可用、幅度不可直接搬」的實證比較。** | announcing; the callout's own title already says it | (cut the sentence) |

## 7. Self-check (adapted from unslop's rubric)

Before the first Reviewer, read three sections aloud and ask:

- **Directness**: does each section open with its point?
- **Reader trust**: is anything explained twice, or a conclusion spelled out that the reader just watched happen?
- **Density**: which sentence could go with no loss? (scaffolding, restated verdicts, labels on every line)
- **Template**: would the outline fit any paper (intro / setup / result / result / result / review / recap)? Does
  every section end the same way?

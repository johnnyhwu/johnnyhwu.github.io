#!/usr/bin/env python3
"""Style warnings for a plan: the patterns that make a post read as generated (`references/style.md`).

The categories are adapted from the `unslop` skill (github.com/theclaymethod/unslop, MIT): template scaffolding,
preview/recap symmetry, meta-commentary, manufactured contrast, count-announced lists, bold-lead listicles, label
clutter. Its scanners are English-only, so the zh patterns here are our own. Every finding is a WARNING: a hit is a
reason to look, never a reason to change a sentence by itself (style.md, "How to use the scan").

Usage: style_scan.py <post.zh.json|post.en.json>      (validate_plan.py also runs it at the draft stage)
"""
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plan_lib as L  # noqa: E402

ZH = {
    "recap_label": re.compile(r"^\s*(\*\*)?(小結|總結|一句話總結|重點整理|結論)(\*\*)?\s*[：:]"),
    "scaffold": ["先講結論", "一句話總結", "一句話來說", "順帶一提", "先退一步", "值得注意的是", "值得一提的是",
                 "不難發現", "總的來說", "綜上所述", "總而言之", "簡單來說", "換句話說", "說白了", "讓我們",
                 "我們來看看", "接下來我們", "下面我們", "本文將", "本節將", "如前所述", "正如前面提到",
                 "毫無疑問", "不可否認", "至關重要", "扮演著", "賦能", "劃時代", "革命性", "無縫",
                 "深入探討", "一探究竟", "帶你", "看完數字", "回頭評估"],
    "contrast": re.compile(r"不是[^，。；！？\n]{1,24}[，,]\s*而是|不只是[^，。；\n]{1,24}[，,]\s*更是"),
    "count_decl": re.compile(r"(有|分成|包括|分為)[一二三四五六七八九十兩\d]+(個|點|項|種|件|條)[^。\n]{0,6}[：:]"),
    "labels": re.compile(r"我的推論|我的推測|論文作者|論文未說明|論文沒有說明|論文沒說|一般知識|自編例子|原文語氣"),
    "route": re.compile(r"(先看|先講|首先).{0,60}(再看|接著|然後).{0,60}(最後|最終)"),
    "dash": "——",
}
EN = {
    "recap_label": re.compile(r"^\s*(\*\*)?(In short|Recap|Summary|In summary|Takeaway|Bottom line|The short version)"
                              r"(\*\*)?\s*:", re.I),
    "scaffold": ["in summary", "to summarize", "in conclusion", "in other words", "to put it simply", "simply put",
                 "it's worth noting", "it is worth noting", "worth mentioning", "let's ", "let us ", "here's the thing",
                 "bottom line", "at its core", "when it comes to", "a testament", "delve", "pivotal", "landscape",
                 "seamless", "unlock", "game-changer", "game changer", "plays a key role", "plays a crucial role",
                 "first things first", "spoiler", "plot twist", "we'll look at", "we will look at", "as mentioned",
                 "step back"],
    "contrast": re.compile(r"\bnot (just |only |merely )?[^.,;\n]{1,30}, but\b|\bisn't [^.;\n]{1,30}[;:] it's\b", re.I),
    "count_decl": re.compile(r"\b(two|three|four|five|six|\d) (things|reasons|strengths|weaknesses|points|takeaways|"
                             r"lessons|problems|questions)\b[^.\n]{0,20}:", re.I),
    "labels": re.compile(r"my inference|my guess|the paper does not say|the paper doesn't say|general knowledge|"
                         r"made-up example|the paper's authors", re.I),
    "route": re.compile(r"\b(first|we start)\b.{0,80}\b(then|next)\b.{0,80}\b(finally|last)\b", re.I),
    "dash": "—",
}
BOLD_LEAD_RE = re.compile(r"^\s*\*\*[^*]{1,40}\*\*\s*[：:]")


def _texts(b):
    """Prose a reader reads as sentences (tables, code, diagrams and captions excluded)."""
    t = b.get("type")
    if t in ("paragraph", "callout"):
        return [b.get("text", "")]
    if t == "list":
        return list(b.get("items", []))
    return []


def scan(plan, lang):
    """Return a list of warning strings."""
    P = EN if lang == "en" else ZH
    order = L.ordered_blocks(plan)
    out = []
    recap_blocks = [b["id"] for b in order for s in _texts(b)[:1] if P["recap_label"].match(s)]
    if recap_blocks:
        out.append(f"style: {len(recap_blocks)} block(s) open with a recap label ({', '.join(recap_blocks[:6])}); "
                   "a recap earns its place only by adding something, and never needs the label (style.md §1)")
    hits, first = Counter(), {}
    prose = [(b, s) for b in order for s in _texts(b)]
    for b, s in prose:
        low = s.lower() if lang == "en" else s
        for ph in P["scaffold"]:
            n = low.count(ph)
            if n:
                hits[ph] += n
                first.setdefault(ph, b["id"])
    if hits:
        listed = ", ".join(f"{ph.strip()!r}×{n} ({first[ph]})" for ph, n in hits.most_common(10))
        out.append(f"style: scaffolding / meta phrases: {listed}; cut the phrase and lead with the content (style.md §2)")
    contrast = [b["id"] for b, s in prose for _ in P["contrast"].finditer(s)]
    if len(contrast) >= 3:
        out.append(f"style: {len(contrast)} 'not X, but Y' contrasts ({', '.join(contrast[:6])}); keep the ones that "
                   "correct a real misreading (style.md §2)")
    for b, s in prose:
        m = P["count_decl"].search(s)
        if m:
            out.append(f"style: {b['id']}: count-announced list {m.group(0)!r}; let the list show its length (style.md §3)")
    items = [s for b in order if b.get("type") == "list" for s in b.get("items", [])]
    bold = sum(1 for s in items if BOLD_LEAD_RE.match(s))
    if bold >= 8 and bold > 0.4 * len(items):
        out.append(f"style: {bold} of {len(items)} list items start with a bold label; keep bold leads for genuinely "
                   "parallel categories (style.md §3)")
    for b, s in prose:
        n = len(P["labels"].findall(s))
        if n >= 3:
            out.append(f"style: {b['id']}: {n} voice/source labels in one block; label the block once, or gather the "
                       "inferences into one labelled callout (style.md §4)")
    if order:
        top = order[0].get("section")
        for b, s in prose:
            if b.get("section") == top and P["route"].search(s):
                out.append(f"style: {b['id']}: a route paragraph that previews the sections; the headings already do "
                           "that (style.md §1)")
                break
    tables = sum(1 for b in order if b.get("type") == "table")
    if tables >= 12:
        out.append(f"style: {tables} tables; check that each one compares something the prose cannot (style.md §3)")
    dashes = sum(s.count(P["dash"]) for _, s in prose)
    if dashes >= 3:
        out.append(f"style: {dashes} dashes ({P['dash']}) in prose; use a comma, colon or a new sentence (style.md §2)")
    return out


def check(r, plan, lang):
    for w in scan(plan, lang):
        r.warn(w)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = sys.argv[1]
    plan = L.load(path)
    lang = "en" if path.endswith(".en.json") else "zh-tw"
    ws = scan(plan, lang)
    for w in ws:
        print("WARN:  " + w)
    print(f"{len(ws)} style warning(s) [{lang}]")


if __name__ == "__main__":
    main()

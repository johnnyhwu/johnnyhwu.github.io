#!/usr/bin/env python3
"""One-page summary of a plan, for the author to review (not for the Reviewers).

  brief.py <post.zh.json> [--article article.md] [--out skeleton.md]

Works on a skeleton (meta + outline + ledger, no blocks yet) and on a full draft. It leads with what the author
must decide (what was folded, dropped or reworded, what the Planner added on its own), then the story: title
candidates, hook, the three takeaways and the outline with where every detail was placed.
"""
import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plan_lib as L  # noqa: E402


def attention(plan, ledger):
    """Decisions grouped by (kind, reason, whether the author must decide), so seven identical 'this guess moved to
    the deep-dives' decisions read as one line with seven items, not seven lines."""
    groups = {}
    for d in plan.get("decisions", []):
        groups.setdefault((d["kind"], d["why"], bool(d.get("needs_human"))), []).append(d["ledger"])
    out = []
    for (kind, why, human), lids in sorted(groups.items(), key=lambda kv: (not kv[0][2], kv[0][0])):
        flag = "NEEDS YOUR CALL" if human else "fyi"
        out.append(f"- **{kind}** x{len(lids)} [{flag}]: {why}")
        shown = lids if human else lids[:3]
        for lid in shown:
            it = ledger.get(lid, {})
            out.append(f"  - `{lid}` ({it.get('kind', '?')}, {it.get('layer', '?')}): {it.get('gist', '')}")
        if len(shown) < len(lids):
            out.append(f"  - ... and {len(lids) - len(shown)} more like it")
    decided = {d["ledger"] for d in plan.get("decisions", [])}
    for it in ledger.values():
        if it.get("kind") in ("caveat", "inference") and it.get("layer") in ("fold", "appendix") and it["id"] not in decided:
            out.append(f"- **demoted without a decision** `{it['id']}` ({it['kind']}): {it['gist']}")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan")
    ap.add_argument("--article")
    ap.add_argument("--out")
    a = ap.parse_args()
    plan = L.load(a.plan)
    m = plan["meta"]
    ledger = {it["id"]: it for it in plan.get("ledger", [])}
    out = [f"# Brief: {m['slug']}", ""]

    att = attention(plan, ledger)
    out += ["## Needs your attention", ""] + (att or ["- nothing folded, dropped or reworded"]) + [""]

    out += ["## Hook and title", "",
            f"- **Title:** {m['title']}"]
    out += [f"- alt: {t}" for t in m.get("title_alts", [])]
    out += [f"- **Description:** {m['description']}",
            f"- **Hook ({m['hook']['kind']}):** {m['hook']['text']}",
            f"- **Reader:** {m['reader']['persona']} — promise: {m['reader']['promise']}"]
    if m.get("running_example"):
        out.append(f"- **Running example:** {m['running_example'].get('desc', '')}")
    out += [f"- **Cover idea:** {m['cover_brief']['metaphor']}", ""]
    if m.get("seo"):
        out += [f"- **SEO notes:** {m['seo'].get('notes', '')} (queries: {', '.join(m['seo'].get('queries', []))})", ""]

    out += ["## Takeaways", ""]
    for t in m["takeaways"]:
        out.append(f"- **{t['id']}** {t['text']}" + (f"  _(memory hook: {t['memory_hook']})_" if t.get("memory_hook") else ""))
    out.append("")

    out += ["## Outline (where each detail went)", ""]
    by_section = {}
    for it in ledger.values():
        by_section.setdefault(it.get("section"), []).append(it)
    for node, depth in L.outline_nodes(plan["outline"]):
        items = by_section.get(node["id"], [])
        layers = Counter(i["layer"] for i in items)
        mix = ", ".join(f"{k} {v}" for k, v in sorted(layers.items())) or "no details"
        serves = ",".join(node.get("serves", []))
        out.append("  " * (depth - 1) + f"- **{node['title']}** [{node['role']}] → {serves}: {node.get('goal', '')}  ({mix})")
        for it in items:
            if it["layer"] == "fold":
                out.append("  " * depth + f"- _fold_ `{it['id']}` {it['gist']}")
    out.append("")

    blocks = [b for b, _ in L.iter_blocks(plan.get("blocks", []))]
    if blocks:
        by_layer = Counter(b["layer"] for b in blocks)
        main_chars = sum(len(s) for b in blocks if b["layer"] == "main" for s in L.block_text(b, with_code=False))
        out += ["## Draft stats", "",
                f"- {len(blocks)} blocks: " + ", ".join(f"{k} {v}" for k, v in sorted(by_layer.items())),
                f"- main line: about {main_chars} characters (roughly {max(1, round(main_chars / 400))} min at 400 chars/min)"]
        ed = [b for b in blocks if b["origin"] == "editorial"]
        out += [f"- {len(ed)} editorial block(s) the Planner added:"]
        for b in ed:
            txt = " ".join(L.block_text(b, with_code=False))[:70]
            out.append(f"  - `{b['id']}` ({b['type']}{', illustrative' if b.get('illustrative') else ''}): {txt}")
        out.append("")
    elif a.article:
        art = L.Article(a.article)
        out += ["## Coverage", "", f"- {len(ledger)} ledger items over {len(art.lines)} article lines", ""]

    text = "\n".join(out)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {a.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()

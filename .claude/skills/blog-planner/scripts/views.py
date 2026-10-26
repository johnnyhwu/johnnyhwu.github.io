#!/usr/bin/env python3
"""Make the files a Reviewer reads, from the plan JSON. The Reviewers never see the JSON itself.

  views.py reader   <plan.json> [--delta delta.json] [--out file]
      What a reader sees: title, description, headings and blocks as plain markdown. No ledger, no source text.
      Each block is tagged ⟦id⟧ so a finding can point at it; ignore the tags when reading as a reader.
  views.py fidelity <plan.json> --article <article.md> [--delta delta.json] [--out file]
      For the fidelity check: each block next to the verbatim article.md lines of the ledger items it cites, plus
      the decisions, and any ledger item that lands in no block, with its source lines.

Without --delta the view is the whole post (round 1). With --delta ({"round": 2, "changed": ["s3.b2", ...]}) it is
the outline plus each changed block with one neighbour on each side, which is all a later round needs.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plan_lib as L  # noqa: E402


def tree_lines(node, depth=0):
    out = ["  " * depth + "- " + node.get("label", "")]
    for c in node.get("children", []):
        out += tree_lines(c, depth + 1)
    return out


def block_view(b):
    t = b["type"]
    if t == "paragraph":
        return b["text"]
    if t == "list":
        return "\n".join((f"{i}. {x}" if b.get("ordered") else f"- {x}") for i, x in enumerate(b["items"], 1))
    if t == "table":
        rows = ["| " + " | ".join(b["headers"]) + " |", "| " + " | ".join("---" for _ in b["headers"]) + " |"]
        rows += ["| " + " | ".join(str(c) for c in r) + " |" for r in b["rows"]]
        return "\n".join(rows)
    if t == "formula":
        return "$$\n" + b["latex"] + "\n$$"
    if t == "figure":
        return f"[Figure: {b['alt']}]\nCaption: {b['caption']}"
    if t == "callout":
        return f"> [{b['tone']} callout — {b['title']}]\n> " + b["text"].replace("\n", "\n> ")
    if t == "fold":
        inner = "\n\n".join(f"⟦{c['id']}⟧ " + block_view(c) for c in b["children"])
        return (f"[COLLAPSED section, closed by default, the reader must click to open: \"{b['title']}\"]\n"
                + "\n".join("  | " + ln for ln in inner.split("\n")))
    if t == "diagram":
        if b["kind"] == "flow":
            names = {n["id"]: n["label"] for n in b["nodes"]}
            return "[Diagram: flow]\n" + "\n".join(
                f"  {names[e['from']]} -> {names[e['to']]}" + (f" ({e['label']})" if e.get("label") else "")
                for e in b["edges"])
        return f"[Diagram: {b['kind']}]\n" + "\n".join(tree_lines(b["tree"]))
    if t == "code":
        return "```" + b.get("lang", "") + "\n" + b["code"] + "\n```"
    return ""


def outline_view(plan):
    out = []
    for node, depth in L.outline_nodes(plan["outline"]):
        n = sum(1 for b in L.ordered_blocks(plan) if b.get("section") == node["id"])
        out.append("  " * (depth - 1) + f"- {node['title']}  ({n} blocks)")
    return "\n".join(out)


def sections_of(plan):
    sec = {}
    for node, depth in L.outline_nodes(plan["outline"]):
        sec[node["id"]] = (node, depth)
    return sec


def flat_with_context(plan, changed):
    """Reading-order blocks to show: every changed block plus one neighbour each side."""
    order = L.ordered_blocks(plan)
    idx = {b["id"]: i for i, b in enumerate(order)}
    keep = set()
    for cid in changed:
        i = idx.get(cid)
        if i is None:
            continue
        keep.update({max(0, i - 1), i, min(len(order) - 1, i + 1)})
    return [order[i] for i in sorted(keep)]


def header(plan):
    m = plan["meta"]
    return f"# {m['title']}\n\n> {m['description']}\n"


def reader(plan, delta=None):
    secs = sections_of(plan)
    if delta:
        out = [f"ROUND {delta.get('round', '?')} — changed blocks only. Outline of the whole post:\n",
               outline_view(plan), ""]
        changed = set(delta["changed"])
        last_sec = None
        for b in flat_with_context(plan, delta["changed"]):
            if b.get("section") != last_sec and b.get("section") in secs:
                out.append(f"\n--- section: {secs[b['section']][0]['title']} ---")
                last_sec = b.get("section")
            mark = ">>> CHANGED " if b["id"] in changed else ""
            out.append(f"{mark}⟦{b['id']}⟧ " + block_view(b) + "\n")
        return "\n".join(out)
    out = [header(plan)]
    blocks = plan.get("blocks", [])
    for node, depth in L.outline_nodes(plan["outline"]):
        out.append("#" * (depth + 1) + " " + node["title"] + "\n")
        for b in blocks:
            if b.get("section") == node["id"]:
                out.append(f"⟦{b['id']}⟧ " + block_view(b) + "\n")
    return "\n".join(out)


def fidelity(plan, article, delta=None):
    ledger = {it["id"]: it for it in plan.get("ledger", [])}

    def src(lid):
        it = ledger[lid]
        a, b = it["src"]["lines"]
        text = "\n".join(article.lines[a - 1:b])
        return f"   [{lid} · {it['kind']} · layer {it['layer']} · article.md L{a}-{b}] gist: {it['gist']}\n" + \
               "\n".join("   | " + ln for ln in text.split("\n"))

    out = []
    decisions = plan.get("decisions", [])
    if decisions:
        out.append("DECISIONS the Planner recorded:")
        for d in decisions:
            out.append(f"  {d['id']} {d['kind']} {d['ledger']} (needs_human={bool(d.get('needs_human'))}): {d['why']}")
        out.append("")
    unplaced = [it for it in ledger.values() if it["kind"] != "nav" and not it.get("dest")]
    if unplaced:
        out.append("LEDGER ITEMS THAT LAND IN NO BLOCK (check the dropped decision is justified):")
        out += [src(it["id"]) for it in unplaced]
        out.append("")
    if delta:
        out.append(f"ROUND {delta.get('round', '?')} — changed blocks only.\n")
        shown = flat_with_context(plan, delta["changed"])
        changed = set(delta["changed"])
    else:
        shown = L.ordered_blocks(plan)
        changed = set()
    for b in shown:
        mark = ">>> CHANGED " if b["id"] in changed else ""
        out.append(f"{mark}⟦{b['id']}⟧ type={b['type']} layer={b['layer']} origin={b['origin']} "
                   f"ledger={b.get('ledger', [])}")
        out.append(block_view(b))
        if b["origin"] == "editorial":
            out.append("   (editorial: must assert nothing about the paper that the source does not)")
        for lid in b.get("ledger", []):
            if lid in ledger:
                out.append(src(lid))
        out.append("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("view", choices=["reader", "fidelity"])
    ap.add_argument("plan")
    ap.add_argument("--article")
    ap.add_argument("--delta")
    ap.add_argument("--out")
    a = ap.parse_args()
    plan = L.load(a.plan)
    delta = json.loads(Path(a.delta).read_text(encoding="utf-8")) if a.delta else None
    if a.view == "reader":
        text = reader(plan, delta)
    else:
        if not a.article:
            ap.error("fidelity needs --article")
        text = fidelity(plan, L.Article(a.article), delta)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {a.out} ({len(text)} chars)")
    else:
        print(text)


if __name__ == "__main__":
    main()

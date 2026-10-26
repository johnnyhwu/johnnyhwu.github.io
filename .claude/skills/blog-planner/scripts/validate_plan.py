#!/usr/bin/env python3
"""Zero-token gate for a Planner's JSON (schema `post-plan/1`), run before any Reviewer sees it.

It checks structure and fidelity mechanically, so the Reviewers can spend their attention on judgement:
  - schema: required fields, enums, unique ids, every reference resolves
  - ledger coverage: every knowledge line of article.md belongs to some ledger item; every ledger item lands in a
    block (or carries an explicit `dropped` decision); caveats and inferences are never demoted silently
  - numbers: every number in article.md appears in the post (or its line is waived by a decision); an editorial
    block may not introduce a new number unless it is marked `illustrative`
  - glossary: a defined term is not used before the block that defines it
  - hygiene: no `$` imbalance, no hand-numbered headings, no half-width punctuation in zh text, no CJK in en text
  - parity (en): same block ids, types, ledger refs, figures and per-block numbers as the zh plan

Usage:
  validate_plan.py <post.zh.json> --article <article.md> --manifest <image-manifest.json> [--stage skeleton|draft]
  validate_plan.py <post.en.json> --zh <post.zh.json> --article <article.md> --manifest <...>
Exit 0 = no errors (warnings are printed), 1 = errors.
"""
import argparse
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plan_lib as L  # noqa: E402

HALF_WIDTH_PUNCT_RE = re.compile(r"[一-鿿][,;:]|[,;:][一-鿿]|[一-鿿][?!](?!\S)|(?<!\S)[?!][一-鿿]")
MANUAL_NUMBER_RE = re.compile(r"^\s*(\d+(\.\d+)*[\.\s、]|[一二三四五六七八九十]+、)")
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def err(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)


def need(r, d, key, typ, where):
    if not isinstance(d, dict) or key not in d:
        r.err(f"{where}: missing '{key}'")
        return None
    v = d[key]
    if not isinstance(v, typ):
        r.err(f"{where}.{key}: expected {typ.__name__ if isinstance(typ, type) else typ}, got {type(v).__name__}")
        return None
    return v


def check_meta(r, plan, lang):
    meta = need(r, plan, "meta", dict, "plan")
    if meta is None:
        return
    sec = need(r, meta, "section", str, "meta")
    if sec and sec not in L.SECTIONS:
        r.err(f"meta.section '{sec}' is not one of {sorted(L.SECTIONS)}")
    slug = need(r, meta, "slug", str, "meta")
    if slug and not SLUG_RE.match(slug):
        r.err(f"meta.slug '{slug}' must be lowercase-hyphenated")
    need(r, meta, "tags", list, "meta")
    title = need(r, meta, "title", str, "meta")
    desc = need(r, meta, "description", str, "meta")
    lo, hi = (30, 52) if lang == "en" else (10, 55)
    if title and not lo <= len(title) <= hi:
        r.warn(f"meta.title is {len(title)} chars, outside {lo}-{hi}")
    dlo, dhi = (120, 170) if lang == "en" else (40, 180)
    if desc and not dlo <= len(desc) <= dhi:
        r.warn(f"meta.description is {len(desc)} chars, outside {dlo}-{dhi}")
    reader = need(r, meta, "reader", dict, "meta")
    if reader:
        need(r, reader, "persona", str, "meta.reader")
        need(r, reader, "promise", str, "meta.reader")
    tk = need(r, meta, "takeaways", list, "meta")
    if tk is not None:
        if not 2 <= len(tk) <= 5:
            r.warn(f"meta.takeaways has {len(tk)} items; aim for 3")
        for i, t in enumerate(tk):
            need(r, t, "id", str, f"takeaways[{i}]")
            need(r, t, "text", str, f"takeaways[{i}]")
    hook = need(r, meta, "hook", dict, "meta")
    if hook:
        if hook.get("kind") not in L.HOOK_KINDS:
            r.err(f"meta.hook.kind must be one of {sorted(L.HOOK_KINDS)}")
        need(r, hook, "text", str, "meta.hook")
    cb = need(r, meta, "cover_brief", dict, "meta")
    if cb:
        need(r, cb, "metaphor", str, "meta.cover_brief")
        need(r, cb, "labels", list, "meta.cover_brief")


def check_outline(r, plan):
    outline = need(r, plan, "outline", list, "plan")
    if not outline:
        return {}
    ids, nodes = {}, {}
    take_ids = {t.get("id") for t in plan.get("meta", {}).get("takeaways", []) if isinstance(t, dict)}
    served = set()
    for node, depth in L.outline_nodes(outline):
        nid = node.get("id")
        if not nid or nid in ids:
            r.err(f"outline: missing or duplicate id {nid!r}")
            continue
        ids[nid] = node
        nodes[nid] = (node, depth)
        if depth > 3:
            r.err(f"outline {nid}: deeper than H4 (depth {depth})")
        if node.get("role") not in L.ROLES:
            r.err(f"outline {nid}: role must be one of {sorted(L.ROLES)}")
        title = node.get("title", "")
        if not title:
            r.err(f"outline {nid}: empty title")
        elif MANUAL_NUMBER_RE.match(title):
            r.err(f"outline {nid}: title '{title}' carries a hand-written number; the theme numbers headings")
        if not node.get("goal"):
            r.warn(f"outline {nid}: no `goal` (what the reader can do after this section)")
        for t in node.get("serves", []):
            if t not in take_ids:
                r.err(f"outline {nid}: serves unknown takeaway {t!r}")
            served.add(t)
    for t in take_ids - served:
        r.warn(f"takeaway {t} is not served by any outline section")
    return nodes


def check_ledger(r, plan, article, nodes, stage):
    ledger = need(r, plan, "ledger", list, "plan")
    if ledger is None:
        return {}
    decisions = plan.get("decisions", [])
    by_id, covered = {}, set()
    for i, it in enumerate(ledger):
        where = f"ledger[{i}]"
        lid = it.get("id")
        if not lid or lid in by_id:
            r.err(f"{where}: missing or duplicate id {lid!r}")
            continue
        by_id[lid] = it
        if it.get("kind") not in L.LEDGER_KINDS:
            r.err(f"{lid}: kind must be one of {sorted(L.LEDGER_KINDS)}")
        if not it.get("gist"):
            r.err(f"{lid}: empty gist")
        layer = it.get("layer")
        if layer not in L.LAYERS and not (layer == "none" and it.get("kind") == "nav"):
            r.err(f"{lid}: layer must be one of {sorted(L.LAYERS)} (or 'none' for kind nav)")
        try:
            a, b = it["src"]["lines"]
            assert 1 <= a <= b <= len(article.lines)
        except Exception:
            r.err(f"{lid}: src.lines must be [start, end] inside article.md body (1..{len(article.lines)})")
            continue
        covered.update(range(a, b + 1))
        sec = it.get("section")
        if sec is not None and sec not in nodes:
            r.err(f"{lid}: section {sec!r} is not an outline id")
        if stage == "skeleton" and layer != "none" and sec is None:
            r.err(f"{lid}: skeleton needs `section` (where this detail will land)")
    missing = [n for n in range(1, len(article.lines) + 1) if n not in covered and n not in article.exempt]
    if missing:
        snips = [f"L{n}: {article.line(n).strip()[:60]}" for n in missing[:6]]
        r.err(f"{len(missing)} article.md line(s) are in no ledger item (first: " + " | ".join(snips) + ")")
    dec_by_ledger = {}
    for d in decisions:
        for key in ("id", "kind", "ledger", "why"):
            if not d.get(key):
                r.err(f"decision {d.get('id')!r}: missing '{key}'")
        if d.get("kind") not in L.DECISION_KINDS:
            r.err(f"decision {d.get('id')!r}: kind must be one of {sorted(L.DECISION_KINDS)}")
        if d.get("ledger") not in by_id:
            r.err(f"decision {d.get('id')!r}: unknown ledger id {d.get('ledger')!r}")
        dec_by_ledger.setdefault(d.get("ledger"), []).append(d)
        if d.get("kind") == "dropped" and not d.get("needs_human"):
            r.err(f"decision {d.get('id')}: a dropped detail must have needs_human=true")
    for lid, it in by_id.items():
        if it.get("kind") in ("caveat", "inference") and it.get("layer") in ("fold", "appendix"):
            ds = [d for d in dec_by_ledger.get(lid, []) if d.get("kind") == "folded" and d.get("needs_human")]
            if not ds:
                r.err(f"{lid}: a {it['kind']} is demoted to '{it['layer']}' without a `folded` decision "
                      "(needs_human=true), so the author would never see it was hidden")
    return by_id


def check_blocks(r, plan, by_id, nodes, article, manifest_ids, stage):
    blocks = need(r, plan, "blocks", list, "plan")
    if blocks is None:
        return
    seen = {}
    glossary_skip = set(plan.get("meta", {}).get("reader", {}).get("assumes", []))
    order = L.ordered_blocks(plan)
    pos = {b.get("id"): i for i, b in enumerate(order)}
    for b, parent in L.iter_blocks(blocks):
        bid = b.get("id")
        if not bid or bid in seen:
            r.err(f"block: missing or duplicate id {bid!r}")
            continue
        seen[bid] = b
        if parent is None and b.get("section") not in nodes:
            r.err(f"{bid}: section {b.get('section')!r} is not an outline id")
        t = b.get("type")
        if t not in L.BLOCK_TYPES:
            r.err(f"{bid}: type must be one of {sorted(L.BLOCK_TYPES)}")
            continue
        if b.get("layer") not in L.LAYERS:
            r.err(f"{bid}: layer must be one of {sorted(L.LAYERS)}")
        origin = b.get("origin")
        if origin not in ("source", "editorial"):
            r.err(f"{bid}: origin must be 'source' or 'editorial'")
        for lid in b.get("ledger", []):
            if lid not in by_id:
                r.err(f"{bid}: unknown ledger id {lid!r}")
            elif bid not in by_id[lid].get("dest", []):
                r.err(f"{bid}: cites {lid} but {lid}.dest does not list this block")
        if origin == "source" and not b.get("ledger"):
            r.err(f"{bid}: a source block must cite at least one ledger item")
        check_block_fields(r, b, t, manifest_ids, pos)
        if b.get("layer") == "fold" and not (parent and parent.get("type") == "fold"):
            r.err(f"{bid}: layer 'fold' blocks must sit inside a fold block's children")
        if parent and parent.get("type") == "fold" and b.get("layer") not in ("fold", "appendix"):
            r.err(f"{bid}: children of a fold must have layer 'fold' or 'appendix'")
        if parent and t in ("fold", "callout"):
            r.err(f"{bid}: a {t} cannot be nested inside a fold")
        if b.get("layer") == "appendix" and not parent:
            node = nodes.get(b.get("section"), ({},))[0]
            if node.get("role") != "deep-dive":
                r.warn(f"{bid}: layer 'appendix' outside a deep-dive section")
    for lid, it in by_id.items():
        for d in it.get("dest", []):
            if d not in seen:
                r.err(f"{lid}: dest block {d!r} does not exist")
            elif lid not in seen[d].get("ledger", []):
                r.err(f"{lid}: dest {d} does not cite it back")
        if it.get("kind") != "nav" and not it.get("dest"):
            dropped = [d for d in plan.get("decisions", []) if d.get("ledger") == lid and d.get("kind") == "dropped"]
            if not dropped:
                r.err(f"{lid}: lands in no block and has no `dropped` decision")
    fig_ids = {b.get("manifest_id") for b, _ in L.iter_blocks(blocks) if b.get("type") == "figure"}
    for iid in article.image_ids:
        if iid not in fig_ids:
            r.err(f"article.md references {iid} but no figure block uses it")
    check_glossary(r, plan, order, glossary_skip)
    return seen


def check_block_fields(r, b, t, manifest_ids, pos):
    bid = b["id"]
    if t == "paragraph" and not b.get("text"):
        r.err(f"{bid}: paragraph needs text")
    elif t == "list":
        if not b.get("items") or not all(isinstance(x, str) for x in b["items"]):
            r.err(f"{bid}: list needs string items")
    elif t == "table":
        h, rows = b.get("headers"), b.get("rows")
        if not h or not isinstance(rows, list) or not rows:
            r.err(f"{bid}: table needs headers and rows")
        elif any(len(row) != len(h) for row in rows):
            r.err(f"{bid}: every table row must have {len(h)} cells")
    elif t == "formula":
        if not b.get("latex"):
            r.err(f"{bid}: formula needs latex")
        elif "$" in b["latex"]:
            r.err(f"{bid}: formula latex must not include $ delimiters")
        ib = b.get("intuition")
        if ib and (ib not in pos or pos[ib] >= pos.get(bid, 10 ** 9)):
            r.err(f"{bid}: `intuition` block {ib!r} must exist and come before the formula")
    elif t == "figure":
        if b.get("manifest_id") not in manifest_ids:
            r.err(f"{bid}: manifest_id {b.get('manifest_id')!r} is not in the image manifest")
        for k in ("alt", "caption"):
            if not b.get(k):
                r.err(f"{bid}: figure needs {k}")
    elif t == "callout":
        if b.get("tone") not in L.CALLOUT_TONES:
            r.err(f"{bid}: callout tone must be one of {sorted(L.CALLOUT_TONES)}")
        if not b.get("title") or not b.get("text"):
            r.err(f"{bid}: callout needs title and text")
    elif t == "fold":
        if not b.get("title") or not b.get("children"):
            r.err(f"{bid}: fold needs a title and children")
    elif t == "diagram":
        k = b.get("kind")
        if k not in L.DIAGRAM_KINDS:
            r.err(f"{bid}: diagram kind must be one of {sorted(L.DIAGRAM_KINDS)}")
        elif k == "flow":
            ids = {n.get("id") for n in b.get("nodes", [])}
            if not ids or not b.get("edges"):
                r.err(f"{bid}: flow diagram needs nodes and edges")
            for e in b.get("edges", []):
                if e.get("from") not in ids or e.get("to") not in ids:
                    r.err(f"{bid}: edge {e} references an unknown node")
        elif not isinstance(b.get("tree"), dict):
            r.err(f"{bid}: {k} diagram needs a `tree` object")
    elif t == "code" and not b.get("code"):
        r.err(f"{bid}: code needs code")


def check_glossary(r, plan, order, skip):
    pos = {b["id"]: i for i, b in enumerate(order)}
    texts = ["\n".join(L.block_text(b, with_code=False)).lower() for b in order]
    for g in plan.get("glossary", []):
        term, dfn = g.get("term", ""), g.get("defined_in")
        if not term or dfn not in pos:
            r.err(f"glossary {term!r}: defined_in {dfn!r} is not a block")
            continue
        if term in skip:
            continue
        first = next((i for i, t in enumerate(texts) if term.lower() in t), None)
        if first is None or first > pos[dfn]:
            r.err(f"glossary {term!r}: not found in its defining block {dfn}")
        elif first < pos[dfn]:
            r.err(f"glossary {term!r}: used in {order[first]['id']} before it is defined in {dfn}")


def check_numbers(r, plan, article, by_id):
    post_nums = set(L.num_tokens(L.plan_text(plan, with_code=False)))
    waived = set()
    for d in plan.get("decisions", []):
        if d.get("kind") in ("dropped", "reworded") and d.get("ledger") in by_id:
            waived.update(L.ledger_lines(by_id[d["ledger"]]))
    miss = []
    for tok, lines in article.number_lines().items():
        if tok not in post_nums and not all(n in waived for n in lines):
            miss.append((tok, lines[0]))
    if miss:
        r.err(f"{len(miss)} number(s) from article.md are missing from the post (keep them, or record a "
              "`dropped`/`reworded` decision): " + ", ".join(f"{t} (L{n})" for t, n in miss[:10]))
    art_nums = set(article.number_lines())
    for b in L.ordered_blocks(plan):
        if b.get("origin") != "editorial" or b.get("illustrative"):
            continue
        for tok in L.num_tokens("\n".join(L.block_text(b, with_code=False))):
            if tok not in art_nums and not re.fullmatch(r"\d", tok):
                r.err(f"{b['id']}: editorial block introduces the number {tok} that is not in article.md "
                      "(mark it `illustrative`, or remove it)")


def check_hygiene(r, plan, lang):
    for b in L.ordered_blocks(plan):
        for s in L.block_text(b, with_code=False):
            plain = L.INLINE_CODE_RE.sub(" ", s)
            if plain.replace("$$", "").count("$") % 2:
                r.err(f"{b['id']}: odd number of '$' (use $...$ only for math; spell out prices)")
            if lang == "zh-tw" and HALF_WIDTH_PUNCT_RE.search(L.strip_code_and_math_delims(plain)):
                r.warn(f"{b['id']}: half-width , ; : ? ! next to Chinese text: {plain[:50]!r}")
            if lang == "en" and L.CJK_RE.search(plain):
                r.warn(f"{b['id']}: Chinese characters in the English plan: {plain[:50]!r}")


def block_index(plan):
    return {b["id"]: b for b, _ in L.iter_blocks(plan.get("blocks", [])) if "id" in b}


def check_parity(r, zh, en):
    zb, eb = block_index(zh), block_index(en)
    for bid in zb.keys() - eb.keys():
        r.err(f"en plan is missing block {bid}")
    for bid in eb.keys() - zb.keys():
        r.err(f"en plan has an extra block {bid}")
    for bid in zb.keys() & eb.keys():
        z, e = zb[bid], eb[bid]
        for key in ("type", "section", "layer", "origin", "ledger", "manifest_id", "tone", "kind"):
            if z.get(key) != e.get(key):
                r.err(f"{bid}: '{key}' differs between zh ({z.get(key)!r}) and en ({e.get(key)!r})")
        zc = [c["id"] for c in z.get("children", [])]
        ec = [c["id"] for c in e.get("children", [])]
        if zc != ec:
            r.err(f"{bid}: fold children differ between zh and en")
        z_nums = Counter(L.num_tokens("\n".join(L.block_text(z, with_code=False))))
        e_nums = Counter(L.num_tokens("\n".join(L.block_text(e, with_code=False))))
        if z_nums != e_nums:
            r.err(f"{bid}: numbers differ between zh {sorted(z_nums.elements())} and en {sorted(e_nums.elements())}")
    zo = [(n["id"], d) for n, d in L.outline_nodes(zh.get("outline", []))]
    eo = [(n["id"], d) for n, d in L.outline_nodes(en.get("outline", []))]
    if zo != eo:
        r.err("outline ids/depths differ between zh and en")
    zo_order = [b["id"] for b in L.ordered_blocks(zh)]
    eo_order = [b["id"] for b in L.ordered_blocks(en)]
    if zo_order != eo_order:
        r.err("block reading order differs between zh and en")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan")
    ap.add_argument("--article", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--stage", choices=["skeleton", "draft"], default="draft")
    ap.add_argument("--zh", help="the zh plan; makes this an en plan check (parity)")
    a = ap.parse_args()

    r = Report()
    plan = L.load(a.plan)
    lang = "en" if a.zh else "zh-tw"
    if plan.get("schema") != L.SCHEMA:
        r.err(f"schema must be {L.SCHEMA!r}")
    article = L.Article(a.article)
    manifest = L.load(a.manifest)
    manifest_ids = {e["id"] for e in manifest.get("images", [])}

    check_meta(r, plan, lang)
    nodes = check_outline(r, plan)
    if a.zh:
        zh = L.load(a.zh)
        by_id = {it["id"]: it for it in zh.get("ledger", [])}
        check_blocks(r, {**plan, "ledger": zh.get("ledger", []), "decisions": zh.get("decisions", [])},
                     by_id, nodes, article, manifest_ids, "draft")
        check_hygiene(r, plan, "en")
        check_parity(r, zh, plan)
    else:
        by_id = check_ledger(r, plan, article, nodes, a.stage)
        if a.stage == "draft":
            check_blocks(r, plan, by_id, nodes, article, manifest_ids, a.stage)
            check_numbers(r, plan, article, by_id)
            check_hygiene(r, plan, lang)
    for w in r.warnings:
        print("WARN:  " + w)
    for e in r.errors:
        print("ERROR: " + e)
    print(f"{len(r.errors)} error(s), {len(r.warnings)} warning(s) [{lang}, stage={a.stage}]")
    sys.exit(1 if r.errors else 0)


if __name__ == "__main__":
    main()

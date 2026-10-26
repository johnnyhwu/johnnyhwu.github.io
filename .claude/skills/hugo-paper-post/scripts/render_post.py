#!/usr/bin/env python3
"""Render a Planner's final plan JSON (schema `post-plan/1`) into this site's Hugo bundle. Deterministic: the same
plan always gives the same files, so nothing about the markup is hand-written or hand-fixed.

  plans/<slug>/post.zh.json  -> content/posts/<section>/<slug>/index.zh-tw.md
  plans/<slug>/post.en.json  -> content/posts/<section>/<slug>/index.en.md
  plans/<slug>/links.json    -> optional internal-link overlay applied while rendering
  figures                    -> copied into the bundle (figureN.png / tableN.png, named by the paper's number)

It decides FORM only (shortcodes, tables, mermaid, math delimiters, tilde escaping, image widths); it never
changes what the plan says. The cover (`featured-image.png`) is made separately; `verify_post.py` fails until it
exists.

Usage (from the repo root):
  render_post.py plans/<slug> [--lang zh-tw|en|both] [--base .] [--out-root content/posts]
                 [--date YYYY-MM-DD] [--lastmod YYYY-MM-DD]
`--base` is what the plan's `source.manifest` / `source.root` paths are relative to (default: the current dir).
If the target index file already exists, its `date` is kept (a rebuild of a live post must not move its date).
"""
import argparse
import datetime
import json
import re
import shutil
import struct
import sys
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILLS / "blog-planner" / "scripts"))
import plan_lib as L  # noqa: E402

MIN_WIDTH_PCT = 75
MERMAID_INIT = ("%%{init: {'theme':'base', 'themeVariables': { 'primaryColor':'#dbeafe', "
                "'primaryBorderColor':'#3b82f6', 'primaryTextColor':'#1e3a5f', 'lineColor':'#3b82f6', "
                "'secondaryColor':'#eff6ff', 'tertiaryColor':'#eff6ff', 'clusterBkg':'#eff6ff', "
                "'clusterBorder':'#93c5fd', 'edgeLabelBackground':'#ffffff' }}}%%")
INLINE_MATH_RE = re.compile(r"(?<!\$)\$([^$\n]+?)\$(?!\$)")
TILDE_RE = re.compile(r"(?<!\\)(?<=\S)~(?=\S)")
CODE_SPAN_RE = re.compile(r"(`[^`\n]*`)")
LINK_SPAN_RE = re.compile(r"(`[^`\n]*`|\[[^\]\n]*\]\([^)\n]*\))")
FIG_NAME_RE = re.compile(r"(Fig(?:ure)?|Table)\.?\s*(\d+)", re.I)


def png_width(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">I", head[16:20])[0]


def esc_attr(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def convert_math(text):
    """$..$ -> \\( .. \\) outside inline code (this site's passthrough only renders \\( \\))."""
    parts = CODE_SPAN_RE.split(text)
    for i in range(0, len(parts), 2):
        parts[i] = INLINE_MATH_RE.sub(lambda m: "\\( " + m.group(1).strip() + " \\)", parts[i])
    return "".join(parts)


def escape_tildes(text):
    """Two tight '~' on one line would be paired into a strikethrough by Goldmark; escape them (renders the same)."""
    out = []
    for line in text.split("\n"):
        parts = CODE_SPAN_RE.split(line)
        plain = "".join(parts[0::2])
        if len(TILDE_RE.findall(plain)) >= 2:
            for i in range(0, len(parts), 2):
                parts[i] = TILDE_RE.sub(r"\\~", parts[i])
        out.append("".join(parts))
    return "\n".join(out)


def prose(text):
    return escape_tildes(convert_math(text))


def apply_link(text, anchor, target):
    """Link the first occurrence of `anchor` that is not already inside code or a link. Returns (text, applied)."""
    parts = LINK_SPAN_RE.split(text)
    for i in range(0, len(parts), 2):
        k = parts[i].find(anchor)
        if k >= 0:
            parts[i] = parts[i][:k] + f"[{anchor}]({target})" + parts[i][k + len(anchor):]
            return "".join(parts), True
    return text, False


def md_table(headers, rows):
    def cell(c):
        return prose(str(c)).replace("|", "\\|").replace("\n", " ")
    lines = ["| " + " | ".join(cell(h) for h in headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    lines += ["| " + " | ".join(cell(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def mer_label(s):
    return str(s).replace('"', "#quot;")


def mer_mind(s):
    return re.sub(r"[()\[\]{}\"]", "", str(s)).strip() or "-"


def render_diagram(b):
    kind = b["kind"]
    lines = [MERMAID_INIT]
    if kind == "flow":
        lines.append(f"graph {b.get('direction', 'TD')}")
        for n in b["nodes"]:
            lines.append(f'    {n["id"]}["{mer_label(n["label"])}"]')
        for e in b["edges"]:
            arrow = f'-->|{mer_label(e["label"])}|' if e.get("label") else "-->"
            lines.append(f'    {e["from"]} {arrow} {e["to"]}')
    elif kind == "tree":
        lines.append("graph TD")
        counter = [0]

        def walk(node, parent):
            nid = f"n{counter[0]}"
            counter[0] += 1
            lines.append(f'    {nid}["{mer_label(node["label"])}"]')
            if parent:
                lines.append(f"    {parent} --> {nid}")
            for c in node.get("children", []):
                walk(c, nid)
        walk(b["tree"], None)
    else:  # mindmap
        lines.append("mindmap")

        def walk(node, depth):
            pad = "  " * (depth + 1)
            lines.append(f"{pad}root(({mer_mind(node['label'])}))" if depth == 0 else f"{pad}{mer_mind(node['label'])}")
            for c in node.get("children", []):
                walk(c, depth + 1)
        walk(b["tree"], 0)
    return "```mermaid\n" + "\n".join(lines) + "\n```"


class Renderer:
    def __init__(self, plan, lang, fig_files, widths, links):
        self.plan, self.lang = plan, lang
        self.fig_files, self.widths, self.links = fig_files, widths, links
        self.links_used = set()

    def linked(self, b, text, key):
        for lk in self.links:
            if lk["block"] != b["id"]:
                continue
            anchor = lk.get("zh" if self.lang == "zh-tw" else "en")
            if not anchor:
                continue
            text, ok = apply_link(text, anchor, lk["target"])
            if ok:
                self.links_used.add((lk["block"], lk["target"]))
        return text

    def block(self, b):
        t = b["type"]
        if t == "paragraph":
            return self.linked(b, prose(b["text"]), "text")
        if t == "list":
            items = [self.linked(b, prose(x), "item") for x in b["items"]]
            if b.get("ordered"):
                return "\n".join(f"{i}. {x}" for i, x in enumerate(items, 1))
            return "\n".join(f"- {x}" for x in items)
        if t == "table":
            return md_table(b["headers"], b["rows"])
        if t == "formula":
            return "$$\n" + b["latex"].strip() + "\n$$"
        if t == "figure":
            return self.figure(b)
        if t == "callout":
            return ('{{< admonition %s "%s" >}}\n%s\n{{< /admonition >}}'
                    % (b["tone"], esc_attr(b["title"]), self.linked(b, prose(b["text"]), "text")))
        if t == "fold":
            inner = "\n\n".join(self.block(c) for c in b["children"])
            return ('{{< fold title="%s" tone="%s" >}}\n%s\n{{< /fold >}}'
                    % (esc_attr(b["title"]), b.get("tone", "info"), inner))
        if t == "diagram":
            return render_diagram(b)
        if t == "code":
            return "```%s\n%s\n```" % (b.get("lang", "text"), b["code"].rstrip("\n"))
        raise ValueError(f"unknown block type {t!r}")

    def figure(self, b):
        name, label = self.fig_files[b["manifest_id"]]
        label = b.get("paper_label") or label
        attrib = (f"（來源：原始論文 {label}。）" if self.lang == "zh-tw"
                  else f" (Source: original paper, {label}.)") if label else ""
        cap = b["caption"].rstrip() + attrib
        w = self.widths.get(name)
        attr = f' width="{w}"' if w else ""
        return '{{< image src="%s" alt="%s" caption="%s"%s >}}' % (name, esc_attr(b["alt"]), esc_attr(cap), attr)

    def body(self):
        out = []
        blocks = self.plan.get("blocks", [])
        for node, depth in L.outline_nodes(self.plan["outline"]):
            out.append("#" * (depth + 1) + " " + node["title"])
            for b in blocks:
                if b.get("section") == node["id"]:
                    out.append(self.block(b))
        text = "\n\n".join(out)
        return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def front_matter(plan, date, lastmod):
    m = plan["meta"]
    sec = m["section"]
    return (
        "---\n# weight: 1\n"
        f'title: "{esc_attr(m["title"])}"\n'
        f"date: {date}\nlastmod: {lastmod}\ndraft: false\n"
        f'description: "{esc_attr(m["description"])}"\n'
        'featuredImage: "featured-image.png"\n\n'
        f"tags: {json.dumps(m['tags'], ensure_ascii=False)}\n"
        f'categories: ["{sec}"]\n# series: ["getting-start"]\n# series_weight: 1\nlightgallery: true\n\n'
        f'url: "{sec}/:contentbasename"\n---\n\n<!--more-->\n\n'
    )


def check_rendered(text, where):
    scrub = L.CODE_FENCE_RE.sub(" ", text)
    scrub = re.sub(r"\$\$.*?\$\$", " ", scrub, flags=re.S)
    scrub = L.INLINE_CODE_RE.sub(" ", scrub)
    if "$" in scrub:
        raise SystemExit(f"{where}: a literal '$' survived rendering (unbalanced math or a price); fix the plan")


def existing_date(path):
    if path.exists():
        m = re.search(r"^date:\s*(\S+)", path.read_text(encoding="utf-8"), re.M)
        if m:
            return m.group(1)
    return None


def collect_figures(plans, manifest, root):
    """Bundle names and display widths shared by both languages (the page bundle is one set of files)."""
    entries = {e["id"]: e for e in manifest["images"]}
    ids = []
    for plan in plans:
        for b, _ in L.iter_blocks(plan.get("blocks", [])):
            if b.get("type") == "figure" and b["manifest_id"] not in ids:
                ids.append(b["manifest_id"])
    fig_files, srcs = {}, {}
    for iid in ids:
        e = entries[iid]
        m = FIG_NAME_RE.match(e.get("caption", ""))
        if m:
            kind = "table" if m.group(1).lower() == "table" else "figure"
            name, label = f"{kind}{m.group(2)}.png", f"{kind.capitalize()} {m.group(2)}"
        else:
            name, label = f"{iid}.png", None
        fig_files[iid] = (name, label)
        srcs[name] = root / e["file"]
    pix = {n: png_width(p) for n, p in srcs.items()}
    known = [w for w in pix.values() if w]
    widest = max(known) if known else 0
    widths = {}
    for n, w in pix.items():
        if w and widest and w < 0.9 * widest:
            widths[n] = f"{max(MIN_WIDTH_PCT, round(w / widest * 100))}%"
    return fig_files, widths, srcs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan_dir")
    ap.add_argument("--lang", choices=["zh-tw", "en", "both"], default="both")
    ap.add_argument("--base", default=".")
    ap.add_argument("--out-root", default="content/posts")
    ap.add_argument("--date")
    ap.add_argument("--lastmod")
    a = ap.parse_args()

    pdir, base = Path(a.plan_dir), Path(a.base)
    langs = ["zh-tw", "en"] if a.lang == "both" else [a.lang]
    plans = {"zh-tw": L.load(pdir / "post.zh.json")}
    if (pdir / "post.en.json").exists():
        plans["en"] = L.load(pdir / "post.en.json")
    for lg in langs:
        if lg not in plans:
            raise SystemExit(f"missing plan for {lg}")
    ref = plans["zh-tw"]
    src = ref["source"]
    manifest = L.load(base / src["manifest"])
    fig_files, widths, srcs = collect_figures(list(plans.values()), manifest, base / src.get("root", "."))
    links = L.load(pdir / "links.json") if (pdir / "links.json").exists() else []

    meta = ref["meta"]
    out = Path(a.out_root) / meta["section"] / meta["slug"]
    out.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()
    for lg in langs:
        plan = plans[lg]
        fname = "index.zh-tw.md" if lg == "zh-tw" else "index.en.md"
        r = Renderer(plan, lg, fig_files, widths, links)
        body = r.body()
        date = existing_date(out / fname) or a.date or plan["meta"].get("date") or today
        text = front_matter(plan, date, a.lastmod or today) + body
        check_rendered(text, fname)
        unused = [(lk["block"], lk["target"]) for lk in links
                  if lk.get("zh" if lg == "zh-tw" else "en") and (lk["block"], lk["target"]) not in r.links_used]
        if unused:
            raise SystemExit(f"{fname}: link overlay entries that did not apply: {unused}")
        (out / fname).write_text(text, encoding="utf-8")
        print(f"wrote {out / fname}")
    for name, path in srcs.items():
        shutil.copy(path, out / name)
    print(f"copied {len(srcs)} image(s): " + ", ".join(srcs) + (f"; widths {widths}" if widths else ""))


if __name__ == "__main__":
    main()

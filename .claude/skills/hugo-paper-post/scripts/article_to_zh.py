#!/usr/bin/env python3
"""Mechanical first pass: article.md -> content/posts/<section>/<slug>/index.zh-tw.md plus the image files.

Does the deterministic parts so they are not redone by hand (and not done wrong): drops the H1 and the
trailing figure-map block and `---` rules, strips manual heading numbers (`一、`, `2.1`, `1.`, `概念3：`), converts
`![alt](img-00N)` + italic caption into {{< image >}} (bundle names figureN/tableN from the manifest caption,
width= from pixel widths with a 75% floor, source attribution normalised), converts inline `$..$` to `\\( .. \\)`
outside code fences, and copies the images.

Still yours afterwards: front matter (written as TODO placeholders so verify_post.py complains until filled),
rewriting cross-references to section numbers ("見 2.1 節"), admonitions, internal links, mermaid, the English
file. Usage:
  python3 article_to_zh.py <TopicDir> <section> <slug>     # <TopicDir> = AI-Research/done/unpublished/<Topic>
"""
import json, re, shutil, struct, sys
from pathlib import Path

MIN_WIDTH_PCT = 75


def png_width(p):
    with open(p, "rb") as f:
        return struct.unpack(">I", f.read(24)[16:20])[0]


def main():
    topic, section, slug = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    repo = Path(__file__).resolve().parents[4]
    out = repo / "content" / "posts" / section / slug
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((topic / "assets" / "image-manifest.json").read_text())
    root = topic.parents[2] if topic.parent.name in ("unpublished", "published") else topic.parent
    imgs = {}
    for e in manifest["images"]:
        m = re.match(r"(Fig(?:ure)?|Table)\.?\s*(\d+)", e["caption"], re.I)
        name = f"{'table' if m.group(1).lower() == 'table' else 'figure'}{m.group(2)}.png" if m else f"{e['id']}.png"
        src = root / e["file"]
        imgs[e["id"]] = (name, f"{'Table' if name.startswith('table') else 'Figure'} {m.group(2)}" if m else None, src)

    text = (topic / "article.md").read_text(encoding="utf-8").split("```figure-map")[0].rstrip() + "\n"
    lines, res, in_fence = text.split("\n"), [], False
    for ln in lines:
        if ln.startswith("```"):
            in_fence = not in_fence
            res.append(ln)
        elif in_fence:
            res.append(ln)
        elif ln.startswith("# ") or ln.strip() == "---" or ln.startswith("<!-- NO-MANIFEST"):
            continue
        elif re.match(r"^#{2,6} ", ln):
            h, t = ln.split(" ", 1)
            t = re.sub(r"^[一二三四五六七八九十]+、|^\d+(\.\d+)* |^概念\d+：", "", t)
            res.append(f"{h} {t}")
        elif not ln.startswith("$$"):
            res.append(re.sub(r"(?<!\$)\$([^$\n]+?)\$(?!\$)", lambda m: "\\( " + m.group(1).strip() + " \\)", ln))
        else:
            res.append(ln)

    used = {}
    final, i = [], 0
    while i < len(res):
        m = re.match(r"^!\[(.*)\]\((img-\d+)\)$", res[i])
        if not m:
            final.append(res[i]); i += 1; continue
        alt, iid = m.groups()
        name, fig, src = imgs[iid]
        cap = res[i + 1].strip("*")
        if fig:
            cap = re.sub(r"原始論文 (Fig\.|Figure|Table) ?\d+", f"原始論文 {fig}", cap)
        assert '"' not in alt + cap, f"double quote in alt/caption of {iid}"
        used[name] = src
        final.append((alt, name, cap)); i += 2
    widest = max(png_width(s) for s in used.values()) if used else 0
    body = []
    for item in final:
        if isinstance(item, str):
            body.append(item); continue
        alt, name, cap = item
        w = png_width(used[name])
        pct = round(w / widest * 100) if widest else 100
        attr = f' width="{max(MIN_WIDTH_PCT, pct)}%"' if w < 0.9 * widest else ""
        body.append(f'{{{{< image src="{name}" alt="{alt}" caption="{cap}"{attr} >}}}}')
    for name, src in used.items():
        shutil.copy(src, out / name)
    fm = ('---\n# weight: 1\ntitle: "TODO"\ndate: TODO\nlastmod: TODO\ndraft: false\ndescription: "TODO"\n'
          'featuredImage: "featured-image.png"\n\ntags: []\ncategories: ["%s"]\nlightgallery: true\n\n'
          'url: "%s/:contentbasename"\n---\n\n<!--more-->\n\n' % (section, section))
    (out / "index.zh-tw.md").write_text(fm + re.sub(r"\n{3,}", "\n\n", "\n".join(body)).strip() + "\n", encoding="utf-8")
    print(f"wrote {out}/index.zh-tw.md and {len(used)} image(s): " + ", ".join(used))


if __name__ == "__main__":
    main()

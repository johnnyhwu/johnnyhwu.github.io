"""Shared helpers for the blog-planner scripts (stdlib only).

A *plan* is the JSON the Planner writes (schema `post-plan/1`, see references/plan-schema.md). These helpers load
it, walk its blocks in reading order, and pull comparable text and numbers out of it and out of `article.md`.
"""
import json
import re
from pathlib import Path

SCHEMA = "post-plan/1"
SECTIONS = {"paper-intro", "ai-concept", "python-tutorial", "other"}
BLOCK_TYPES = {"paragraph", "list", "table", "formula", "figure", "callout", "fold", "diagram", "code"}
LAYERS = {"main", "support", "fold", "appendix"}
LEDGER_KINDS = {"claim", "number", "caveat", "inference", "definition", "table", "figure", "formula",
                "example", "nav"}
CALLOUT_TONES = {"note", "abstract", "info", "tip", "success", "question", "warning", "example", "quote"}
ROLES = {"hook", "context", "mechanism", "evidence", "caveat", "takeaway", "deep-dive"}
DECISION_KINDS = {"moved", "folded", "reworded", "dropped"}
HOOK_KINDS = {"tension", "scenario", "question"}
DIAGRAM_KINDS = {"flow", "tree", "mindmap"}

CODE_FENCE_RE = re.compile(r"^```.*?^```[ \t]*$", re.S | re.M)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
CJK_RE = re.compile(r"[一-鿿]")
IMG_LINE_RE = re.compile(r"^!\[.*\]\((img-\d+)\)\s*$")
# Cross-references that are renumbered on purpose (our own figure labels, the paper's section numbers) are not data.
REF_RE = re.compile(
    r"(?:圖|表|第)\s?\d+(?:\.\d+)*(?:\s?節)?"
    r"|(?<![A-Za-z])(?:Figure|Fig\.|Table|Section|Sections|Appendix|Step|Round|R)\s?[A-Z]?\d+(?:\.\d+)*")
NUM_RE = re.compile(r"(?<![\w.])(\d[\d,]*(?:\.\d+)?)(?!\w)")


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def iter_blocks(blocks, parent=None):
    """Pre-order walk over blocks, descending into `children` (fold blocks). Yields (block, parent)."""
    for b in blocks:
        yield b, parent
        if isinstance(b.get("children"), list):
            yield from iter_blocks(b["children"], b)


def outline_nodes(outline, depth=1):
    for n in outline:
        yield n, depth
        yield from outline_nodes(n.get("children", []), depth + 1)


def ordered_blocks(plan):
    """Blocks in reading order: outline order, then the blocks of each section in list order (folds expanded)."""
    top = plan.get("blocks", [])
    out = []
    for node, _ in outline_nodes(plan.get("outline", [])):
        mine = [b for b in top if b.get("section") == node["id"]]
        out.extend(x for x, _ in iter_blocks(mine))
    return out


def block_text(b, with_code=True):
    """All human text of one block as a list of strings (cells, items, captions, labels)."""
    t = b.get("type")
    parts = []
    if t == "paragraph" or t == "callout":
        parts += [b.get("title", ""), b.get("text", "")]
    elif t == "list":
        parts += list(b.get("items", []))
    elif t == "table":
        parts += list(b.get("headers", []))
        for row in b.get("rows", []):
            parts += list(row)
    elif t == "formula":
        parts += [b.get("latex", "")]
    elif t == "figure":
        parts += [b.get("alt", ""), b.get("caption", "")]
    elif t == "fold":
        parts += [b.get("title", "")]
    elif t == "diagram":
        parts += [n.get("label", "") for n in b.get("nodes", [])]
        parts += [e.get("label", "") for e in b.get("edges", []) if e.get("label")]
        parts += _tree_labels(b.get("tree"))
    elif t == "code" and with_code:
        parts += [b.get("code", "")]
    return [p for p in parts if isinstance(p, str) and p]


def _tree_labels(node):
    if not isinstance(node, dict):
        return []
    out = [node.get("label", "")]
    for c in node.get("children", []):
        out += _tree_labels(c)
    return out


def plan_text(plan, with_code=False):
    """Concatenated reader-facing text of the whole post."""
    chunks = []
    for b in ordered_blocks(plan):
        chunks += block_text(b, with_code=with_code)
    return "\n".join(chunks)


def strip_code_and_math_delims(text):
    text = CODE_FENCE_RE.sub(" ", text)
    return text.replace("$$", " ").replace("$", " ")


def num_tokens(text):
    """Comparable numeric tokens: thousands separators and signs dropped, our own figure/section refs removed."""
    text = strip_code_and_math_delims(text)
    text = INLINE_CODE_RE.sub(" ", text)
    text = re.sub(r"^\s*\d+\.\s", " ", text, flags=re.M)        # ordered-list markers
    text = REF_RE.sub(" ", text)
    out = []
    for m in NUM_RE.finditer(text):
        tok = m.group(1).replace(",", "")
        out.append(tok.rstrip("."))
    return out


class Article:
    """article.md as the Writer left it: body lines (up to the figure-map block) with 1-based numbering."""

    def __init__(self, path):
        raw = Path(path).read_text(encoding="utf-8").split("\n")
        end = len(raw)
        for i, ln in enumerate(raw):
            if ln.startswith("```figure-map"):
                end = i
                break
        self.lines = raw[:end]
        self.image_ids = []
        self.exempt = set()          # 1-based line numbers that need no ledger entry (structure, not knowledge)
        in_fence = False
        prev_img = False
        for i, ln in enumerate(self.lines, 1):
            s = ln.strip()
            if ln.startswith("```"):
                in_fence = not in_fence
                self.exempt.add(i)
                prev_img = False
                continue
            if in_fence:
                prev_img = False
                continue
            m = IMG_LINE_RE.match(s)
            if m:
                self.image_ids.append(m.group(1))
                self.exempt.add(i)
                prev_img = True
                continue
            if prev_img and s.startswith("*") and s.endswith("*"):
                self.exempt.add(i)
                prev_img = False
                continue
            prev_img = False
            if not s or s.startswith("#") or re.fullmatch(r"-{3,}", s) or re.fullmatch(r"\|?[\s:|-]+\|?", s):
                self.exempt.add(i)

    def line(self, n):
        return self.lines[n - 1]

    def numbered_text(self, lines):
        """Text of the given 1-based line numbers, joined (fenced code, headings, image lines excluded)."""
        in_fence = False
        fenced = set()
        for i, ln in enumerate(self.lines, 1):
            if ln.startswith("```"):
                in_fence = not in_fence
                fenced.add(i)
            elif in_fence:
                fenced.add(i)
        return "\n".join(self.lines[n - 1] for n in lines
                         if n not in fenced and n not in self.exempt)

    def number_lines(self):
        """token -> sorted list of 1-based lines it appears on (comparable tokens only)."""
        found = {}
        in_fence = False
        for i, ln in enumerate(self.lines, 1):
            if ln.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence or i in self.exempt:
                continue
            for tok in num_tokens(ln):
                found.setdefault(tok, []).append(i)
        return found


def ledger_lines(item):
    a, b = item["src"]["lines"]
    return range(a, b + 1)

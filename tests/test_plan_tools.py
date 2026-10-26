"""Tests for the Step 3 / Step 4 plan tooling: validate_plan.py, views.py, brief.py and render_post.py.

Run from the repo root:  uv run python -m unittest discover -s tests -v
They use the tiny fixture in tests/fixtures/mini (a zh plan, its en twin, an article, a manifest) and need no network.
"""
import copy
import json
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures" / "mini"
PLANNER = ROOT / ".claude" / "skills" / "blog-planner" / "scripts"
PUBLISHER = ROOT / ".claude" / "skills" / "hugo-publisher" / "scripts"
sys.path.insert(0, str(PLANNER))
sys.path.insert(0, str(PUBLISHER))
import render_post  # noqa: E402


def make_png(path, w, h):
    raw = b"".join(b"\x00" + b"\xff" * (w * 3) for _ in range(h))

    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                           + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.base = self.tmp / "base"
        shutil.copytree(FIX, self.base)
        make_png(self.base / "img-001.png", 1000, 500)
        self.zh = json.loads((self.base / "post.zh.json").read_text(encoding="utf-8"))
        self.en = json.loads((self.base / "post.en.json").read_text(encoding="utf-8"))

    def write(self, name, obj):
        p = self.base / name
        p.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
        return p

    def run_cli(self, script, *args):
        r = subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True, cwd=ROOT)
        return r.returncode, r.stdout + r.stderr

    def validate(self, plan=None, stage="draft", en=None, article=None):
        article = article or self.base / "article.md"
        common = ["--article", article, "--manifest", self.base / "image-manifest.json"]
        if en is not None:
            return self.run_cli(PLANNER / "validate_plan.py", self.write("e.json", en), "--zh",
                                self.write("z.json", plan or self.zh), *common)
        return self.run_cli(PLANNER / "validate_plan.py", self.write("p.json", plan or self.zh), "--stage", stage, *common)


class TestValidate(Base):
    def test_good_plan_passes(self):
        code, out = self.validate()
        self.assertEqual(code, 0, out)

    def test_good_skeleton_passes(self):
        code, out = self.validate(stage="skeleton")
        self.assertEqual(code, 0, out)

    def test_good_en_passes(self):
        code, out = self.validate(en=self.en)
        self.assertEqual(code, 0, out)

    def test_ledger_item_without_block(self):
        z = copy.deepcopy(self.zh)
        z["ledger"][2]["dest"] = []
        code, out = self.validate(z)
        self.assertEqual(code, 1)
        self.assertIn("lands in no block", out)

    def test_dropped_decision_allows_missing_dest(self):
        z = copy.deepcopy(self.zh)
        z["ledger"][2]["dest"] = []
        z["blocks"][4]["ledger"] = []
        z["blocks"][4]["origin"] = "editorial"
        z["decisions"].append({"id": "D2", "kind": "dropped", "ledger": "L3", "why": "unclear in the notes",
                               "needs_human": True})
        code, out = self.validate(z)
        self.assertEqual(code, 0, out)

    def test_dropped_decision_must_flag_the_author(self):
        z = copy.deepcopy(self.zh)
        z["decisions"].append({"id": "D2", "kind": "dropped", "ledger": "L3", "why": "x", "needs_human": False})
        code, out = self.validate(z)
        self.assertIn("needs_human=true", out)

    def test_uncovered_article_line(self):
        art = self.base / "article.md"
        text = art.read_text(encoding="utf-8").replace("接下來看實驗。", "接下來看實驗。\n\n這句話沒有任何帳目。")
        art.write_text(text, encoding="utf-8")
        code, out = self.validate()
        self.assertEqual(code, 1)
        self.assertIn("in no ledger item", out)

    def test_missing_number(self):
        z = copy.deepcopy(self.zh)
        z["blocks"][1]["text"] = "先給結論：方法 A 在多數格中為正。"
        code, out = self.validate(z)
        self.assertEqual(code, 1)
        self.assertIn("missing from the post", out)

    def test_editorial_block_may_not_invent_a_number(self):
        z = copy.deepcopy(self.zh)
        z["blocks"][5]["text"] += "大約 37 個團隊都這樣做。"
        code, out = self.validate(z)
        self.assertEqual(code, 1)
        self.assertIn("introduces the number 37", out)

    def test_illustrative_number_is_allowed(self):
        z = copy.deepcopy(self.zh)
        z["blocks"][5]["text"] += "假設有 37 個團隊。"
        z["blocks"][5]["illustrative"] = True
        code, out = self.validate(z)
        self.assertEqual(code, 0, out)

    def test_term_used_before_definition(self):
        z = copy.deepcopy(self.zh)
        z["glossary"][0]["defined_in"] = "s3.b2"          # ReAct is used earlier, in s2.b1
        code, out = self.validate(z)
        self.assertEqual(code, 1)
        self.assertIn("before it is defined", out)

    def test_hidden_caveat_needs_a_decision(self):
        z = copy.deepcopy(self.zh)
        z["decisions"] = []
        code, out = self.validate(z)
        self.assertEqual(code, 1)
        self.assertIn("demoted", out)

    def test_figure_must_be_used(self):
        z = copy.deepcopy(self.zh)
        z["blocks"] = [b for b in z["blocks"] if b["id"] != "s2.b2"]
        z["ledger"][6]["dest"] = []
        z["decisions"].append({"id": "D2", "kind": "dropped", "ledger": "L7", "why": "x", "needs_human": True})
        code, out = self.validate(z)
        self.assertEqual(code, 1)
        self.assertIn("no figure block uses it", out)

    def test_odd_dollar_signs(self):
        z = copy.deepcopy(self.zh)
        z["blocks"][2]["text"] += "價格是 $5。"
        code, out = self.validate(z)
        self.assertEqual(code, 1)
        self.assertIn("'$'", out)

    def test_hand_numbered_heading(self):
        z = copy.deepcopy(self.zh)
        z["outline"][1]["title"] = "二、問題"
        code, out = self.validate(z)
        self.assertIn("hand-written number", out)

    def test_en_missing_block(self):
        e = copy.deepcopy(self.en)
        e["blocks"] = [b for b in e["blocks"] if b["id"] != "s1.b1"]
        code, out = self.validate(en=e)
        self.assertEqual(code, 1)
        self.assertIn("missing block s1.b1", out)

    def test_en_number_drift(self):
        e = copy.deepcopy(self.en)
        e["blocks"][1]["text"] = e["blocks"][1]["text"].replace("23 of 24", "22 of 24")
        code, out = self.validate(en=e)
        self.assertEqual(code, 1)
        self.assertIn("numbers differ", out)


class TestNumberTokens(unittest.TestCase):
    def test_figure_label_does_not_swallow_the_next_table_cell(self):
        import plan_lib
        self.assertEqual(plan_lib.num_tokens("無圖\n58.8\n-"), ["58.8"])
        self.assertEqual(plan_lib.num_tokens("看圖 2 和表 3"), [])


class TestViews(Base):
    def test_reader_view_hides_source(self):
        code, out = self.run_cli(PLANNER / "views.py", "reader", self.base / "post.zh.json")
        self.assertEqual(code, 0, out)
        self.assertIn("⟦s3.b2⟧", out)
        self.assertNotIn("L5", out)
        self.assertIn("COLLAPSED", out)

    def test_delta_view_shows_only_neighbours(self):
        d = self.base / "d.json"
        d.write_text(json.dumps({"round": 2, "changed": ["s3.b2"]}))
        code, out = self.run_cli(PLANNER / "views.py", "fidelity", self.base / "post.zh.json", "--article",
                                 self.base / "article.md", "--delta", d)
        self.assertEqual(code, 0, out)
        self.assertIn(">>> CHANGED ⟦s3.b2⟧", out)
        self.assertIn("⟦s3.b1⟧", out)
        self.assertIn("⟦s3.b3⟧", out)
        self.assertNotIn("⟦s1.b1⟧", out)
        self.assertIn("article.md L18-22", out)

    def test_brief_flags_the_fold(self):
        code, out = self.run_cli(PLANNER / "brief.py", self.base / "post.zh.json")
        self.assertEqual(code, 0, out)
        self.assertIn("NEEDS YOUR CALL", out)
        self.assertIn("editorial block", out)


class TestRender(Base):
    def render(self, *extra):
        plan_dir = self.tmp / "plan"
        plan_dir.mkdir(exist_ok=True)
        for n in ("post.zh.json", "post.en.json"):
            shutil.copy(self.base / n, plan_dir / n)
        return self.run_cli(PUBLISHER / "render_post.py", plan_dir, "--base", self.base, "--out-root", self.tmp / "out",
                            "--date", "2026-10-26", "--lastmod", "2026-10-26", *extra)

    def test_matches_golden_files(self):
        code, out = self.render()
        self.assertEqual(code, 0, out)
        bundle = self.tmp / "out" / "paper-intro" / "mini-post"
        for name in ("index.zh-tw.md", "index.en.md"):
            self.assertEqual((bundle / name).read_text(encoding="utf-8"),
                             (FIX / "expected" / name).read_text(encoding="utf-8"), name)
        self.assertTrue((bundle / "figure1.png").exists())

    def test_rerender_keeps_existing_date(self):
        self.render()
        code, out = self.run_cli(PUBLISHER / "render_post.py", self.tmp / "plan", "--base", self.base, "--out-root",
                                 self.tmp / "out", "--date", "2030-01-01", "--lastmod", "2030-01-02")
        text = (self.tmp / "out" / "paper-intro" / "mini-post" / "index.en.md").read_text(encoding="utf-8")
        self.assertIn("date: 2026-10-26", text)
        self.assertIn("lastmod: 2030-01-02", text)

    def test_link_overlay(self):
        self.render()
        (self.tmp / "plan" / "links.json").write_text(json.dumps(
            [{"block": "s2.b1", "zh": "ReAct", "en": "ReAct", "target": "../react/"}]))
        code, out = self.run_cli(PUBLISHER / "render_post.py", self.tmp / "plan", "--base", self.base, "--out-root",
                                 self.tmp / "out", "--date", "2026-10-26", "--lastmod", "2026-10-26")
        self.assertEqual(code, 0, out)
        text = (self.tmp / "out" / "paper-intro" / "mini-post" / "index.zh-tw.md").read_text(encoding="utf-8")
        self.assertIn("[ReAct](../react/)", text)

    def test_link_that_cannot_apply_fails_loud(self):
        self.render()
        (self.tmp / "plan" / "links.json").write_text(json.dumps(
            [{"block": "s2.b1", "zh": "不存在的詞", "en": "nothing", "target": "../x/"}]))
        code, out = self.run_cli(PUBLISHER / "render_post.py", self.tmp / "plan", "--base", self.base, "--out-root",
                                 self.tmp / "out")
        self.assertNotEqual(code, 0)
        self.assertIn("did not apply", out)

    def test_math_and_tildes(self):
        self.assertEqual(render_post.convert_math("設 $x_i$ 與 `$y$`"), "設 \\( x_i \\) 與 `$y$`")
        self.assertEqual(render_post.escape_tildes("從 1~250 到 251~500"), "從 1\\~250 到 251\\~500")
        self.assertEqual(render_post.escape_tildes("約 ~40% 與 0 ~ 1"), "約 ~40% 與 0 ~ 1")

    def test_width_rule(self):
        make_png(self.base / "a.png", 1000, 400)
        make_png(self.base / "b.png", 600, 400)
        make_png(self.base / "c.png", 950, 400)
        manifest = {"images": [
            {"id": "img-a", "file": "a.png", "caption": "Figure 1 | a"},
            {"id": "img-b", "file": "b.png", "caption": "Table 2 | b"},
            {"id": "img-c", "file": "c.png", "caption": "Figure 3 | c"}]}
        plan = {"blocks": [{"type": "figure", "manifest_id": i} for i in ("img-a", "img-b", "img-c")]}
        files, widths, _ = render_post.collect_figures([plan], manifest, self.base)
        self.assertEqual(files["img-b"][0], "table2.png")
        self.assertEqual(widths, {"table2.png": "75%"})      # 60% is lifted to the 75% floor; 95% needs none

    def test_diagram_render(self):
        flow = render_post.render_diagram({"kind": "flow", "direction": "LR",
                                           "nodes": [{"id": "a", "label": "Search"}, {"id": "b", "label": "Verify"}],
                                           "edges": [{"from": "a", "to": "b", "label": "ok"}]})
        self.assertIn('a["Search"]', flow)
        self.assertIn("a -->|ok| b", flow)
        mind = render_post.render_diagram({"kind": "mindmap", "tree": {"label": "Root", "children": [{"label": "A (x)"}]}})
        self.assertIn("root((Root))", mind)
        self.assertIn("A x", mind)


if __name__ == "__main__":
    unittest.main()

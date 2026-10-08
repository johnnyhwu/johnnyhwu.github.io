# Getting a real local Hugo build running to verify a post

`scripts/verify_post.py` catches the common mistakes fast, but it cannot
catch a bug like the one in `bilingual-bundle-gotcha.md` — that one only
showed up in actual rendered HTML from a real `hugo build`. For any
non-trivial change (a new post, not a one-line typo fix), get a real build
running and actually look at the rendered `<img>` tags, not just the
source Markdown.

## Quickest path: the project-local wrapper

```bash
git submodule update --init themes/DoIt     # theme only; a bare --init also clones AI-Research
.claude/skills/hugo-paper-post/scripts/hugo.sh --gc --minify --baseURL "https://datasciocean.com/" -d .tools/public
```

`scripts/hugo.sh` reads `HUGO_VERSION` from `.github/workflows/hugo.yaml`, downloads exactly that release into
`.tools/hugo/<version>/` (gitignored; on macOS it unpacks the release `.pkg` with `pkgutil` instead of running
the installer, on Linux it untars the release), and runs it with its cache in `.tools/hugo-cache`. Nothing is
installed system-wide and `~/Library/Caches/hugo_cache` is not touched. Arguments go straight to hugo. The first
run downloads about 40MB (resumable and retried, since the connection can be slow); later runs reuse the binary.
Write the build output under `.tools/` (as above) so it never lands in the repo. The sections below explain the
problems this solves and what to check in the output; they are the manual route if the wrapper can't be used.

## Check the rendered page in a browser

A build proves the HTML exists, not that it *looks* right: KaTeX typesets in
the browser after Hugo is done. After building into `.tools/public`:

```bash
node .claude/skills/hugo-paper-post/scripts/check_layout.js <section>/<slug> [--root .tools/public]
```

It serves the build locally, opens the zh-tw and en pages in Chromium at
1280px and 390px, and exits 1 on horizontal page overflow, a KaTeX error, or
an inline formula wider than the text column. Exit 2 = Playwright or Chromium
missing (cloud sessions have both; locally `npm i -g playwright` then
`npx playwright install chromium`). Tables and code blocks scroll on their
own and are not counted. Calibrated against 20 existing posts (no false
positives) and against the pre-fix JEV English page (fails on the `$` pair).

Mermaid diagrams are a separate check, because the theme loads mermaid from
a CDN that sandboxes block and `check_layout.js` therefore reports them as
"NOT checked":

```bash
node .claude/skills/hugo-paper-post/scripts/check_mermaid.js <section>/<slug> --shots .tools/shots
```

It fetches mermaid@10 once with `npm pack` into `.tools/mermaid/`, renders
every diagram in both languages at 1280px and 390px, fails on a syntax error
(mermaid still draws an SVG, an error graphic, so "an svg exists" is not
proof) or an over-wide diagram, and saves a PNG per diagram. View one
screenshot per diagram: a clipped subgraph title is a valid SVG.

## Two symptoms you will meet without `hugo.sh`

1. **`hugo` is not preinstalled in a fresh sandbox**, and the theme
   (`themes/DoIt`) is a git submodule that isn't checked out by default
   (`hugo.sh` downloads the binary; the theme you init yourself, as above).
2. **A several-versions-old Hugo (for example from `apt`) fails with an
   unrelated-looking error** such as
   `error expanding ":contentbasename": permalink attribute not recognised`.
   This repo relies on newer permalink/URL features (the
   `url: "paper-intro/:contentbasename"` front-matter pattern used by every
   post). It has nothing to do with your change: the local `hugo` is too old.
   Match the `HUGO_VERSION` in `.github/workflows/hugo.yaml` exactly; don't
   guess a version.

## Fallback: when `hugo.sh` cannot download Hugo

`hugo.sh` fetches the release named by `HUGO_VERSION` in
`.github/workflows/hugo.yaml`. If that download is blocked (GitHub release
assets are not always reachable from a sandbox) and `hugo version` on PATH
is older than that version, build Hugo from source with Go, which
usually has access to `proxy.golang.org`:

```bash
HUGO_VERSION=$(grep -oP 'HUGO_VERSION:\s*\K\S+' .github/workflows/hugo.yaml)
go install -tags extended "github.com/gohugoio/hugo@v${HUGO_VERSION}"
"$(go env GOPATH)/bin/hugo" version    # must report the CI version, not an apt one
```

Then run that binary with the same arguments as `hugo.sh` (including
`-d .tools/public`). Don't `brew install` / `apt-get install` Hugo: an old
package fails with the unrelated-looking `:contentbasename` error above.

## Running the build

```bash
git submodule update --init themes/DoIt
.claude/skills/hugo-paper-post/scripts/hugo.sh --gc --minify --baseURL "https://datasciocean.com/" -d .tools/public
```

(Match `baseURL` and flags to `.github/workflows/hugo.yaml` if they have
changed.) A successful run prints a small table with `ZH - TW` / `EN` page
counts. The two page counts should be equal after your change; a mismatch is
itself a signal something is off (for example the missing zh-tw file bug this
skill exists to prevent). "Non-page files" is counted for the default
language only, which is expected.

## What to actually check in the output

Don't just check that the build exits 0 — inspect the rendered HTML for the
specific post:

```bash
grep -o '<img[^>]*src=[^ >]*' .tools/public/en/paper-intro/<slug>/index.html
grep -o '<img[^>]*src=[^ >]*' .tools/public/paper-intro/<slug>/index.html   # zh-tw output has no /en/ prefix (it's the default language)
```

Use those commands as written: `--minify` strips attribute quotes, so the
rendered HTML contains `src=/ai-concept/foo.png`, not `src="..."`. Grepping
for `src="` returns **zero matches on a perfectly healthy build** — don't
read that as "the images are broken". (Same trap when checking math: the
KaTeX output that server-rendering produces ends in `</annotation>`, which
truncates to a confusing-looking `</a` in narrow grep context.)

**A math grep only proves the LaTeX parsed — not that it renders at the
right size.** Hugo's built-in server-side math renderer and the theme's
vendored `lib/katex/katex.min.css` are two independently-versioned things;
if their CSS class names for font-size scaling ever drift apart again (it
happened once — see `assets/css/_custom.scss` for the fix and its comment
explaining the exact class mismatch), subscripts/superscripts will keep
the right DOM structure and position but silently render at full size
instead of shrinking, e.g. `v_1` shows a full-size `1` instead of a small
one. `grep` for `</annotation>` or `msub` cannot catch this — the markup
looks identical either way. If a rendering complaint like this comes up
again, first check whether `assets/css/_custom.scss` still matches the
class names Hugo is actually emitting (`grep -o 'class="sizing[^"]*"'` on
a built page) before re-diagnosing from scratch; only fall back to an
actual screenshot (build + serve + Playwright) if that override is
present and still doesn't fix it.

**Checking internal links has its own version of this trap.** A body link
written `[text](../other-slug/)` renders **relative**, verbatim —
`href=../other-slug/` — while the theme's own prev/next navigation renders
the *same* post as an absolute `href=/ai-concept/other-slug/`. So grepping
for the absolute form finds the nav link and misses every body link, which
looks exactly like "my cross-post links didn't render". Grep for the bare
slug instead:

```bash
grep -c 'other-slug' .tools/public/ai-concept/<linking-post>/index.html
```

then confirm `.tools/public/<section>/<other-slug>/` exists. Relative body links
are correct and are what every existing post on this site uses.

Every `src=` should look like a real permalink
(`/paper-intro/<slug>/figure1.png`) and the file should actually exist
under `.tools/public/` at that path. A literal bare filename in `src=` (e.g.
`src=figure1.png`) is the exact fingerprint of the bug in
`bilingual-bundle-gotcha.md` — go fix that, don't just note it and move on.

## Cleaning up after yourself

With `-d .tools/public` there is nothing to clean: `.tools/` (the Hugo binary,
its cache, the build output, the mermaid copy and screenshots) is gitignored.
If you ever build without `-d`, Hugo writes `public/` and `resources/` at the
repo root (both are in `.gitignore` too, but remove them anyway so a stray
`public/` is not mistaken for the real site).

Leave `themes/DoIt`'s submodule checkout alone either way: a submodule
checkout is a gitlink reference, not tracked file content, so there is
nothing to undo there. The same goes for `AI-Research`: if you ran
`git submodule update --remote` to read newer content, `git status` shows
`M AI-Research`; either commit that pointer bump deliberately with the post
(it must name a commit already on `AI-Research`'s `main`) or reset it with
`git submodule update --init AI-Research`.

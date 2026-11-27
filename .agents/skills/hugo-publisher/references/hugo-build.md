# Getting a real local Hugo build running to verify a post

`scripts/verify_post.py` catches the common mistakes fast, but some bugs (the one in `bilingual-bundle-gotcha.md`,
a page silently skipped, a formula that overflows) only show in a real build. Every new post gets one.

## Build

```bash
git submodule update --init themes/DoIt     # theme only; a bare --init also clones AI-Research
.agents/skills/hugo-publisher/scripts/hugo.sh --gc --minify --baseURL "https://datasciocean.com/" -d .tools/public
```

`scripts/hugo.sh` reads `HUGO_VERSION` from `.github/workflows/hugo.yaml`, downloads exactly that release into
`.tools/hugo/<version>/` (gitignored; on macOS it unpacks the `.pkg` with `pkgutil`, on Linux it untars), and runs
it with its cache in `.tools/hugo-cache`. Nothing is installed system-wide. Arguments go straight to hugo (match
`baseURL` and flags to the workflow if they change). The first run downloads about 40MB, resumable and retried.

A successful run prints `ZH - TW` / `EN` page counts. They should be equal; a mismatch usually means a
one-language bundle. "Non-page files" is counted for the default language only, which is expected.

**If the download is blocked** (GitHub release assets are not always reachable from a sandbox), build that exact
version from source into `.tools/`, never onto the machine (an older Hugo from `brew` or `apt` fails with an
unrelated-looking `:contentbasename` error):

```bash
HUGO_VERSION=$(grep -oE 'HUGO_VERSION:[[:space:]]*[^[:space:]]+' .github/workflows/hugo.yaml | awk '{print $2}')
GOBIN="$PWD/.tools/bin" go install -tags extended "github.com/gohugoio/hugo@v${HUGO_VERSION}"
.tools/bin/hugo version    # must report the CI version
```

Then run `.tools/bin/hugo` with the same arguments as above.

## Confirm the post was actually built

Exit code 0 does not prove *your* post is in the output. Hugo silently skips a page whose `date` is in the future,
and the build clock is UTC, so a post dated today (local time) can be "tomorrow" there:

```bash
ls .tools/public/<section>/<slug>/index.html .tools/public/en/<section>/<slug>/index.html
```

If either is missing, rerun with `--buildFuture` or date the post on or before the UTC date. A date that was
"future" only during local verification is fine (CI builds after the merge), but say so in the PR.

## Links and images: `check_links.py`

```bash
python3 .agents/skills/hugo-publisher/scripts/check_links.py .tools/public
```

It resolves every internal link and image `src` in every built post against the output, so do not grep the HTML by
hand. If you ever do: `--minify` strips attribute quotes (`src=/paper-intro/x/figure1.png`, so `src="` finds
nothing on a healthy build), and body links stay relative (`href=../other-slug/`) while the theme's prev/next links
are absolute, so grep for the bare slug. A bare filename in `src=` (`src=figure1.png`) is the fingerprint of
`bilingual-bundle-gotcha.md`.

## The rendered page in a browser

A build proves the HTML exists, not that it looks right: KaTeX and mermaid run in the browser. `scripts/node.sh` is
the project-local Node with Playwright and Chromium (downloaded into `.tools/` on first use).

```bash
S=.agents/skills/hugo-publisher/scripts
$S/node.sh $S/check_layout.js <section>/<slug>                         # always
$S/node.sh $S/check_mermaid.js <section>/<slug> --shots .tools/shots   # post has a diagram
$S/node.sh tests/check_fold.js <section>/<slug>                         # post has a fold
```

- `check_layout.js` opens both languages at 1280 and 390 px and exits 1 on horizontal page overflow, a KaTeX error,
  or an inline formula wider than the column (tables and code scroll on their own). **Exit 2 means it did not run**
  (Playwright or Chromium missing): say so, do not report a pass.
- `check_mermaid.js` serves a local mermaid@10 (the theme's CDN is blocked in sandboxes), fails on a syntax error or
  an over-wide diagram, and saves one PNG per diagram. Look at each: a clipped subgraph title is still a valid SVG.
- Math that parses can still render at the wrong size if Hugo's KaTeX class names drift from the theme's CSS (it
  happened once; the fix is in `assets/css/_custom.scss`). If subscripts render full-size, compare
  `grep -o 'class="sizing[^"]*"'` on a built page with that override before re-diagnosing.

## Cleaning up

With `-d .tools/public` there is nothing to clean: `.tools/` is gitignored. A build without `-d` writes `public/`
and `resources/` at the repo root (also gitignored); remove them. A `git submodule update --remote` shows
`M AI-Research`: commit that pointer deliberately with the post (it must name a commit on `AI-Research`'s `main`) or
reset it with `git submodule update --init AI-Research`.

# Getting a real local Hugo build running to verify a post

`scripts/verify_post.py` catches the common mistakes fast, but it cannot
catch a bug like the one in `bilingual-bundle-gotcha.md` — that one only
showed up in actual rendered HTML from a real `hugo build`. For any
non-trivial change (a new post, not a one-line typo fix), get a real build
running and actually look at the rendered `<img>` tags, not just the
source Markdown.

## The two things that will trip you up

1. **`hugo` is not preinstalled in a fresh sandbox**, and the theme
   (`themes/DoIt`) is a **git submodule that isn't checked out by default**.
2. **`apt-get install hugo` gives a version too old for this site.** This
   repo relies on newer Hugo permalink/URL features (e.g. the
   `url: "paper-intro/:contentbasename"` front-matter pattern used by every
   post) that a several-versions-old `apt` package doesn't support — you'll
   get an unrelated-looking error like
   `error expanding ":contentbasename": permalink attribute not recognised`
   that has nothing to do with your actual change. Don't debug that error
   as if it's about your post; it means the local `hugo` binary is too old,
   full stop.

Check `.github/workflows/hugo.yaml`'s `HUGO_VERSION` env var for the exact
version this site's CI actually builds with, and match it — don't guess a
version.

## Getting the right Hugo version without the CI's own install method

CI downloads the official `.deb` straight from a GitHub release URL. That
exact URL is very likely to 403 from inside a sandboxed session (GitHub
access here is typically scoped to specific repos this session was granted,
and a raw release-asset download isn't one of them). Don't waste time
retrying that path. Instead, build it from source with Go, which this
environment does have:

```bash
# 1. Check out the theme submodule (needed for an accurate build either way)
git submodule update --init --depth 1

# 2. Get the exact version CI uses
HUGO_VERSION=$(grep -oP 'HUGO_VERSION:\s*\K\S+' .github/workflows/hugo.yaml)

# 3. If apt's hugo is missing or too old, build the real version with Go
#    (go install pulls from proxy.golang.org, which is normally reachable
#    even when raw github.com asset downloads aren't)
go install -tags extended "github.com/gohugoio/hugo@v${HUGO_VERSION}"

# 4. Use the go-installed binary explicitly -- don't rely on PATH ordering,
#    apt may have put an older `hugo` earlier on PATH
HUGO_BIN="$(go env GOPATH)/bin/hugo"
$HUGO_BIN version   # confirm it reports the CI version, not an apt one
```

If `apt-get install -y hugo` happens to already give you the right major
version, you can skip the `go install` step — just confirm with
`hugo version` first rather than assuming.

## Running the build

```bash
$HUGO_BIN --gc --minify --baseURL "https://datasciocean.com/"
```

(Match the actual `baseURL`/flags from `.github/workflows/hugo.yaml` if
they've changed since this was written.) This writes to `./public`. A
successful run prints a small table with `ZH-TW` / `EN` page counts —
those two numbers should be equal (or explainably close) after your change;
a mismatch is itself a signal something's off (e.g. exactly the missing
zh-tw file bug this skill exists to prevent).

## What to actually check in the output

Don't just check that the build exits 0 — inspect the rendered HTML for the
specific post:

```bash
grep -o '<img[^>]*src=[^ >]*' public/en/paper-intro/<slug>/index.html
grep -o '<img[^>]*src=[^ >]*' public/paper-intro/<slug>/index.html   # zh-tw output has no /en/ prefix (it's the default language)
```

Every `src=` should look like a real permalink
(`/paper-intro/<slug>/figure1.png`) and the file should actually exist
under `public/` at that path. A literal bare filename in `src=` (e.g.
`src=figure1.png`) is the exact fingerprint of the bug in
`bilingual-bundle-gotcha.md` — go fix that, don't just note it and move on.

## Cleaning up after yourself

The build creates `public/` and `resources/` (a Hugo build cache) at the
repo root. Neither is tracked by this repo (there's no `.gitignore` line
for them because they've simply never existed in a committed state before
-- CI only uploads `public/` as a Pages deploy artifact, never commits it
back). Remove both before finishing:

```bash
rm -rf public resources
```

Leave `themes/DoIt`'s submodule checkout alone either way — checking it out
locally doesn't affect the actual repo state (submodule pointers are just a
gitlink commit reference, not file content tracked by this repo directly),
so there's nothing to clean up there.

# Why a post needs BOTH `index.en.md` and `index.zh-tw.md` — always

This is the single most expensive lesson from the first time this skill's
process was run by hand (publishing the SkillOpt post): shipping only
`index.en.md` silently broke **every image on the page** — not a missing
translation, an actively broken English post.

## Root cause

This site's `defaultContentLanguage` is `zh-TW`
(`config/_default/hugo.toml`). In a multilingual Hugo site, a leaf-bundle
page (an `index.<lang>.md` file plus sibling asset files in the same
directory — a "page bundle") has its resources (`.Page.Resources` — the
image files sitting next to it) associated with the bundle through its
**default-language translation**. If the bundle has no translation in the
site's default content language, Hugo cannot resolve `.Page.Resources` for
*any* translation of that page — not just the missing one.

Concretely: with only `content/posts/paper-intro/skillopt/index.en.md` (no
`index.zh-tw.md`) present alongside `figure1.png`, `table1.png`, etc., this
theme's `{{< image src="figure1.png" ... >}}` shortcode calls
`.Resources.Get "figure1.png"` and gets `nil` back — every single time, for
every image. The shortcode's `default` fallback then renders the *literal*
string `figure1.png` as the `<img src=...>` value instead of a real
permalink like `/paper-intro/skillopt/figure1.png`. The build **succeeds
with no warnings or errors** — this is a silent failure, not a build break,
which is exactly why it's easy to ship without noticing.

This was confirmed empirically, not guessed: a temporary `warnf` debug line
added to `themes/DoIt/layouts/shortcodes/image.html` showed
`resourcesLen=0` for every image call on the English-only bundle. Adding a
placeholder `index.zh-tw.md` to the same directory and rebuilding flipped it
to `resourcesLen=8` (the correct count) instantly, for both language pages.

## The rule this implies

**Every post directory under `content/posts/paper-intro/<slug>/` must ship
both `index.en.md` and `index.zh-tw.md` in the same change.** There is no
existing post on this site that violates this (every other post already has
both), which is exactly why this failure mode had never been hit before
SkillOpt was the first to (temporarily) break the pattern.

If a future source article only exists in one language and translating it
right away seems like unnecessary work: it isn't optional here. Translate
it as part of the same task. If you are ever tempted to ship "just the
English version for now, Chinese later" — don't; that leaves the English
version's images broken in production until the Chinese file shows up,
which is worse than doing both up front.

## If you ever suspect this bug again

Fastest way to confirm/deny without guessing:
1. Check both `index.en.md` and `index.zh-tw.md` exist in the post's
   directory. If only one does, that's very likely the entire bug — stop
   here and add the missing translation.
2. If both exist and images still look broken, get a real local build
   running (`references/hugo-build.md`) and grep the rendered HTML for the
   image shortcode's output — a literal bare filename in `src=` (e.g.
   `src=figure1.png` instead of `src=/paper-intro/<slug>/figure1.png`) is
   the fingerprint of `.Page.Resources` resolving empty.

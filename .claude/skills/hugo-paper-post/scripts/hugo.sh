#!/usr/bin/env bash
# Project-local Hugo: downloads the version CI uses into .tools/ (gitignored) and runs it
# with its cache inside .tools/ too, so nothing is installed system-wide and
# ~/Library/Caches/hugo_cache is left alone.
#
# Usage (from anywhere inside the repo):
#   .claude/skills/hugo-paper-post/scripts/hugo.sh --gc --minify --baseURL "https://datasciocean.com/" -d .tools/public
# Any arguments are passed straight to hugo. The first run downloads ~40MB (resumable, retried);
# later runs reuse .tools/hugo/<version>/hugo.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
VERSION="$(sed -n 's/^ *HUGO_VERSION: *//p' "$ROOT/.github/workflows/hugo.yaml" | head -1)"
[ -n "$VERSION" ] || { echo "could not read HUGO_VERSION from .github/workflows/hugo.yaml" >&2; exit 1; }

TOOLS="$ROOT/.tools/hugo"
BIN="$TOOLS/$VERSION/hugo"
BASE="https://github.com/gohugoio/hugo/releases/download/v$VERSION"

fetch() { # fetch <url> <file>; resumable, retried (the connection can be slow or drop)
  local i
  for i in 1 2 3 4 5 6 7 8 9 10; do
    curl -fsSL -C - --connect-timeout 20 -o "$2" "$1" && return 0
    [ -s "$2" ] && return 0   # curl -C - on a finished file can exit non-zero; extraction below is the real check
    sleep 2
  done
  return 1
}

if [ ! -x "$BIN" ]; then
  mkdir -p "$TOOLS/$VERSION" "$TOOLS/download"
  case "$(uname -s)" in
    Darwin)
      PKG="$TOOLS/download/hugo_extended_${VERSION}_darwin-universal.pkg"
      for attempt in 1 2 3 4 5; do
        fetch "$BASE/$(basename "$PKG")" "$PKG" || true
        rm -rf "$TOOLS/download/expanded"
        # unpack the .pkg payload without running the installer
        pkgutil --expand-full "$PKG" "$TOOLS/download/expanded" 2>/dev/null && break
        [ "$attempt" = 5 ] && { echo "could not download/expand $PKG" >&2; exit 1; }
      done
      cp "$TOOLS/download/expanded/Payload/hugo" "$BIN"
      ;;
    Linux)
      case "$(uname -m)" in x86_64) ARCH=amd64 ;; aarch64|arm64) ARCH=arm64 ;; *) echo "unsupported arch $(uname -m)" >&2; exit 1 ;; esac
      TGZ="$TOOLS/download/hugo_extended_${VERSION}_linux-${ARCH}.tar.gz"
      fetch "$BASE/$(basename "$TGZ")" "$TGZ"
      tar -xzf "$TGZ" -C "$TOOLS/$VERSION" hugo
      ;;
    *) echo "unsupported OS $(uname -s)" >&2; exit 1 ;;
  esac
  chmod +x "$BIN"
  rm -rf "$TOOLS/download"
fi

[ -f "$ROOT/themes/DoIt/theme.toml" ] || {
  echo "theme missing: run  git submodule update --init themes/DoIt  (not a bare --init: that also clones AI-Research)" >&2
  exit 1
}

cd "$ROOT"
export HUGO_CACHEDIR="$ROOT/.tools/hugo-cache"   # env var works for every subcommand, unlike --cacheDir
exec "$BIN" "$@"

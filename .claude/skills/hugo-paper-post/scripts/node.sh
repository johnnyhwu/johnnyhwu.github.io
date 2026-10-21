#!/usr/bin/env bash
# Project-local Node + Playwright + Chromium for check_layout.js / check_mermaid.js.
# Everything lands under .tools/ (gitignored): the Node binary in .tools/node/<version>/, Playwright in
# .tools/node_modules/, the browser in .tools/browsers/, npm's cache in .tools/npm-cache. Nothing is installed
# system-wide and ~/.npm, ~/Library/Caches/ms-playwright are not touched.
#
# Usage (from anywhere inside the repo); arguments go straight to node:
#   .claude/skills/hugo-paper-post/scripts/node.sh .claude/skills/hugo-paper-post/scripts/check_layout.js <section>/<slug>
#   .claude/skills/hugo-paper-post/scripts/node.sh --version
# The first run downloads about 40MB of Node, then Playwright and Chromium (a few hundred MB); later runs reuse them.
# Prefer a Node you already have? Any `node` on PATH works for the scripts too, but then Playwright must be
# resolvable from it (see loadPlaywright in check_layout.js).
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
NODE_MAJOR=22
PLAYWRIGHT_VERSION=1.49.1
TOOLS="$ROOT/.tools"

case "$(uname -s)-$(uname -m)" in
  Darwin-arm64) PLATFORM=darwin-arm64 ;;
  Darwin-x86_64) PLATFORM=darwin-x64 ;;
  Linux-x86_64) PLATFORM=linux-x64 ;;
  Linux-aarch64) PLATFORM=linux-arm64 ;;
  *) echo "unsupported platform $(uname -s)-$(uname -m)" >&2; exit 1 ;;
esac

fetch() { # fetch <url> <file>; resumable, retried
  local i
  for i in 1 2 3 4 5 6 7 8 9 10; do
    curl -fsSL -C - --connect-timeout 20 -o "$2" "$1" && return 0
    [ -s "$2" ] && return 0
    sleep 2
  done
  return 1
}

NODE_DIR="$(ls -d "$TOOLS"/node/v${NODE_MAJOR}.*-"$PLATFORM" 2>/dev/null | sort -V | tail -1 || true)"
if [ -z "$NODE_DIR" ] || [ ! -x "$NODE_DIR/bin/node" ]; then
  INDEX="https://nodejs.org/dist/latest-v${NODE_MAJOR}.x"
  FILE="$(curl -fsSL "$INDEX/SHASUMS256.txt" | awk '{print $2}' | grep "^node-v.*-$PLATFORM.tar.gz$" | head -1)"
  [ -n "$FILE" ] || { echo "could not find a Node $NODE_MAJOR release for $PLATFORM" >&2; exit 1; }
  mkdir -p "$TOOLS/node" "$TOOLS/download"
  fetch "$INDEX/$FILE" "$TOOLS/download/$FILE"
  tar -xzf "$TOOLS/download/$FILE" -C "$TOOLS/node"
  NODE_DIR="$TOOLS/node/${FILE%.tar.gz}"
fi

export PATH="$NODE_DIR/bin:$PATH"
export npm_config_cache="$TOOLS/npm-cache"
export PLAYWRIGHT_BROWSERS_PATH="$TOOLS/browsers"
export NODE_PATH="$TOOLS/node_modules${NODE_PATH:+:$NODE_PATH}"

if [ ! -d "$TOOLS/node_modules/playwright" ]; then
  npm install --prefix "$TOOLS" --no-save --no-audit --no-fund "playwright@$PLAYWRIGHT_VERSION" >&2
fi
if ! ls "$PLAYWRIGHT_BROWSERS_PATH"/chromium-* >/dev/null 2>&1; then
  (cd "$TOOLS" && npx --no-install playwright install chromium >&2)
fi

exec node "$@"

#!/usr/bin/env python3
"""What people type into Google, from its autocomplete endpoint. No key, no browser.

    python3 .agents/skills/seo/scripts/suggest.py "dpo" "direct preference optimization"
    python3 .agents/skills/seo/scripts/suggest.py --lang en --expand "bash agent"

For each term it prints Google's suggestions for that term (Taiwan, zh-TW by default; `--lang en` uses
the US, English). `--expand` also asks for the usual question forms (zh: 「是什麼」「介紹」「vs」; en:
"what is", "vs"). What to read from the output:

- a suggestion that means something else (「dpo 醫學」, 「dpo 造血針」) is a name collision: the title
  needs a plain-words hook that says which meaning this post is;
- comparison and question forms (「dpo ppo 區別」, "grpo vs dpo") are sections or H2s readers want;
- no suggestions, or only the bare term, means nobody types it yet (most new paper names).

Suggestions are not search volume and are not personalised here (no cookies are sent). The endpoint is
unofficial: if it fails or the shape changes, the script says so and exits 2; skip the check and say so.
Stdlib only, one request per second.
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ENDPOINT = "https://suggestqueries.google.com/complete/search"
LOCALES = {"zh": {"hl": "zh-TW", "gl": "tw"}, "en": {"hl": "en", "gl": "us"}}
EXPANSIONS = {"zh": ["{} 是什麼", "{} 介紹", "{} vs"], "en": ["what is {}", "{} vs"]}


def fetch(query, lang):
    params = {"client": "firefox", "ie": "utf-8", "oe": "utf-8", "q": query, **LOCALES[lang]}
    req = urllib.request.Request(ENDPOINT + "?" + urllib.parse.urlencode(params),
                                 headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if not (isinstance(data, list) and len(data) >= 2 and isinstance(data[1], list)):
        raise ValueError("unexpected response shape")
    return [s for s in data[1] if isinstance(s, str)]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("terms", nargs="+")
    ap.add_argument("--lang", choices=sorted(LOCALES), default="zh")
    ap.add_argument("--expand", action="store_true", help="also ask the question and comparison forms")
    args = ap.parse_args()

    queries = []
    for term in args.terms:
        queries.append(term)
        if args.expand:
            queries += [form.format(term) for form in EXPANSIONS[args.lang]]

    for i, query in enumerate(queries):
        if i:
            time.sleep(1)
        try:
            suggestions = fetch(query, args.lang)
        except (urllib.error.URLError, ValueError, json.JSONDecodeError, TimeoutError) as exc:
            print(f"suggest.py: '{query}' failed ({exc}); skip this check and say so", file=sys.stderr)
            return 2
        others = [s for s in suggestions if s.strip().lower() != query.strip().lower()]
        print(f"== {query} ({LOCALES[args.lang]['gl']})")
        print("\n".join(f"  {s}" for s in others) if others else "  (no suggestions beyond the term)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

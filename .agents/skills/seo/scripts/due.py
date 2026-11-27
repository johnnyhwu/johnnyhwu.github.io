#!/usr/bin/env python3
"""SessionStart hook: inject due SEO follow-ups from seo/followups.md.

Speaks the Antigravity SessionStart JSON stdout contract:
outputs {} when nothing is due, or {"injectSteps": [{"systemMessage": ...}]}.
Stdlib only; never fails the session.
"""
import datetime
import json
import pathlib
import re
import sys


def main():
    path = pathlib.Path(__file__).resolve().parents[4] / "seo" / "followups.md"
    if not path.exists():
        print("{}")
        return
    try:  # the author is in Taiwan; a UTC cloud VM would otherwise be a day behind
        from zoneinfo import ZoneInfo

        today = datetime.datetime.now(ZoneInfo("Asia/Taipei")).date()
    except Exception:
        today = datetime.date.today()
    section = None
    due = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:].strip().lower()
            continue
        if section != "open" or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", cells[0]):
            continue
        try:
            when = datetime.date.fromisoformat(cells[0])
        except ValueError:
            continue
        if when <= today:
            due.append((when, cells[1], cells[2]))
    if not due:
        print("{}")
        return
    lines = [
        f"SEO follow-ups due as of {today} (seo/followups.md, recipe: .agents/skills/seo/SKILL.md):"
    ]
    for when, kind, item in sorted(due):
        late = (today - when).days
        lines.append(f"- [{kind}] {item} (due {when}{f', {late}d late' if late else ''})")
    lines.append(
        "Mention these to the user in one line, then carry on with their task. Run them only when the "
        "task is publishing/SEO or the user agrees, and only if GSC is available (seo skill preflight)."
    )
    payload = {
        "injectSteps": [
            {
                "systemMessage": {
                    "systemMessage": "\n".join(lines),
                }
            }
        ]
    }
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # a hook must never break the session
        print("{}")
        print(f"seo due.py failed: {exc}", file=sys.stderr)

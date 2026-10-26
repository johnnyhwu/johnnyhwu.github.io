#!/usr/bin/env python3
"""SessionStart hook: print the SEO follow-ups in seo/followups.md that are due.

Prints nothing when nothing is due, so a session that has no SEO work costs no context.
Stdlib only; never fails the session.
"""
import datetime
import pathlib
import re
import sys


def main():
    path = pathlib.Path(__file__).resolve().parents[4] / "seo" / "followups.md"
    if not path.exists():
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
        return
    print(f"SEO follow-ups due as of {today} (seo/followups.md, recipe: .claude/skills/seo/SKILL.md):")
    for when, kind, item in sorted(due):
        late = (today - when).days
        print(f"- [{kind}] {item} (due {when}{f', {late}d late' if late else ''})")
    print(
        "Tell the user these are due. Run them only if the GSC tools are available "
        "(see the seo skill's preflight); otherwise just report them as not done."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # a hook must never break the session
        print(f"seo due.py failed: {exc}", file=sys.stderr)

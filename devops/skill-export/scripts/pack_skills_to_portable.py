#!/usr/bin/env python3
"""Pack Hermes SKILL.md files into a portable standalone format.

Output format (per skill, written as BOTH <id>.md and <id>.txt):
    <skill-id>
    name: <name>
    description: <description>

    ## Instructions

    <full body, code examples preserved>

Usage:
    python3 pack_skills_to_portable.py OUTDIR SKILL.md [SKILL.md ...]

    # Pack every SKILL.md under a skills tree:
    find ~/.hermes/skills -name SKILL.md > /tmp/list.txt
    python3 pack_skills_to_portable.py OUTDIR $(cat /tmp/list.txt)

Stdlib only (re, pathlib) — no third-party deps.
"""
import re
import sys
import pathlib

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


def parse_skill(text: str):
    """Return (name, description, body) from a SKILL.md with YAML frontmatter."""
    m = FRONTMATTER_RE.match(text)
    fm, body = (m.group(1), m.group(2)) if m else ("", text)
    name = desc = ""
    for line in fm.splitlines():
        if line.startswith("name:"):
            name = line.split(":", 1)[1].strip().strip('"\'')
        elif line.startswith("description:"):
            desc = line.split(":", 1)[1].strip().strip('"\'')
    return name, desc, body.strip("\n")


def clean_body(body: str) -> str:
    """Drop a leading top-level '# Title' heading — the name already lives in the name: field."""
    lines = body.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and re.match(r"^#\s+\S", lines[0]) and not lines[0].startswith("##"):
        lines.pop(0)
        while lines and not lines[0].strip():
            lines.pop(0)
    return "\n".join(lines)


def pack(src: pathlib.Path, outdir: pathlib.Path):
    name, desc, body = parse_skill(src.read_text(encoding="utf-8"))
    body = clean_body(body)
    sid = name or src.parent.name
    content = f"{sid}\n\nname: {sid}\ndescription: {desc}\n\n## Instructions\n\n{body}\n"
    (outdir / f"{sid}.md").write_text(content, encoding="utf-8")
    (outdir / f"{sid}.txt").write_text(content, encoding="utf-8")
    return sid, len(content)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if len(args) < 2:
        print(__doc__)
        sys.exit(1)
    outdir = pathlib.Path(args[0]).expanduser()
    outdir.mkdir(parents=True, exist_ok=True)
    for p in args[1:]:
        src = pathlib.Path(p).expanduser()
        sid, n = pack(src, outdir)
        print(f"wrote {sid}.md / {sid}.txt  ({n} chars)")


if __name__ == "__main__":
    main()

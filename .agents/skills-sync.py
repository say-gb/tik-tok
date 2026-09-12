#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""낭만클럽 스킬을 Codex에서도 쓰게 포인터를 만든다.

원본:  낭만클럽-세팅/.claude/skills/<이름>/SKILL.md   (여기만 고친다)
생성:  .codex/skills/<이름>/SKILL.md                  (자동 생성. 직접 고치지 말 것)

실행:  python .agents/skills-sync.py
"""
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "낭만클럽-세팅" / ".claude" / "skills"
DST = ROOT / ".codex" / "skills"

TEMPLATE = """---
name: {name}
description: {description}
---

# {name} — Codex용 포인터

**본문은 이 파일에 없다. 아래 원본을 지금 바로 열어 전부 읽고, 그 규칙대로 쓴다.**

- 스킬 원본: `{src}`
- 말투·정체성 원본: `낭만클럽-세팅/CLAUDE.md`
- 협업 규약: `AGENTS.md`

원본을 읽지 않고 기억으로 쓰면 톤이 무너진다. 반드시 읽는다.

<!-- 이 파일은 `python .agents/skills-sync.py` 가 자동 생성한다. 고칠 곳은 원본이다. -->
"""


def parse_front_matter(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return None
    block = m.group(1)
    out = {}
    key = None
    for line in block.splitlines():
        hit = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if hit:
            key = hit.group(1)
            out[key] = hit.group(2).strip()
        elif key and line.strip():
            out[key] += " " + line.strip()
    return out


def main():
    if not SRC.is_dir():
        print("원본 스킬 폴더가 없다: %s" % SRC)
        return 1

    if DST.exists():
        shutil.rmtree(DST)
    DST.mkdir(parents=True)

    made = 0
    for skill_dir in sorted(p for p in SRC.iterdir() if p.is_dir()):
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            continue
        meta = parse_front_matter(skill_file.read_text(encoding="utf-8")) or {}
        name = meta.get("name") or skill_dir.name
        desc = meta.get("description")
        if not desc:
            print("  ! %s : description 없음 — 건너뜀" % skill_dir.name)
            continue
        rel_src = skill_file.relative_to(ROOT).as_posix()
        target = DST / skill_dir.name
        target.mkdir(parents=True, exist_ok=True)
        (target / "SKILL.md").write_text(
            TEMPLATE.format(name=name, description=desc, src=rel_src),
            encoding="utf-8",
        )
        print("  + .codex/skills/%s/SKILL.md" % skill_dir.name)
        made += 1

    print("스킬 %d개 동기화 완료." % made)
    return 0


if __name__ == "__main__":
    sys.exit(main())

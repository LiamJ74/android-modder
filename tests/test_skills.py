"""The .claude/skills copy must match skills/ exactly, and every SKILL.md must have name+description."""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILLS = REPO / "skills"
CLAUDE_SKILLS = REPO / ".claude" / "skills"


def _tree(root: Path) -> dict[str, bytes]:
    return {str(p.relative_to(root)).replace("\\", "/"): p.read_bytes()
            for p in root.rglob("*") if p.is_file()}


def test_claude_skills_is_a_copy_of_skills():
    assert CLAUDE_SKILLS.is_dir(), ".claude/skills is missing — copy skills/ into it"
    src, dst = _tree(SKILLS), _tree(CLAUDE_SKILLS)
    missing = sorted(set(src) - set(dst))
    extra = sorted(set(dst) - set(src))
    differ = sorted(k for k in src.keys() & dst.keys() if src[k] != dst[k])
    assert not missing, f"missing from .claude/skills: {missing}"
    assert not extra, f"extra in .claude/skills: {extra}"
    assert not differ, f"out of sync (re-copy skills/ to .claude/skills/): {differ}"


def test_every_skill_has_frontmatter():
    for skill in SKILLS.glob("*/SKILL.md"):
        text = skill.read_text(encoding="utf-8")
        assert text.startswith("---"), f"{skill} has no front matter"
        fm = text.split("---", 2)[1]
        assert re.search(r"^name:\s*\S", fm, re.M), f"{skill} missing name:"
        assert re.search(r"^description:\s*\S", fm, re.M), f"{skill} missing description:"


def test_main_skill_references_exist():
    eng = SKILLS / "mod-android-game" / "references" / "engines"
    for name in ("unity-mono", "unity-il2cpp", "godot", "libgdx", "unreal", "native-cpp",
                 "java-kotlin", "html5-webview"):
        assert (eng / f"{name}.md").exists(), f"missing engine playbook: {name}.md"
    assert (SKILLS / "mod-android-game" / "references" / "safety.md").exists()

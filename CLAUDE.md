@AGENTS.md

## Claude Code specifics
- Installed as a plugin, the skills are namespaced (`/android-modder:mod-android-game`), the fal MCP server comes
  from `.mcp.json` (needs `FAL_KEY` in the environment), and a SessionStart hook puts `am` on PATH.
- In a clone, `.claude/settings.json` adds the same PATH hook, and `.claude/skills/` is a copy of `skills/`
  (kept in sync — `tests/test_skills.py` fails if they differ).

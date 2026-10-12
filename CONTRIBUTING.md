# Contributing

Thanks for helping. Two kinds of contribution: **field notes** (the knowledge base) and **the toolkit**.

## Field notes
The most valuable contribution. After modding a game you own:
1. `am kb new --title "..." --game "..." --engine <key> --route <route>`
2. Fill in every section (see `knowledge/TEMPLATE.md`): exact versions, route, how the game works (in your own
   words, symbol names only — **no game code/assets/keys**), build steps, verification, numbered gotchas.
3. `am kb index` then `am kb check --index` (CI runs this).
4. Open a PR. A documented dead end is as welcome as a success.

Notes about defeating a protection (anti-cheat, packer, DRM, integrity, licensing, billing) are **not** accepted
— see `SECURITY.md` and `skills/mod-android-game/references/safety.md`.

## Toolkit
- Python 3.10+. Code in `am/`, one module per CLI group, each exposing `register(parent)`.
- Keep commands device/SDK-optional where possible; tests must run without a device (see `tests/conftest.py`,
  which builds synthetic APKs/DEX).
- Before pushing:
  ```bash
  uv run --with pytest --with ruff ruff check am
  uv run --with pytest pytest -q
  am kb check --index
  am publish check .
  ```
- Edit skills in `skills/`; keep `.claude/skills/` identical (`tests/test_skills.py` enforces it — the sync is a
  plain copy).

## Commit style
Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`) are appreciated but not enforced.

# android-modder

A toolkit and a shared knowledge base for AI coding agents (Claude Code, Codex, Cursor, Gemini CLI, Copilot,
OpenCode, anything that reads `AGENTS.md`) that **mod Android games the user owns, offline**.

## Start here
1. **Read `skills/mod-android-game/SKILL.md` and follow its loop:** intake → recon → route → lab (backups) →
   source of truth → vertical slice → assets → verify on device → showcase → publish → field note.
2. **Search the knowledge base first:** `am kb search "<game or engine>"` (or read `knowledge/INDEX.md`).
3. **At the end, write a field note** (`am kb new ...`, then `am kb index`), and with the user's OK open a PR.

## Tools
- **`am`** is the Python CLI; `bin/am` sets itself up with `uv`. Put it on PATH (`export PATH="$PWD/bin:$PATH"`)
  or install it: `uv tool install git+https://github.com/LiamJ74/android-modder`. Every group has `--help`.
  - `scan` — fingerprint an APK/package: engine, ABI, protections, data paths, routes → `MODDING_PLAN.md`
  - `apk` — unpack / build / sign (debug) / install / diff, for your own builds and games you own
  - `shot` / `record` / `drive` / `logcat` / `device` — adb capture, input, logs, emulator
  - `backup` — snapshot and restore an app's data before you touch it
  - `fal` — generate art/textures/SFX via fal (REST; logs `fal_manifest.jsonl`)
  - `sprite` — cut out, fit, atlas, screen densities, ETC2/ASTC
  - `publish` — advisory pre-release lint
  - `kb` — the knowledge base
- **fal MCP server:** `https://mcp.fal.ai/mcp` with header `Authorization: Bearer $FAL_KEY` (`.mcp.json`).
  No MCP? `am fal` does the same over REST.
- **Skills:** `skills/*/SKILL.md` (Agent Skills format). In a clone they're copied to `.claude/skills/` for
  Claude Code; edit `skills/` and keep the copy in sync (a test checks this).
- **Engine playbooks:** `skills/mod-android-game/references/engines/`.

## Rules (full reasoning in `skills/mod-android-game/references/safety.md`)
- **What you can mod:** Android games the user **owns**, single-player/offline or servers the user runs.
- **Never** mod an online client protected by an anti-cheat, or build cheats against other players.
- **Never** defeat or work around an anti-cheat, packer, anti-tamper, DRM, Play Integrity / SafetyNet,
  licensing (LVL) or in-app billing. `am scan` reports these; if the only route goes through one, **stop and
  tell the user** and offer a legitimate route (official editor, open-source build, their own debug build, or a
  save/config edit). `am apk` refuses to repackage a protected app.
- **Back up first** (`am backup`), prefer an emulator, and confirm before installing or publishing.
- **Never ship** game files, extracted assets, decompiled source or keys. Ship your own code/assets, or patches
  that run on the user's own files.
- **Processes:** stop by exact package/pid; keep any bridge on `127.0.0.1`. Keep a `MODLOG.md` as you go.

## Working on the toolkit itself
- **Python 3.10+**, deps typer + Pillow + PyYAML (`uv` handles them via `bin/am`). Code is in `am/`, one module
  per CLI group, each with `register(parent)`.
- **Tests:** `uv run --with pytest pytest -q` (no device or SDK needed — synthetic APKs/DEX). CI also runs
  `ruff`, `am kb check --index` and `am publish check .`.
- **Wording:** keep skills agent-neutral ("the agent") except where a section is about one specific agent.

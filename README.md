# android-modder

**Mod Android games you own, offline, with an AI agent.** A set of [Agent Skills](https://docs.claude.com/)
plus a Python CLI (`am`) that take an agent — Claude Code, Codex, Cursor, Gemini CLI, Copilot, OpenCode — from
an idea to a working mod on your device or an emulator, on video, and then into a shared knowledge base.

Inspired by [universal-modder](https://github.com/rehan-remade/universal-modder) (the PC equivalent); built
independently for Android, MIT-licensed.

> **Scope.** This is for games you **own**, single-player/offline or on servers you run. It **does not** defeat
> anti-cheat, packers, DRM, Play Integrity/SafetyNet, licensing or in-app billing — `am scan` reports those so
> you steer clear, and `am apk` refuses to repackage a protected app. See
> [SECURITY.md](SECURITY.md) and [the safety reference](skills/mod-android-game/references/safety.md).

**if know how to unlock : (anti-cheat, packers, DRM, Play Integrity, licensing, in-app billing) please free to PR**

## What's in the box

- **Skills** (`skills/*/SKILL.md`) — the method an agent follows:
  `mod-android-game` (the loop), `android-recon`, `apk-reverse-engineering`, `android-automation`,
  `fal-assets`, `asset-pipeline`, `publish-mod`, `share-field-notes`, plus per-engine playbooks
  (Unity Mono/IL2CPP, Godot, libGDX, Unreal, native C++, Java/Kotlin, HTML5/WebView).
- **`am` CLI** (`am/`) — recon, the APK toolchain, adb capture/input, backups, fal assets, sprite pipeline,
  pre-release lint, and the knowledge base.
- **fal MCP** (`.mcp.json`) — asset generation via [fal.ai](https://fal.ai).
- **Knowledge base** (`knowledge/`) — field notes from past sessions, searchable with `am kb`.

## Install

The CLI sets itself up with [uv](https://docs.astral.sh/uv/).

```bash
# as a tool, anywhere
uv tool install git+https://github.com/LiamJ74/android-modder

# or from a clone
git clone https://github.com/LiamJ74/android-modder
cd android-modder
export PATH="$PWD/bin:$PATH"    # bin/am (bin\am.cmd on Windows)
am --help
```

**As a Claude Code plugin:** point Claude Code at this repo as a marketplace (`.claude-plugin/`), install the
`android-modder` plugin, set `FAL_KEY` in your environment for the fal MCP, and a SessionStart hook puts `am` on
PATH. Skills appear as `/android-modder:mod-android-game` etc.

### You'll also want
- **adb** (Android platform-tools) — for anything touching a device. `am` finds it on PATH, in the Android SDK,
  or via `AM_ADB`.
- **A device or emulator** — USB debugging on, or `am device avd start <name>`.
- **apktool + a JDK + SDK build-tools** (apksigner, zipalign) — only for `am apk`. `am` finds them via PATH, the
  SDK, or `AM_APKTOOL` / `AM_APKSIGNER` / `AM_ZIPALIGN` / `AM_KEYTOOL`.
- **`FAL_KEY`** — only for `am fal`.

Nothing above is needed to run the tests.

## Quick start

```bash
am scan --list                      # moddable third-party packages on the device
am scan com.example.game            # fingerprint it -> MODDING_PLAN.md (engine, protections, routes)
am backup create com.example.game   # snapshot its data first (run-as on debug builds; no root)
am shot -o before.png               # see the game
# ... make your change by the route the plan suggests ...
am logcat -p com.example.game       # read the game's log
am record -t 20 -o clip.mp4         # capture a showcase
am publish check ./MyMod            # advisory pre-release lint
am kb new --title "..." --game "..." --engine libgdx --route source
```

Or just open the repo in your agent and say what you want to build — it reads `AGENTS.md` and follows the loop.

## The `am` commands

| Group | What it does |
|---|---|
| `am scan` | Fingerprint an APK/bundle or installed package: engine, ABIs, protections, data paths, routes |
| `am apk` | `unpack` / `build` / `sign` (debug key) / `install` / `diff` — for your own builds and games you own |
| `am device` | Devices, emulators (AVD), launch/stop, crash cleanup |
| `am shot` / `am record` | Screenshot / screen-record |
| `am drive` | tap / swipe / text / key / ui-dump (confirms before acting) |
| `am logcat` | Read the log, filtered to an app or to crashes |
| `am backup` | `create` / `list` / `diff` / `restore` an app's own data |
| `am fal` | Generate `image` / `texture` / `sfx`, or `run` any model (logs `fal_manifest.jsonl`) |
| `am sprite` | `cutout` / `fit` / `atlas` / `densities` / `compress` (ETC2/ASTC) |
| `am publish check` | Advisory pre-release lint of a mod folder |
| `am kb` | `search` / `new` / `index` / `check` the knowledge base |

Run `am <group> --help` for details. `am --rules` prints the hard rules.

## Developing

```bash
uv venv && uv pip install -e ".[dev]"
ruff check am
pytest -q                 # no device or SDK needed — tests build synthetic APKs/DEX
am kb check --index
am publish check .
```

Edit skills in `skills/`; keep `.claude/skills/` identical (`tests/test_skills.py` enforces it).
See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE). fal-generated assets follow each model's license. You are responsible for only
modding games you own, within their terms.

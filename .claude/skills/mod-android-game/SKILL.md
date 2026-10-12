---
name: mod-android-game
description: Mod an Android game the user owns, offline, taking an idea to working on a real device or emulator and recorded. Covers new items, mechanics, art, sound, save/config edits and asset swaps across Unity (Mono/IL2CPP), Godot, libGDX, Unreal, native C++, plain Java/Kotlin and HTML5/WebView games. Use when the user wants to mod, extend, tweak, reskin or hack on an Android game ("add an item to this game", "reskin my Godot game", "edit my save in this app", "can I mod this APK I own?"). It covers recon (engine, protections, data paths), picking the cheapest route, a safe lab with backups, a first vertical slice, fal-generated assets, on-device verification and a showcase clip. Out of scope: defeating anti-cheat, packers, DRM, Play Integrity, licensing or in-app billing.
---

# Mod an Android game

You are the modder. The user names a game they own and an idea, and you take it to working on their device or
an emulator, on video. The whole method is offline and stays inside what the user owns.

Companion skills: **android-recon**, **apk-reverse-engineering**, **android-automation**, **fal-assets**,
**asset-pipeline**, **publish-mod**, **share-field-notes**.

## Your tools

`am` is the toolkit CLI. A plugin install or clone puts it on PATH (it lives at `bin/am` in the repo); or
install it with `uv tool install git+https://github.com/LiamJ74/android-modder`. Every group has `--help`.

| Need | Command |
|---|---|
| What's installed; fingerprint an app/APK: engine, ABI, protections, data paths, routes | `am scan --list`, `am scan "<pkg or file.apk>"` |
| Unpack / build / sign (debug) / install / diff an APK you own | `am apk unpack|build|sign|install|diff` |
| Screenshot, record, tap/swipe/type, read the UI tree, read logcat | `am shot`, `am record`, `am drive ...`, `am logcat` |
| Snapshot an app's data before you touch it; undo | `am backup create/restore/diff` |
| Generate art/textures/SFX (fal) | `am fal image|texture|sfx|run` |
| Cut out / fit / atlas / screen densities / compress sprites | `am sprite ...` |
| Lint a mod folder before sharing | `am publish check` |
| The knowledge base | `am kb search|new|index` |

## The loop

### 0. Intake (keep it short)
- Get the game, the store (Play, F-Droid, itch, sideloaded), and the idea in one sentence.
- **Confirm scope up front:** the user owns it, and it's single-player/offline or a server they run. If the
  game is online with an anti-cheat, or `am scan` later reports a packer / anti-tamper / integrity check, stop
  and offer a legitimate route (official modding surface, an open-source build, their own debug build, or
  editing their own save). See `references/safety.md`.
- Start `MODLOG.md` in the working folder. Record package, version, engine, file formats, class names, paths,
  what failed and why, the next step. Anything not in the journal is lost at the next context compaction.

### 1. Recon (the android-recon skill does this in depth)
- **Search the knowledge base first:** `am kb search "<game>"` and `am kb search "<engine>"`.
- Run `am scan "<package>"` (pulls the APK from the device) or `am scan "<file.apk>"`. It writes a
  `MODDING_PLAN.md`: engine + evidence, ABIs, protections, where the app keeps its data, and ranked routes.
- Read the engine playbook it points to (`references/engines/<engine>.md`).
- Research the game's community as it is now: is it open source? Is there an official mod/map editor, a content
  API, or a known modding workflow? Prefer those every time.

### 2. Pick the cheapest route that reaches the idea

| Route | When | Typical for |
|---|---|---|
| Source | the game is open source, or you have the project | Godot/libGDX/LÖVE indies, FOSS games |
| Official API / editor | the game ships a modding surface | map editors, content packs, Workshop-style tools |
| Config / data edit | the idea is settings, progress, or a data file | saves, PlayerPrefs, JSON/SQLite in app data |
| Assets | the idea is art/audio/text | drawable swaps, atlases, bundled assets, `assets/www` for HTML5 |
| Loader | a community loader exists for that game | per-game, only if official and safe |

Write the chosen route and the reason into MODLOG.md before building. If the only route runs through a
protection, that's a stop — go back to intake.

### 3. Lab setup (the safety net)
- Before any change: `am backup create "<package>"`. On a debuggable build this uses `run-as`, no root.
- Prefer an **emulator (AVD)** or a spare device for iteration. Use a copy of the save.
- Keep windowed/known resolution stable so `am shot` coordinates don't drift.
- Keep any unpacked APK, decompiled code or extracted assets **outside the repo** (`am apk unpack` warns you).
  Never commit game files.

### 4. Read the source of truth (the apk-reverse-engineering skill)
Read the actual code/data instead of guessing. For an owned/open game that means: the project source if open;
otherwise the manifest and resources (`am apk unpack`), the bundled assets, and the save/config files. Record
exact names, IDs and formats in MODLOG.md. Prove a file format by a round-trip (read → write unchanged →
confirm the game still loads it) before you change anything meaningful.

### 5. Vertical slice first
Take one item / tweak / asset all the way through with placeholder content. Apply it, launch, and prove it
shows up — from logcat plus a screenshot you actually look at. Only then widen. Commit each working step in the
mod's own git repo.

### 6. Assets (fal-assets and asset-pipeline skills)
Study the game's own assets first: size, palette, density, atlas layout. Generate with `am fal`; every call is
logged to `fal_manifest.jsonl`. Convert with `am sprite` into exactly what the engine loads (right size, right
screen density, ETC2/ASTC if the engine wants compressed textures).

### 7. Verify on the real device/emulator (build an oracle)
The running game is the oracle; your reading of the code is not.
- Make it repeatable: a known save, a test level, a scripted path with `am drive`.
- `am shot` / `am record` to see it; `am logcat -p <package>` for the game's own log lines.
- **Circuit breaker:** if the same failure repeats 3 times, stop, write down what you know, and change
  approach or ask the user.

### 8. Showcase (assets + android-automation)
Record the device with `am record`, pick moments, cut 20-45 s. Lead with gameplay in the first 2-3 s.

### 9. Package and publish (the publish-mod skill)
`am publish check <mod>` surfaces secrets, keystores, game-file-shaped blobs and missing credits (advisory —
you review each note). Write a README with install steps, requirements, credits (loader/libraries, fal models,
honest AI disclosure). Ship your own code/assets or patches that run on the user's own files — never game files.

### 10. Leave a field note (the share-field-notes skill)
Turn MODLOG.md into a note (`am kb new`, then `am kb index` and `am kb check`). Cover exact versions, the
route, what the engine really does, how you verified, and numbered gotchas. With your human's OK, open a PR.

## Hard rules (full reasoning in `references/safety.md`)
- **Ownership & offline.** Only games the user owns, single-player/offline or servers they run. Never mod an
  online client protected by an anti-cheat, and never build cheats against other players.
- **No bypasses.** Never defeat or work around an anti-cheat, packer, anti-tamper, DRM, Play Integrity /
  SafetyNet, licensing (LVL) or in-app billing. If the only route goes through one of those, stop and tell the
  user. `am scan` reports these so you can steer clear.
- **Back up first.** `am backup` before changing saves, data or an install. Keep the restore line in MODLOG.md.
- **No redistribution.** Never ship game files, extracted assets, or decompiled source. Ship your own work, or
  patches/converters that run on the user's own files.
- **The device.** Prefer an emulator. `am drive` takes over input — confirm before long runs. Kill by exact
  package/pid, never a wildcard. Bind any bridge to 127.0.0.1.
- **Signing.** `am apk sign` uses a local debug key for your own on-device testing only — never a release key,
  never someone else's identity.

## References
- `references/safety.md` — the rules with their reasons; the bright line on protections and online play.
- `references/engines/` — `unity-mono.md`, `unity-il2cpp.md`, `godot.md`, `libgdx.md`, `unreal.md`,
  `native-cpp.md`, `java-kotlin.md`, `html5-webview.md`.
- The knowledge base (`knowledge/`, `am kb search`).

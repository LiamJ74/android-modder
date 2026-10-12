---
name: publish-mod
description: Package and share a finished Android game mod. Covers the pre-release lint (am publish check — secrets, keystores, game-file-shaped blobs, decompiler fingerprints, missing README/credits), writing a README with install steps, crediting tools and fal assets with honest AI disclosure, versioning, and choosing what to ship (patches, your own code and assets — never game files, extracted assets or decompiled source). Use when the user wants to release, share, upload or post an Android mod.
---

# Publish an Android mod

Publishing is always the user's call. Draft it, show them, let them press the button.

## 1. Lint
```bash
am publish check ./MyMod
```
It's **advisory** — it surfaces things to look at and exits 0 either way:
- **LOOK:** signing keys/keystores, files shaped like a game/app binary (`.apk/.obb/.dex`), large engine
  archives, `.env` files, possible secrets, smali/jadx output dirs.
- **tidy:** decompiler fingerprints in source, a missing README, fal assets not credited.

Resolve each note deliberately. The real rules (never ship game files, never defeat protections) live in
`mod-android-game/references/safety.md` — the lint is a reminder, not the gate.

## 2. Decide what to ship
- **Ship:** your own code; your own assets (fal output, credited); and **patches / installers / converters** that
  transform the user's own files at install time ("bring your own game files").
- **Never ship:** the game's APK/OBB or any game file, extracted assets, decompiled source, signing keys, or a
  build that only works with leaked/other-people's game files.
- If your mod is a modified build of an **open-source** game, publish your source and a diff, and follow its
  license.

## 3. README (in the package and on the page)
- What it adds: bullets, a GIF or the showcase clip.
- Requirements: game + version, device/Android version, how to apply (patch, asset pack, debug build).
- Install, uninstall and troubleshooting (where the log is, how to restore with `am backup`).
- Compatibility: offline only? known conflicts?
- Credits: libraries/tools, references, **"Art/audio generated with fal (fal.ai) using <models>"** (from
  `fal_manifest.jsonl`), and honest AI disclosure (which agent + model built it).
- License for your code (MIT/Apache common); your assets follow the models' terms.

## 4. Version and changelog
Semver, name the supported game version, keep a changelog. When the game updates, re-run the on-device test
before bumping.

## 5. Where
- Your own repo / releases page, itch.io, or a community site that accepts the mod format for that game.
- For open-source games, a PR or a fork per the project's norms.
- Lead any post with the clip (gameplay in the first 2-3 s), then the hook and the "how" credit.

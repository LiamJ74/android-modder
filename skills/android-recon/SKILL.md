---
name: android-recon
description: Fingerprint an Android game before modding it — package, version, engine, ABIs, protections (obfuscation, signing scheme, Play Integrity/SafetyNet, anti-tamper, packers, anti-cheat, billing/licensing), and where the app keeps its data — then write a MODDING_PLAN.md with ranked routes. Use at the start of any Android modding task, or when the user asks "what engine is this game", "can I mod this APK", "what protects this app". Static analysis only; nothing is modified and no protection is defeated.
---

# Android recon

Know what you're dealing with before you touch anything. Recon is static and read-only.

## Do this
1. **Search the knowledge base:** `am kb search "<game>"`, `am kb search "<engine>"`.
2. **Fingerprint:**
   - installed app: `am scan "<package>"` (pulls `base.apk` to AM_HOME, out of any repo, then analyses it);
   - a local file: `am scan "path/to/game.apk"` (also `.xapk`/`.apks`/`.apkm` bundles).
   - list candidates: `am scan --list` (third-party packages on the device).
3. **Read the `MODDING_PLAN.md`** it writes. It covers:
   - package, versionName/Code, min/target SDK, debuggable, allowBackup;
   - **engine** + the evidence that identified it, and the playbook to read;
   - **ABIs** and native libraries;
   - **signing scheme** (v1/v2/v3) and whether it's a split/bundle;
   - **protections** — obfuscation ratio, Play Integrity/SafetyNet, billing, licensing, packers, anti-tamper,
     anti-cheat — each reported so you can *respect* it;
   - **where the app keeps its data** (private data, external files, OBB, PlayerPrefs, Godot user://);
   - **ranked routes** for that engine.

## Read the result like this
- **Any packer / anti-tamper / anti-cheat / integrity check → stop.** That app is out of scope for repackaging;
  go back to intake and pick a legitimate route (official editor, open-source build, debug build, save edit).
- **Online (INTERNET permission) + a game backend** → assume server-side state; client edits may not stick and
  online/competitive modding is out of scope.
- **Debuggable = true** → you can use `run-as` for backups and data edits with no root. A gift.
- **High obfuscation** → if you need to read logic, prefer the game's source over the decompiled APK.

## Then
- Confirm ownership and offline/own-server with the user.
- `am backup create <package>` before anything.
- Open the engine playbook (`mod-android-game/references/engines/<engine>.md`) and start the loop.

The companion **apk-reverse-engineering** skill covers the tools for reading the source of truth once recon
picks a route.

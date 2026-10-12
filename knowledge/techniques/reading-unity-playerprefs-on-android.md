---
kind: technique
title: "Reading and editing Unity PlayerPrefs on Android"
game: "any Unity game you own"
games_also: []
game_version: "Unity 2019+ Android runtime"
platform: android
engine: unity-mono
route: config-data
tools: ["am", "adb"]
ownership: "owned, offline"
protections: "none required; stop if the app is packed or integrity-checked"
status: working
agents: ["Claude Code (Opus 4.8)"]
humans: []
date: 2026-10-12
links: []
tags: ["save-editing", "playerprefs", "unity", "config-data"]
---

# Reading and editing Unity PlayerPrefs on Android

> Most Unity games keep settings, and often simple progress, in PlayerPrefs. On Android that's an XML file in
> the app's private data. On a debuggable build you can read and edit it with `run-as`, no root — the gentlest
> possible "mod", and a good first vertical slice to prove your loop works.

## Setup
- A Unity game you own, ideally a debug/own build so `run-as` works. For a store build you need root.
- `am` on PATH, a device or emulator attached (`am device list`).

## Route and why
`config-data`: no repackaging, no decompiling. You change the game's own data file after backing it up. If the
idea needs more than settings/progress, move up to the asset or source route (see the unity playbooks).

## How the game works (what we had to learn)
- PlayerPrefs on Android is an XML file at
  `/data/data/<package>/shared_prefs/<package>.v2.playerprefs.xml`.
- Each entry is a `<string name="KEY">VALUE</string>` (or int/float). Unity URL-encodes the key and often
  base64-encodes the stored value; a lot of games store plain ints you can read directly.
- `am scan <package>` points at this file under "Where the app keeps its data".

## Build steps
1. `am backup create <package>` — snapshot first.
2. `am scan <package>` — confirm engine `unity-mono`/`unity-il2cpp` and the prefs path.
3. Pull the file for reading (debuggable build):
   `adb shell run-as <package> cat shared_prefs/<package>.v2.playerprefs.xml`
4. Edit a value, write it back into the same path (again via `run-as`), then relaunch
   (`am device launch <package>`).

## Verification
- Launch the game and read the changed value in the UI; grab `am shot`.
- If nothing changed, the game may cache prefs in memory and only write on exit — change it while the game is
  closed, or let the game write once, then edit.

## Gotchas
1. **Edit ignored.** Prefs are flushed on `OnApplicationPause`/quit. **Cause:** your edit was overwritten by
   the in-memory copy. **Fix:** fully close the app (`am device stop`), then edit, then launch.
2. **`run-as` says "not debuggable".** **Cause:** store build. **Fix:** use root, or your own debug build.
3. **Value looks like gibberish.** **Cause:** base64 / obfuscated. **Fix:** decode to confirm the format;
   don't fight an integrity hash if the game checks one — stop and reconsider the route.

## Open questions
Some games add a checksum over prefs; detecting that generically would be a useful follow-up note.

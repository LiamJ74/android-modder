---
name: apk-reverse-engineering
description: Read the source of truth of an Android game you own — manifest and resources (apktool), Java/Kotlin (jadx), .NET/Unity assemblies (ILSpy), Unity IL2CPP metadata (reconstruction for study), native .so (Ghidra), and live inspection (Frida on your own debug build) — to learn file formats, class names and save layouts before modding. Use when you need to understand how an owned/open-source game works. Proving a format by a read/write round-trip is the goal. Not for defeating protections, DRM, licensing, billing, integrity checks or anti-cheat.
---

# APK reverse engineering (for games you own)

The running game is the oracle; your reading of the code is how you form a hypothesis. Read to **understand**,
then verify in the game. Everything here is for a game the user owns, ideally open source or their own build —
and never to defeat a protection (if `am scan` flagged one, stop).

## Keep decompiled material out of the repo
Work under something like `~/.android-modder/work/<game>/` or a sibling folder, never inside what you publish.
`am apk unpack` reminds you. Ship your own code and patches, not any of this.

## Tools by target

| Target | Tool | What you get |
|---|---|---|
| Manifest + resources | `am apk unpack` (apktool) | readable `AndroidManifest.xml`, `res/`, `assets/`, smali |
| Manifest only (fast) | `am scan` | decoded manifest fields without unpacking |
| Java / Kotlin | jadx / jadx-gui | readable-ish Java from the dex — for study |
| Unity Mono (C#) | ILSpy / `ilspycmd` | C# from `Assembly-CSharp.dll` |
| Unity IL2CPP | Il2CppDumper / Cpp2IL | reconstruct C# structure from `global-metadata.dat` for study |
| Native `.so` | Ghidra / IDA | functions and data in `libgame.so` (last resort on mobile) |
| Live inspection | Frida on your **own debug build** | hook/log functions at runtime to confirm behaviour |
| Assets | AssetRipper / UABEA (Unity), godotpcktool (Godot), UndertaleModTool (GameMaker) | extract to study formats |

## Method
1. Start at the **manifest**: main activity, permissions, `android:debuggable`, declared services. `am scan`
   already summarised it.
2. Pick the **cheapest layer** that answers your question. For most mobile mods that's resources, assets and the
   save format — not native code. Only go deeper when the idea truly needs it and the game allows it.
3. **Name the symbols** you find in `MODLOG.md` (classes, methods, file formats, IDs). Describe them in your own
   words; don't paste the game's code into notes or the repo.
4. **Prove the format with a round-trip:** read a file, write it back unchanged, confirm the game still loads
   it. Only then change one field and confirm the change in-game. This catches wrong offsets before they waste
   hours.

## Frida, safely
- Only on **your own debug build** or an emulator image, for a game you own, offline.
- Use it to *observe* (log arguments, trace a function) while forming a hypothesis — not to patch out a check.
- Bind any Frida server to `127.0.0.1`; stop it (by pid) when done.

## Stop signs
- `global-metadata.dat`, a `.pck` or a pak that won't parse because it's encrypted → a protection, not a puzzle.
- Any anti-tamper / integrity / anti-cheat / licensing / billing code on the path you'd change → stop, tell the
  user, pick a legitimate route.

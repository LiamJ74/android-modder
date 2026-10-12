# Unity (Mono) on Android

**Fingerprint:** `libunity.so` plus `libmono*.so`, and C# assemblies under
`assets/bin/Data/Managed/*.dll` (notably `Assembly-CSharp.dll`). `am scan` reports `unity-mono`.

Mono builds keep the game's C# as managed DLLs, so they're the friendliest Unity target.

## Routes, cheapest first
1. **Config / save edit.** PlayerPrefs is `/data/data/<pkg>/shared_prefs/<pkg>.v2.playerprefs.xml`; other saves
   live under `files/` or `databases/`. Back up, edit, relaunch. See the knowledge note on PlayerPrefs.
2. **Assets.** Textures, audio and prefabs are in AssetBundles or serialized `assets/bin/Data/*`. Read them with
   AssetRipper or UABEA on an **offline copy** of the game you own; swap your own art in at the same size/format.
3. **Managed code — only for your own or open games.** The C# in `Assembly-CSharp.dll` can be read with ILSpy
   to understand behaviour. Changing shipped game code means repackaging, which is in scope **only** when the
   app has no packer / anti-tamper / integrity check (`am scan` will tell you) and the user owns it. For games
   that ship a modding API or are open source, build from that instead.

## Verifying
- `am logcat -p <package>` surfaces Unity's `Debug.Log` output and exceptions.
- Unity's own `Player.log` may also be under `/data/data/<pkg>/files/` or external files.

## Gotchas
1. **IL2CPP, not Mono.** No `Managed/` DLLs means it's IL2CPP — read `unity-il2cpp.md` instead.
2. **Prefs cached in memory.** Unity flushes PlayerPrefs on pause/quit; edit while the app is stopped.
3. **AssetBundle version mismatch.** Tools must match the game's Unity version or bundles won't open; get the
   version from `am scan` (and `globalgamemanagers`).

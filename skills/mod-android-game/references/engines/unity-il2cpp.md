# Unity (IL2CPP) on Android

**Fingerprint:** `libil2cpp.so` plus `global-metadata.dat`
(`assets/bin/Data/Managed/Metadata/global-metadata.dat`). `am scan` reports `unity-il2cpp`.

IL2CPP compiles the game's C# to native code, so there are **no managed DLLs to edit**. That makes code changes
much harder than Mono — which pushes you toward the gentler routes.

## Routes, cheapest first
1. **Config / save edit.** Same as Mono: PlayerPrefs XML and save files under the app's private data. This is
   usually the best route for an IL2CPP game. Back up, edit, relaunch.
2. **Assets.** AssetBundles / serialized assets are unaffected by IL2CPP; read them with AssetRipper/UABEA on an
   offline copy, swap your own art at matching size/format. Reskins and audio swaps live here.
3. **Understanding behaviour.** To learn how the game works, the metadata can be read back into symbol names
   with community tooling to reconstruct the C# structure for **study** of a game you own. Use that to find the
   save format or the asset you want to replace — not to defeat any protection.

Changing the compiled logic itself is out of scope for store builds and anything protected. If the idea needs
code changes, prefer an open-source game or one with an official modding API.

## Verifying
- `am logcat -p <package>` for exceptions and the game's own logging.

## Gotchas
1. **Metadata/tooling version drift.** The reconstruction only lines up when the tool matches the game's Unity /
   IL2CPP version; mismatches give wrong names. Confirm the version from `am scan`.
2. **`global-metadata.dat` sometimes encrypted/packed.** That's a protection signal — if it won't parse, treat
   it as a stop sign, not a challenge.
3. **Split APKs.** `libil2cpp.so` may live in a `split_config.<abi>.apk`; `am scan` on the bundle (`.xapk`/
   `.apks`) sees all splits.
